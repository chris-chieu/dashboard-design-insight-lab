"""
Test Function Page - Dashboard Layout Analyzer

This module uses vision AI to analyze dashboard screenshots and extract:
- General layout structure (grid dimensions)
- Widget types and positions
"""

from dash import html, dcc, no_update
import dash_bootstrap_components as dbc
import base64
import json


def get_test_function_layout():
    """
    Returns the layout for the Test Function page
    """
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("🔍 Dashboard Layout Analyzer", className="text-center mb-3 mt-3"),
                html.P(
                    "Upload a dashboard screenshot and AI will analyze its layout structure, "
                    "identifying widget types and positions.",
                    className="text-center text-muted mb-4"
                )
            ])
        ]),
        
        # Upload Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("📷 Upload Dashboard Screenshot")),
                    dbc.CardBody([
                        html.P("Upload an image of a dashboard to analyze its layout:", className="mb-3"),
                        dcc.Upload(
                            id='dashboard-layout-upload',
                            children=html.Div([
                                '🖼️ Drag and Drop or ',
                                html.A('Select Dashboard Image', style={'cursor': 'pointer', 'textDecoration': 'underline'})
                            ]),
                            style={
                                'width': '100%',
                                'height': '120px',
                                'lineHeight': '120px',
                                'borderWidth': '3px',
                                'borderStyle': 'dashed',
                                'borderRadius': '10px',
                                'textAlign': 'center',
                                'cursor': 'pointer',
                                'backgroundColor': '#f8f9fa',
                                'fontSize': '16px'
                            },
                            multiple=False
                        ),
                        html.Div(id='dashboard-upload-preview', className="mt-3")
                    ])
                ], className="mb-4")
            ], width=12)
        ]),
        
        # Analysis Results Section
        dbc.Row([
            dbc.Col([
                dcc.Loading(
                    id="layout-analysis-loading",
                    type="default",
                    children=html.Div(id='layout-analysis-results')
                )
            ], width=12)
        ]),
        
        # Validation Section
        dbc.Row([
            dbc.Col([
                html.Div(id='layout-validation-section')
            ], width=12)
        ]),
        
        # Refinement Section (shown when user clicks "Refine Analysis")
        dbc.Row([
            dbc.Col([
                html.Div(
                    id='layout-refinement-section',
                    style={'display': 'none'},  # Hidden by default
                    children=[
                        dbc.Card([
                            dbc.CardHeader(html.H5("🔄 Refine Analysis")),
                            dbc.CardBody([
                                html.P([
                                    "Provide additional context or corrections to improve the analysis. ",
                                    "For example: 'The counter at the top should be at position x=2, y=0' or ",
                                    "'There are actually 4 widgets, not 3'"
                                ], className="text-muted mb-3"),
                                dcc.Textarea(
                                    id='layout-refinement-input',
                                    placeholder='Enter your refinement instructions here...\n\nExample:\n- The bar chart should be wider\n- There is a filter widget at the top left that was missed\n- The KPI counter positions are incorrect',
                                    style={
                                        'width': '100%',
                                        'height': '150px',
                                        'padding': '10px',
                                        'borderRadius': '5px',
                                        'border': '2px solid #ddd',
                                        'fontSize': '14px'
                                    },
                                    className="mb-3"
                                ),
                                dbc.Button(
                                    "🔍 Refine Analysis",
                                    id="submit-refinement-btn",
                                    color="primary",
                                    size="lg",
                                    className="w-100"
                                ),
                                html.Div(id='refinement-status', className="mt-3")
                            ])
                        ], className="mb-3")
                    ]
                )
            ], width=12)
        ]),
        
        # Final Results Section (shown after validation or refinement)
        dbc.Row([
            dbc.Col([
                dcc.Loading(
                    id="layout-final-loading",
                    type="default",
                    children=html.Div(id='layout-final-results')
                )
            ], width=12)
        ]),
        
        # Hidden stores for state management
        dcc.Store(id='uploaded-dashboard-image'),
        dcc.Store(id='initial-analysis-data'),
        dcc.Store(id='initial-analysis-text')
    ])


