"""
Design Infusion Module

Extracts design elements (colors and fonts) from uploaded images using Vision LLM.
Includes intelligent analysis and iterative refinement capabilities.
"""

import json
from dash import html
import dash_bootstrap_components as dbc


def extract_design_from_image(contents, filename, llm_client):
    """
    Extract design elements (colors and fonts) from uploaded image using Vision LLM
    
    Args:
        contents: Base64 encoded image data
        filename: Name of uploaded file
        llm_client: OpenAI client instance
        
    Returns:
        tuple: (result_display, design_data)
    """
    if contents is None:
        return "", None
    
    try:
        import base64
        
        # Handle base64 encoding of uploaded image
        # dcc.Upload provides contents with data URL prefix (e.g., "data:image/png;base64,...")
        if ',' in contents:
            # Strip the data URL prefix if present
            image_data = contents.split(',')[1]
        else:
            # If no prefix, assume it's already base64 encoded
            image_data = contents
        
        # Prepare the vision LLM prompt
        vision_prompt = """Analyze this image and extract the following design elements in JSON format:

{
    "canvasBackgroundColor": "#HEXCODE",  // Main background/canvas color
    "widgetBackgroundColor": "#HEXCODE",  // Widget/card background color
    "widgetBorderColor": "#HEXCODE",      // Border color for widgets/cards
    "fontColor": "#HEXCODE",              // Primary text/font color
    "visualizationColors": ["#HEX1", "#HEX2", "#HEX3", "#HEX4", "#HEX5"],  // Array of 5-10 colors used in charts/visualizations
    "fontFamily": "Font Name"             // Primary font family (pick from list below)
}

Please analyze all visual elements including:
- Canvas/page background color (canvasBackgroundColor)
- Widget/card background colors (widgetBackgroundColor)
- Widget/card border colors (widgetBorderColor)
- Text/font colors (fontColor)
- Chart colors, accent colors, data visualization colors (visualizationColors - provide 5-10 colors)
- Font family used for text

For fontFamily, please pick the closest match from these options:
- Arial
- Brush Script MT
- Courier New
- Georgia
- Impact
- Tahoma
- Times New Roman
- Trebuchet MS
- Verdana

CRITICAL RULES FOR VISUALIZATION COLORS:
1. NEVER use white (#FFFFFF) or very light colors (lightness > 90%) as visualization colors if the canvas and widget backgrounds are white!

IMPORTANT: Return ONLY valid JSON without any markdown formatting or code blocks."""

        # Call Vision LLM
        print("🔍 Calling vision LLM for image analysis...")
        response = llm_client.chat.completions.create(
            model="databricks-gpt-5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        # Validate response
        if not response or not hasattr(response, 'choices') or not response.choices:
            raise ValueError("Empty or invalid response from LLM API. The model may not support vision/image inputs.")
        
        if not response.choices[0].message or not response.choices[0].message.content:
            raise ValueError("LLM response has no content. The model may have failed to process the image.")
        
        # Parse the LLM response
        llm_response = response.choices[0].message.content
        print(f"✅ Received response from vision LLM ({len(llm_response)} characters)")
        
        # Clean up response (remove markdown code blocks if present)
        llm_response = llm_response.strip()
        if llm_response.startswith('```'):
            lines = llm_response.split('\n')
            llm_response = '\n'.join(lines[1:-1]) if len(lines) > 2 else llm_response
        
        extracted_data = json.loads(llm_response)
        
        # Build the complete uiSettings structure
        ui_settings = {
            "uiSettings": {
                "theme": {
                    "canvasBackgroundColor": {
                        "light": extracted_data.get('canvasBackgroundColor', '#FAFAFB'),
                        "dark": "#1F272D"
                    },
                    "widgetBackgroundColor": {
                        "light": extracted_data.get('widgetBackgroundColor', '#FFFFFF'),
                        "dark": "#11171C"
                    },
                    "widgetBorderColor": {
                        "light": extracted_data.get('widgetBorderColor', '#E0E0E0')
                    },
                    "fontColor": {
                        "light": extracted_data.get('fontColor', '#11171C'),
                        "dark": "#E8ECF0"
                    },
                    "selectionColor": {
                        "light": "#2272B4",
                        "dark": "#8ACAFF"
                    },
                    "visualizationColors": extracted_data.get('visualizationColors', [
                        "#077A9D", "#FFAB00", "#00A972", "#FF3621", "#8BCAE7",
                        "#AB4057", "#99DDB4", "#FCA4A1", "#919191", "#BF7080"
                    ]),
                    "widgetHeaderAlignment": "LEFT",
                    "fontFamily": extracted_data.get('fontFamily', 'Times New Roman')
                },
                "genieSpace": {
                    "isEnabled": False,
                    "enablementMode": "DISABLED"
                },
                "applyModeEnabled": False
            }
        }
        
        # Create display with formatted JSON
        result_text = html.Div([
            html.H6("🎨 Extracted Design Elements", className="mb-3"),
            html.Div([
                html.P([
                    html.Strong("Canvas Background Color: "),
                    html.Span(extracted_data.get('canvasBackgroundColor', 'N/A'))
                ], className="mb-2"),
                html.P([
                    html.Strong("Widget Background Color: "),
                    html.Span(extracted_data.get('widgetBackgroundColor', 'N/A'))
                ], className="mb-2"),
                html.P([
                    html.Strong("Widget Border Color: "),
                    html.Span(extracted_data.get('widgetBorderColor', 'N/A'))
                ], className="mb-2"),
                html.P([
                    html.Strong("Font Color: "),
                    html.Span(extracted_data.get('fontColor', 'N/A'))
                ], className="mb-2"),
                html.P([
                    html.Strong("Visualization Colors: "),
                    html.Span(', '.join(extracted_data.get('visualizationColors', [])))
                ], className="mb-2"),
                html.P([
                    html.Strong("Font Family: "),
                    html.Span(extracted_data.get('fontFamily', 'N/A'))
                ], className="mb-2"),
                html.Hr(),
                html.P(html.Strong("Complete uiSettings JSON:"), className="mb-2"),
                html.Pre(
                    json.dumps(ui_settings, indent=2),
                    style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '10px',
                        'borderRadius': '5px',
                        'fontSize': '12px',
                        'maxHeight': '300px',
                        'overflowY': 'auto'
                    }
                )
            ], style={'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '8px', 'border': '1px solid #dee2e6'})
        ])
        
        return result_text, ui_settings
        
    except json.JSONDecodeError as e:
        import traceback
        traceback.print_exc()
        print(f"❌ JSON Decode Error in image analysis: {str(e)}")
        print(f"   Raw LLM response: {llm_response if 'llm_response' in locals() else 'Not available'}")
        error_msg = dbc.Alert([
            html.Strong("❌ Failed to parse LLM response"),
            html.Br(),
            html.P("The AI response was not in valid JSON format.", className="mb-2"),
            html.Small(f"Error: {str(e)}", className="mb-2"),
            html.Hr(),
            html.Small("Check the console for the raw response.", className="text-muted")
        ], color="danger")
        return error_msg, None
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Error analyzing image: {str(e)}")
        print(f"   Full traceback:\n{error_trace}")
        
        # Provide specific error messages
        error_details = str(e)
        if 'subscript' in error_details.lower() or 'NoneType' in error_details:
            specific_msg = "The vision model (databricks-gpt-5) may not support image analysis or returned an empty response. Consider using a vision-capable model like databricks-gpt-4o or databricks-claude-sonnet."
        elif 'API' in error_details or 'authentication' in error_details.lower():
            specific_msg = "API authentication or connection error."
        elif 'model' in error_details.lower():
            specific_msg = "Model error. The specified model may not support vision/image inputs."
        else:
            specific_msg = "An unexpected error occurred during image analysis."
        
        error_msg = dbc.Alert([
            html.Strong("❌ Error analyzing image"),
            html.Br(),
            html.P(specific_msg, className="mb-2"),
            html.Small([
                html.Strong("Error: "),
                str(e)
            ], className="mb-2"),
            html.Hr(),
            html.Small("Tip: Ensure you're using a vision-capable model and that the image is a valid format (PNG, JPG, etc.).", className="text-muted")
        ], color="danger")
        return error_msg, None


def generate_design_from_prompt(prompt_text, llm_client):
    """
    Generate design elements based on text prompt using LLM reasoning
    
    Args:
        prompt_text: User's description of desired design style
        llm_client: OpenAI client instance
        
    Returns:
        tuple: (result_display, design_data)
    """
    if not prompt_text or not prompt_text.strip():
        return "", None
    
    try:
        # Prepare the LLM prompt for design generation
        design_prompt = f"""Based on the following user request, generate a complete design theme for a dashboard.

User Request: "{prompt_text}"

Generate design elements that match the style, mood, and aesthetic described. Think about:
- What colors would represent this style? (background, widgets, text, visualizations)
- What font would match this aesthetic?

Return your design as JSON in this EXACT format:

{{
    "canvasBackgroundColor": "#HEXCODE",  // Main background/canvas color
    "widgetBackgroundColor": "#HEXCODE",  // Widget/card background color
    "widgetBorderColor": "#HEXCODE",      // Border color for widgets/cards
    "fontColor": "#HEXCODE",              // Primary text/font color
    "visualizationColors": ["#HEX1", "#HEX2", "#HEX3", "#HEX4", "#HEX5", "#HEX6", "#HEX7", "#HEX8"],  // Array of 5-10 colors for charts/visualizations
    "fontFamily": "Font Name"             // Primary font family (pick from list below)
}}

CRITICAL RULES FOR VISUALIZATION COLORS:
1. Colors MUST be clearly distinguishable from each other on charts (bar charts, pie charts, etc.)
2. Avoid colors that are too similar in hue, saturation, or lightness (e.g., #8BC34A and #9CCC65 are TOO CLOSE)
3. Prefer using DIFFERENT color families (e.g., blue, orange, green, red, purple) rather than multiple shades of the same color
4. If using colors from the same family, ensure SIGNIFICANT contrast (at least 40% difference in lightness/saturation)
5. Test for accessibility: colors should be distinguishable even for color-blind users
6. NEVER use white (#FFFFFF) or very light colors (lightness > 90%) as visualization colors if the canvas and widget backgrounds are white!
7. Good example: ["#2196F3", "#FF9800", "#4CAF50", "#F44336", "#9C27B0", "#00BCD4", "#FFEB3B", "#795548"]
8. Bad example: ["#8BC34A", "#9CCC65", "#AED581"] - too similar!
9. Bad example: ["#FFFFFF", "#FAFAFA", "#F5F5F5"] - too light, invisible on white background!

For fontFamily, you MUST pick ONE from these options:
- Arial
- Brush Script MT
- Courier New
- Georgia
- Impact
- Tahoma
- Times New Roman
- Trebuchet MS
- Verdana

Examples:
- For "Van Gogh painting style": Use vibrant blues (#4169E1), yellows (#FFD700), oranges (#FF8C00), greens (#228B22), purples (#8B008B), contrasting warm colors, "Brush Script MT"
- For "Modern minimalist": Use distinct blues (#2196F3), teals (#00BCD4), grays (#9E9E9E), blacks (#424242), with high contrast, "Arial"
- For "Corporate professional": Use navy (#003366), teal (#00796B), orange (#F57C00), slate (#455A64), distinct professional colors, "Georgia"

IMPORTANT: Return ONLY valid JSON without any markdown formatting or code blocks."""

        # Call LLM
        response = llm_client.chat.completions.create(
            model="databricks-gpt-5",
            messages=[
                {
                    "role": "user",
                    "content": design_prompt
                }
            ],
            max_tokens=500
        )
        
        # Parse the LLM response
        llm_response = response.choices[0].message.content
        
        # Clean up response (remove markdown code blocks if present)
        llm_response = llm_response.strip()
        if llm_response.startswith('```'):
            lines = llm_response.split('\n')
            llm_response = '\n'.join(lines[1:-1]) if len(lines) > 2 else llm_response
        
        extracted_data = json.loads(llm_response)
        
        # Build the complete uiSettings structure
        ui_settings = {
            "uiSettings": {
                "theme": {
                    "canvasBackgroundColor": {
                        "light": extracted_data.get('canvasBackgroundColor', '#FAFAFB'),
                        "dark": "#1F272D"
                    },
                    "widgetBackgroundColor": {
                        "light": extracted_data.get('widgetBackgroundColor', '#FFFFFF'),
                        "dark": "#11171C"
                    },
                    "widgetBorderColor": {
                        "light": extracted_data.get('widgetBorderColor', '#E0E0E0')
                    },
                    "fontColor": {
                        "light": extracted_data.get('fontColor', '#11171C'),
                        "dark": "#E8ECF0"
                    },
                    "selectionColor": {
                        "light": "#2272B4",
                        "dark": "#8ACAFF"
                    },
                    "visualizationColors": extracted_data.get('visualizationColors', [
                        "#077A9D", "#FFAB00", "#00A972", "#FF3621", "#8BCAE7",
                        "#AB4057", "#99DDB4", "#FCA4A1", "#919191", "#BF7080"
                    ]),
                    "widgetHeaderAlignment": "LEFT",
                    "fontFamily": extracted_data.get('fontFamily', 'Times New Roman')
                },
                "genieSpace": {
                    "isEnabled": False,
                    "enablementMode": "DISABLED"
                },
                "applyModeEnabled": False
            }
        }
        
        # Create display with formatted JSON
        result_text = html.Div([
            html.H6("🎨 AI-Generated Design Elements", className="mb-3"),
            dbc.Alert([
                html.Strong("💡 AI Interpretation: "),
                html.Span(f'Generated design based on: "{prompt_text}"')
            ], color="info", className="mb-3"),
            html.Div([
                html.P([
                    html.Strong("Canvas Background Color: "),
                    html.Span(extracted_data.get('canvasBackgroundColor', 'N/A'))
                ], className="mb-2"),
                html.P([
                    html.Strong("Widget Background Color: "),
                    html.Span(extracted_data.get('widgetBackgroundColor', 'N/A'))
                ], className="mb-2"),
                html.P([
                    html.Strong("Widget Border Color: "),
                    html.Span(extracted_data.get('widgetBorderColor', 'N/A'))
                ], className="mb-2"),
                html.P([
                    html.Strong("Font Color: "),
                    html.Span(extracted_data.get('fontColor', 'N/A'))
                ], className="mb-2"),
                html.P([
                    html.Strong("Visualization Colors: "),
                    html.Span(', '.join(extracted_data.get('visualizationColors', [])))
                ], className="mb-2"),
                html.P([
                    html.Strong("Font Family: "),
                    html.Span(extracted_data.get('fontFamily', 'N/A'))
                ], className="mb-2"),
                html.Hr(),
                html.P(html.Strong("Complete uiSettings JSON:"), className="mb-2"),
                html.Pre(
                    json.dumps(ui_settings, indent=2),
                    style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '10px',
                        'borderRadius': '5px',
                        'fontSize': '12px',
                        'maxHeight': '300px',
                        'overflowY': 'auto'
                    }
                )
            ], style={'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '8px', 'border': '1px solid #dee2e6'})
        ])
        
        return result_text, ui_settings
        
    except json.JSONDecodeError as e:
        error_msg = dbc.Alert([
            html.Strong("❌ Failed to parse AI response"),
            html.Br(),
            html.Small(f"The AI response was not in valid JSON format. Error: {str(e)}")
        ], color="danger")
        return error_msg, None
        
    except Exception as e:
        error_msg = dbc.Alert([
            html.Strong("❌ Error generating design"),
            html.Br(),
            html.Small(f"Error: {str(e)}")
        ], color="danger")
        return error_msg, None


def analyze_dashboard_layout(dashboard_config):
    """
    Analyze the current dashboard configuration to extract layout information.
    
    Args:
        dashboard_config: Dashboard configuration dict (with serialized_dashboard)
        
    Returns:
        dict: Analysis with widget counts, current colors, layout structure
    """
    try:
        # Extract serialized_dashboard if wrapped
        if 'serialized_dashboard' in dashboard_config:
            config = dashboard_config['serialized_dashboard']
            if isinstance(config, str):
                config = json.loads(config)
        else:
            config = dashboard_config
        
        # Extract layout information
        layout = config.get('pages', [{}])[0].get('layout', [])
        
        # Count widget types
        widget_counts = {}
        widget_details = []
        
        for item in layout:
            widget = item.get('widget', {})
            position = item.get('position', {})
            
            # Determine widget type
            widget_type = "Unknown"
            if 'tableSpec' in widget:
                widget_type = "Table"
            elif 'filterSpec' in widget:
                widget_type = "Filter"
            elif 'chartSpec' in widget:
                chart_type = widget['chartSpec'].get('type', 'Unknown')
                widget_type = f"{chart_type.capitalize()} Chart"
            elif 'counterSpec' in widget:
                widget_type = "Counter (KPI)"
            elif 'pivotSpec' in widget:
                widget_type = "Pivot Table"
            elif 'multilineTextboxSpec' in widget:
                widget_type = "Text/Spacer"
            
            # Count
            widget_counts[widget_type] = widget_counts.get(widget_type, 0) + 1
            
            # Store details
            widget_details.append({
                'type': widget_type,
                'position': position,
                'name': widget.get('name', 'N/A')
            })
        
        # Extract current theme if exists
        current_theme = config.get('uiSettings', {}).get('theme', {})
        current_colors = {
            'canvasBackground': current_theme.get('canvasBackgroundColor', {}).get('light', '#FAFAFB'),
            'widgetBackground': current_theme.get('widgetBackgroundColor', {}).get('light', '#FFFFFF'),
            'widgetBorder': current_theme.get('widgetBorderColor', {}).get('light', '#E0E0E0'),
            'fontColor': current_theme.get('fontColor', {}).get('light', '#11171C'),
            'visualizationColors': current_theme.get('visualizationColors', []),
            'fontFamily': current_theme.get('fontFamily', 'Arial')
        }
        
        # Calculate layout metrics
        max_y = max([item.get('position', {}).get('y', 0) + item.get('position', {}).get('height', 0) for item in layout]) if layout else 0
        max_x = max([item.get('position', {}).get('x', 0) + item.get('position', {}).get('width', 0) for item in layout]) if layout else 0
        
        analysis = {
            'total_widgets': len(layout),
            'widget_counts': widget_counts,
            'widget_details': widget_details,
            'current_colors': current_colors,
            'layout_dimensions': {
                'max_y': max_y,
                'max_x': max_x,
                'estimated_rows': max_y // 2  # Rough estimate
            },
            'has_filters': 'Filter' in widget_counts,
            'has_kpis': 'Counter (KPI)' in widget_counts,
            'has_charts': any('Chart' in wtype for wtype in widget_counts.keys()),
            'has_tables': 'Table' in widget_counts or 'Pivot Table' in widget_counts
        }
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing dashboard layout: {e}")
        return {
            'error': str(e),
            'total_widgets': 0,
            'widget_counts': {},
            'current_colors': {}
        }


def generate_design_with_analysis(prompt_text, dashboard_config, llm_client):
    """
    Generate design with AI reasoning based on dashboard analysis and user prompt.
    This is a multi-step process that returns analysis and reasoning before applying.
    
    Args:
        prompt_text: User's design description
        dashboard_config: Current dashboard configuration
        llm_client: OpenAI client instance
        
    Returns:
        tuple: (analysis_display, reasoning_display, design_data, analysis_text, reasoning_text)
    """
    if not prompt_text or not prompt_text.strip():
        return "", "", None, None, None
    
    try:
        # Step 1: Analyze current dashboard
        print("🔍 Step 1: Analyzing current dashboard layout...")
        analysis = analyze_dashboard_layout(dashboard_config)
        
        # Create analysis display
        analysis_display = html.Div([
            html.H6("📊 Dashboard Analysis", className="mb-3"),
            dbc.Card([
                dbc.CardBody([
                    html.P([
                        html.Strong("Total Widgets: "),
                        html.Span(str(analysis['total_widgets']))
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Widget Types: "),
                        html.Ul([
                            html.Li(f"{wtype}: {count}") 
                            for wtype, count in analysis.get('widget_counts', {}).items()
                        ])
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Current Colors: "),
                        html.Ul([
                            html.Li(f"Canvas: {analysis['current_colors'].get('canvasBackground', 'N/A')}"),
                            html.Li(f"Widgets: {analysis['current_colors'].get('widgetBackground', 'N/A')}"),
                            html.Li(f"Font: {analysis['current_colors'].get('fontColor', 'N/A')}"),
                            html.Li(f"Font Family: {analysis['current_colors'].get('fontFamily', 'N/A')}")
                        ])
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Layout Structure: "),
                        html.Span(f"~{analysis['layout_dimensions'].get('estimated_rows', 0)} rows, ")
                    ] + [
                        html.Span(f"{'✓ Filters' if analysis.get('has_filters') else ''} "),
                        html.Span(f"{'✓ KPIs' if analysis.get('has_kpis') else ''} "),
                        html.Span(f"{'✓ Charts' if analysis.get('has_charts') else ''} "),
                        html.Span(f"{'✓ Tables' if analysis.get('has_tables') else ''} ")
                    ], className="mb-2")
                ])
            ], color="light", className="mb-3")
        ])
        
        # Create analysis text for LLM
        analysis_text = f"""Dashboard Structure Analysis:
- Total widgets: {analysis['total_widgets']}
- Widget types: {', '.join([f'{k} ({v})' for k, v in analysis.get('widget_counts', {}).items()])}
- Current colors: Canvas {analysis['current_colors'].get('canvasBackground')}, Widgets {analysis['current_colors'].get('widgetBackground')}, Font {analysis['current_colors'].get('fontColor')}
- Current font: {analysis['current_colors'].get('fontFamily')}
- Layout: ~{analysis['layout_dimensions'].get('estimated_rows', 0)} rows with {'filters, ' if analysis.get('has_filters') else ''}{'KPIs, ' if analysis.get('has_kpis') else ''}{'charts, ' if analysis.get('has_charts') else ''}{'tables' if analysis.get('has_tables') else ''}"""
        
        # Step 2: Generate design with reasoning
        print("🎨 Step 2: Generating design with AI reasoning...")
        
        reasoning_prompt = f"""You are an expert dashboard designer. You have analyzed the current dashboard and received a design request from the user.

CURRENT DASHBOARD ANALYSIS:
{analysis_text}

USER'S DESIGN REQUEST:
"{prompt_text}"

Your task is to:
1. First, provide feedback on the CURRENT dashboard design
2. Then, create a new design that fulfills the user's request

Please provide your response in THREE parts:

PART 1 - CURRENT STYLE FEEDBACK:
Evaluate the current dashboard design in a structured format:

✅ What works well:
[Describe what's good about current colors, contrast, readability]

⚠️ What could be improved:
[Specific issues with current colors, font, etc. If the design is already excellent, state "The current design is already well-executed with good color choices, contrast, and readability. No major improvements needed from a design quality perspective."]

📊 Impact on usability:
[How the current design affects dashboard usability - be honest if it's already good]

💡 Overall impression:
[Professional, casual, cluttered, clean, etc. and why - acknowledge if the design is already strong]

IMPORTANT: Use line breaks between each section for readability.
NOTE: Be honest - if the current design is already visually appealing and follows best practices, acknowledge that!

PART 2 - NEW DESIGN REASONING:
Explain your new design choices in a structured format:

🎯 Design interpretation:
[How the user's request translates to visual design]

🔧 Specific changes:
[What changes you're making to achieve the user's requested style. If the current design is already good, frame this as "style transformation" rather than "fixes" - e.g., "While the current design is solid, we're transforming it to match the user's requested [style] aesthetic by..."]

🎨 Color palette rationale:
[What palette represents this style and why]

📈 Readability enhancement:
[How these colors will maintain or enhance readability for the {analysis['total_widgets']} widgets. If current design is already readable, emphasize "maintaining excellent readability while..."]

✍️ Font choice:
[What font complements this aesthetic and why. If keeping same font because it works well, explain why it remains a good choice.]

🔍 Special considerations:
[Any layout-specific considerations]

IMPORTANT: Use line breaks between each section for readability.
NOTE: Remember - design changes can be about style preference, not just fixing problems. A well-designed dashboard can still be transformed to match a different aesthetic!

PART 3 - DESIGN SPECIFICATION (JSON):
Return the complete response as JSON in this EXACT format:

{{
    "current_style_feedback": "Your evaluation of the current design from Part 1",
    "reasoning": "Your new design reasoning from Part 2",
    "design": {{
        "canvasBackgroundColor": "#HEXCODE",
        "widgetBackgroundColor": "#HEXCODE",
        "widgetBorderColor": "#HEXCODE",
        "fontColor": "#HEXCODE",
        "visualizationColors": ["#HEX1", "#HEX2", "#HEX3", ... 30 colors total],
        "fontFamily": "Font Name"
    }}
}}

CRITICAL RULES:
1. visualizationColors MUST contain EXACTLY 30 colors to cover all edge cases
2. Visualization colors MUST be clearly distinguishable (different hues, not just shades)
3. NEVER use white or very light colors (lightness > 90%) for visualizations if background is white
4. Ensure high contrast between text and background for readability
5. Font family MUST be one of: Arial, Brush Script MT, Courier New, Georgia, Impact, Tahoma, Times New Roman, Trebuchet MS, Verdana
6. Consider the dashboard has {analysis['total_widgets']} widgets - colors should work at scale
7. Be specific and constructive in your current design feedback
8. Create a diverse palette with distinct hues (reds, blues, greens, yellows, purples, oranges, teals, pinks, etc.)

IMPORTANT: Return ONLY valid JSON without markdown formatting."""

        # Call LLM for reasoning + design
        response = llm_client.chat.completions.create(
            model="databricks-gpt-5",
            messages=[
                {
                    "role": "user",
                    "content": reasoning_prompt
                }
            ],
            max_tokens=1000
        )
        
        # Parse LLM response
        llm_response = response.choices[0].message.content.strip()
        
        # Clean up markdown if present
        if llm_response.startswith('```'):
            lines = llm_response.split('\n')
            llm_response = '\n'.join(lines[1:-1]) if len(lines) > 2 else llm_response
        
        response_data = json.loads(llm_response)
        current_style_feedback = response_data.get('current_style_feedback', 'No feedback provided')
        reasoning_text = response_data.get('reasoning', 'No reasoning provided')
        design_data = response_data.get('design', {})
        
        # Build UI settings
        ui_settings = {
            "uiSettings": {
                "theme": {
                    "canvasBackgroundColor": {
                        "light": design_data.get('canvasBackgroundColor', '#FAFAFB'),
                        "dark": "#1F272D"
                    },
                    "widgetBackgroundColor": {
                        "light": design_data.get('widgetBackgroundColor', '#FFFFFF'),
                        "dark": "#11171C"
                    },
                    "widgetBorderColor": {
                        "light": design_data.get('widgetBorderColor', '#E0E0E0')
                    },
                    "fontColor": {
                        "light": design_data.get('fontColor', '#11171C'),
                        "dark": "#E8ECF0"
                    },
                    "selectionColor": {
                        "light": "#2272B4",
                        "dark": "#8ACAFF"
                    },
                    "visualizationColors": design_data.get('visualizationColors', [
                        "#077A9D", "#FFAB00", "#00A972", "#FF3621", "#8BCAE7", 
                        "#9B59B6", "#E74C3C", "#3498DB", "#2ECC71", "#F39C12",
                        "#1ABC9C", "#E67E22", "#95A5A6", "#34495E", "#C0392B",
                        "#16A085", "#27AE60", "#2980B9", "#8E44AD", "#F1C40F",
                        "#D35400", "#C0392B", "#BDC3C7", "#7F8C8D", "#2C3E50",
                        "#E91E63", "#9C27B0", "#673AB7", "#3F51B5", "#2196F3"
                    ]),
                    "widgetHeaderAlignment": "LEFT",
                    "fontFamily": design_data.get('fontFamily', 'Arial')
                },
                "genieSpace": {
                    "isEnabled": False,
                    "enablementMode": "DISABLED"
                },
                "applyModeEnabled": False
            }
        }
        
        # Create reasoning display
        reasoning_display = html.Div([
            html.H6("💡 AI Design Analysis & Reasoning", className="mb-3"),
            
            # Current Style Feedback Section
            dbc.Card([
                dbc.CardHeader(html.H6("🔍 Current Dashboard Style Feedback", className="mb-0")),
                dbc.CardBody([
                    html.P(current_style_feedback, className="mb-0", style={'whiteSpace': 'pre-wrap'})
                ])
            ], color="light", className="mb-3"),
            
            # New Design Reasoning Section
            dbc.Card([
                dbc.CardHeader(html.H6("✨ New Design Reasoning", className="mb-0")),
                dbc.CardBody([
                    html.P(reasoning_text, className="mb-3", style={'whiteSpace': 'pre-wrap'}),
                    html.Hr(),
                    html.H6("🎨 Generated Design Colors:", className="mb-2"),
                    html.P([
                        html.Strong("Canvas: "),
                        html.Span(design_data.get('canvasBackgroundColor', 'N/A'), 
                                 style={'backgroundColor': design_data.get('canvasBackgroundColor', '#FFF'), 
                                       'padding': '2px 8px', 'borderRadius': '3px', 'marginLeft': '5px'})
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Widgets: "),
                        html.Span(design_data.get('widgetBackgroundColor', 'N/A'),
                                 style={'backgroundColor': design_data.get('widgetBackgroundColor', '#FFF'), 
                                       'padding': '2px 8px', 'borderRadius': '3px', 'marginLeft': '5px', 'border': '1px solid #ddd'})
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Font: "),
                        html.Span(f"{design_data.get('fontColor', 'N/A')} ({design_data.get('fontFamily', 'N/A')})")
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Visualization Colors: "),
                        html.Div([
                            html.Span(
                                color,
                                style={
                                    'backgroundColor': color,
                                    'padding': '5px 15px',
                                    'margin': '2px',
                                    'borderRadius': '3px',
                                    'display': 'inline-block',
                                    'color': '#FFF',
                                    'fontSize': '11px',
                                    'border': '1px solid #ddd'
                                }
                            ) for color in design_data.get('visualizationColors', [])
                        ])
                    ], className="mb-2")
                ])
            ], color="success", outline=True)
        ])
        
        print("✅ Design generated with reasoning")
        return analysis_display, reasoning_display, ui_settings, analysis_text, reasoning_text
        
    except json.JSONDecodeError as e:
        error_msg = dbc.Alert([
            html.Strong("❌ Failed to parse AI response"),
            html.Br(),
            html.Small(f"Error: {str(e)}")
        ], color="danger")
        return error_msg, "", None, None, None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = dbc.Alert([
            html.Strong("❌ Error during design generation"),
            html.Br(),
            html.Small(f"Error: {str(e)}")
        ], color="danger")
        return error_msg, "", None, None, None


def refine_design_from_feedback(original_prompt, feedback_prompt, previous_reasoning, previous_design, dashboard_config, llm_client):
    """
    Refine the design based on user feedback, incorporating previous reasoning.
    
    Args:
        original_prompt: Original user design request
        feedback_prompt: User's refinement feedback
        previous_reasoning: Previous AI reasoning
        previous_design: Previous design specification (dict)
        dashboard_config: Current dashboard configuration
        llm_client: OpenAI client instance
        
    Returns:
        tuple: (reasoning_display, design_data, reasoning_text)
    """
    if not feedback_prompt or not feedback_prompt.strip():
        return "", None, None
    
    try:
        # Get dashboard analysis
        analysis = analyze_dashboard_layout(dashboard_config)
        analysis_text = f"""Dashboard: {analysis['total_widgets']} widgets with {', '.join([f'{k} ({v})' for k, v in analysis.get('widget_counts', {}).items()])}"""
        
        # Build refinement prompt
        refinement_prompt = f"""You are an expert dashboard designer. You previously created a design, and the user has provided feedback for refinement.

DASHBOARD CONTEXT:
{analysis_text}

ORIGINAL USER REQUEST:
"{original_prompt}"

YOUR PREVIOUS REASONING:
{previous_reasoning}

YOUR PREVIOUS DESIGN:
{json.dumps(previous_design, indent=2)}

USER'S REFINEMENT FEEDBACK:
"{feedback_prompt}"

Based on the user's feedback, refine your design. Explain what you're changing and why, then provide the updated design.

Return your response in this EXACT JSON format:

{{
    "current_style_feedback": "Brief evaluation of your previous design and how the user's feedback addresses it (use line breaks for structure)",
    "reasoning": "Explain what feedback you received, what you're changing, and why this refinement improves the design (use line breaks for structure)",
    "design": {{
        "canvasBackgroundColor": "#HEXCODE",
        "widgetBackgroundColor": "#HEXCODE",
        "widgetBorderColor": "#HEXCODE",
        "fontColor": "#HEXCODE",
        "visualizationColors": ["#HEX1", "#HEX2", "#HEX3", ... 30 colors total],
        "fontFamily": "Font Name"
    }}
}}

CRITICAL RULES:
1. visualizationColors MUST contain EXACTLY 30 colors to cover all edge cases
2. Address the user's feedback specifically
3. Keep what worked from the previous design
4. Ensure visualization colors are distinguishable (different hues, not just shades)
5. NEVER use white/very light colors for visualizations if background is white
6. Maintain high contrast for readability
7. Create a diverse palette with distinct hues

IMPORTANT: Return ONLY valid JSON without markdown formatting."""

        # Call LLM
        response = llm_client.chat.completions.create(
            model="databricks-gpt-5",
            messages=[
                {
                    "role": "user",
                    "content": refinement_prompt
                }
            ],
            max_tokens=1000
        )
        
        # Parse response
        llm_response = response.choices[0].message.content.strip()
        
        if llm_response.startswith('```'):
            lines = llm_response.split('\n')
            llm_response = '\n'.join(lines[1:-1]) if len(lines) > 2 else llm_response
        
        response_data = json.loads(llm_response)
        current_style_feedback = response_data.get('current_style_feedback', 'No feedback provided')
        reasoning_text = response_data.get('reasoning', 'No reasoning provided')
        design_data = response_data.get('design', {})
        
        # Build UI settings
        ui_settings = {
            "uiSettings": {
                "theme": {
                    "canvasBackgroundColor": {
                        "light": design_data.get('canvasBackgroundColor', '#FAFAFB'),
                        "dark": "#1F272D"
                    },
                    "widgetBackgroundColor": {
                        "light": design_data.get('widgetBackgroundColor', '#FFFFFF'),
                        "dark": "#11171C"
                    },
                    "widgetBorderColor": {
                        "light": design_data.get('widgetBorderColor', '#E0E0E0')
                    },
                    "fontColor": {
                        "light": design_data.get('fontColor', '#11171C'),
                        "dark": "#E8ECF0"
                    },
                    "selectionColor": {
                        "light": "#2272B4",
                        "dark": "#8ACAFF"
                    },
                    "visualizationColors": design_data.get('visualizationColors', [
                        "#077A9D", "#FFAB00", "#00A972", "#FF3621", "#8BCAE7", 
                        "#9B59B6", "#E74C3C", "#3498DB", "#2ECC71", "#F39C12",
                        "#1ABC9C", "#E67E22", "#95A5A6", "#34495E", "#C0392B",
                        "#16A085", "#27AE60", "#2980B9", "#8E44AD", "#F1C40F",
                        "#D35400", "#C0392B", "#BDC3C7", "#7F8C8D", "#2C3E50",
                        "#E91E63", "#9C27B0", "#673AB7", "#3F51B5", "#2196F3"
                    ]),
                    "widgetHeaderAlignment": "LEFT",
                    "fontFamily": design_data.get('fontFamily', 'Arial')
                },
                "genieSpace": {
                    "isEnabled": False,
                    "enablementMode": "DISABLED"
                },
                "applyModeEnabled": False
            }
        }
        
        # Create refined reasoning display
        reasoning_display = html.Div([
            html.H6("💡 Refined Design Reasoning", className="mb-3"),
            dbc.Alert([
                html.Strong("📝 Your Feedback: "),
                html.Span(f'"{feedback_prompt}"')
            ], color="warning", className="mb-2"),
            dbc.Card([
                dbc.CardBody([
                    html.P(reasoning_text, className="mb-3", style={'whiteSpace': 'pre-wrap'}),
                    html.Hr(),
                    html.H6("🎨 Refined Design Colors:", className="mb-2"),
                    html.P([
                        html.Strong("Canvas: "),
                        html.Span(design_data.get('canvasBackgroundColor', 'N/A'), 
                                 style={'backgroundColor': design_data.get('canvasBackgroundColor', '#FFF'), 
                                       'padding': '2px 8px', 'borderRadius': '3px', 'marginLeft': '5px'})
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Widgets: "),
                        html.Span(design_data.get('widgetBackgroundColor', 'N/A'),
                                 style={'backgroundColor': design_data.get('widgetBackgroundColor', '#FFF'), 
                                       'padding': '2px 8px', 'borderRadius': '3px', 'marginLeft': '5px', 'border': '1px solid #ddd'})
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Font: "),
                        html.Span(f"{design_data.get('fontColor', 'N/A')} ({design_data.get('fontFamily', 'N/A')})")
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Visualization Colors: "),
                        html.Div([
                            html.Span(
                                color,
                                style={
                                    'backgroundColor': color,
                                    'padding': '5px 15px',
                                    'margin': '2px',
                                    'borderRadius': '3px',
                                    'display': 'inline-block',
                                    'color': '#FFF',
                                    'fontSize': '11px',
                                    'border': '1px solid #ddd'
                                }
                            ) for color in design_data.get('visualizationColors', [])
                        ])
                    ], className="mb-2")
                ])
            ], color="success", outline=True)
        ])
        
        print("✅ Design refined based on feedback")
        return reasoning_display, ui_settings, reasoning_text
        
    except json.JSONDecodeError as e:
        error_msg = dbc.Alert([
            html.Strong("❌ Failed to parse AI response"),
            html.Br(),
            html.Small(f"Error: {str(e)}")
        ], color="danger")
        return error_msg, None, None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = dbc.Alert([
            html.Strong("❌ Error during design refinement"),
            html.Br(),
            html.Small(f"Error: {str(e)}")
        ], color="danger")
        return error_msg, None, None

