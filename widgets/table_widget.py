"""
Table Widget Generator
Creates table widget configurations for Databricks Lakeview dashboards
"""
import json
from typing import List
from openai import OpenAI


def create_table_widget(title: str, visible_columns: List[str], dataset_name: str = "39a5402c", all_columns: List[str] = None) -> dict:
    """
    Create a table widget configuration for Databricks Lakeview
    
    Args:
        title: Widget title
        visible_columns: List of column names to display
        dataset_name: Dataset identifier
        all_columns: All columns from the dataset (for invisibleColumns)
        
    Returns:
        Table widget configuration dictionary
    """
    
    def infer_column_type_details(col_name: str) -> dict:
        """Infer column type and return full configuration"""
        col_lower = col_name.lower()
        
        # Base config
        base_config = {
            "booleanValues": ["false", "true"],
            "imageUrlTemplate": "{{ @ }}",
            "imageTitleTemplate": "{{ @ }}",
            "imageWidth": "",
            "imageHeight": "",
            "linkUrlTemplate": "{{ @ }}",
            "linkTextTemplate": "{{ @ }}",
            "linkTitleTemplate": "{{ @ }}",
            "linkOpenInNewTab": True,
            "allowSearch": False,
            "allowHTML": False,
            "highlightLinks": False,
            "useMonospaceFont": False,
            "preserveWhitespace": False
        }
        
        # Timestamp/Date columns
        if any(keyword in col_lower for keyword in ['time', 'date', 'timestamp', 'created', 'updated', 'close']):
            return {
                **base_config,
                "dateTimeFormat": "DD/MM/YYYY HH:mm:ss.SSS",
                "type": "datetime",
                "displayAs": "datetime",
                "alignContent": "right"
            }
        
        # Integer ID columns
        if 'id' in col_lower and not any(x in col_lower for x in ['latitude', 'longitude']):
            return {
                **base_config,
                "numberFormat": "0",
                "type": "integer",
                "displayAs": "number",
                "alignContent": "right"
            }
        
        # Float/Decimal columns
        if any(keyword in col_lower for keyword in ['latitude', 'longitude', 'survey', 'interactions', 'adjusted']):
            return {
                **base_config,
                "numberFormat": "0.00",
                "type": "float",
                "displayAs": "number",
                "alignContent": "right"
            }
        
        # Datetime resolve/response columns
        if any(keyword in col_lower for keyword in ['sla', 'resolution', 'response']) and not 'for' in col_lower:
            return {
                **base_config,
                "dateTimeFormat": "DD/MM/YYYY HH:mm:ss.SSS",
                "type": "datetime",
                "displayAs": "datetime",
                "alignContent": "right"
            }
        
        # Default to string
        return {
            **base_config,
            "type": "string",
            "displayAs": "string",
            "alignContent": "left"
        }
    
    # If all_columns not provided, use visible_columns
    if all_columns is None:
        all_columns = visible_columns
    
    # Create visible columns config
    visible_cols_config = []
    for idx, col in enumerate(visible_columns):
        col_config = infer_column_type_details(col)
        visible_cols_config.append({
            "fieldName": col,
            **col_config,
            "visible": True,
            "order": 100000 + idx,
            "title": col
        })
    
    # Create invisible columns config (all columns not in visible)
    invisible_cols_config = []
    invisible_order = 100000 + len(visible_columns)
    for col in all_columns:
        if col not in visible_columns:
            col_config = infer_column_type_details(col)
            invisible_cols_config.append({
                "name": col,
                **col_config,
                "order": invisible_order,
                "title": col
            })
            invisible_order += 1
    
    widget_config = {
        "name": f"table_{title.replace(' ', '_').lower()}",
        "queries": [
            {
                "name": "main_query",
                "query": {
                    "datasetName": dataset_name,
                    "fields": [
                        {"name": col, "expression": f"`{col}`"}
                        for col in visible_columns
                    ],
                    "disaggregated": True
                }
            }
        ],
        "spec": {
            "version": 1,
            "widgetType": "table",
            "encodings": {
                "columns": visible_cols_config
            },
            "invisibleColumns": invisible_cols_config,
            "allowHTMLByDefault": False,
            "itemsPerPage": 25,
            "paginationSize": "default",
            "condensed": True,
            "withRowNumber": False
        }
    }
    return widget_config


def extract_columns_with_llm(sql_query: str, llm_client: OpenAI, model: str = "databricks-gpt-5") -> List[str]:
    """
    Use LLM to extract column names from SQL query
    
    Args:
        sql_query: SQL query string
        llm_client: OpenAI client configured for Databricks endpoint
        model: LLM model name
        
    Returns:
        List of column names extracted from the query
    """
    try:
        prompt = f"""Analyze this SQL query and extract ALL the column names that would be returned.
Return ONLY a JSON array of column names (strings), nothing else.

SQL Query:
{sql_query}

Return format: ["column1", "column2", "column3", ...]

Return ONLY the JSON array, no explanations."""

        response = llm_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000
        )
        
        llm_response = response.choices[0].message.content
        
        # Extract JSON array from response
        start_idx = llm_response.find('[')
        end_idx = llm_response.rfind(']') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            columns = json.loads(llm_response[start_idx:end_idx])
            return columns
        else:
            return []
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return []

