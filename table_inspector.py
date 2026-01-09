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


def get_table_columns(workspace_client: WorkspaceClient, full_table_name: str) -> Tuple[List[Dict[str, str]], str]:
    """
    Get column information for a Unity Catalog table
    
    Args:
        workspace_client: Databricks workspace client
        full_table_name: Full table name in format 'catalog.schema.table'
        
    Returns:
        Tuple of (list of column info dicts with 'name' and 'type', SQL query string)
    """
    try:
        # Parse the full table name
        parts = full_table_name.split('.')
        if len(parts) != 3:
            return [], ""
        
        catalog, schema, table = parts
        
        # Get table information
        table_info = workspace_client.tables.get(full_name=full_table_name)
        
        # Extract column names and types
        columns = []
        if table_info.columns:
            columns = [
                {
                    'name': col.name,
                    'type': col.type_name if hasattr(col, 'type_name') else col.type_text
                }
                for col in table_info.columns
            ]
        
        # Create SQL query
        sql_query = f"SELECT * FROM {full_table_name}"
        
        return columns, sql_query
    
    except Exception as e:
        print(f"Error getting columns from {full_table_name}: {e}")
        return [], ""


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
        columns_info, sql_query = get_table_columns(workspace_client, full_table_name)
        
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
        # Break the query into lines at logical points
        # IMPORTANT: Unity Catalog tables need backticks around each part of the three-part name
        parts = full_table_name.split('.')
        if len(parts) == 3:
            # Format as: `catalog`.`schema`.`table`
            formatted_table = f"`{parts[0]}`.`{parts[1]}`.`{parts[2]}`"
        else:
            # Fallback if not three parts
            formatted_table = full_table_name
        
        query_lines = [
            "SELECT\n",
            "  *\n",
            "FROM\n",
            f"  {formatted_table}\n"
        ]
        
        # Create dataset configuration matching EXACTLY the structure of existing datasets in datasets.py
        # Only these 3 fields: name, displayName, queryLines
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