def register_test_function_callbacks(app, llm_client):
    """
    Register all callbacks for the Test Function page
    
    Args:
        app: Dash app instance
        llm_client: OpenAI client for vision LLM calls
    """
    from dash import callback, Output, Input, State
    
    @callback(
        [Output('dashboard-upload-preview', 'children'),
         Output('layout-analysis-results', 'children'),
         Output('uploaded-dashboard-image', 'data'),
         Output('initial-analysis-data', 'data'),
         Output('initial-analysis-text', 'data'),
         Output('layout-validation-section', 'children'),
         Output('layout-refinement-section', 'style'),
         Output('layout-final-results', 'children')],
        Input('dashboard-layout-upload', 'contents'),
        State('dashboard-layout-upload', 'filename'),
        prevent_initial_call=True
    )
    def analyze_dashboard_layout(contents, filename):
        """
        Analyze dashboard screenshot using vision LLM
        """
        if not contents:
            return "", "", None, None, None, no_update, {'display': 'none'}, no_update
        
        try:
            # Show uploaded image preview
            preview = dbc.Card([
                dbc.CardHeader(html.H6(f"📷 Uploaded: {filename}")),
                dbc.CardBody([
                    html.Img(
                        src=contents,
                        style={
                            'maxWidth': '100%',
                            'maxHeight': '400px',
                            'border': '1px solid #ddd',
                            'borderRadius': '5px'
                        }
                    )
                ])
            ], className="mb-3")
            
            # Extract base64 image data
            content_type, content_string = contents.split(',')
            image_data = content_string
            
            # Prepare the prompt for the vision LLM
            analysis_prompt = """
You are a dashboard layout analyzer. Analyze this dashboard screenshot and provide a structured JSON output with the following information:

1. **Overall Layout**: Describe the grid structure (e.g., "2x2", "3x3", "2x4", etc.)

2. **Widgets**: For each widget/component in the dashboard, identify:
   - **type**: The type of widget (e.g., "chart", "bar_chart", "line_chart", "pie_chart", "counter", "kpi", "table", "pivot", "filter", "text")
   - **position**: The position and size using this format:
     {
       "x": <column_position>,
       "y": <row_position>,
       "width": <widget_width_in_columns>,
       "height": <widget_height_in_rows>
     }

**Important Guidelines:**
- Use a grid system where x and y start from 0
- Typical dashboard width is 6 columns
- Height is measured in rows (each row ≈ 2 units)
- Be as precise as possible about positions

**Output Format** (JSON only, no additional text):
```json
{
  "layout": {
    "grid": "3x2",
    "total_columns": 6,
    "description": "Brief description of overall layout"
  },
  "widgets": [
    {
      "id": 1,
      "type": "bar_chart",
      "description": "Brief description of what this widget shows",
      "position": {
        "x": 0,
        "y": 0,
        "width": 3,
        "height": 4
      }
    },
    {
      "id": 2,
      "type": "counter",
      "description": "KPI showing total count",
      "position": {
        "x": 3,
        "y": 0,
        "width": 2,
        "height": 2
      }
    }
  ]
}
```

Analyze the dashboard and return ONLY the JSON output.
"""
            
            # Call vision LLM
            print("🔍 Calling vision LLM for dashboard layout analysis...")
            response = llm_client.chat.completions.create(
                model="databricks-gpt-5",  # Vision-capable model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            # Extract and parse the response
            analysis_text = response.choices[0].message.content.strip()
            print(f"📊 LLM Response:\n{analysis_text[:500]}...")
            
            # Try to extract JSON from response
            try:
                # Remove markdown code blocks if present
                if "```json" in analysis_text:
                    analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
                elif "```" in analysis_text:
                    analysis_text = analysis_text.split("```")[1].split("```")[0].strip()
                
                analysis_data = json.loads(analysis_text)
                
                # Create results display
                layout_info = analysis_data.get('layout', {})
                widgets = analysis_data.get('widgets', [])
                
                # Layout overview card
                layout_card = dbc.Card([
                    dbc.CardHeader(html.H5("📐 Layout Structure")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Strong("Grid Structure:"),
                                html.P(layout_info.get('grid', 'N/A'), className="mb-2")
                            ], width=4),
                            dbc.Col([
                                html.Strong("Total Columns:"),
                                html.P(str(layout_info.get('total_columns', 'N/A')), className="mb-2")
                            ], width=4),
                            dbc.Col([
                                html.Strong("Total Widgets:"),
                                html.P(str(len(widgets)), className="mb-2")
                            ], width=4)
                        ]),
                        html.Hr(),
                        html.Strong("Description:"),
                        html.P(layout_info.get('description', 'N/A'), className="text-muted")
                    ])
                ], className="mb-3")
                
                # Widgets table
                widgets_table = dbc.Card([
                    dbc.CardHeader(html.H5("🎯 Detected Widgets")),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("ID"),
                                    html.Th("Type"),
                                    html.Th("Description"),
                                    html.Th("Position (x, y)"),
                                    html.Th("Size (w × h)")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(widget.get('id', 'N/A')),
                                    html.Td(dbc.Badge(widget.get('type', 'unknown'), color="info")),
                                    html.Td(widget.get('description', 'N/A')),
                                    html.Td(f"({widget.get('position', {}).get('x', 0)}, {widget.get('position', {}).get('y', 0)})"),
                                    html.Td(f"{widget.get('position', {}).get('width', 0)} × {widget.get('position', {}).get('height', 0)}")
                                ]) for widget in widgets
                            ])
                        ], bordered=True, hover=True, striped=True)
                    ])
                ], className="mb-3")
                
                # JSON output card
                json_card = dbc.Card([
                    dbc.CardHeader(html.H5("📄 Raw JSON Output")),
                    dbc.CardBody([
                        html.Pre(
                            json.dumps(analysis_data, indent=2),
                            style={
                                'backgroundColor': '#f5f5f5',
                                'padding': '15px',
                                'borderRadius': '5px',
                                'fontSize': '12px',
                                'maxHeight': '400px',
                                'overflowY': 'auto'
                            }
                        )
                    ])
                ])
                
                results = html.Div([
                    dbc.Alert([
                        html.Strong("✅ Analysis Complete!"),
                        html.Br(),
                        html.Small(f"Detected {len(widgets)} widgets in the dashboard")
                    ], color="success", className="mb-3"),
                    layout_card,
                    widgets_table
                ])
                
                # Validation buttons section (separate output)
                validation_section = dbc.Card([
                    dbc.CardBody([
                        html.H5("📋 Validate Results", className="mb-3"),
                        html.P("Are these results accurate? You can validate them or provide refinement instructions.", className="text-muted"),
                        dbc.ButtonGroup([
                            dbc.Button("✅ Validate", id="validate-layout-btn", color="success", className="me-2", size="lg"),
                            dbc.Button("🔄 Refine Analysis", id="refine-layout-btn", color="warning", size="lg")
                        ])
                    ])
                ], className="mb-3")
                
                print(f"✅ Returning results with validation buttons for {len(widgets)} widgets")
                # Hide refinement section and clear final results for fresh analysis
                return preview, results, image_data, analysis_data, analysis_text, validation_section, {'display': 'none'}, ""
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                error_result = dbc.Alert([
                    html.Strong("⚠️ Analysis Complete but Failed to Parse JSON"),
                    html.Hr(),
                    html.P("Raw LLM Response:", className="fw-bold"),
                    html.Pre(
                        analysis_text,
                        style={
                            'backgroundColor': '#f5f5f5',
                            'padding': '10px',
                            'borderRadius': '5px',
                            'fontSize': '12px',
                            'maxHeight': '300px',
                            'overflowY': 'auto'
                        }
                    )
                ], color="warning")
                return preview, error_result, image_data, None, analysis_text, no_update, {'display': 'none'}, no_update
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_alert = dbc.Alert([
                html.Strong("❌ Error analyzing dashboard"),
                html.Br(),
                html.Small(f"Error: {str(e)}")
            ], color="danger")
            return preview if 'preview' in locals() else "", error_alert, None, None, None, no_update, {'display': 'none'}, no_update
    
    
    @callback(
        Output('layout-final-results', 'children', allow_duplicate=True),
        Input('validate-layout-btn', 'n_clicks'),
        State('initial-analysis-data', 'data'),
        prevent_initial_call=True
    )
    def validate_layout_results(n_clicks, analysis_data):
        """
        Handle validation - show the raw JSON output
        """
        if not n_clicks or not analysis_data:
            return ""
        
        # JSON output card
        json_card = dbc.Card([
            dbc.CardHeader(html.H5("📄 Validated JSON Output")),
            dbc.CardBody([
                dbc.Alert([
                    html.Strong("✅ Results Validated!"),
                    html.Br(),
                    html.Small("You can use this JSON structure for your dashboard configuration.")
                ], color="success", className="mb-3"),
                html.Pre(
                    json.dumps(analysis_data, indent=2),
                    style={
                        'backgroundColor': '#f5f5f5',
                        'padding': '15px',
                        'borderRadius': '5px',
                        'fontSize': '12px',
                        'maxHeight': '400px',
                        'overflowY': 'auto'
                    }
                )
            ])
        ])
        
        print(f"✅ Validation complete, showing JSON output")
        return json_card
    
    
    @callback(
        Output('layout-refinement-section', 'style', allow_duplicate=True),
        Input('refine-layout-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def show_layout_analyzer_refinement_section(n_clicks):
        """
        Handle refinement - show the refinement section by toggling visibility
        """
        print(f"🔄 show_refinement_section called with n_clicks={n_clicks}")
        if not n_clicks:
            print("🔄 No clicks, keeping hidden")
            return {'display': 'none'}
        
        print(f"🔄 Showing refinement section (display: block)")
        return {'display': 'block'}
    
    
    @callback(
        [Output('refinement-status', 'children'),
         Output('layout-analysis-results', 'children', allow_duplicate=True),
         Output('initial-analysis-data', 'data', allow_duplicate=True),
         Output('initial-analysis-text', 'data', allow_duplicate=True),
         Output('layout-refinement-section', 'style', allow_duplicate=True)],
        Input('submit-refinement-btn', 'n_clicks'),
        [State('layout-refinement-input', 'value'),
         State('uploaded-dashboard-image', 'data'),
         State('initial-analysis-text', 'data')],
        prevent_initial_call=True
    )
    def refine_layout_analysis(n_clicks, refinement_text, image_data, initial_analysis):
        """
        Refine the analysis based on user feedback
        """
        if not n_clicks or not refinement_text:
            return dbc.Alert("⚠️ Please enter refinement instructions", color="warning"), no_update, no_update, no_update, no_update
        
        if not image_data or not initial_analysis:
            return dbc.Alert("❌ Missing image or initial analysis data", color="danger"), no_update, no_update, no_update, no_update
        
        try:
            # Show processing status
            processing_alert = dbc.Alert([
                dbc.Spinner(size="sm"),
                html.Span(" 🔍 Refining analysis with your feedback...", style={"marginLeft": "10px"})
            ], color="info")
            
            # Prepare refined prompt
            refinement_prompt = f"""
You previously analyzed this dashboard and provided the following analysis:

{initial_analysis}

The user has provided the following refinement instructions:

{refinement_text}

Please analyze the dashboard again, taking into account the user's feedback and corrections. 
Provide an updated and more accurate JSON output following the same format as before.

**Output Format** (JSON only, no additional text):
```json
{{
  "layout": {{
    "grid": "3x2",
    "total_columns": 6,
    "description": "Brief description of overall layout"
  }},
  "widgets": [
    {{
      "id": 1,
      "type": "bar_chart",
      "description": "Brief description of what this widget shows",
      "position": {{
        "x": 0,
        "y": 0,
        "width": 3,
        "height": 4
      }}
    }}
  ]
}}
```

Analyze the dashboard again with the refinements and return ONLY the updated JSON output.
"""
            
            # Call vision LLM with refinement
            print("🔍 Calling vision LLM with refinement instructions...")
            response = llm_client.chat.completions.create(
                model="databricks-gpt-5",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": refinement_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            # Extract and parse the response
            refined_text = response.choices[0].message.content.strip()
            print(f"📊 Refined LLM Response:\n{refined_text[:500]}...")
            
            # Try to extract JSON from response
            try:
                # Remove markdown code blocks if present
                if "```json" in refined_text:
                    refined_text = refined_text.split("```json")[1].split("```")[0].strip()
                elif "```" in refined_text:
                    refined_text = refined_text.split("```")[1].split("```")[0].strip()
                
                refined_data = json.loads(refined_text)
                
                # Create refined results display
                layout_info = refined_data.get('layout', {})
                widgets = refined_data.get('widgets', [])
                
                # Layout overview card
                layout_card = dbc.Card([
                    dbc.CardHeader(html.H5("📐 Refined Layout Structure")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Strong("Grid Structure:"),
                                html.P(layout_info.get('grid', 'N/A'), className="mb-2")
                            ], width=4),
                            dbc.Col([
                                html.Strong("Total Columns:"),
                                html.P(str(layout_info.get('total_columns', 'N/A')), className="mb-2")
                            ], width=4),
                            dbc.Col([
                                html.Strong("Total Widgets:"),
                                html.P(str(len(widgets)), className="mb-2")
                            ], width=4)
                        ]),
                        html.Hr(),
                        html.Strong("Description:"),
                        html.P(layout_info.get('description', 'N/A'), className="text-muted")
                    ])
                ], className="mb-3")
                
                # Widgets table
                widgets_table = dbc.Card([
                    dbc.CardHeader(html.H5("🎯 Refined Widget Detection")),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("ID"),
                                    html.Th("Type"),
                                    html.Th("Description"),
                                    html.Th("Position (x, y)"),
                                    html.Th("Size (w × h)")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(widget.get('id', 'N/A')),
                                    html.Td(dbc.Badge(widget.get('type', 'unknown'), color="info")),
                                    html.Td(widget.get('description', 'N/A')),
                                    html.Td(f"({widget.get('position', {}).get('x', 0)}, {widget.get('position', {}).get('y', 0)})"),
                                    html.Td(f"{widget.get('position', {}).get('width', 0)} × {widget.get('position', {}).get('height', 0)}")
                                ]) for widget in widgets
                            ])
                        ], bordered=True, hover=True, striped=True)
                    ])
                ], className="mb-3")
                
                # Updated results (no JSON output yet - only shown on validate)
                results = html.Div([
                    dbc.Alert([
                        html.Strong("✅ Refinement Complete!"),
                        html.Br(),
                        html.Small(f"Updated analysis with {len(widgets)} widgets based on your feedback. Click 'Validate' to see the JSON output.")
                    ], color="success", className="mb-3"),
                    layout_card,
                    widgets_table
                ])
                
                print(f"✅ Refinement complete, updated analysis with {len(widgets)} widgets")
                # Return: clear status, updated results, updated stored data, hide refinement section
                return "", results, refined_data, refined_text, {'display': 'none'}
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                error_result = dbc.Alert([
                    html.Strong("⚠️ Refinement Complete but Failed to Parse JSON"),
                    html.Hr(),
                    html.P("Raw LLM Response:", className="fw-bold"),
                    html.Pre(
                        refined_text,
                        style={
                            'backgroundColor': '#f5f5f5',
                            'padding': '10px',
                            'borderRadius': '5px',
                            'fontSize': '12px',
                            'maxHeight': '300px',
                            'overflowY': 'auto'
                        }
                    )
                ], color="warning")
                return "", error_result, no_update, no_update, {'display': 'none'}
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_alert = dbc.Alert([
                html.Strong("❌ Error refining analysis"),
                html.Br(),
                html.Small(f"Error: {str(e)}")
            ], color="danger")
            return error_alert, no_update, no_update, no_update, {'display': 'none'}

