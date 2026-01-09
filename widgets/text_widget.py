"""
Text Widget Module

Creates text/markdown widgets for dashboards with customizable content.
"""

def create_text_widget(text_lines, position, dataset_name, title=None):
    """
    Create a text widget configuration for displaying text content
    
    Args:
        text_lines: List of text lines to display (or single string that will be split)
        position: Dict with x, y, width, height for widget placement
        dataset_name: Name of the dataset (not used for text widgets but kept for consistency)
        title: Optional title for the text widget (can be used as first line)
    
    Returns:
        Dict containing the complete widget configuration
    """
    import uuid
    
    # Handle different input types for text_lines
    if isinstance(text_lines, str):
        # If single string, split by newlines
        lines = text_lines.split('\n')
    elif isinstance(text_lines, list):
        lines = text_lines
    else:
        lines = [str(text_lines)]
    
    # If title is provided, add it as the first line with markdown formatting
    if title:
        lines = [f"## {title}"] + lines
    
    widget_config = {
        "widget": {
            "name": str(uuid.uuid4().hex[:8]),
            "multilineTextboxSpec": {
                "lines": lines
            }
        },
        "position": position
    }
    
    return widget_config

