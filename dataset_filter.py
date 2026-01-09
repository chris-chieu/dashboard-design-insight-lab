"""
Dataset Filter Operations
Add WHERE clause filters directly to dataset queries
"""
from typing import List, Dict, Any
import copy


def apply_simple_filter_to_dataset(dataset_config: Dict[str, Any], filter_column: str, filter_values: List[str]) -> Dict[str, Any]:
    """
    Apply a filter directly to a dataset configuration (not full dashboard config)
    
    Args:
        dataset_config: The dataset configuration dictionary
        filter_column: Column name to filter
        filter_values: List of values to filter by
        
    Returns:
        Updated dataset configuration
    """
    updated_config = copy.deepcopy(dataset_config)
    
    # Build filter condition
    if len(filter_values) == 1:
        filter_condition = f"  AND {filter_column} = '{filter_values[0]}'\n"
    else:
        # Multiple values: use IN clause
        values_str = "', '".join(filter_values)
        filter_condition = f"  AND {filter_column} IN ('{values_str}')\n"
    
    # Find the line with semicolon that ends the WHERE clause
    # This should be the line with "!= 0;" or similar at the end of WHERE
    query_lines = updated_config.get("queryLines", [])
    insert_index = -1
    
    # Look for lines that end with semicolon (end of WHERE clause)
    # We want to find the semicolon that's part of the main SELECT, not subqueries
    for i in range(len(query_lines) - 1, -1, -1):  # Search backwards
        line = query_lines[i]
        # Find a line with semicolon that's not inside a subquery
        if ";" in line and "SELECT" not in line.upper() and "FROM" not in line.upper():
            insert_index = i
            break
    
    if insert_index >= 0:
        # Remove semicolon from the line that has it
        query_lines[insert_index] = query_lines[insert_index].replace(";", "")
        # Insert filter condition after that line
        query_lines.insert(insert_index + 1, filter_condition)
        # Add semicolon to the filter condition line
        query_lines[insert_index + 1] = query_lines[insert_index + 1].rstrip("\n") + ";"
    else:
        # Fallback: add at the end
        if query_lines and ";" in query_lines[-1]:
            query_lines[-1] = query_lines[-1].replace(";", "")
            query_lines.append(filter_condition.rstrip("\n") + ";")
        else:
            query_lines.append(filter_condition)
    
    updated_config["queryLines"] = query_lines
    
    return updated_config


def get_dataset_filters_summary(dataset_config: Dict[str, Any]) -> List[str]:
    """
    Extract a summary of WHERE filters from a dataset configuration
    
    Args:
        dataset_config: The dataset configuration dictionary
        
    Returns:
        List of filter condition strings
    """
    query_lines = dataset_config.get('queryLines', [])
    filters = []
    
    in_where = False
    for line in query_lines:
        line_upper = line.upper().strip()
        if 'WHERE' in line_upper:
            in_where = True
            continue
        
        if in_where:
            # Check if we've left the WHERE clause
            if any(keyword in line_upper for keyword in ['ORDER BY', 'GROUP BY', 'LIMIT', 'FROM (']):
                if not line.strip().startswith('AND'):
                    break
            
            # Extract filter condition
            stripped = line.strip().strip(',\n;')
            if stripped and stripped.upper().startswith('AND '):
                filters.append(stripped[4:])  # Remove 'AND '
            elif stripped and not stripped.startswith('(') and '=' in stripped or 'IN' in stripped.upper():
                filters.append(stripped)
    
    return filters

