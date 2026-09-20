import os
import json
import logging
from typing import Optional
from app.ai.provider import AIProvider
from app.models.ai_extraction import AIExtractionResult
from app.ai.exceptions import (
    BedrockError,
    BedrockConfigurationError,
    BedrockInferenceError,
    BedrockExtractionError
)

logger = logging.getLogger("continuity.bedrock")

EXTRACTION_SYSTEM_PROMPT = """You are an expert workplace operational context extractor for the CONTINUITY system.
Your job is to extract verifiable operational facts from messy handoff notes (e.g. chats, emails, tickets).

CRITICAL EXTRACTION RULES:
1. Extract ONLY facts explicitly stated in the handoff text.
2. Do NOT summarize or add filler commentary.
3. Do NOT invent, assume, or guess:
   - deadlines (if no deadline is stated, do not create one)
   - owners (if no owner is stated, leave it empty)
   - commitments (only include explicit promises made to customers/stakeholders)
   - statuses or priorities (do NOT classify as AT_RISK, UNRESOLVED, RESOLVED; deterministic code will do that)
4. Identify conflicts and discrepancies explicitly as 'exceptions':
   - 'expected': What was supposed to happen or what system records indicate.
   - 'found': What was actually reported or received.
   - 'evidence': The conflict between records/statements.
   - 'required_action': The immediate investigative step needed.
   - DO NOT decide whether the customer, employee, or warehouse is correct.
5. If information for any category is not mentioned, return an empty array for that category.
6. Output ONLY a single, valid JSON object matching the requested schema. Do not enclose in markdown code blocks or add preambles.
"""

EXTRACTION_USER_PROMPT_TEMPLATE = """Extract structured operational facts from the following workplace handoff notes into JSON.

JSON SCHEMA:
{{
  "completed": [
    {{"case_hint": "optional related case/order ID or null", "title": "deliverable completed", "description": "details"}}
  ],
  "unresolved": [
    {{"case_hint": "optional related case/order ID or null", "title": "unfinished work item", "description": "details"}}
  ],
  "commitments": [
    {{"case_hint": "optional related case/order ID or null", "description": "explicit promise made", "committed_to": "person/team promised to", "expected_date": "promised date or null"}}
  ],
  "blockers": [
    {{"case_hint": "optional related case/order ID or null", "description": "what is blocking progress", "blocked_by": "department/person/external dependency"}}
  ],
  "deadlines": [
    {{"case_hint": "optional related case/order ID or null", "description": "deadline description", "date_str": "explicit date mentioned (e.g. Today, Tomorrow, Friday)"}}
  ],
  "exceptions": [
    {{"case_hint": "optional related case/order ID or null", "expected": "expected state", "found": "actual state reported", "evidence": "discrepancy details", "impact": "business impact or null", "required_action": "investigative action"}}
  ],
  "next_actions": [
    {{"case_hint": "optional related case/order ID or null", "action": "concrete immediate next step", "assignee": "suggested owner or null"}}
  ]
}}

HANDOFF NOTES:
\"\"\"{raw_notes}\"\"\"
"""

