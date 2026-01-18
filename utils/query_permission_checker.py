"""
Query Permission Checker Utility

This module tests SQL queries for permissions before displaying dashboards.
Instead of testing complex queries directly, it extracts table names and tests
simple SELECT queries on each table.
"""

import re
from dash import html
import dash_bootstrap_components as dbc
from databricks.sdk.service.sql import StatementState


def extract_table_names(sql_query):
    """
    Extract table names from a SQL query.
    
    Args:
        sql_query: SQL query string
    
    Returns:
        Set[str]: Set of fully qualified table names (without backticks)
    """
    # Remove comments
    sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
    sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
    
    # Pattern to match table names in FROM and JOIN clauses
    # Handles:
    # - With backticks: `catalog`.`schema`.`table`
    # - Without backticks: catalog.schema.table
    # - Mixed: catalog.`schema`.table
    # - Optional AS alias
    pattern = r'\b(?:FROM|JOIN)\s+(`?[a-zA-Z0-9_]+`?(?:\.`?[a-zA-Z0-9_]+`?){0,2})(?:\s+(?:AS\s+)?[a-zA-Z0-9_]+)?'
    
    tables = set()
    for match in re.finditer(pattern, sql_query, re.IGNORECASE):
        table_name = match.group(1)
        # Remove backticks from the table name
        table_name = table_name.replace('`', '')
        # Skip if it looks like a CTE or subquery alias (usually single word without dots)
        # But keep it if it has a dot (catalog.schema.table or schema.table)
        if '.' in table_name or table_name.upper() not in ['VALUES', 'LATERAL', 'UNNEST']:
            tables.add(table_name)
    
    return tables


