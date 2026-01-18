"""
Pie Chart Widget Module

Creates pie chart widgets for Databricks dashboards.
"""

import random
import string


def create_pie_chart_widget(value_column, aggregation, category_column, dataset_name, title=None):
    """
    Create a pie chart widget configuration
    
    Args:
        value_column: Column to aggregate for the slice sizes
        aggregation: Aggregation function (COUNT, SUM, AVG, MAX, MIN)
        category_column: Categorical column for pie slices
        dataset_name: Name of the dataset
        title: Optional title to display above the pie chart
        
    Returns:
        dict: Pie chart widget configuration
    """
    # Generate random widget name
    widget_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    # Build aggregation expression
    # For metric views, "NONE" means use MEASURE() directly
    agg_lower = aggregation.lower()
    
    if agg_lower == 'none':
        # Metric view: use MEASURE() directly
        value_field_name = f"measure({value_column})"
        value_expression = f"MEASURE(`{value_column}`)"
    else:
        # Regular table: use aggregation function
        value_field_name = f"{agg_lower}({value_column})"
        value_expression = f"{aggregation.upper()}(`{value_column}`)"
    
    # Generate user-friendly default title if not provided
    if not title:
        # Convert aggregation to readable format
        agg_display = {
            'count': 'Total',
            'sum': 'Total',
            'avg': 'Average',
            'max': 'Maximum',
            'min': 'Minimum',
            'none': ''  # For metric views, no prefix needed
        }.get(agg_lower, agg_lower.title())
        
        # Convert column names to readable format
        value_display = value_column.replace('_', ' ').title()
        category_display = category_column.replace('_', ' ').title()
        
        if agg_display:
            title = f"{agg_display} {value_display} by {category_display}"
        else:
            title = f"{value_display} by {category_display}"
    
    widget = {
        "name": widget_name,
        "queries": [
            {
                "name": "main_query",
                "query": {
                    "datasetName": dataset_name,
                    "fields": [
                        {
                            "name": value_field_name,
                            "expression": value_expression
                        },
                        {
                            "name": category_column,
                            "expression": f"`{category_column}`"
                        }
                    ],
                    "disaggregated": False
                }
            }
        ],
        "spec": {
            "version": 3,
            "widgetType": "pie",
            "encodings": {
                "angle": {
                    "fieldName": value_field_name,
                    "scale": {
                        "type": "quantitative"
                    }
                },
                "color": {
                    "fieldName": category_column,
                    "scale": {
                        "type": "categorical"
                    }
                }
            },
            "frame": {
                "title": title,
                "showTitle": True
            }
        }
    }
    
    return widget

