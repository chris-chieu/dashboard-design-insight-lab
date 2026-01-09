"""
Design Infusion Module

Extracts design elements (colors and fonts) from uploaded images using Vision LLM.
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
        error_msg = dbc.Alert([
            html.Strong("❌ Failed to parse LLM response"),
            html.Br(),
            html.Small(f"The AI response was not in valid JSON format. Error: {str(e)}")
        ], color="danger")
        return error_msg, None
        
    except Exception as e:
        error_msg = dbc.Alert([
            html.Strong("❌ Error analyzing image"),
            html.Br(),
            html.Small(f"Error: {str(e)}")
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

