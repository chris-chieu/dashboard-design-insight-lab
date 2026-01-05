"""
Line Chart Widget Generator
Creates line chart widget configurations for Databricks Lakeview dashboards
"""
from typing import Optional


def create_line_chart_widget(
    x_column: str,
    y_column: str,
    y_aggregation: str = "COUNT",
    time_granularity: str = "MONTH",
    color_column: Optional[str] = None,
    dataset_name: str = "39a5402c",
    widget_name: Optional[str] = None,
    title: Optional[str] = None
) -> dict:
    """
    Create a line chart widget configuration for Databricks Lakeview
    
    Args:
        x_column: Column for X-axis (temporal/date column)
        y_column: Column for Y-axis (measure to aggregate)
        y_aggregation: Aggregation function (COUNT, SUM, AVG, MAX, MIN)
        time_granularity: Time granularity (YEAR, QUARTER, MONTH, WEEK, DAY, HOUR, MINUTE)
        color_column: Optional column for color encoding (multiple lines)
        dataset_name: Dataset identifier
        widget_name: Optional custom widget name
        title: Optional title for the chart
        
    Returns:
        Line chart widget configuration dictionary
    """
    
    if widget_name is None:
        widget_name = f"line_{x_column}_{y_column}".lower()
    
    # Generate user-friendly default title if not provided
    if not title:
        # Convert aggregation to readable format
        agg_display = {
            'count': 'Count',
            'sum': 'Total',
            'avg': 'Average',
            'max': 'Maximum',
            'min': 'Minimum'
        }.get(y_aggregation.lower(), y_aggregation.title())
        
        # Convert column names to readable format
        y_display = y_column.replace('_', ' ').title()
        
        title = f"{agg_display} {y_display} Over Time"
    
    # Build time field with DATE_TRUNC
    time_granularity_upper = time_granularity.upper()
    time_field_name = f"{time_granularity.lower()}({x_column})"
    time_expression = f'DATE_TRUNC("{time_granularity_upper}", `{x_column}`)'
    
    # Build aggregation expression
    agg_field_name = f"{y_aggregation.lower()}({y_column})"
    if y_aggregation.upper() == "COUNT":
        agg_expression = f"COUNT(`{y_column}`)"
    elif y_aggregation.upper() == "SUM":
        agg_expression = f"SUM(`{y_column}`)"
    elif y_aggregation.upper() == "AVG":
        agg_expression = f"AVG(`{y_column}`)"
    elif y_aggregation.upper() == "MAX":
        agg_expression = f"MAX(`{y_column}`)"
    elif y_aggregation.upper() == "MIN":
        agg_expression = f"MIN(`{y_column}`)"
    else:
        agg_expression = f"COUNT(`{y_column}`)"
    
    # Build query fields
    query_fields = [
        {
            "name": time_field_name,
            "expression": time_expression
        },
        {
            "name": agg_field_name,
            "expression": agg_expression
        }
    ]
    
    # Build encodings
    encodings = {
        "x": {
            "fieldName": time_field_name,
            "scale": {
                "type": "temporal"
            }
        },
        "y": {
            "fieldName": agg_field_name,
            "scale": {
                "type": "quantitative"
            }
        }
    }
    
    # Add color encoding if specified (for multiple lines)
    if color_column:
        encodings["color"] = {
            "fieldName": color_column,
            "scale": {
                "type": "categorical"
            }
        }
        # Add color column to query
        query_fields.insert(1, {
            "name": color_column,
            "expression": f"`{color_column}`"
        })
    
    widget_config = {
        "name": widget_name,
        "queries": [
            {
                "name": "main_query",
                "query": {
                    "datasetName": dataset_name,
                    "fields": query_fields,
                    "disaggregated": False
                }
            }
        ],
        "spec": {
            "version": 3,
            "widgetType": "line",
            "encodings": encodings,
            "frame": {
                "title": title,
                "showTitle": True
            }
        }
    }
    
    return widget_config

