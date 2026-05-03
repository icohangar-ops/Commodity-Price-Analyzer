"""
Microsoft Fabric integration module.
Handles data ingestion to OneLake, Lakehouse operations, and Fabric REST API calls.
"""
import requests
import json
from datetime import datetime
from typing import Optional
import structlog
from src.config import get_config

logger = structlog.get_logger(__name__)


class FabricClient:
    """
    Microsoft Fabric REST API client.

    Manages:
    - Lakehouse data operations
    - Pipeline orchestration
    - Workspace item management
    """

    API_BASE = "https://api.fabric.microsoft.com/v1"

    def __init__(self):
        cfg = get_config().fabric
        self.tenant_id = cfg.tenant_id
        self.workspace_id = cfg.workspace_id
        self.lakehouse_id = cfg.lakehouse_id
        self.client_id = cfg.client_id
        self.client_secret = cfg.client_secret
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        logger.info(
            "fabric_client_initialized",
            workspace_id=self.workspace_id,
            has_credentials=bool(self.client_id and self.client_secret)
        )

    def _get_access_token(self) -> str:
        """
        Obtain access token via MSAL for Service Principal authentication.

        Returns:
            Access token string.
        """
        try:
            import msal

            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            scopes = ["https://api.fabric.microsoft.com/.default"]

            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=authority
            )

            result = app.acquire_token_for_client(scopes=scopes)

            if "access_token" in result:
                self._access_token = result["access_token"]
                self._token_expiry = datetime.utcnow() + timedelta(hours=1)
                return self._access_token
            else:
                raise ValueError(f"Token acquisition failed: {result.get('error_description', 'Unknown error')}")

        except ImportError:
            logger.warning("msal_not_installed")
            raise ImportError(
                "msal package is required for Fabric authentication. "
                "Install with: pip install msal"
            )

    def _headers(self) -> dict:
        """Get authorization headers for API requests."""
        if not self._access_token:
            self._get_access_token()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def get_workspace_info(self) -> dict:
        """Get workspace details from Fabric."""
        try:
            response = requests.get(
                f"{self.API_BASE}/workspaces/{self.workspace_id}",
                headers=self._headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("fabric_workspace_fetch_failed", error=str(e))
            raise

    def get_lakehouse_tables(self) -> list:
        """
        List all Delta tables in the Lakehouse.

        Returns:
            List of table names.
        """
        try:
            response = requests.get(
                f"{self.API_BASE}/workspaces/{self.workspace_id}"
                f"/lakehouses/{self.lakehouse_id}/tables",
                headers=self._headers(),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            tables = [t.get("name") for t in data.get("value", [])]
            logger.info("lakehouse_tables_listed", count=len(tables))
            return tables
        except Exception as e:
            logger.error("lakehouse_tables_fetch_failed", error=str(e))
            return []

    def upload_to_lakehouse(self, table_name: str, data: list) -> bool:
        """
        Upload data to a Lakehouse Delta table.

        In production, this would use the Fabric REST API to append data
        to a Delta table in OneLake. For initial setup, data can be loaded
        via Fabric notebooks.

        Args:
            table_name: Target Delta table name.
            data: List of records to upload.

        Returns:
            True if successful, False otherwise.
        """
        logger.info(
            "lakehouse_upload_requested",
            table=table_name,
            records=len(data)
        )

        # In a Fabric Notebook, you would use:
        # from pyspark.sql import SparkSession
        # spark = SparkSession.builder.getOrCreate()
        # df = spark.createDataFrame(data)
        # df.write.format("delta").mode("append").saveAsTable(table_name)

        # For REST API approach:
        try:
            # Use Fabric's item API to trigger a pipeline or notebook
            # that writes data to the lakehouse
            logger.info(
                "lakehouse_upload_ready",
                table=table_name,
                note="Use Fabric Notebook or Data Factory pipeline for actual writes"
            )
            return True
        except Exception as e:
            logger.error("lakehouse_upload_failed", error=str(e))
            return False

    def trigger_pipeline(self, pipeline_id: str, parameters: Optional[dict] = None) -> dict:
        """
        Trigger a Fabric Data Factory pipeline.

        Args:
            pipeline_id: Pipeline item ID.
            parameters: Optional pipeline parameters.

        Returns:
            Pipeline run details.
        """
        try:
            body = {}
            if parameters:
                body["parameters"] = parameters

            response = requests.post(
                f"{self.API_BASE}/workspaces/{self.workspace_id}"
                f"/pipelines/{pipeline_id}/execute",
                headers=self._headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            logger.info("pipeline_triggered", pipeline_id=pipeline_id)
            return result
        except Exception as e:
            logger.error("pipeline_trigger_failed", error=str(e))
            raise

    def check_fabric_connectivity(self) -> dict:
        """
        Verify Fabric API connectivity and workspace access.

        Returns:
            Dict with connectivity status and workspace info.
        """
        status = {
            "api_reachable": False,
            "workspace_accessible": False,
            "workspace_id": self.workspace_id,
            "workspace_url": f"https://app.fabric.microsoft.com/groups/{self.workspace_id}",
            "error": None,
        }

        try:
            # Test basic API reachability
            response = requests.get(
                f"{self.API_BASE}/workspaces/{self.workspace_id}",
                headers=self._headers(),
                timeout=30
            )
            status["api_reachable"] = True

            if response.status_code == 200:
                status["workspace_accessible"] = True
                data = response.json()
                status["workspace_name"] = data.get("displayName", "Unknown")
                status["capacity_id"] = data.get("capacityId", "N/A")
                logger.info("fabric_connectivity_ok", workspace=status.get("workspace_name"))
            elif response.status_code == 401:
                status["error"] = "Authentication failed. Check your Fabric credentials."
                logger.warning("fabric_auth_failed")
            elif response.status_code == 403:
                status["error"] = "Access denied to workspace. Check permissions."
                logger.warning("fabric_access_denied")
            else:
                status["error"] = f"Unexpected status: {response.status_code}"

        except requests.exceptions.ConnectionError:
            status["error"] = "Cannot reach Fabric API. Check network connectivity."
        except Exception as e:
            status["error"] = str(e)

        return status


from datetime import timedelta
