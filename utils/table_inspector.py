"""
Table Inspector Module

Provides utilities to inspect Unity Catalog tables and extract their metadata.
"""

from databricks.sdk import WorkspaceClient
from typing import List, Dict, Tuple


def list_tables_from_schema(workspace_client: WorkspaceClient, catalog: str, schema: str) -> List[Dict[str, str]]:
    """
    List all tables from a specific Unity Catalog schema
    
    Args:
        workspace_client: Databricks workspace client
        catalog: Catalog name (e.g., 'christophe_chieu')
        schema: Schema name (e.g., 'certified_tables')
        
    Returns:
        List of dictionaries with table information for dropdown options
    """
    try:
        tables = []
        # List all tables in the schema
        for table in workspace_client.tables.list(catalog_name=catalog, schema_name=schema):
            full_name = f"{table.catalog_name}.{table.schema_name}.{table.name}"
            tables.append({
                'label': f"{table.name} ({table.table_type})",
                'value': full_name
            })
        
        return sorted(tables, key=lambda x: x['label'])
    
    except Exception as e:
        print(f"Error listing tables from {catalog}.{schema}: {e}")
        return []


def get_table_columns(workspace_client: WorkspaceClient, full_table_name: str) -> Tuple[List[Dict[str, str]], str, str, bool]:
    """
    Get column information for a Unity Catalog table
    
    Args:
        workspace_client: Databricks workspace client
        full_table_name: Full table name in format 'catalog.schema.table'
        
    Returns:
        Tuple of (list of column info dicts with 'name', 'type', 'comment', and 'is_measure', 
                  SQL query string, table comment, is_metric_view)
    """
    try:
        # Parse the full table name
        parts = full_table_name.split('.')
        if len(parts) != 3:
            return [], "", "", False
        
        catalog, schema, table = parts
        
        # Get table information
        table_info = workspace_client.tables.get(full_name=full_table_name)
        
        # Extract table comment
        table_comment = table_info.comment if hasattr(table_info, 'comment') and table_info.comment else "No description available"
        
        # Check if this is a metric view by looking for measure columns in type_json metadata
        is_metric_view = False
        columns = []
        if table_info.columns:
            for col in table_info.columns:
                col_type = col.type_name if hasattr(col, 'type_name') else col.type_text
                
                # Check type_json metadata for metric_view.type
                is_measure = False
                if hasattr(col, 'type_json') and col.type_json:
                    try:
                        import json
                        type_data = json.loads(col.type_json) if isinstance(col.type_json, str) else col.type_json
                        metadata = type_data.get('metadata', {})
                        metric_view_type = metadata.get('metric_view.type', '')
                        
                        if metric_view_type == 'measure':
                            is_measure = True
                            is_metric_view = True  # If we find any measure column, it's a metric view
                            print(f"   📏 Measure column detected: {col.name}")
                        elif metric_view_type == 'dimension':
                            print(f"   📐 Dimension column: {col.name}")
                    except:
                        pass
                
                columns.append({
                    'name': col.name,
                    'type': col_type if col_type and col_type != "NONE" else "MEASURE" if is_measure else "STRING",
                    'comment': col.comment if hasattr(col, 'comment') and col.comment else "No description available",
                    'is_measure': is_measure
                })
        
        print(f"📊 Table type: {table_info.table_type if hasattr(table_info, 'table_type') else 'UNKNOWN'}")
        print(f"📊 Is metric view: {is_metric_view}")
        
        # Create SQL query
        sql_query = f"SELECT * FROM {full_table_name}"
        
        return columns, sql_query, table_comment, is_metric_view
    
    except Exception as e:
        print(f"Error getting columns from {full_table_name}: {e}")
        return [], "", "", False


def create_dataset_from_table(workspace_client: WorkspaceClient, full_table_name: str) -> Dict:
    """
    Create a dataset configuration from a Unity Catalog table
    
    Args:
        workspace_client: Databricks workspace client
        full_table_name: Full table name in format 'catalog.schema.table'
        
    Returns:
        Dataset configuration dictionary matching Databricks dashboard format
    """
    try:
        columns_info, sql_query, table_comment, is_metric_view = get_table_columns(workspace_client, full_table_name)
        
        if not columns_info:
            return None
        
        # Extract just the column names for the dataset
        column_names = [col['name'] for col in columns_info]
        
        # Generate a unique 8-character alphanumeric name for the dataset
        # (matching the format used by existing datasets like "39a5402c")
        import random
        import string
        dataset_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        # Format SQL query as multi-line for better readability (matching existing format)
        # IMPORTANT: Unity Catalog tables need backticks around each part of the three-part name
        parts = full_table_name.split('.')
        if len(parts) == 3:
            # Format as: `catalog`.`schema`.`table`
            formatted_table = f"`{parts[0]}`.`{parts[1]}`.`{parts[2]}`"
        else:
            # Fallback if not three parts
            formatted_table = full_table_name
        
        # For metric views, use asset_name instead of queryLines
        if is_metric_view:
            print(f"📊 Creating dataset for METRIC VIEW using asset_name")
            dataset = {
                'name': dataset_id,  # Use short generated ID
                'displayName': full_table_name.split('.')[-1],  # Just the table name for display
                'asset_name': full_table_name  # Point directly to the metric view
            }
        else:
            # Regular table - use SELECT * with queryLines
            query_lines = [
                "SELECT\n",
                "  *\n",
                "FROM\n",
                f"  {formatted_table}\n"
            ]
            
            dataset = {
                'name': dataset_id,  # Use short generated ID, not the full table name
                'displayName': full_table_name.split('.')[-1],  # Just the table name for display
                'queryLines': query_lines  # Array of query line strings
            }
        
        # Return both the dataset and the columns info (columns info is used separately, not in dataset)
        return dataset
    
    except Exception as e:
        print(f"Error creating dataset from {full_table_name}: {e}")
        return None