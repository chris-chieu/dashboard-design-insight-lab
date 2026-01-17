"""
Dashboard Manager Module
Unified interface for all dashboard operations
"""
from databricks.sdk import WorkspaceClient
from .dashboard_creation import DashboardCreator
from .dashboard_deployment import DashboardDeployer
from .dashboard_deletion import delete_dashboard_complete
from .dashboard_catalog_operations import (
    save_dashboard_to_catalog,
    get_saved_dashboards_for_user
)


class DashboardManager:
    """
    Unified manager for dashboard operations combining creation, deployment, 
    deletion, and catalog persistence
    """
    
    def __init__(self, workspace_client: WorkspaceClient, warehouse_id: str, parent_path: str = "/Shared"):
        """
        Initialize Dashboard Manager
        
        Args:
            workspace_client: Databricks WorkspaceClient instance
            warehouse_id: SQL Warehouse ID for dashboard queries
            parent_path: Parent path for dashboard storage
        """
        self.workspace_client = workspace_client
        self.warehouse_id = warehouse_id
        self.parent_path = parent_path
        
        # Initialize specialized handlers
        self.creator = DashboardCreator(workspace_client, warehouse_id, parent_path)
        self.deployer = DashboardDeployer(workspace_client)
    
    def create_dashboard(self, config: dict, dashboard_name: str) -> str:
        """
        Create a new dashboard
        
        Args:
            config: Dashboard configuration
            dashboard_name: Name for the dashboard
            
        Returns:
            Dashboard ID
        """
        dashboard_id = self.creator.create_dashboard(config, dashboard_name)
        self.deployer.publish_dashboard(dashboard_id)
        return dashboard_id
    
    def update_dashboard(self, dashboard_id: str, config: dict) -> str:
        """
        Update an existing dashboard
        
        Args:
            dashboard_id: ID of the dashboard to update
            config: New dashboard configuration
            
        Returns:
            Dashboard ID
        """
        dashboard_id = self.creator.update_dashboard(dashboard_id, config)
        self.deployer.republish_dashboard(dashboard_id)
        return dashboard_id
    
    def get_dashboard_config(self, dashboard_id: str) -> dict:
        """
        Get the configuration/definition of an existing dashboard
        
        Args:
            dashboard_id: ID of the dashboard to retrieve
            
        Returns:
            Dashboard configuration dictionary
        """
        try:
            dashboard = self.workspace_client.lakeview.get(dashboard_id)
            dashboard_dict = dashboard.as_dict()
            
            # Debug: Check structure
            print(f"🔍 Dashboard structure - Top-level keys: {list(dashboard_dict.keys())}")
            if 'genieSpace' in dashboard_dict:
                print(f"   genieSpace at TOP LEVEL: {dashboard_dict['genieSpace']}")
            if 'serialized_dashboard' in dashboard_dict:
                if isinstance(dashboard_dict['serialized_dashboard'], str):
                    import json
                    serialized = json.loads(dashboard_dict['serialized_dashboard'])
                else:
                    serialized = dashboard_dict['serialized_dashboard']
                if 'genieSpace' in serialized:
                    print(f"   genieSpace in SERIALIZED: {serialized['genieSpace']}")
            
            return dashboard_dict
        except Exception as e:
            print(f"Error retrieving dashboard config: {e}")
            return {}
    
    def get_embed_url(self, dashboard_id: str) -> str:
        """
        Get embed URL for a dashboard
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            Embedded iframe URL
        """
        return self.deployer.get_embed_url(dashboard_id)
    
    def delete_dashboard(self, dashboard_id: str, dashboard_name: str = None) -> tuple[bool, str]:
        """
        Delete a dashboard from Databricks and optionally from Unity Catalog
        
        Args:
            dashboard_id: Dashboard ID to delete
            dashboard_name: Dashboard name (optional, for UC deletion)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        return delete_dashboard_complete(
            self.workspace_client,
            dashboard_id,
            self.warehouse_id if dashboard_name else None,
            dashboard_name
        )
    
    def save_dashboard(self, dashboard_id: str, dashboard_name: str, dashboard_config: dict) -> tuple[bool, str]:
        """
        Save dashboard to Unity Catalog
        
        Args:
            dashboard_id: Dashboard ID
            dashboard_name: Dashboard name
            dashboard_config: Dashboard configuration
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        embed_url = self.get_embed_url(dashboard_id)
        return save_dashboard_to_catalog(
            self.workspace_client,
            self.warehouse_id,
            dashboard_id,
            dashboard_name,
            dashboard_config,
            embed_url
        )
    
    def get_saved_dashboards(self) -> tuple[bool, list, str]:
        """
        Get all saved dashboards for the current user
        
        Returns:
            Tuple of (success: bool, dashboards: List[Dict], message: str)
        """
        return get_saved_dashboards_for_user(self.workspace_client, self.warehouse_id)

