"""
Dashboard Deletion Module
Handles deletion of dashboards from Databricks and Unity Catalog
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import LakeviewAPI
from databricks.sdk.service.sql import StatementState


def delete_dashboard_from_databricks(
    workspace_client: WorkspaceClient,
    dashboard_id: str
) -> tuple[bool, str]:
    """
    Delete a dashboard from Databricks
    
    Args:
        workspace_client: Databricks workspace client
        dashboard_id: Dashboard ID to delete
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Use Lakeview API to delete (trash the dashboard)
        lakeview = LakeviewAPI(workspace_client.api_client)
        lakeview.trash(dashboard_id=dashboard_id)
        return True, f"Dashboard {dashboard_id} deleted from Databricks"
    except Exception as e:
        # Fallback to regular dashboards API
        try:
            workspace_client.dashboards.delete(dashboard_id)
            return True, f"Dashboard {dashboard_id} deleted from Databricks"
        except Exception as fallback_error:
            return False, f"Error deleting dashboard: {str(e)} | Fallback error: {str(fallback_error)}"


def delete_dashboard_from_unity_catalog(
    workspace_client: WorkspaceClient,
    warehouse_id: str,
    dashboard_name: str
) -> tuple[bool, str]:
    """
    Delete dashboard record from Unity Catalog
    
    Args:
        workspace_client: Databricks workspace client
        warehouse_id: SQL Warehouse ID
        dashboard_name: Dashboard name to delete
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Get current username
        current_user = workspace_client.current_user.me()
        username = current_user.user_name
        
        # Escape single quotes for SQL
        username_escaped = username.replace("'", "''")
        dashboard_name_escaped = dashboard_name.replace("'", "''")
        
        # Delete from Unity Catalog table
        delete_query = f"""
        DELETE FROM christophe_chieu.intelligent_embedded_dashboard.save_dashboards
        WHERE username = '{username_escaped}'
          AND name_dashboard = '{dashboard_name_escaped}'
        """
        
        # Execute the SQL statement
        statement = workspace_client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=delete_query,
            wait_timeout="30s"
        )
        
        if statement.status.state == StatementState.SUCCEEDED:
            return True, "Record deleted from Unity Catalog"
        else:
            return False, f"Failed to delete from Unity Catalog. Status: {statement.status.state}"
            
    except Exception as e:
        return False, f"Error deleting from Unity Catalog: {str(e)}"


def delete_dashboard_complete(
    workspace_client: WorkspaceClient,
    dashboard_id: str,
    warehouse_id: str = None,
    dashboard_name: str = None
) -> tuple[bool, str]:
    """
    Complete dashboard deletion: remove from Databricks and optionally from Unity Catalog
    
    Args:
        workspace_client: Databricks workspace client
        dashboard_id: Dashboard ID to delete
        warehouse_id: SQL Warehouse ID (optional, for UC deletion)
        dashboard_name: Dashboard name (optional, for UC deletion)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    messages = []
    overall_success = True
    
    # Delete from Databricks
    success, message = delete_dashboard_from_databricks(workspace_client, dashboard_id)
    messages.append(message)
    if not success:
        overall_success = False
    
    # Also delete from Unity Catalog if credentials provided
    if warehouse_id and dashboard_name:
        success, message = delete_dashboard_from_unity_catalog(
            workspace_client, 
            warehouse_id, 
            dashboard_name
        )
        messages.append(message)
        if not success:
            # UC deletion failure is not critical
            messages[-1] = f"Warning: {message}"
    
    return overall_success, " | ".join(messages)

