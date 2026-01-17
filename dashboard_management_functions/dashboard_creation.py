"""
Dashboard Creation Module
Handles the creation and configuration of Databricks dashboards
"""
import json
from typing import Dict, Any
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import LakeviewAPI


class DashboardCreator:
    """Creates and configures Databricks dashboard structures"""
    
    def __init__(self, workspace_client: WorkspaceClient, warehouse_id: str, parent_path: str = "/Shared"):
        """
        Initialize Dashboard Creator
        
        Args:
            workspace_client: Databricks WorkspaceClient instance
            warehouse_id: SQL Warehouse ID for dashboard queries
            parent_path: Parent path for dashboard storage
        """
        self.client = workspace_client
        self.warehouse_id = warehouse_id
        self.parent_path = parent_path
    
    def create_dashboard(self, config: Dict[str, Any], dashboard_name: str) -> str:
        """
        Create a new dashboard from configuration
        
        Args:
            config: Dashboard configuration with pages/layout structure
            dashboard_name: Name for the dashboard
            
        Returns:
            Dashboard ID
        """
        # Convert config to JSON string
        dashboard_json_text = json.dumps(config)
        
        # Generate unique path for the dashboard
        dashboard_path = f"{dashboard_name.replace(' ', '_').lower()}.lvdash.json"
        
        # Use the client's lakeview API directly with all parameters
        created_dashboard = self.client.lakeview.create(
            display_name=dashboard_name,
            warehouse_id=self.warehouse_id,
            serialized_dashboard=dashboard_json_text,
            parent_path=self.parent_path
        )
        
        return created_dashboard.dashboard_id
    
    def update_dashboard(self, dashboard_id: str, config: Dict[str, Any]) -> str:
        """
        Update an existing dashboard with new configuration
        
        Args:
            dashboard_id: ID of the dashboard to update
            config: New dashboard configuration with pages/layout structure
            
        Returns:
            Dashboard ID (same as input)
        """
        # Convert config to JSON string
        dashboard_json_text = json.dumps(config)
        
        # First, get the dashboard to retrieve its etag (required for update)
        dashboard = self.client.lakeview.get(dashboard_id)
        
        # Debug: Check if genieSpace is in the config
        if 'genieSpace' in config:
            print(f"🔍 Updating dashboard with genieSpace: {config['genieSpace']}")
        
        # Update the dashboard using the SDK's update method with etag
        self.client.lakeview.update(
            dashboard_id=dashboard_id,
            serialized_dashboard=dashboard_json_text,
            etag=dashboard.etag
        )
        
        return dashboard_id

