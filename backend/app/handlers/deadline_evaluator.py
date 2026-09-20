"""AWS Lambda Handler for CONTINUITY Scheduled Deadline Evaluation.

This handler can be triggered directly by AWS EventBridge (Scheduled Rules or
EventBridge Scheduler) on a recurring schedule (e.g. hourly or daily).

It evaluates cases in DynamoDB against deadlines, applies deterministic policy,
persists changes idempotently, logs audit events, and returns a structured summary.
"""
import json
import logging
from typing import Dict, Any

from app.services.deadline_service import DeadlineEvaluationService
from app.repositories.factory import get_repository

logger = logging.getLogger("continuity.deadline_evaluator")
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda entry point for scheduled deadline evaluation."""
    logger.info("Starting scheduled deadline evaluation triggered by EventBridge: %s", event)

    try:
        service = DeadlineEvaluationService()
        summary = service.evaluate_all_cases()

        response_body = {
            "statusCode": 200,
            "body": {
                "evaluated": summary.evaluated,
                "changed": summary.changed,
                "at_risk": summary.at_risk,
                "overdue": summary.overdue,
                "unchanged": summary.unchanged,
            }
        }

        logger.info(
            "Completed deadline evaluation. Evaluated: %d, Changed: %d, Overdue: %d, At Risk: %d, Unchanged: %d",
            summary.evaluated, summary.changed, summary.overdue, summary.at_risk, summary.unchanged
        )
        return response_body

    except Exception as e:
        logger.error("Error during scheduled deadline evaluation: %s", str(e), exc_info=True)
        return {
            "statusCode": 500,
            "body": {
                "error": "Deadline evaluation failed",
                "details": str(e)
            }
        }

if __name__ == "__main__":
    # Local CLI execution support
    from dotenv import load_dotenv
    load_dotenv()
    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2))
