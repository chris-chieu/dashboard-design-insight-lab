"""
Query Permission Checker Utility

This module tests SQL queries for permissions before displaying dashboards.
"""

from dash import html
import dash_bootstrap_components as dbc
from databricks.sdk.service.sql import StatementState


def test_dashboard_queries_for_permissions(dashboard_queries, workspace_client, warehouse_id):
    """
    Test all dashboard queries for permissions.
    
    Args:
        dashboard_queries: List of dict with 'name' and 'query' keys
        workspace_client: Databricks workspace client
        warehouse_id: Warehouse ID for SQL execution
    
    Returns:
        tuple: (success: bool, error_alert: dbc.Alert or None)
            - If all queries pass: (True, None)
            - If any query fails: (False, dbc.Alert with error details)
    """
    if not dashboard_queries:
        print("ℹ️ No queries to test")
        return True, None
    
    print(f"🔒 Testing {len(dashboard_queries)} queries for permissions...")
    
    for idx, query_info in enumerate(dashboard_queries, 1):
        sql_query = query_info['query']
        
        # Add LIMIT 1 to make it fast
        if 'LIMIT' not in sql_query.upper():
            test_query = f"{sql_query.rstrip(';')} LIMIT 1"
        else:
            test_query = sql_query
        
        print(f"🔒 Auto-testing query {idx}/{len(dashboard_queries)}: {query_info['name']}")
        
        try:
            response = workspace_client.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=test_query,
                wait_timeout='30s'
            )
            
            if response.status and response.status.state == StatementState.FAILED:
                error_msg = str(response.status.error) if response.status.error else "Unknown error"
                print(f"❌ Query {idx} failed: {error_msg}")
                
                # Block dashboard if there's a ServiceError or permission error
                if 'ServiceError' in error_msg or 'INSUFFICIENT_PERMISSIONS' in error_msg or 'does not have' in error_msg.lower():
                    error_alert = dbc.Alert([
                        html.H5("🔒 Insufficient Permissions", className="alert-heading"),
                        html.P([
                            "You don't have permissions to access its data.",
                            html.Br(),
                            html.Br(),
                            html.Strong(f"Failed Query: {query_info['name']}")
                        ]),
                        html.Hr(),
                        html.P(error_msg, className="mb-0 small text-muted")
                    ], color="danger")
                    return False, error_alert
            
            print(f"✅ Query {idx} passed permission check")
        
        except Exception as test_error:
            error_msg = str(test_error)
            print(f"❌ Error testing query {idx}: {error_msg}")
            
            # Block dashboard if there's a ServiceError or permission error
            if 'ServiceError' in error_msg or 'INSUFFICIENT_PERMISSIONS' in error_msg or 'does not have' in error_msg.lower():
                error_alert = dbc.Alert([
                    html.H5("🔒 Insufficient Permissions", className="alert-heading"),
                    html.P([
                        "You don't have permissions to access its data.",
                        html.Br(),
                        html.Br(),
                        html.Strong(f"Failed Query: {query_info['name']}")
                    ]),
                    html.Hr(),
                    html.P(error_msg, className="mb-0 small text-muted")
                ], color="danger")
                return False, error_alert
    
    print(f"✅ All {len(dashboard_queries)} queries passed permission checks")
    return True, None

