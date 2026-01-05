"""
Filter Widget Generator
Creates filter widget configurations for Databricks Lakeview dashboards
"""
from typing import List


def create_filter_widget(filter_column: str, dataset_name: str = "39a5402c", dashboard_id: str = "temp_dashboard") -> dict:
    """
    Create a filter widget configuration for Databricks Lakeview
    
    Args:
        filter_column: Column name to use for filtering
        dataset_name: Dataset identifier
        dashboard_id: Dashboard ID for query naming
        
    Returns:
        Filter widget configuration dictionary
    """
    
    # Generate unique query name
    query_name = f"dashboards/{dashboard_id}/datasets/{dataset_name}_{filter_column}"
    
    widget_config = {
        "name": f"filter_{filter_column.lower()}",
        "queries": [
            {
                "name": query_name,
                "query": {
                    "datasetName": dataset_name,
                    "fields": [
                        {
                            "name": filter_column,
                            "expression": f"`{filter_column}`"
                        },
                        {
                            "name": f"{filter_column}_associativity",
                            "expression": "COUNT_IF(`associative_filter_predicate_group`)"
                        }
                    ],
                    "disaggregated": False
                }
            }
        ],
        "spec": {
            "version": 2,
            "widgetType": "filter-single-select",
            "encodings": {
                "fields": [
                    {
                        "fieldName": filter_column,
                        "queryName": query_name
                    }
                ]
            },
            "frame": {
                "showTitle": True
            }
        }
    }
    
    return widget_config

