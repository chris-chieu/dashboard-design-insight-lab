"""
Counter Widget Module

Creates counter/KPI widgets for Databricks dashboards.
"""

import random
import string


def create_counter_widget(value_column, aggregation, dataset_name, title=None):
    """
    Create a counter/KPI widget configuration
    
    Args:
        value_column: Column to aggregate and display
        aggregation: Aggregation function (COUNT, SUM, AVG, MAX, MIN)
        dataset_name: Name of the dataset
        title: Optional title to display above the counter
        
    Returns:
        dict: Counter widget configuration
    """
    # Generate random widget name
    widget_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    # Build aggregation expression
    agg_lower = aggregation.lower()
    field_name = f"{agg_lower}({value_column})"
    expression = f"{aggregation.upper()}(`{value_column}`)"
    
    # Generate user-friendly default title if not provided
    if not title:
        # Convert aggregation to readable format
        agg_display = {
            'count': 'Total',
            'sum': 'Total',
            'avg': 'Average',
            'max': 'Maximum',
            'min': 'Minimum'
        }.get(agg_lower, agg_lower.title())
        
        # Convert column name to readable format (replace underscores with spaces, title case)
        column_display = value_column.replace('_', ' ').title()
        
        title = f"{agg_display} {column_display}"
    
    widget = {
        "name": widget_name,
        "queries": [
            {
                "name": "main_query",
                "query": {
                    "datasetName": dataset_name,
                    "fields": [
                        {
                            "name": field_name,
                            "expression": expression
                        }
                    ],
                    "disaggregated": False
                }
            }
        ],
        "spec": {
            "version": 2,
            "widgetType": "counter",
            "encodings": {
                "value": {
                    "fieldName": field_name
                }
            },
            "frame": {
                "showTitle": True,
                "title": title
            }
        }
    }
    
    return widget

