"""
Dashboard Unity Catalog Operations Module
Handles saving and retrieving dashboard metadata from Unity Catalog
"""
import json
from typing import List, Dict, Any
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState


def save_dashboard_to_catalog(
    workspace_client: WorkspaceClient,
    warehouse_id: str,
    dashboard_id: str,
    dashboard_name: str,
    dashboard_config: dict,
    embed_url: str
) -> tuple[bool, str]:
    """
    Save dashboard information to Unity Catalog table
    
    Args:
        workspace_client: Databricks workspace client
        warehouse_id: SQL Warehouse ID
        dashboard_id: Dashboard ID
        dashboard_name: Dashboard name
        dashboard_config: Dashboard configuration dictionary
        embed_url: Dashboard embed URL
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Get current username
        current_user = workspace_client.current_user.me()
        username = current_user.user_name
        
        # Convert dashboard config to JSON string
        config_json = json.dumps(dashboard_config)
        
        # Escape single quotes for SQL
        dashboard_name_escaped = dashboard_name.replace("'", "''")
        config_json_escaped = config_json.replace("'", "''")
        
        # Insert into Unity Catalog table
        insert_query = f"""
        INSERT INTO christophe_chieu.intelligent_embedded_dashboard.save_dashboards
        (username, name_dashboard, url, json)
        VALUES (
            '{username}',
            '{dashboard_name_escaped}',
            '{embed_url}',
            '{config_json_escaped}'
        )
        """
        
        # Execute the SQL statement
        statement = workspace_client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=insert_query,
            wait_timeout="30s"
        )
        
        if statement.status.state == StatementState.SUCCEEDED:
            return True, f"Dashboard '{dashboard_name}' saved to Unity Catalog successfully!"
        else:
            return False, f"Failed to save dashboard. Status: {statement.status.state}"
            
    except Exception as e:
        return False, f"Error saving dashboard: {str(e)}"


def get_saved_dashboards_for_user(
    workspace_client: WorkspaceClient,
    warehouse_id: str
) -> tuple[bool, List[Dict[str, Any]], str]:
    """
    Get all saved dashboards for the current user from Unity Catalog
    
    Args:
        workspace_client: Databricks workspace client
        warehouse_id: SQL Warehouse ID
        
    Returns:
        Tuple of (success: bool, dashboards: List[Dict], message: str)
    """
    try:
        # Get current username
        current_user = workspace_client.current_user.me()
        username = current_user.user_name
        username_escaped = username.replace("'", "''")
        
        # Query Unity Catalog table
        query = f"""
        SELECT name_dashboard, url, json
        FROM christophe_chieu.intelligent_embedded_dashboard.save_dashboards
        WHERE username = '{username_escaped}'
        """
        
        # Execute the SQL statement
        statement = workspace_client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=query,
            wait_timeout="30s"
        )
        
        if statement.status.state == StatementState.SUCCEEDED:
            # Parse results
            dashboards = []
            if statement.result and statement.result.data_array:
                for row in statement.result.data_array:
                    dashboards.append({
                        'name': row[0],
                        'url': row[1],
                        'config': row[2]
                    })
            
            return True, dashboards, f"Found {len(dashboards)} saved dashboard(s)"
        else:
            error_msg = f"Failed to fetch dashboards. Status: {statement.status.state}"
            if hasattr(statement.status, 'error') and statement.status.error:
                error_msg += f" | Error: {statement.status.error.message}"
            return False, [], error_msg
            
    except Exception as e:
        return False, [], f"Error fetching saved dashboards: {str(e)}"


def update_dashboard_in_catalog(
    workspace_client: WorkspaceClient,
    warehouse_id: str,
    dashboard_name: str,
    new_config: dict,
    new_embed_url: str = None
) -> tuple[bool, str]:
    """
    Update dashboard information in Unity Catalog
    
    Args:
        workspace_client: Databricks workspace client
        warehouse_id: SQL Warehouse ID
        dashboard_name: Dashboard name to update
        new_config: New dashboard configuration dictionary
        new_embed_url: New embed URL (optional)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Get current username
        current_user = workspace_client.current_user.me()
        username = current_user.user_name
        
        # Convert dashboard config to JSON string
        config_json = json.dumps(new_config)
        
        # Escape single quotes for SQL
        username_escaped = username.replace("'", "''")
        dashboard_name_escaped = dashboard_name.replace("'", "''")
        config_json_escaped = config_json.replace("'", "''")
        
        # Build update query
        if new_embed_url:
            new_embed_url_escaped = new_embed_url.replace("'", "''")
            update_query = f"""
            UPDATE christophe_chieu.intelligent_embedded_dashboard.save_dashboards
            SET json = '{config_json_escaped}',
                url = '{new_embed_url_escaped}'
            WHERE username = '{username_escaped}'
              AND name_dashboard = '{dashboard_name_escaped}'
            """
        else:
            update_query = f"""
            UPDATE christophe_chieu.intelligent_embedded_dashboard.save_dashboards
            SET json = '{config_json_escaped}'
            WHERE username = '{username_escaped}'
              AND name_dashboard = '{dashboard_name_escaped}'
            """
        
        # Execute the SQL statement
        statement = workspace_client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=update_query,
            wait_timeout="30s"
        )
        
        if statement.status.state == StatementState.SUCCEEDED:
            return True, f"Dashboard '{dashboard_name}' updated in Unity Catalog successfully!"
        else:
            return False, f"Failed to update dashboard. Status: {statement.status.state}"
            
    except Exception as e:
        return False, f"Error updating dashboard: {str(e)}"