def test_dashboard_queries_for_permissions(dashboard_queries, workspace_client, warehouse_id):
    """
    Test all dashboard queries for permissions by extracting table names
    and testing simple SELECT queries on each table.
    
    Args:
        dashboard_queries: List of dict with 'name' and 'query' keys
        workspace_client: Databricks workspace client
        warehouse_id: Warehouse ID for SQL execution
    
    Returns:
        tuple: (success: bool, error_alert: dbc.Alert or None)
            - If all tables are accessible: (True, None)
            - If any table fails: (False, dbc.Alert with error details)
    """
    
    if not dashboard_queries:
        print("ℹ️ No queries to test")
        return True, None
    
    print(f"🔒 Extracting tables from {len(dashboard_queries)} queries for permission testing...")
    
    # Collect all unique tables from all queries
    all_tables = set()
    for query_info in dashboard_queries:
        sql_query = query_info['query']
        tables = extract_table_names(sql_query)
        all_tables.update(tables)
    
    # Filter out CTEs and dynamic tables (like IDENTIFIER())
    # Keep only fully qualified table names (with dots)
    tables_to_test = [t for t in all_tables if '.' in t and not t.upper().startswith('IDENTIFIER')]
    
    if not tables_to_test:
        print("⚠️ No tables detected for permission testing - this should not happen normally")
        print(f"   Queries processed: {len(dashboard_queries)}")
        # Fail-safe: If we can't detect tables, we should be cautious and block the dashboard
        # rather than allowing potential permission violations
        error_alert = dbc.Alert([
            html.H5("⚠️ Unable to Verify Permissions", className="alert-heading"),
            html.P([
                "Could not extract table names from dashboard queries for permission verification.",
                html.Br(),
                html.Br(),
                "This may indicate:",
                html.Ul([
                    html.Li("Complex query patterns that require special handling"),
                    html.Li("Dynamic table references (IDENTIFIER, variables)"),
                    html.Li("Queries that need to be verified manually")
                ])
            ]),
            html.Hr(),
            html.P("Please contact your administrator to verify you have appropriate permissions for this dashboard.", className="mb-0 small")
        ], color="warning")
        return False, error_alert
    
    print(f"🔒 Found {len(tables_to_test)} unique tables to test: {', '.join(sorted(tables_to_test))}")
    
    # Test each table with a simple SELECT
    for idx, table_name in enumerate(sorted(tables_to_test), 1):
        print(f"🔒 Testing table {idx}/{len(tables_to_test)}: {table_name}")
        
        # First, check if this is a metric view by getting table info
        is_metric_view = False
        test_query = f"SELECT * FROM {table_name} LIMIT 1"  # Default fallback
        
        try:
            print(f"   📋 Getting table info for: {table_name}")
            table_info = workspace_client.tables.get(full_name=table_name)
            
            # Check both table_type attribute and look for measure columns
            table_type = table_info.table_type if hasattr(table_info, 'table_type') else 'UNKNOWN'
            print(f"   📋 Table type: {table_type}")
            
            # Metric views can be identified by checking type_json metadata
            # Check if any columns have "metric_view.type": "measure" in their metadata
            has_measure_columns = False
            if table_info.columns:
                print(f"   📋 Checking {len(table_info.columns)} columns for metric view types...")
                for idx, col in enumerate(table_info.columns):
                    # Parse type_json to check for metric_view.type
                    is_measure = False
                    if hasattr(col, 'type_json') and col.type_json:
                        try:
                            import json
                            type_data = json.loads(col.type_json) if isinstance(col.type_json, str) else col.type_json
                            metadata = type_data.get('metadata', {})
                            metric_view_type = metadata.get('metric_view.type', '')
                            
                            if metric_view_type == 'measure':
                                is_measure = True
                                has_measure_columns = True
                                if idx < 3:
                                    print(f"      ✅ Col {idx}: {col.name} = MEASURE")
                            elif idx < 3:
                                print(f"      📐 Col {idx}: {col.name} = DIMENSION")
                        except Exception as e:
                            if idx < 2:
                                print(f"      ⚠️ Col {idx}: Could not parse type_json: {e}")
                    
                print(f"   📊 Metric view detected: {has_measure_columns}")
            else:
                print(f"   ⚠️ No columns found in table_info")
            
            # If we have measure columns, treat it as a metric view
            is_metric_view = has_measure_columns
            
            if is_metric_view:
                print(f"   📊 METRIC VIEW DETECTED: {table_name}")
                
                # Build a simple test query with 1 measure and 1 dimension
                # (Selecting all would require GROUP BY)
                if table_info.columns:
                    first_dimension = None
                    first_measure = None
                    
                    for col in table_info.columns:
                        # Check type_json metadata for metric_view.type
                        is_measure = False
                        if hasattr(col, 'type_json') and col.type_json:
                            try:
                                import json
                                type_data = json.loads(col.type_json) if isinstance(col.type_json, str) else col.type_json
                                metadata = type_data.get('metadata', {})
                                metric_view_type = metadata.get('metric_view.type', '')
                                is_measure = (metric_view_type == 'measure')
                            except:
                                pass
                        
                        if is_measure and not first_measure:
                            first_measure = col.name
                        elif not is_measure and not first_dimension:
                            first_dimension = col.name
                        
                        if first_measure and first_dimension:
                            break
                    
                    # Build simple test query with 1 measure and 1 dimension (requires GROUP BY)
                    if first_measure and first_dimension:
                        test_query = f"SELECT {first_dimension}, MEASURE({first_measure}) FROM {table_name} GROUP BY {first_dimension} LIMIT 1"
                        print(f"   🔍 Query: SELECT {first_dimension}, MEASURE({first_measure}) ... GROUP BY {first_dimension}")
                    elif first_measure:
                        # Only measures - no GROUP BY needed
                        test_query = f"SELECT MEASURE({first_measure}) FROM {table_name} LIMIT 1"
                        print(f"   🔍 Query: SELECT MEASURE({first_measure}) ...")
                    else:
                        print(f"   ⚠️ No measure columns found, using SELECT *")
                        test_query = f"SELECT * FROM {table_name} LIMIT 1"
                else:
                    print(f"   ⚠️ No columns found, using SELECT *")
            else:
                print(f"   📋 Regular table, using SELECT *")
                
        except Exception as table_info_error:
            print(f"   ❌ Error getting table info: {table_info_error}")
            print(f"   ⚠️ Falling back to SELECT *")
        
        try:
            response = workspace_client.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=test_query,
                wait_timeout='30s'
            )
            
            if response.status and response.status.state == StatementState.FAILED:
                error_msg = str(response.status.error) if response.status.error else "Unknown error"
                print(f"❌ Permission test failed for table '{table_name}': {error_msg}")
                
                # Block dashboard if there's a permission error
                if 'INSUFFICIENT_PERMISSIONS' in error_msg or 'does not have' in error_msg.lower() or 'ServiceError' in error_msg:
                    error_alert = dbc.Alert([
                        html.H5("🔒 Insufficient Permissions", className="alert-heading"),
                        html.P([
                            "You don't have permissions to access the required tables.",
                            html.Br(),
                            html.Br(),
                            html.Strong(f"Table: {table_name}")
                        ]),
                        html.Hr(),
                        html.P(error_msg, className="mb-0 small text-muted")
                    ], color="danger")
                    return False, error_alert
                else:
                    # Other errors (like table not found) - still block
                    error_alert = dbc.Alert([
                        html.H5("❌ Table Access Error", className="alert-heading"),
                        html.P([
                            f"Cannot access table: {table_name}",
                            html.Br(),
                            html.Br(),
                            "This may be a permissions issue or the table may not exist."
                        ]),
                        html.Hr(),
                        html.P(error_msg, className="mb-0 small text-muted")
                    ], color="danger")
                    return False, error_alert
            
            print(f"✅ Table '{table_name}' - permission OK")
        
        except Exception as test_error:
            error_msg = str(test_error)
            print(f"❌ Error testing table '{table_name}': {error_msg}")
            
            # Block dashboard if there's a permission error
            if 'INSUFFICIENT_PERMISSIONS' in error_msg or 'does not have' in error_msg.lower() or 'ServiceError' in error_msg:
                error_alert = dbc.Alert([
                    html.H5("🔒 Insufficient Permissions", className="alert-heading"),
                    html.P([
                        "You don't have permissions to access the required tables.",
                        html.Br(),
                        html.Br(),
                        html.Strong(f"Table: {table_name}")
                    ]),
                    html.Hr(),
                    html.P(error_msg, className="mb-0 small text-muted")
                ], color="danger")
                return False, error_alert
            else:
                # Other errors - still block
                error_alert = dbc.Alert([
                    html.H5("❌ Error Testing Table Access", className="alert-heading"),
                    html.P([
                        f"An error occurred while testing access to: {table_name}",
                        html.Br(),
                        html.Br(),
                        "This may be a permissions issue or the table may not exist."
                    ]),
                    html.Hr(),
                    html.P(error_msg, className="mb-0 small text-muted")
                ], color="danger")
                return False, error_alert
    
    print(f"✅ All {len(tables_to_test)} tables passed permission checks")
    return True, None