class BedrockAIProvider(AIProvider):
    """Amazon Bedrock AI Provider for production workplace context extraction.
    
    Uses standard AWS credential chain via boto3 and connects to the Bedrock Runtime Converse API.
    Does NOT determine operational status; only extracts structured facts.
    """

    def __init__(self, region: Optional[str] = None, model_id: Optional[str] = None, client: Optional[object] = None):
        self.region = region or os.getenv("AWS_REGION", "ap-south-1")
        if model_id is not None:
            self.model_id = model_id.strip()
        else:
            self.model_id = os.getenv("BEDROCK_MODEL_ID", "global.amazon.nova-2-lite-v1:0").strip()
        self._client = client

    def _get_client(self):
        """Lazy-initialize boto3 bedrock-runtime client using standard credential chain."""
        if self._client is not None:
            return self._client
        
        try:
            import boto3
            if self.region:
                os.environ.setdefault("AWS_DEFAULT_REGION", self.region)
            session = boto3.Session(region_name=self.region)
            self._client = session.client("bedrock-runtime", region_name=self.region)
            return self._client
        except Exception as e:
            logger.error(f"Failed to initialize boto3 Bedrock client: {e}")
            raise BedrockInferenceError(
                f"Failed to initialize AWS Bedrock client in region '{self.region}': {str(e)}"
            )

    async def extract_work_state(self, raw_notes: str) -> AIExtractionResult:
        """Extract structured work state using Amazon Bedrock.
        
        Raises:
            BedrockConfigurationError: If BEDROCK_MODEL_ID is not configured.
            BedrockInferenceError: If AWS credentials or Bedrock invocation fails.
            BedrockExtractionError: If model response cannot be parsed or validated against Pydantic schema.
        """
        if not self.model_id:
            raise BedrockConfigurationError(
                "BEDROCK_MODEL_ID is not configured. Please set BEDROCK_MODEL_ID in your environment or .env file."
            )

        client = self._get_client()
        prompt = EXTRACTION_USER_PROMPT_TEMPLATE.format(raw_notes=raw_notes)

        # Attempt invocation using Converse API (supported across modern Bedrock models including Nova)
        try:
            response_text = self._invoke_bedrock(client, prompt)
        except BedrockError:
            raise
        except Exception as e:
            err_msg = str(e)
            if "NoCredentialsError" in err_msg or "Unable to locate credentials" in err_msg:
                raise BedrockInferenceError(
                    "Bedrock credentials are not configured. Please configure AWS credentials via AWS CLI, environment variables, or IAM role."
                )
            elif "AccessDeniedException" in err_msg:
                raise BedrockInferenceError(
                    f"Bedrock access denied for model '{self.model_id}' in region '{self.region}'. "
                    "Ensure your AWS credentials have 'bedrock:InvokeModel' permission and model access is granted."
                )
            elif "ResourceNotFoundException" in err_msg:
                raise BedrockInferenceError(
                    f"Bedrock model '{self.model_id}' not found in region '{self.region}'. "
                    "Verify the model ID and regional availability."
                )
            else:
                raise BedrockInferenceError(f"Bedrock inference failed: {err_msg}")

        # Parse and validate JSON against Pydantic model
        return self._parse_and_validate(response_text)

    def _invoke_bedrock(self, client, prompt: str) -> str:
        """Invokes Bedrock via the Bedrock Runtime Converse API."""
        try:
            response = client.converse(
                modelId=self.model_id,
                system=[{"text": EXTRACTION_SYSTEM_PROMPT}],
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                inferenceConfig={
                    "temperature": 0.0,
                    "maxTokens": 3000
                }
            )
            output_message = response.get("output", {}).get("message", {})
            content_list = output_message.get("content", [])
            if not content_list or "text" not in content_list[0]:
                raise BedrockExtractionError(
                    f"Bedrock Converse API returned unexpected output structure: {response.get('output')}"
                )
            return content_list[0]["text"]
        except BedrockError:
            raise
        except Exception as e:
            err_msg = str(e)
            if "NoCredentialsError" in err_msg or "Unable to locate credentials" in err_msg:
                raise BedrockInferenceError(
                    "Bedrock credentials are not configured. Please configure AWS credentials via AWS CLI, environment variables, or IAM role."
                )
            elif "AccessDeniedException" in err_msg:
                raise BedrockInferenceError(
                    f"Bedrock access denied for model '{self.model_id}' in region '{self.region}'. "
                    "Ensure your AWS credentials have 'bedrock:InvokeModel' permission and model access is granted."
                )
            elif "ResourceNotFoundException" in err_msg:
                raise BedrockInferenceError(
                    f"Bedrock model '{self.model_id}' not found in region '{self.region}'. "
                    "Verify the model ID and regional availability."
                )
            else:
                raise BedrockInferenceError(f"Bedrock Converse invocation failed for model '{self.model_id}': {err_msg}")

    def _parse_and_validate(self, text: str) -> AIExtractionResult:
        """Parses model output text, extracts JSON, and validates with Pydantic."""
        cleaned_text = text.strip()
        
        # Remove potential markdown code block wrappers
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        cleaned_text = cleaned_text.strip()

        # Find enclosing JSON brackets
        start = cleaned_text.find("{")
        end = cleaned_text.rfind("}") + 1
        
        if start == -1 or end == 0:
            raise BedrockExtractionError(
                f"Bedrock returned invalid structured output: No JSON object found in response: '{text[:200]}...'"
            )

        json_str = cleaned_text[start:end]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise BedrockExtractionError(
                f"Bedrock returned invalid structured output: Malformed JSON ({str(e)}). Content: '{json_str[:200]}...'"
            )

        try:
            return AIExtractionResult.model_validate(data)
        except Exception as e:
            raise BedrockExtractionError(
                f"Bedrock returned invalid structured output: Schema validation failed ({str(e)})"
            )
