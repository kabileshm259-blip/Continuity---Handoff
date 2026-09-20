import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.case import Case, Handoff, AuditEvent

logger = logging.getLogger("continuity.dynamodb")

class DynamoDBRepository(BaseRepository):
    """Amazon DynamoDB repository for CONTINUITY.
    
    Persists cases and handoffs into a single DynamoDB table.
    Uses standard AWS credential provider chain via boto3.
    """

    def __init__(
        self,
        table_name: Optional[str] = None,
        region: Optional[str] = None,
        table_resource: Optional[Any] = None
    ):
        self.region = region or os.getenv("AWS_REGION", "ap-south-1")
        self.table_name = table_name or os.getenv("DYNAMODB_TABLE", "continuity-cases-dev")
        self._table = table_resource

    def _get_table(self):
        """Lazy-initialize boto3 DynamoDB Table resource using standard credential chain."""
        if self._table is not None:
            return self._table

        try:
            import boto3
            from botocore.config import Config
            if self.region:
                os.environ.setdefault("AWS_DEFAULT_REGION", self.region)
            session = boto3.Session(region_name=self.region)
            config = Config(account_id_endpoint_mode="disabled")
            dynamodb = session.resource("dynamodb", region_name=self.region, config=config)
            self._table = dynamodb.Table(self.table_name)
            return self._table
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB table resource: {e}")
            raise RuntimeError(f"DynamoDB connection error for table '{self.table_name}': {str(e)}")

    def get_all_cases(self) -> List[Case]:
        table = self._get_table()
        try:
            response = table.scan()
            items = response.get("Items", [])
            
            # Handle pagination if necessary
            while "LastEvaluatedKey" in response:
                response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                items.extend(response.get("Items", []))

            cases = []
            for item in items:
                # Filter out handoff records stored with HANDOFF# prefix
                if str(item.get("case_id", "")).startswith("HANDOFF#"):
                    continue
                if item.get("item_type") == "HANDOFF":
                    continue
                try:
                    # Remove internal storage helper keys before Pydantic validation
                    clean_item = {k: v for k, v in item.items() if k not in ["item_type"]}
                    cases.append(Case.model_validate(clean_item))
                except Exception as val_err:
                    logger.warning(f"Skipping malformed DynamoDB case item {item.get('case_id')}: {val_err}")

            return cases
        except Exception as e:
            logger.error(f"DynamoDB scan failed: {e}")
            raise RuntimeError(f"Failed to fetch cases from DynamoDB table '{self.table_name}': {str(e)}")

    def get_case(self, case_id: str) -> Optional[Case]:
        table = self._get_table()
        try:
            response = table.get_item(Key={"case_id": case_id})
            item = response.get("Item")
            if not item or str(item.get("case_id", "")).startswith("HANDOFF#"):
                return None
            
            clean_item = {k: v for k, v in item.items() if k not in ["item_type"]}
            return Case.model_validate(clean_item)
        except Exception as e:
            logger.error(f"DynamoDB get_item failed for case {case_id}: {e}")
            raise RuntimeError(f"Failed to retrieve case '{case_id}' from DynamoDB: {str(e)}")

    def save_case(self, case: Case) -> Case:
        table = self._get_table()
        now_str = datetime.now().strftime("%I:%M %p")
        case.updated_at = f"Today, {now_str}"
        
        try:
            item = case.model_dump()
            item["item_type"] = "CASE"
            table.put_item(Item=item)
            return case
        except Exception as e:
            logger.error(f"DynamoDB put_item failed for case {case.case_id}: {e}")
            raise RuntimeError(f"Failed to persist case '{case.case_id}' to DynamoDB: {str(e)}")

    def save_handoff(self, handoff: Handoff) -> Handoff:
        table = self._get_table()
        try:
            item = handoff.model_dump()
            # Store with prefix so partition key case_id remains unique
            item["case_id"] = f"HANDOFF#{handoff.handoff_id}"
            item["item_type"] = "HANDOFF"
            table.put_item(Item=item)
            return handoff
        except Exception as e:
            logger.error(f"DynamoDB put_item failed for handoff {handoff.handoff_id}: {e}")
            raise RuntimeError(f"Failed to persist handoff '{handoff.handoff_id}' to DynamoDB: {str(e)}")

    def get_handoff(self, handoff_id: str) -> Optional[Handoff]:
        table = self._get_table()
        try:
            response = table.get_item(Key={"case_id": f"HANDOFF#{handoff_id}"})
            item = response.get("Item")
            if not item:
                return None
            clean_item = {k: v for k, v in item.items() if k not in ["item_type", "case_id"]}
            return Handoff.model_validate(clean_item)
        except Exception as e:
            logger.error(f"DynamoDB get_item failed for handoff {handoff_id}: {e}")
            raise RuntimeError(f"Failed to retrieve handoff '{handoff_id}' from DynamoDB: {str(e)}")

    def add_audit_event(self, case_id: str, actor: str, action: str, details: str) -> Optional[AuditEvent]:
        case = self.get_case(case_id)
        if not case:
            return None
        
        event_id = f"EVT-{case_id}-{len(case.audit_history) + 1}"
        timestamp = datetime.now().strftime("%I:%M %p")
        event = AuditEvent(
            event_id=event_id,
            case_id=case_id,
            timestamp=timestamp,
            actor=actor,
            action=action,
            details=details
        )
        case.audit_history.append(event)
        self.save_case(case)
        return event

    def health_check(self) -> Dict[str, Any]:
        """Lightweight connectivity check that does not crash if DynamoDB is unreachable."""
        try:
            table = self._get_table()
            # table.load() makes a lightweight DescribeTable call
            table.load()
            status = getattr(table, "table_status", "UNKNOWN")
            item_count = getattr(table, "item_count", 0)
            return {
                "provider": "dynamodb",
                "status": "healthy",
                "table": self.table_name,
                "region": self.region,
                "table_status": status,
                "item_count": item_count
            }
        except Exception as e:
            logger.warning(f"DynamoDB health check warning: {e}")
            return {
                "provider": "dynamodb",
                "status": "degraded",
                "table": self.table_name,
                "region": self.region,
                "error": str(e)
            }
