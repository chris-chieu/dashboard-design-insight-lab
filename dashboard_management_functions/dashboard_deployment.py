"""
Dashboard Deployment Module
Handles publishing dashboards to Databricks and retrieving embed URLs
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import LakeviewAPI


class DashboardDeployer:
    """Deploys and publishes Databricks dashboards"""
    
    def __init__(self, workspace_client: WorkspaceClient):
        """
        Initialize Dashboard Deployer
        
        Args:
            workspace_client: Databricks WorkspaceClient instance
        """
        self.client = workspace_client
    
    def publish_dashboard(self, dashboard_id: str, embed_credentials: bool = False) -> None:
        """
        Publish a dashboard to make it available
        
        Args:
            dashboard_id: ID of the dashboard to publish
            embed_credentials: Whether to embed credentials in the dashboard
        """
        self.client.lakeview.publish(
            dashboard_id=dashboard_id,
            embed_credentials=embed_credentials
        )
    
    def republish_dashboard(self, dashboard_id: str) -> None:
        """
        Republish an existing dashboard after updates
        
        Args:
            dashboard_id: ID of the dashboard to republish
        """
        lakeview = LakeviewAPI(self.client.api_client)
        lakeview.publish(dashboard_id=dashboard_id, embed_credentials=False)
    
    def get_embed_url(self, dashboard_id: str) -> str:
        """
        Get the embedded iframe URL for a Lakeview dashboard
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            Embedded iframe URL
        """
        workspace_url = self.client.config.host
        org_id = "0"  # Default for most cases
        embed_url = f"{workspace_url}/embed/dashboardsv3/{dashboard_id}?o={org_id}"
        return embed_url
    
    def deploy_dashboard(self, dashboard_id: str) -> str:
        """
        Complete deployment: publish dashboard and get embed URL
        
        Args:
            dashboard_id: ID of the dashboard to deploy
            
        Returns:
            Embedded iframe URL
        """
        self.publish_dashboard(dashboard_id)
        return self.get_embed_url(dashboard_id)

