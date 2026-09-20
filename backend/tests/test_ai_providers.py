import os
import json
import asyncio
import unittest
from unittest.mock import MagicMock, patch

from app.ai.mock_provider import MockAIProvider
from app.ai.bedrock_provider import BedrockAIProvider
from app.ai.factory import get_ai_provider
from app.ai.exceptions import (
    BedrockConfigurationError,
    BedrockInferenceError,
    BedrockExtractionError
)
from app.models.ai_extraction import AIExtractionResult
from app.policy.engine import PolicyEngine
from app.models.enums import CaseStatus, Priority

def is_aws_available() -> bool:
    """Check if real AWS credentials and ap-south-1 Bedrock access are genuinely available."""
    try:
        import boto3
        region = os.getenv("AWS_REGION", "ap-south-1")
        sts = boto3.client("sts", region_name=region)
        sts.get_caller_identity()
        return True
    except Exception:
        return False

class TestAIProviders(unittest.TestCase):

    def setUp(self):
        self.sample_notes = (
            "I handled the replacement request from Priya. Customer sent the damaged product photos yesterday. "
            "I already contacted warehouse and they said they should confirm stock by tomorrow. "
            "I promised the customer that I would update her by Friday. "
            "For the invoice correction, finance hasn't approved the change yet. I sent them the updated invoice this morning. "
            "If they don't respond today, someone should follow up. "
            "Also there is one issue with order #8821. Customer says they received the wrong item but the warehouse "
            "system shows the correct SKU. I haven't figured out which one is correct yet."
        )
        self.nova_sample_notes = (
            "Payment API integration is complete. Webhook handling is still pending. "
            "Finance has not approved the discount yet. I promised the client the revised version before Friday. "
            "Follow up with Finance and finish webhook validation."
        )

    def test_mock_provider_works_and_validates_schema(self):
        """MockAIProvider continues to work and returns valid AIExtractionResult."""
        provider = MockAIProvider()
        result = asyncio.run(provider.extract_work_state(self.sample_notes))
        
        self.assertIsInstance(result, AIExtractionResult)
        self.assertGreater(len(result.completed), 0)
        self.assertGreater(len(result.unresolved), 0)
        self.assertGreater(len(result.commitments), 0)
        self.assertGreater(len(result.blockers), 0)
        self.assertGreater(len(result.exceptions), 0)
        self.assertGreater(len(result.next_actions), 0)

    def test_bedrock_provider_initialization_with_nova_2_lite(self):
        """Requirement 13A: Bedrock provider initializes correctly with Nova 2 Lite default."""
        with patch.dict(os.environ, {"BEDROCK_MODEL_ID": "global.amazon.nova-2-lite-v1:0"}):
            provider = BedrockAIProvider(region="ap-south-1")
            self.assertEqual(provider.region, "ap-south-1")
            self.assertEqual(provider.model_id, "global.amazon.nova-2-lite-v1:0")

    def test_missing_bedrock_model_id_raises_configuration_error(self):
        """Missing BEDROCK_MODEL_ID produces a clear BedrockConfigurationError."""
        provider = BedrockAIProvider(region="ap-south-1", model_id="")
        with self.assertRaises(BedrockConfigurationError) as ctx:
            asyncio.run(provider.extract_work_state(self.sample_notes))
        self.assertIn("BEDROCK_MODEL_ID is not configured", str(ctx.exception))

    def test_bedrock_provider_passes_correct_model_id_and_parses_json(self):
        """Requirement 13B, 13C, 13D, 13E: Correct model ID passed to Converse, text extracted, JSON parsed, Pydantic validated."""
        mock_facts = {
            "completed": [
                {"case_hint": None, "title": "Payment API integration", "description": "Payment API integration is complete"}
            ],
            "unresolved": [
                {"case_hint": None, "title": "Webhook handling", "description": "Webhook handling is still pending"}
            ],
            "commitments": [
                {"case_hint": None, "description": "Promised revised version", "committed_to": "client", "expected_date": "Friday"}
            ],
            "blockers": [
                {"case_hint": None, "description": "Discount approval", "blocked_by": "Finance"}
            ],
            "deadlines": [
                {"case_hint": None, "description": "Revised version delivery", "date_str": "Friday"}
            ],
            "exceptions": [],
            "next_actions": [
                {"case_hint": None, "action": "Follow up with Finance", "assignee": None},
                {"case_hint": None, "action": "finish webhook validation", "assignee": None}
            ]
        }

        mock_client = MagicMock()
        # Nova typically returns JSON wrapped in markdown code blocks
        raw_nova_response = f"```json\n{json.dumps(mock_facts, indent=2)}\n```"
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [
                        {"text": raw_nova_response}
                    ]
                }
            }
        }

        provider = BedrockAIProvider(
            region="ap-south-1",
            model_id="global.amazon.nova-2-lite-v1:0",
            client=mock_client
        )
        result = asyncio.run(provider.extract_work_state(self.sample_notes))

        # 13B: Verify correct model ID passed to Converse
        mock_client.converse.assert_called_once()
        call_kwargs = mock_client.converse.call_args.kwargs
        self.assertEqual(call_kwargs["modelId"], "global.amazon.nova-2-lite-v1:0")
        self.assertIn("inferenceConfig", call_kwargs)
        self.assertIn("messages", call_kwargs)
        self.assertIn("system", call_kwargs)

        # 13C, 13D, 13E: Verify result parsed and validated against Pydantic schema
        self.assertIsInstance(result, AIExtractionResult)
        self.assertEqual(len(result.completed), 1)
        self.assertEqual(result.completed[0].title, "Payment API integration")
        self.assertEqual(len(result.unresolved), 1)
        self.assertEqual(result.unresolved[0].title, "Webhook handling")
        self.assertEqual(len(result.commitments), 1)
        self.assertEqual(result.commitments[0].committed_to, "client")
        self.assertEqual(len(result.blockers), 1)
        self.assertEqual(result.blockers[0].blocked_by, "Finance")
        self.assertEqual(len(result.deadlines), 1)
        self.assertEqual(result.deadlines[0].date_str, "Friday")
        self.assertEqual(len(result.next_actions), 2)

    def test_bedrock_provider_malformed_json_raises_extraction_error(self):
        """Requirement 13F: Malformed AI output raises BedrockExtractionError."""
        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [
                        {"text": "I am an AI and here is your summary: Completed: Payment API"}
                    ]
                }
            }
        }

        provider = BedrockAIProvider(
            region="ap-south-1",
            model_id="global.amazon.nova-2-lite-v1:0",
            client=mock_client
        )
        with self.assertRaises(BedrockExtractionError) as ctx:
            asyncio.run(provider.extract_work_state(self.sample_notes))
        self.assertIn("No JSON object found", str(ctx.exception))

    def test_bedrock_provider_schema_mismatch_raises_extraction_error(self):
        """Requirement 13F: Schema mismatch (e.g. string instead of list) raises BedrockExtractionError."""
        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [
                        {"text": '{"completed": "not-a-list", "unresolved": []}'}
                    ]
                }
            }
        }

        provider = BedrockAIProvider(
            region="ap-south-1",
            model_id="global.amazon.nova-2-lite-v1:0",
            client=mock_client
        )
        with self.assertRaises(BedrockExtractionError) as ctx:
            asyncio.run(provider.extract_work_state(self.sample_notes))
        self.assertIn("Schema validation failed", str(ctx.exception))

    def test_bedrock_provider_inference_failure_raises_inference_error(self):
        """Requirement 13G: Bedrock inference failures raise BedrockInferenceError."""
        mock_client = MagicMock()
        mock_client.converse.side_effect = Exception("ServiceUnavailableException: Bedrock runtime down")

        provider = BedrockAIProvider(
            region="ap-south-1",
            model_id="global.amazon.nova-2-lite-v1:0",
            client=mock_client
        )
        with self.assertRaises(BedrockInferenceError) as ctx:
            asyncio.run(provider.extract_work_state(self.sample_notes))
        self.assertIn("Bedrock Converse invocation failed", str(ctx.exception))

    def test_no_mock_fallback_when_ai_provider_bedrock(self):
        """Requirement 13H: No mock fallback occurs when AI_PROVIDER=bedrock."""
        with patch.dict(os.environ, {"AI_PROVIDER": "bedrock", "BEDROCK_MODEL_ID": "global.amazon.nova-2-lite-v1:0"}):
            provider = get_ai_provider()
            self.assertIsInstance(provider, BedrockAIProvider)
            self.assertNotIsInstance(provider, MockAIProvider)

    @unittest.skipUnless(is_aws_available(), "Real AWS credentials not available in environment")
    def test_real_bedrock_nova_2_lite_integration(self):
        """Requirement 14 & 15: Real Amazon Bedrock Nova 2 Lite integration test in ap-south-1."""
        provider = BedrockAIProvider(
            region="ap-south-1",
            model_id="global.amazon.nova-2-lite-v1:0"
        )
        
        test_notes = (
            "Payment API integration is complete. Webhook handling is still pending. "
            "Finance has not approved the discount yet. I promised the client the revised version before Friday. "
            "Follow up with Finance and finish webhook validation."
        )

        result: AIExtractionResult = asyncio.run(provider.extract_work_state(test_notes))

        # Verify AIExtractionResult instance
        self.assertIsInstance(result, AIExtractionResult)

        # Semantic validations:
        # Completed: Payment API integration
        completed_titles = " ".join(c.title.lower() + " " + (c.description or "").lower() for c in result.completed)
        self.assertTrue(
            "payment" in completed_titles or "api" in completed_titles,
            f"Expected completed work to mention payment/API, got: {completed_titles}"
        )

        # Unresolved: Webhook handling
        unresolved_titles = " ".join(u.title.lower() + " " + (u.description or "").lower() for u in result.unresolved)
        self.assertTrue(
            "webhook" in unresolved_titles or "pending" in unresolved_titles,
            f"Expected unresolved work to mention webhook, got: {unresolved_titles}"
        )

        # Blocker: Finance approval
        blocker_descriptions = " ".join((b.description.lower() + " " + b.blocked_by.lower()) for b in result.blockers)
        self.assertTrue(
            "finance" in blocker_descriptions or "discount" in blocker_descriptions,
            f"Expected blocker to mention Finance or discount, got: {blocker_descriptions}"
        )

        # Commitment / Deadline: revised version before Friday
        commitment_or_deadline = " ".join(
            [c.description.lower() + " " + (c.expected_date or "").lower() for c in result.commitments] +
            [d.description.lower() + " " + d.date_str.lower() for d in result.deadlines]
        )
        self.assertTrue(
            "friday" in commitment_or_deadline or "revised" in commitment_or_deadline,
            f"Expected commitment/deadline to mention Friday or revised version, got: {commitment_or_deadline}"
        )

        # Next action: follow up with Finance / finish webhook validation
        actions = " ".join(n.action.lower() for n in result.next_actions)
        self.assertTrue(
            "finance" in actions or "webhook" in actions,
            f"Expected next action to mention Finance or webhook, got: {actions}"
        )

    def test_policy_engine_enforces_status_from_facts(self):
        """Deterministic policy engine evaluates status based on facts, not AI opinion."""
        # Blocker + approaching deadline -> AT_RISK
        status, priority, rationale = PolicyEngine.evaluate_status(
            is_completed=False,
            has_exception=False,
            has_active_blocker=True,
            deadline_str="Today",
            is_unfinished=True
        )
        self.assertEqual(status, CaseStatus.AT_RISK)
        self.assertEqual(priority, Priority.HIGH)

        # Exception -> EXCEPTION
        status, priority, _ = PolicyEngine.evaluate_status(
            is_completed=False,
            has_exception=True,
            has_active_blocker=False,
            deadline_str=None,
            is_unfinished=True
        )
        self.assertEqual(status, CaseStatus.EXCEPTION)

        # Completed -> RESOLVED
        status, priority, _ = PolicyEngine.evaluate_status(
            is_completed=True,
            has_exception=False,
            has_active_blocker=False,
            deadline_str=None,
            is_unfinished=False
        )
        self.assertEqual(status, CaseStatus.RESOLVED)

if __name__ == "__main__":
    unittest.main()
