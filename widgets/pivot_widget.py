"""
Pivot Widget Generator
Creates pivot table widget configurations for Databricks Lakeview dashboards
"""
from typing import List, Optional


def create_pivot_widget(
    row_columns: List[str],
    value_column: str,
    aggregation: str = "SUM",
    dataset_name: str = "39a5402c",
    widget_name: Optional[str] = None,
    title: Optional[str] = None
) -> dict:
    """
    Create a pivot table widget configuration for Databricks Lakeview
    
    Args:
        row_columns: List of columns to use as row dimensions
        value_column: Column to aggregate in cells
        aggregation: Aggregation function (SUM, COUNT, AVG, MAX, MIN)
        dataset_name: Dataset identifier
        widget_name: Optional custom widget name
        title: Optional title for the pivot table
        
    Returns:
        Pivot widget configuration dictionary
    """
    
    if widget_name is None:
        widget_name = f"pivot_{'_'.join(row_columns[:2])}".lower()
    
    # Generate user-friendly default title if not provided
    if not title:
        # Convert aggregation to readable format
        agg_display = {
            'count': 'Count',
            'sum': 'Total',
            'avg': 'Average',
            'max': 'Maximum',
            'min': 'Minimum',
            'none': ''  # For metric views, no prefix needed
        }.get(aggregation.lower(), aggregation.title())
        
        # Convert column names to readable format
        value_display = value_column.replace('_', ' ').title()
        row_display = ', '.join([col.replace('_', ' ').title() for col in row_columns])
        
        if agg_display:
            title = f"{agg_display} {value_display} by {row_display}"
        else:
            title = f"{value_display} by {row_display}"
    
    # Build aggregation expression
    # For metric views, "NONE" means use MEASURE() directly
    if aggregation.upper() == "NONE":
        agg_field_name = f"measure({value_column})"
        agg_expression = f"MEASURE(`{value_column}`)"
    elif aggregation.upper() == "COUNT":
        agg_field_name = f"{aggregation.lower()}({value_column})"
        agg_expression = f"COUNT(`{value_column}`)"
    elif aggregation.upper() == "SUM":
        agg_field_name = f"{aggregation.lower()}({value_column})"
        agg_expression = f"SUM(`{value_column}`)"
    elif aggregation.upper() == "AVG":
        agg_field_name = f"{aggregation.lower()}({value_column})"
        agg_expression = f"AVG(`{value_column}`)"
    elif aggregation.upper() == "MAX":
        agg_field_name = f"{aggregation.lower()}({value_column})"
        agg_expression = f"MAX(`{value_column}`)"
    elif aggregation.upper() == "MIN":
        agg_field_name = f"{aggregation.lower()}({value_column})"
        agg_expression = f"MIN(`{value_column}`)"
    else:
        agg_field_name = f"{aggregation.lower()}({value_column})"
        agg_expression = f"SUM(`{value_column}`)"
    
    # Build query fields - row columns first, then aggregated value
    query_fields = []
    for row_col in row_columns:
        query_fields.append({
            "name": row_col,
            "expression": f"`{row_col}`"
        })
    
    query_fields.append({
        "name": agg_field_name,
        "expression": agg_expression
    })
    
    # Build cube grouping sets
    # First set has all row columns, second set is empty for totals
    grouping_sets = [
        {"fieldNames": row_columns},
        {}
    ]
    
    # Build orders - sort by first row column
    orders = [
        {
            "direction": "ASC",
            "expression": f"`{row_columns[0]}`"
        }
    ]
    
    # Build row encodings
    row_encodings = []
    for row_col in row_columns:
        row_encodings.append({
            "fieldName": row_col
        })
    
    widget_config = {
        "name": widget_name,
        "queries": [
            {
                "name": "main_query",
                "query": {
                    "datasetName": dataset_name,
                    "fields": query_fields,
                    "cubeGroupingSets": {
                        "sets": grouping_sets
                    },
                    "disaggregated": False,
                    "orders": orders
                }
            }
        ],
        "spec": {
            "version": 3,
            "widgetType": "pivot",
            "encodings": {
                "rows": row_encodings,
                "cell": {
                    "type": "multi-cell",
                    "fields": [
                        {
                            "fieldName": agg_field_name,
                            "cellType": "text"
                        }
                    ]
                }
            },
            "frame": {
                "title": title,
                "showTitle": True
            }
        }
    }
    
    return widget_config

