"""
Bar Chart Widget Generator
Creates bar chart widget configurations for Databricks Lakeview dashboards
"""
from typing import Optional


def create_bar_chart_widget(
    x_column: str,
    y_column: str,
    y_aggregation: str = "COUNT",
    color_column: Optional[str] = None,
    dataset_name: str = "39a5402c",
    widget_name: Optional[str] = None,
    title: Optional[str] = None
) -> dict:
    """
    Create a bar chart widget configuration for Databricks Lakeview
    
    Args:
        x_column: Column for X-axis (measure/quantitative)
        y_column: Column for Y-axis (dimension/categorical)
        y_aggregation: Aggregation function (COUNT, SUM, AVG, MAX, MIN)
        color_column: Optional column for color encoding
        dataset_name: Dataset identifier
        widget_name: Optional custom widget name
        title: Optional title for the chart
        
    Returns:
        Bar chart widget configuration dictionary
    """
    
    if widget_name is None:
        widget_name = f"bar_{y_column}_{x_column}".lower()
    
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
        x_display = x_column.replace('_', ' ').title()
        y_display = y_column.replace('_', ' ').title()
        
        title = f"{agg_display} {x_display} by {y_display}"
    
    # Build aggregation expression
    agg_field_name = f"{y_aggregation.lower()}({x_column})"
    if y_aggregation.upper() == "COUNT":
        agg_expression = f"COUNT(`{x_column}`)"
    elif y_aggregation.upper() == "SUM":
        agg_expression = f"SUM(`{x_column}`)"
    elif y_aggregation.upper() == "AVG":
        agg_expression = f"AVG(`{x_column}`)"
    elif y_aggregation.upper() == "MAX":
        agg_expression = f"MAX(`{x_column}`)"
    elif y_aggregation.upper() == "MIN":
        agg_expression = f"MIN(`{x_column}`)"
    else:
        agg_expression = f"COUNT(`{x_column}`)"
    
    # Build query fields
    query_fields = [
        {
            "name": y_column,
            "expression": f"`{y_column}`"
        },
        {
            "name": agg_field_name,
            "expression": agg_expression
        }
    ]
    
    # Build encodings
    encodings = {
        "x": {
            "fieldName": agg_field_name,
            "scale": {
                "type": "quantitative"
            }
        },
        "y": {
            "fieldName": y_column,
            "scale": {
                "type": "categorical"
            }
        }
    }
    
    # Add color encoding if specified
    if color_column:
        encodings["color"] = {
            "fieldName": color_column,
            "scale": {
                "type": "categorical"
            }
        }
        # Add color column to query if it's different from y_column
        if color_column != y_column:
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
            "widgetType": "bar",
            "encodings": encodings,
            "frame": {
                "title": title,
                "showTitle": True
            }
        }
    }
    
    return widget_config

