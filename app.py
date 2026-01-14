"""
Dashboard App with LLM-powered Table Widget Generation
"""
import json
import os
import sys
import time
import traceback

# Add startup logging for Databricks Apps debugging
print("=" * 60)
print("🚀 Starting Intelligent Embedded Dashboard App...")
print("=" * 60)

try:
    print("📦 Importing core dependencies...")
    from dash import Dash, html, dcc, callback, Output, Input, State, no_update
    import dash_bootstrap_components as dbc
    from openai import OpenAI
    from databricks.sdk import WorkspaceClient
    import mlflow
    print("✅ Core dependencies imported")
    
    print("📦 Importing dashboard modules...")
    from dashboard_management_functions import DashboardManager
    from widgets import (
        create_table_widget, extract_columns_with_llm,
        create_filter_widget, create_bar_chart_widget,
        create_line_chart_widget, create_pivot_widget
    )
    from example_datasets.datasets import DATASETS as datasets
    from dataset_filter import apply_simple_filter_to_dataset, get_dataset_filters_summary
    print("✅ Dashboard modules imported")
    
    print("📦 Importing AI dashboard generator...")
    from dashboard_management_functions import generate_dashboard_background
    print("✅ AI dashboard generator imported successfully")
    
    print("📦 Importing design infusion module...")
    from dashboard_management_functions import (
        extract_design_from_image, 
        generate_design_from_prompt,
        analyze_dashboard_layout,
        generate_design_with_analysis,
        refine_design_from_feedback
    )
    print("✅ Design infusion module imported successfully")
    
    print("📦 Importing page layouts...")
    from pages import (
        get_new_dashboard_layout, 
        get_existing_dashboard_layout,
        get_test_function_layout,
        register_existing_dashboard_callbacks, 
        register_new_dashboard_callbacks,
        register_test_function_callbacks
    )
    print("✅ Page layouts imported successfully")
    
    print("📦 Importing manual dashboard config...")
    from dashboard_management_functions import register_manual_config_callbacks
    print("✅ Manual dashboard config imported successfully")
    
except Exception as e:
    print(f"❌ CRITICAL ERROR during imports: {e}", file=sys.stderr)
    print(f"Error type: {type(e).__name__}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

print("🔧 Initializing Dash app...")
# Use Bootstrap as base + custom Databricks styling (from assets/databricks_style.css)
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Suppress callback exceptions for dynamically generated components
app.config.suppress_callback_exceptions = True
print("✅ Dash app created with Databricks One styling")

# Configuration - Update these values for your environment
DATABRICKS_TOKEN = '<YOUR_DATABRICKS_TOKEN>'
DATABRICKS_HOST = "https://e2-demo-field-eng.cloud.databricks.com"
WAREHOUSE_ID = "8baced1ff014912d"
UNITY_CATALOG = "christophe_chieu"
UNITY_SCHEMA = "certified_tables"
LLM_MODEL = "databricks-gpt-5"
VISION_MODEL = "databricks-gpt-5"
print(f"✅ Configuration loaded (Host: {DATABRICKS_HOST})")

# Clear OAuth env vars
for key in ['DATABRICKS_CLIENT_ID', 'DATABRICKS_CLIENT_SECRET']:
    if key in os.environ:
        del os.environ[key]

try:
    print("🔧 Initializing OpenAI client...")
    llm_client = OpenAI(
        api_key=DATABRICKS_TOKEN,
        base_url=f"{DATABRICKS_HOST}/serving-endpoints"
    )
    print("✅ OpenAI client initialized")
    
    print("🔧 Configuring MLflow...")
    os.environ["DATABRICKS_HOST"] = DATABRICKS_HOST
    os.environ["DATABRICKS_TOKEN"] = DATABRICKS_TOKEN
    mlflow.set_tracking_uri("databricks")
    mlflow.set_experiment("/Users/christophe.chieu@databricks.com/intelligent-dashboard-generator")
    print("✅ MLflow configured")
    
    # Enable MLflow autologging for OpenAI
    try:
        mlflow.openai.autolog()
        print("✅ MLflow OpenAI autologging enabled")
    except Exception as e:
        print(f"⚠️ Could not enable MLflow OpenAI autologging: {e}")
    
    print("🔧 Initializing Databricks client...")
    workspace_client = WorkspaceClient(
        host=DATABRICKS_HOST,
        token=DATABRICKS_TOKEN
    )
    print("✅ Databricks client initialized")

    print("🔧 Initializing Dashboard Manager...")
    dashboard_manager = DashboardManager(workspace_client, WAREHOUSE_ID, "/Shared")
    print("✅ Dashboard Manager initialized")
    
    # Global progress tracking for AI dashboard generation
    import threading
    ai_progress_store = {}
    ai_results_store = {}
    print("✅ Progress tracking initialized")
    
    print("=" * 60)
    print("✅ All initialization complete - App ready to start")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ CRITICAL ERROR during initialization: {e}", file=sys.stderr)
    print(f"Error type: {type(e).__name__}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)


app.layout = html.Div([
    # Store for extracted columns and dashboard config
    dcc.Store(id='extracted-columns'),
    dcc.Store(id='extracted-columns-types'),  # Store for column types from UC tables
    dcc.Store(id='current-widget'),
    dcc.Store(id='filter-widgets', data=[]),
    dcc.Store(id='bar-chart-widgets', data=[]),
    dcc.Store(id='line-chart-widgets', data=[]),
    dcc.Store(id='pivot-widgets', data=[]),
    dcc.Store(id='original-dataset'),  # Store for original dataset (no filters)
    dcc.Store(id='filtered-dataset'),  # Store for dataset with WHERE filters applied
    dcc.Store(id='uc-dataset-store'),  # Store for Unity Catalog table dataset
    dcc.Store(id='dashboard-config'),
    dcc.Store(id='deployed-dashboard-id'),
    dcc.Store(id='selected-widgets', data=[]),  # Store for widget selection
    dcc.Store(id='ai-generation-session', data=None),  # Store for tracking active AI generation
    dcc.Store(id='ai-last-update', data=None),  # Track last update to prevent unnecessary re-renders
    dcc.Store(id='infusion-design-data', data=None),  # Store for design infusion extracted data
    dcc.Store(id='current-dashboard-config', data=None),  # Store current dashboard config for infusion (NEW DASHBOARD PAGE)
    dcc.Store(id='current-dashboard-name', data=None),  # Store current dashboard name for infusion (NEW DASHBOARD PAGE)
    dcc.Store(id='active-page', data='new-dashboard'),  # Store for active page
    
    # NEW DASHBOARD INTELLIGENT INFUSION STORES
    dcc.Store(id='new-dashboard-design-analysis-text', data=None),  # Store dashboard analysis for new dashboard
    dcc.Store(id='new-dashboard-design-reasoning-text', data=None),  # Store AI reasoning for new dashboard
    dcc.Store(id='new-dashboard-design-generated-ui-settings', data=None),  # Store generated design for new dashboard
    dcc.Store(id='new-dashboard-original-design-prompt', data=None),  # Store original prompt for new dashboard
    dcc.Store(id='new-dashboard-previous-design-data', data=None),  # Store previous design for new dashboard refinement
    
    # Separate stores for EXISTING DASHBOARD PAGE
    dcc.Store(id='existing-dashboard-id', data=None),  # Store for existing dashboard ID
    dcc.Store(id='existing-dashboard-config', data=None),  # Store for existing dashboard config
    dcc.Store(id='existing-dashboard-name', data=None),  # Store for existing dashboard name
    
    # Stores for INTELLIGENT DESIGN INFUSION workflow
    dcc.Store(id='design-analysis-text', data=None),  # Store dashboard analysis text
    dcc.Store(id='design-reasoning-text', data=None),  # Store AI reasoning text
    dcc.Store(id='design-generated-ui-settings', data=None),  # Store generated design (not yet applied)
    dcc.Store(id='original-design-prompt', data=None),  # Store original prompt for refinement
    dcc.Store(id='previous-design-data', data=None),  # Store previous design for refinement
    
    dcc.Interval(id='ai-progress-interval', interval=500, disabled=True, n_intervals=0, max_intervals=300),  # Poll every 500ms, max 2.5 mins
    
    # Layout with fixed sidebar
    dbc.Row([
        # Fixed Sidebar Navigation
        dbc.Col([
            html.Div([
                # Header
                html.Div([
                    html.H5("Dashboard Lab", style={
                        'fontSize': '18px',
                        'fontWeight': '700',
                        'color': '#1F272D',
                        'marginBottom': '8px'
                    }),
                    html.P("AI-Powered Design", style={
                        'fontSize': '12px',
                        'color': '#8B98A3',
                        'marginBottom': '24px'
                    })
                ]),
                
                # Navigation Links
                html.Div([
                    dbc.Button([
                        html.I(className="me-2"),
                        "New Dashboard"
                    ], id="nav-new-dashboard", color="link", className="w-100 text-start mb-2 nav-link-btn", n_clicks=0),
                    
                    dbc.Button([
                        html.I(className="me-2"),
                        "Existing Dashboard"
                    ], id="nav-existing-dashboard", color="link", className="w-100 text-start mb-2 nav-link-btn", n_clicks=0),
                    
                    dbc.Button([
                        html.I(className="me-2"),
                        "Layout Analyzer"
                    ], id="nav-layout-analyzer", color="link", className="w-100 text-start mb-2 nav-link-btn", n_clicks=0)
                ])
            ], style={
                'position': 'fixed',
                'top': '0',
                'left': '0',
                'width': '240px',
                'height': '100vh',
                'backgroundColor': '#FFFFFF',
                'borderRight': '1px solid #E0E5E8',
                'padding': '24px 16px',
                'overflowY': 'auto',
                'zIndex': '1000'
            })
        ], width=2, style={'padding': '0'}),
        
        # Main Content Area
        dbc.Col([
            dbc.Container([
                # Header
                html.Div([
                    html.H1("Dashboard Design & Insight Lab", 
                           style={
                               'fontSize': '28px',
                               'fontWeight': '700',
                               'letterSpacing': '-0.5px',
                               'marginBottom': '8px',
                               'color': '#1F272D'
                           }),
                    html.P("Create, analyze, and customize Lakeview dashboards with AI-powered design", 
                          style={
                              'fontSize': '14px',
                              'color': '#5A6C75',
                              'marginBottom': '0'
                          })
                ], style={'padding': '24px 0 16px 0'}),
                html.Hr(style={'margin': '0 0 24px 0', 'borderColor': '#E0E5E8'}),
                
                # Dynamic content area
                html.Div(id='page-content')
            ], fluid=True)
        ], width=10, style={'marginLeft': '240px', 'padding': '0'}),
    ], style={'margin': '0'}),
    
      # Modal for applying infusion to new dashboard (after generation) - WITH INTELLIGENT WORKFLOW
      dbc.Modal([
          dbc.ModalHeader(dbc.ModalTitle("Intelligent Design Infusion")),
          dbc.ModalBody([
              html.P("Choose how you want to generate your design:", className="mb-3"),
              
              # Options Side by Side
              dbc.Row([
                  # Option 1: Upload Image
                  dbc.Col([
                      dbc.Card([
                          dbc.CardBody([
                              html.H6("Option 1: Upload an Image", className="mb-3"),
                              html.P("Upload a picture and the AI will extract colors and fonts from it.", className="text-muted small mb-3"),
                              dcc.Upload(
                                  id='post-gen-infusion-upload',
                                  children=html.Div([
                                      'Drag and Drop or ',
                                      html.A('Select Image', style={'cursor': 'pointer', 'textDecoration': 'underline'})
                                  ]),
                                  style={
                                      'width': '100%',
                                      'height': '100px',
                                      'lineHeight': '100px',
                                      'borderWidth': '2px',
                                      'borderStyle': 'dashed',
                                      'borderRadius': '10px',
                                      'textAlign': 'center',
                                      'cursor': 'pointer',
                                      'backgroundColor': '#f8f9fa'
                                  },
                                  multiple=False
                              )
                          ])
                      ], style={'height': '100%'})
                  ], width=6),
                  
                  # Option 2: Text Prompt (with Intelligent Analysis)
                  dbc.Col([
                      dbc.Card([
                          dbc.CardBody([
                              html.H6("Option 2: Describe Your Design (AI-Assisted)", className="mb-3"),
                              html.P("Describe the style you want. AI will analyze your dashboard and explain design choices before applying.", className="text-muted small mb-3"),
                              dbc.Textarea(
                                  id='post-gen-infusion-prompt',
                                  placeholder="Example: Modern professional theme with blue accents...",
                                  style={'width': '100%', 'minHeight': '80px'},
                                  className="mb-2"
                              ),
                              dbc.Button("Analyze & Generate Design", id="post-gen-generate-design-btn", color="primary", size="sm")
                          ])
                      ], style={'height': '100%'})
                  ], width=6)
              ], className="mb-3"),
              
              # Analysis & Reasoning Display Section (NEW)
              dcc.Loading(
                  id="new-dashboard-design-analysis-loading",
                  type="default",
                  children=html.Div(id='new-dashboard-design-analysis-display', className="mt-3")
              ),
              
              dcc.Loading(
                  id="new-dashboard-design-reasoning-loading",
                  type="default",
                  children=html.Div(id='new-dashboard-design-reasoning-display', className="mt-3")
              ),
              
              # Validation Section (NEW - shown after design generation)
              html.Div(
                  id='new-dashboard-design-validation-section',
                  children=[
                      html.Hr(className="my-3"),
                      dbc.ButtonGroup([
                          dbc.Button("Validate & Apply Design", id="new-dashboard-validate-design-btn", color="success", size="sm"),
                          dbc.Button("Refine Design", id="new-dashboard-refine-design-btn", color="warning", size="sm")
                      ], className="mb-3 w-100"),
                      
                      # Refinement Input (hidden by default)
                      dbc.Collapse(
                          dbc.Card([
                              dbc.CardBody([
                                  html.H6("Provide Refinement Feedback:", className="mb-2"),
                                  html.P("Tell the AI what to improve (e.g., 'Make colors darker', 'Use more blue', 'Increase contrast')", 
                                         className="text-muted small mb-2"),
                                  dbc.Textarea(
                                      id='new-dashboard-design-refinement-prompt',
                                      placeholder="Example: Make the blue darker and add more contrast between widgets...",
                                      style={'minHeight': '80px'}
                                  ),
                                  dbc.Button("Apply Refinement", id="new-dashboard-apply-refinement-btn", color="primary", size="sm", className="mt-2")
                              ])
                          ]),
                          id="new-dashboard-refinement-collapse",
                          is_open=False
                      )
                  ],
                  style={'display': 'none'}  # Hidden until reasoning is generated
              ),
              
              # Loading/Status for image-based infusion
              dcc.Loading(
                  id="post-gen-infusion-loading",
                  type="default",
                  children=html.Div(id='post-gen-infusion-status', className="mt-3")
              )
          ]),
          dbc.ModalFooter([
              dbc.Button("Close", id="close-infusion-modal", color="secondary", size="sm")
          ])
      ], id="infusion-modal", size="xl", is_open=False),
    
    # Separate Modal for Existing Dashboard Page (Enhanced with Intelligent Workflow)
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Intelligent Design Infusion")),
        dbc.ModalBody([
            html.P("Choose how you want to generate your design:", className="mb-3"),
            
            # Options Side by Side
            dbc.Row([
                # Option 1: Upload Image
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Option 1: Upload an Image", className="mb-3"),
                            html.P("Upload a picture and the AI will extract colors and fonts from it.", className="text-muted small mb-3"),
                            dcc.Upload(
                                id='existing-dashboard-infusion-upload',
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select Image', style={'cursor': 'pointer', 'textDecoration': 'underline'})
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '100px',
                                    'lineHeight': '100px',
                                    'borderWidth': '2px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '10px',
                                    'textAlign': 'center',
                                    'cursor': 'pointer',
                                    'backgroundColor': '#f8f9fa'
                                },
                                multiple=False
                            )
                        ])
                    ], style={'height': '100%'})
                ], width=6),
                
                # Option 2: Text Prompt (with Intelligent Analysis)
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Option 2: Describe Your Design (AI-Assisted)", className="mb-3"),
                            html.P("Describe the style you want. AI will analyze your dashboard and explain design choices before applying.", className="text-muted small mb-3"),
                            dbc.Textarea(
                                id='existing-dashboard-infusion-prompt',
                                placeholder="Example: Modern professional theme with blue accents...",
                                style={'width': '100%', 'minHeight': '80px'},
                                className="mb-2"
                            ),
                            dbc.Button("Analyze & Generate Design", id="existing-generate-design-from-prompt-btn", color="primary", size="sm")
                        ])
                    ], style={'height': '100%'})
                ], width=6)
            ], className="mb-3"),
            
            # Analysis & Reasoning Display Section (NEW)
            dcc.Loading(
                id="existing-design-analysis-loading",
                type="default",
                children=html.Div(id='existing-design-analysis-display', className="mt-3")
            ),
            
            dcc.Loading(
                id="existing-design-reasoning-loading",
                type="default",
                children=html.Div(id='existing-design-reasoning-display', className="mt-3")
            ),
            
            # Validation Section (NEW - shown after design generation)
            html.Div(
                id='existing-design-validation-section',
                children=[
                    html.Hr(className="my-3"),
                    dbc.ButtonGroup([
                        dbc.Button("Validate & Apply Design", id="existing-validate-design-btn", color="success", size="sm"),
                        dbc.Button("Refine Design", id="existing-refine-design-btn", color="warning", size="sm")
                    ], className="mb-3 w-100"),
                    
                    # Refinement Input (hidden by default)
                    dbc.Collapse(
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Provide Refinement Feedback:", className="mb-2"),
                                html.P("Tell the AI what to improve (e.g., 'Make colors darker', 'Use more blue', 'Increase contrast')", 
                                       className="text-muted small mb-2"),
                                dbc.Textarea(
                                    id='existing-design-refinement-prompt',
                                    placeholder="Example: Make the blue darker and add more contrast between widgets...",
                                    style={'minHeight': '80px'}
                                ),
                                dbc.Button("Apply Refinement", id="existing-apply-refinement-btn", color="primary", size="sm", className="mt-2")
                            ])
                        ]),
                        id="existing-refinement-collapse",
                        is_open=False
                    )
                ],
                style={'display': 'none'}  # Hidden until reasoning is generated
            ),
            
            # Loading/Status for image-based infusion (legacy support)
            dcc.Loading(
                id="existing-dashboard-infusion-loading",
                type="default",
                children=html.Div(id='existing-dashboard-infusion-status', className="mt-3")
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-existing-infusion-modal", color="secondary", size="sm")
        ])
    ], id="existing-infusion-modal", size="xl", is_open=False)
    
])


@callback(
    [Output('dataset-json', 'children'),
     Output('generate-btn', 'disabled'),
     Output('original-dataset', 'data')],
    Input('dataset-dropdown', 'value'),
    prevent_initial_call=False
)
def show_dataset_json(value):
    if not value:
        return "", True, None
    
    dataset = datasets.get(value)
    if not dataset:
        return dbc.Alert("Dataset not found", color="warning"), True, None
    
    dataset_card = dbc.Card([
        dbc.CardHeader(html.H5("📄 Dataset Configuration")),
        dbc.CardBody([
            dbc.Alert("✅ Dataset loaded successfully!", color="success", className="mb-3"),
            html.Pre(
                json.dumps(dataset, indent=2),
                style={
                    'backgroundColor': '#f8f9fa',
                    'padding': '15px',
                    'borderRadius': '5px',
                    'overflow': 'auto',
                    'maxHeight': '500px',
                    'fontSize': '11px'
                }
            )
        ])
    ])
    
    # Store original dataset for filtering later
    import copy
    return dataset_card, False, copy.deepcopy(dataset)




# ============================================================================
# EXISTING DASHBOARD CALLBACKS (Moved to existing_dashboard_page.py)
# ============================================================================
# The retrieve and delete callbacks for existing dashboards have been moved
# to existing_dashboard_page.py and are registered via register_existing_dashboard_callbacks()

# ============================================================================
# DESIGN INFUSION CALLBACKS
# ============================================================================

@callback(
    Output("infusion-collapse", "is_open"),
    Input("infusion-toggle-btn", "n_clicks"),
    State("infusion-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_infusion(n_clicks, is_open):
    """Toggle the infusion upload section"""
    if n_clicks:
        return not is_open
    return is_open


@callback(
    [Output('infusion-result', 'children'),
     Output('infusion-design-data', 'data')],
    Input('infusion-image-upload', 'contents'),
    State('infusion-image-upload', 'filename'),
    prevent_initial_call=True
)
def process_infusion_upload(contents, filename):
    """
    Process uploaded image and extract design elements (pre-generation)
    """
    # Call the extract function from design_infusion module
    return extract_design_from_image(contents, filename, llm_client)


@callback(
    [Output('pre-generation-infusion-result', 'children'),
     Output('infusion-design-data', 'data', allow_duplicate=True)],
    Input('pre-generation-design-from-prompt-btn', 'n_clicks'),
    State('pre-generation-infusion-prompt', 'value'),
    prevent_initial_call=True
)
def process_pre_generation_infusion_prompt(n_clicks, prompt_text):
    """
    Process text prompt and generate design elements (pre-generation)
    """
    if not n_clicks or not prompt_text or not prompt_text.strip():
        return no_update, no_update
    
    # Call the generate function from design_infusion module
    return generate_design_from_prompt(prompt_text, llm_client)


@callback(
    Output('infusion-modal', 'is_open', allow_duplicate=True),
    Input('apply-infusion-btn', 'n_clicks'),
    State('infusion-modal', 'is_open'),
    prevent_initial_call=True
)
def open_infusion_modal(n_clicks, is_open):
    """Open the infusion modal when Infusion button is clicked (New Dashboard page)"""
    if n_clicks:
        return True
    return is_open


@callback(
    Output('existing-infusion-modal', 'is_open', allow_duplicate=True),
    Input('existing-apply-infusion-btn', 'n_clicks'),
    State('existing-infusion-modal', 'is_open'),
    prevent_initial_call=True
)
def open_existing_infusion_modal(n_clicks, is_open):
    """Open the infusion modal when Infusion button is clicked (Existing Dashboard page)"""
    if n_clicks:
        return True
    return is_open


@callback(
    [Output('infusion-modal', 'is_open', allow_duplicate=True),
     Output('dashboard-infusion-upload', 'contents', allow_duplicate=True),
     Output('dashboard-infusion-prompt', 'value', allow_duplicate=True)],
    Input('close-infusion-modal', 'n_clicks'),
    State('infusion-modal', 'is_open'),
    prevent_initial_call=True
)
def close_infusion_modal(n_clicks, is_open):
    """Close the infusion modal and clear upload/prompt (New Dashboard page)"""
    if n_clicks:
        return False, None, ""  # Close modal and clear both upload and prompt
    return is_open, no_update, no_update


@callback(
    [Output('existing-infusion-modal', 'is_open', allow_duplicate=True),
     Output('existing-dashboard-infusion-upload', 'contents', allow_duplicate=True),
     Output('existing-dashboard-infusion-prompt', 'value', allow_duplicate=True)],
    Input('close-existing-infusion-modal', 'n_clicks'),
    State('existing-infusion-modal', 'is_open'),
    prevent_initial_call=True
)
def close_existing_infusion_modal(n_clicks, is_open):
    """Close the infusion modal and clear upload/prompt (Existing Dashboard page)"""
    if n_clicks:
        return False, None, ""  # Close modal and clear both upload and prompt
    return is_open, no_update, no_update


@callback(
    [Output('dashboard-infusion-status', 'children', allow_duplicate=True),
     Output('dashboard-preview', 'children', allow_duplicate=True),
     Output('deployed-dashboard-id', 'data', allow_duplicate=True),
     Output('current-dashboard-config', 'data', allow_duplicate=True),
     Output('current-dashboard-name', 'data', allow_duplicate=True),
     Output('infusion-modal', 'is_open', allow_duplicate=True),
     Output('dashboard-infusion-upload', 'contents', allow_duplicate=True),
     Output('dashboard-infusion-prompt', 'value', allow_duplicate=True)],
    [Input('dashboard-infusion-upload', 'contents'),
     Input('generate-design-from-prompt-btn', 'n_clicks')],
    [State('dashboard-infusion-upload', 'filename'),
     State('dashboard-infusion-prompt', 'value'),
     State('deployed-dashboard-id', 'data'),
     State('current-dashboard-config', 'data'),
     State('current-dashboard-name', 'data')],
    prevent_initial_call=True
)
def apply_infusion_to_new_dashboard(contents, prompt_btn_clicks, filename, prompt_text, dashboard_id, dashboard_config, dashboard_name):
    """Process uploaded image OR text prompt and apply design infusion to NEW dashboard (from New Dashboard page)"""
    from dash import callback_context
    
    # Check what triggered the callback
    if not callback_context.triggered:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    
    # Validate that we have dashboard data
    if not dashboard_id or not dashboard_config:
        error_msg = dbc.Alert("⚠️ Missing dashboard data", color="warning")
        return error_msg, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    # Validate that we have either image or prompt
    if trigger_id == 'dashboard-infusion-upload' and not contents:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    if trigger_id == 'generate-design-from-prompt-btn' and (not prompt_text or not prompt_text.strip()):
        error_msg = dbc.Alert("⚠️ Please enter a design description", color="warning")
        return error_msg, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    try:
        # Extract/Generate design based on input type
        # design_infusion functions already imported from dashboard at module level
        import copy
        
        print(f"🎨 Processing new design infusion for dashboard {dashboard_id}")
        
        # Handle different input types
        if trigger_id == 'dashboard-infusion-upload':
            print(f"📷 Processing image upload")
            result_display, design_data = extract_design_from_image(contents, filename, llm_client)
            # Check if result_display is an error (design_data will be None)
            if design_data is None:
                print(f"❌ Image extraction failed - returning error display")
                return result_display, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        else:  # generate-design-from-prompt-btn
            print(f"✍️ Generating design from prompt: {prompt_text[:50]}...")
            result_display, design_data = generate_design_from_prompt(prompt_text, llm_client)
            # Check if result_display is an error (design_data will be None)
            if design_data is None:
                print(f"❌ Design generation from prompt failed - returning error display")
                return result_display, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        if not design_data or 'uiSettings' not in design_data:
            error_msg = dbc.Alert("⚠️ Failed to extract/generate design elements", color="warning")
            return error_msg, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        print(f"✅ New design extracted/generated successfully")
        
        # Extract the serialized_dashboard from the config (for retrieved dashboards)
        if 'serialized_dashboard' in dashboard_config:
            print(f"📋 Extracting serialized_dashboard from retrieved config")
            serialized = dashboard_config.get('serialized_dashboard', {})
            
            # Parse if it's a JSON string
            if isinstance(serialized, str):
                try:
                    serialized = json.loads(serialized)
                except json.JSONDecodeError as e:
                    print(f"Error parsing serialized_dashboard: {e}")
                    error_msg = dbc.Alert(f"⚠️ Error parsing dashboard configuration: {str(e)}", color="danger")
                    return error_msg, no_update, no_update, no_update, no_update, no_update, no_update, no_update
            
            # Use the serialized dashboard as the config
            updated_config = copy.deepcopy(serialized)
        else:
            # For newly created dashboards, the config is already in the right format
            updated_config = copy.deepcopy(dashboard_config)
        
        # Remove old uiSettings if exists, then add new one
        if 'uiSettings' in updated_config:
            print(f"🔄 Replacing existing design with new infused design")
            del updated_config['uiSettings']
        
        updated_config['uiSettings'] = design_data['uiSettings']
        print(f"✅ New uiSettings applied to config")
        
        # Update dashboard in place using Lakeview API (instead of delete+recreate)
        # # Delete the old dashboard
        # print(f"🗑️ Deleting old dashboard {dashboard_id}")
        # dashboard_manager.delete_dashboard(dashboard_id)
        # 
        # # Create new dashboard with updated config
        # print(f"🚀 Creating new dashboard with infused design")
        # new_dashboard_id = dashboard_manager.create_dashboard(updated_config, dashboard_name)
        
        print(f"🔄 Updating dashboard {dashboard_id} with infused design")
        new_dashboard_id = dashboard_manager.update_dashboard(dashboard_id, updated_config)
        new_embed_url = dashboard_manager.get_embed_url(new_dashboard_id)
        
        # Add cache-busting parameter to force iframe refresh
        cache_buster = f"?_refresh={int(time.time() * 1000)}"
        new_embed_url_with_refresh = new_embed_url + cache_buster
        
        # Create new preview
        preview_card = dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H4(f"✅ Dashboard Updated with Design Infusion: {dashboard_name}"),
                        html.Small(f"Dashboard ID: {new_dashboard_id}", className="text-muted")
                    ], width=7),
                    dbc.Col([
                        dbc.Button("Apply Infusion", id="apply-infusion-btn", color="primary", size="sm", className="me-2"),
                            dbc.Button("Delete Dashboard", id="delete-dashboard-btn", color="danger", size="sm")
                    ], width=5, className="text-end")
                ], align="center")
            ]),
            dbc.CardBody([
                html.Iframe(
                    src=new_embed_url_with_refresh,
                    style={
                        'width': '100%',
                        'height': '800px',
                        'border': '1px solid #ddd',
                        'borderRadius': '5px'
                    }
                )
            ])
        ])
        
        success_msg = dbc.Alert([
            html.Strong("✅ Design infusion applied successfully!"),
            html.Br(),
            html.Small("Dashboard has been updated with new theme.")
        ], color="success")
        
        # For new dashboards, no need to wrap in serialized_dashboard
        # Store config directly
        
        # Close modal and clear both upload and prompt after success
        return success_msg, preview_card, new_dashboard_id, updated_config, dashboard_name, False, None, ""
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = dbc.Alert([
            html.Strong("❌ Error applying infusion"),
            html.Br(),
            html.Small(f"Error: {str(e)}")
        ], color="danger")
        return error_msg, no_update, no_update, no_update, no_update, no_update, no_update, no_update


@callback(
    [Output('existing-design-analysis-display', 'children'),
     Output('existing-design-reasoning-display', 'children'),
     Output('existing-design-validation-section', 'style'),
     Output('design-analysis-text', 'data'),
     Output('design-reasoning-text', 'data'),
     Output('design-generated-ui-settings', 'data'),
     Output('original-design-prompt', 'data'),
     Output('previous-design-data', 'data'),
     Output('existing-dashboard-infusion-status', 'children'),
     Output('existing-dashboard-preview', 'children', allow_duplicate=True),
     Output('existing-infusion-modal', 'is_open', allow_duplicate=True),
     Output('existing-dashboard-config', 'data', allow_duplicate=True)],
    [Input('existing-dashboard-infusion-upload', 'contents'),
     Input('existing-generate-design-from-prompt-btn', 'n_clicks')],
    [State('existing-dashboard-infusion-upload', 'filename'),
     State('existing-dashboard-infusion-prompt', 'value'),
     State('existing-dashboard-id', 'data'),
     State('existing-dashboard-config', 'data'),
     State('existing-dashboard-name', 'data')],
    prevent_initial_call=True
)
def generate_design_for_existing_dashboard(contents, prompt_btn_clicks, filename, prompt_text, dashboard_id, dashboard_config, dashboard_name):
    """Generate design with analysis and reasoning (NEW INTELLIGENT WORKFLOW - doesn't apply immediately)"""
    from dash import callback_context
    
    # Check what triggered the callback
    if not callback_context.triggered:
        return "", "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
    
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    
    # Validate that we have dashboard data
    if not dashboard_id or not dashboard_config:
        error_msg = dbc.Alert("⚠️ Missing dashboard data", color="warning")
        return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
    
    # Handle image upload path separately (legacy direct application)
    if trigger_id == 'existing-dashboard-infusion-upload':
        # Image upload path
        if not contents:
            # No image provided
            return "", "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
        
        try:
            print(f"📷 Processing image upload for immediate application")
            result_display, design_data = extract_design_from_image(contents, filename, llm_client)
            
            # Check if result_display is an error (Alert component)
            if design_data is None:
                # extract_design_from_image returned an error in result_display
                print(f"❌ Image extraction failed - returning error display")
                return result_display, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
            
            if not design_data or 'uiSettings' not in design_data:
                error_msg = dbc.Alert("⚠️ Failed to extract design elements from image", color="warning")
                return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
            
            print(f"✅ Design extracted from image successfully")
            
            # Apply the design immediately (same as new dashboard)
            serialized = dashboard_config.get('serialized_dashboard', {})
            if isinstance(serialized, str):
                serialized = json.loads(serialized)
            
            # Update config with new design
            import copy
            updated_config = copy.deepcopy(serialized)
            if 'uiSettings' in updated_config:
                print(f"🔄 Replacing existing design with image-extracted design")
                del updated_config['uiSettings']
            
            updated_config['uiSettings'] = design_data['uiSettings']
            print(f"✅ New uiSettings applied to config")
            
            # Update dashboard and get new embed URL
            print(f"🔄 Updating dashboard {dashboard_id} with image-extracted design")
            dashboard_manager.update_dashboard(dashboard_id, updated_config)
            new_embed_url = dashboard_manager.get_embed_url(dashboard_id)
            
            # Add cache-busting parameter
            import time
            cache_buster = f"?_refresh={int(time.time() * 1000)}"
            new_embed_url_with_refresh = new_embed_url + cache_buster
            
            # Create updated preview card (same as validation callback)
            dashboard_name = dashboard_config.get('display_name', f'Dashboard {dashboard_id[:8]}')
            preview_card = dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H4(f"✅ Dashboard Updated: {dashboard_name}"),
                            html.Small(f"Dashboard ID: {dashboard_id}", className="text-muted")
                        ], width=7),
                        dbc.Col([
                            dbc.Button("Apply Infusion", id="existing-apply-infusion-btn", color="primary", size="sm", className="me-2"),
                            dbc.Button("Delete Dashboard", id="existing-delete-dashboard-btn", color="danger", size="sm")
                        ], width=5, className="text-end")
                    ], align="center")
                ]),
                dbc.CardBody([
                    html.Iframe(
                        src=new_embed_url_with_refresh,
                        style={
                            'width': '100%',
                            'height': '800px',
                            'border': '1px solid #ddd',
                            'borderRadius': '5px'
                        }
                    )
                ])
            ])
            
            # Update the stored config
            full_updated_config = {
                'serialized_dashboard': updated_config,
                'display_name': dashboard_name
            }
            
            print(f"✅ Image-based design applied successfully! Closing modal and refreshing preview.")
            
            # Return: empty analysis/reasoning displays, hide validation section, 
            # update preview, close modal (False), update config
            return "", "", {'display': 'none'}, None, None, None, None, None, "", preview_card, False, full_updated_config
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Unexpected exception in existing dashboard image upload: {str(e)}")
            error_msg = dbc.Alert([
                html.Strong("❌ Error processing image upload"),
                html.Br(),
                html.Small(f"Error: {str(e)}")
            ], color="danger")
            return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
    
    # Handle text prompt path (intelligent workflow)
    if trigger_id == 'existing-generate-design-from-prompt-btn':
        if not prompt_text or not prompt_text.strip():
            error_msg = dbc.Alert("⚠️ Please enter a design description", color="warning")
            return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
        
        try:
            # INTELLIGENT WORKFLOW for text prompts
            print(f"🎨 [INTELLIGENT] Analyzing dashboard and generating design with reasoning")
            print(f"   Dashboard: {dashboard_id}")
            print(f"   Prompt: {prompt_text[:50]}...")
            
            # Call the new intelligent function
            analysis_display, reasoning_display, ui_settings, analysis_txt, reasoning_txt = generate_design_with_analysis(
                prompt_text,
                dashboard_config,
                llm_client
            )
            
            if not ui_settings or 'uiSettings' not in ui_settings:
                # Check if analysis_display contains error details
                if analysis_display and hasattr(analysis_display, 'children'):
                    # Return the actual error from the design_infusion function
                    return analysis_display, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
                else:
                    error_msg = dbc.Alert([
                        html.Strong("⚠️ Failed to generate design"),
                        html.Br(),
                        html.Small("Check the console/terminal for detailed error information.")
                    ], color="warning")
                    return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
            
            print(f"✅ Design generated with analysis and reasoning")
            
            # Extract previous design for refinement
            serialized = dashboard_config.get('serialized_dashboard', {})
            if isinstance(serialized, str):
                serialized = json.loads(serialized)
            
            previous_theme = serialized.get('uiSettings', {}).get('theme', {})
            previous_design = {
                'canvasBackgroundColor': previous_theme.get('canvasBackgroundColor', {}).get('light', '#FAFAFB'),
                'widgetBackgroundColor': previous_theme.get('widgetBackgroundColor', {}).get('light', '#FFFFFF'),
                'widgetBorderColor': previous_theme.get('widgetBorderColor', {}).get('light', '#E0E0E0'),
                'fontColor': previous_theme.get('fontColor', {}).get('light', '#11171C'),
                'visualizationColors': previous_theme.get('visualizationColors', []),
                'fontFamily': previous_theme.get('fontFamily', 'Arial')
            }
            
            # Show validation section
            validation_style = {'display': 'block'}
            
            return (
                "",  # Don't show analysis display (user doesn't need to see it)
                reasoning_display,
                validation_style,
                analysis_txt,
                reasoning_txt,
                ui_settings,
                prompt_text,  # Store original prompt for refinement
                previous_design,  # Store previous design
                "",  # Clear status
                no_update,  # Don't update preview yet (wait for validation)
                no_update,  # Don't close modal yet (wait for validation)
                no_update  # Don't update config yet (wait for validation)
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = dbc.Alert([
                html.Strong("❌ Error during design generation"),
                html.Br(),
                html.Small(f"Error: {str(e)}")
            ], color="danger")
            return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
    
    # If we reach here, neither condition was met (shouldn't happen)
    return "", "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update


# NEW CALLBACKS FOR INTELLIGENT DESIGN INFUSION WORKFLOW

@callback(
    [Output('existing-dashboard-preview', 'children', allow_duplicate=True),
     Output('existing-dashboard-id', 'data', allow_duplicate=True),
     Output('existing-dashboard-config', 'data', allow_duplicate=True),
     Output('existing-infusion-modal', 'is_open', allow_duplicate=True),
     Output('existing-dashboard-infusion-prompt', 'value', allow_duplicate=True),
     Output('existing-design-validation-section', 'style', allow_duplicate=True),
     Output('existing-dashboard-infusion-status', 'children', allow_duplicate=True)],
    Input('existing-validate-design-btn', 'n_clicks'),
    [State('design-generated-ui-settings', 'data'),
     State('existing-dashboard-id', 'data'),
     State('existing-dashboard-config', 'data'),
     State('existing-dashboard-name', 'data')],
    prevent_initial_call=True
)
def apply_validated_design_to_existing(n_clicks, ui_settings, dashboard_id, dashboard_config, dashboard_name):
    """Apply the validated design to the existing dashboard"""
    if not n_clicks or not ui_settings or not dashboard_id:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    try:
        import copy
        
        print(f"✅ [VALIDATION] Applying validated design to dashboard {dashboard_id}")
        
        # Extract serialized_dashboard
        serialized = dashboard_config.get('serialized_dashboard', {})
        if isinstance(serialized, str):
            serialized = json.loads(serialized)
        
        updated_config = copy.deepcopy(serialized)
        
        # Remove old uiSettings and apply new one
        if 'uiSettings' in updated_config:
            del updated_config['uiSettings']
        
        updated_config['uiSettings'] = ui_settings['uiSettings']
        print(f"✅ uiSettings applied to config")
        
        # Update dashboard
        print(f"🔄 Updating dashboard...")
        updated_dashboard_id = dashboard_manager.update_dashboard(dashboard_id, updated_config)
        new_embed_url = dashboard_manager.get_embed_url(updated_dashboard_id)
        
        # Add cache-busting
        cache_buster = f"?_refresh={int(time.time() * 1000)}"
        new_embed_url_with_refresh = new_embed_url + cache_buster
        
        # Create preview
        preview_card = dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H4(f"✅ Dashboard Updated: {dashboard_name}"),
                        html.Small(f"Dashboard ID: {updated_dashboard_id}", className="text-muted")
                    ], width=7),
                    dbc.Col([
                        dbc.Button("Apply Infusion", id="existing-apply-infusion-btn", color="primary", size="sm", className="me-2"),
                        dbc.Button("Delete Dashboard", id="existing-delete-dashboard-btn", color="danger", size="sm")
                    ], width=5, className="text-end")
                ], align="center")
            ]),
            dbc.CardBody([
                html.Iframe(
                    src=new_embed_url_with_refresh,
                    style={
                        'width': '100%',
                        'height': '800px',
                        'border': '1px solid #ddd',
                        'borderRadius': '5px'
                    }
                )
            ])
        ])
        
        # Store updated config
        full_updated_config = {
            'serialized_dashboard': updated_config
        }
        
        success_msg = dbc.Alert("✅ Design applied successfully!", color="success")
        
        # Close modal, clear prompt, hide validation section
        return preview_card, updated_dashboard_id, full_updated_config, False, "", {'display': 'none'}, success_msg
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = dbc.Alert(f"❌ Error applying design: {str(e)}", color="danger")
        return no_update, no_update, no_update, no_update, no_update, no_update, error_msg


@callback(
    Output('existing-refinement-collapse', 'is_open'),
    Input('existing-refine-design-btn', 'n_clicks'),
    State('existing-refinement-collapse', 'is_open'),
    prevent_initial_call=True
)
def toggle_existing_refinement(n_clicks, is_open):
    """Toggle the refinement input section"""
    if n_clicks:
        return not is_open
    return is_open


@callback(
    [Output('existing-design-reasoning-display', 'children', allow_duplicate=True),
     Output('design-reasoning-text', 'data', allow_duplicate=True),
     Output('design-generated-ui-settings', 'data', allow_duplicate=True),
     Output('existing-refinement-collapse', 'is_open', allow_duplicate=True),
     Output('existing-dashboard-infusion-status', 'children', allow_duplicate=True)],
    Input('existing-apply-refinement-btn', 'n_clicks'),
    [State('existing-design-refinement-prompt', 'value'),
     State('original-design-prompt', 'data'),
     State('design-reasoning-text', 'data'),
     State('previous-design-data', 'data'),
     State('existing-dashboard-config', 'data')],
    prevent_initial_call=True
)
def apply_design_refinement_to_existing(n_clicks, feedback, original_prompt, previous_reasoning, previous_design, dashboard_config):
    """Refine design based on user feedback"""
    if not n_clicks or not feedback or not feedback.strip():
        return no_update, no_update, no_update, no_update, no_update
    
    try:
        print(f"🔄 [REFINEMENT] Applying feedback: {feedback[:50]}...")
        
        # Call refinement function
        refined_reasoning, refined_ui_settings, refined_txt = refine_design_from_feedback(
            original_prompt,
            feedback,
            previous_reasoning,
            previous_design,
            dashboard_config,
            llm_client
        )
        
        if not refined_ui_settings or 'uiSettings' not in refined_ui_settings:
            error_msg = dbc.Alert("⚠️ Failed to refine design", color="warning")
            return error_msg, no_update, no_update, no_update, ""
        
        print(f"✅ Design refined successfully")
        
        success_msg = dbc.Alert("✅ Design refined! Review and validate or refine again.", color="info")
        
        # Update reasoning display, close refinement section
        return refined_reasoning, refined_txt, refined_ui_settings, False, success_msg
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = dbc.Alert(f"❌ Refinement error: {str(e)}", color="danger")
        return error_msg, no_update, no_update, no_update, ""


# ============================================================================
# NEW DASHBOARD INTELLIGENT INFUSION CALLBACKS (POST-GENERATION)
# ============================================================================

@callback(
    [Output('new-dashboard-design-analysis-display', 'children'),
     Output('new-dashboard-design-reasoning-display', 'children'),
     Output('new-dashboard-design-validation-section', 'style'),
     Output('new-dashboard-design-analysis-text', 'data'),
     Output('new-dashboard-design-reasoning-text', 'data'),
     Output('new-dashboard-design-generated-ui-settings', 'data'),
     Output('new-dashboard-original-design-prompt', 'data'),
     Output('new-dashboard-previous-design-data', 'data'),
     Output('post-gen-infusion-status', 'children'),
     Output('dashboard-preview', 'children', allow_duplicate=True),
     Output('infusion-modal', 'is_open', allow_duplicate=True),
     Output('current-dashboard-config', 'data', allow_duplicate=True)],
    [Input('post-gen-infusion-upload', 'contents'),
     Input('post-gen-generate-design-btn', 'n_clicks')],
    [State('post-gen-infusion-upload', 'filename'),
     State('post-gen-infusion-prompt', 'value'),
     State('deployed-dashboard-id', 'data'),
     State('current-dashboard-config', 'data'),
     State('current-dashboard-name', 'data')],
    prevent_initial_call=True
)
def generate_design_for_new_dashboard(contents, prompt_btn_clicks, filename, prompt_text, dashboard_id, dashboard_config, dashboard_name):
    """Generate design with analysis and reasoning for NEW dashboard (after generation)"""
    from dash import callback_context
    
    # Check what triggered the callback
    if not callback_context.triggered:
        return "", "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
    
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    
    # Validate that we have dashboard data
    if not dashboard_id or not dashboard_config:
        error_msg = dbc.Alert("⚠️ Missing dashboard data", color="warning")
        return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
    
    # Handle image upload path separately (legacy direct application)
    if trigger_id == 'post-gen-infusion-upload':
        # Image upload path - immediate application
        if not contents:
            return "", "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
        
        try:
            print(f"📷 Processing image upload for NEW dashboard - immediate application")
            result_display, design_data = extract_design_from_image(contents, filename, llm_client)
            
            if design_data is None:
                print(f"❌ Image extraction failed")
                return result_display, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
            
            if not design_data or 'uiSettings' not in design_data:
                error_msg = dbc.Alert("⚠️ Failed to extract design elements from image", color="warning")
                return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
            
            print(f"✅ Design extracted from image successfully")
            
            # Apply the design immediately
            serialized = dashboard_config.get('serialized_dashboard', {})
            if isinstance(serialized, str):
                serialized = json.loads(serialized)
            
            import copy
            updated_config = copy.deepcopy(serialized)
            if 'uiSettings' in updated_config:
                del updated_config['uiSettings']
            
            updated_config['uiSettings'] = design_data['uiSettings']
            
            # Update dashboard
            dashboard_manager.update_dashboard(dashboard_id, updated_config)
            new_embed_url = dashboard_manager.get_embed_url(dashboard_id)
            
            # Add cache-busting
            import time
            cache_buster = f"?_refresh={int(time.time() * 1000)}"
            new_embed_url_with_refresh = new_embed_url + cache_buster
            
            # Construct dashboard URL
            workspace_url = workspace_client.config.host
            dashboard_url = f"{workspace_url}/dashboardsv3/{dashboard_id}"
            
            # Create updated preview card
            preview_card = dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H4(f"✅ Dashboard Updated: {dashboard_name}"),
                            html.A(
                                "Open Dashboard in New Tab",
                                href=dashboard_url,
                                target="_blank",
                                className="text-muted small d-block mt-1"
                            )
                        ], width=7),
                        dbc.Col([
                            dbc.Button("Apply Infusion", id="apply-infusion-btn", color="primary", size="sm", className="me-2"),
                            dbc.Button("Delete Dashboard", id="delete-dashboard-btn", color="danger", size="sm")
                        ], width=5, className="text-end")
                    ], align="center")
                ]),
                dbc.CardBody([
                    html.Iframe(
                        src=new_embed_url_with_refresh,
                        style={
                            'width': '100%',
                            'height': '800px',
                            'border': '1px solid #ddd',
                            'borderRadius': '5px'
                        }
                    )
                ])
            ])
            
            # Update stored config
            full_updated_config = {
                'serialized_dashboard': updated_config,
                'display_name': dashboard_name
            }
            
            print(f"✅ Image-based design applied! Closing modal and refreshing preview.")
            
            return "", "", {'display': 'none'}, None, None, None, None, None, "", preview_card, False, full_updated_config
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = dbc.Alert([
                html.Strong("❌ Error processing image upload"),
                html.Br(),
                html.Small(f"Error: {str(e)}")
            ], color="danger")
            return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
    
    # Handle text prompt path (intelligent workflow)
    if trigger_id == 'post-gen-generate-design-btn':
        if not prompt_text or not prompt_text.strip():
            error_msg = dbc.Alert("⚠️ Please enter a design description", color="warning")
            return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
        
        try:
            print(f"🎨 [INTELLIGENT] Analyzing NEW dashboard and generating design with reasoning")
            print(f"   Dashboard: {dashboard_id}")
            print(f"   Prompt: {prompt_text[:50]}...")
            
            # Call the intelligent function
            analysis_display, reasoning_display, ui_settings, analysis_txt, reasoning_txt = generate_design_with_analysis(
                prompt_text,
                dashboard_config,
                llm_client
            )
            
            if not ui_settings or 'uiSettings' not in ui_settings:
                if analysis_display and hasattr(analysis_display, 'children'):
                    return analysis_display, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
                else:
                    error_msg = dbc.Alert([
                        html.Strong("⚠️ Failed to generate design"),
                        html.Br(),
                        html.Small("Check the console/terminal for detailed error information.")
                    ], color="warning")
                    return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
            
            print(f"✅ Design generated with analysis and reasoning")
            
            # Extract previous design for refinement
            serialized = dashboard_config.get('serialized_dashboard', {})
            if isinstance(serialized, str):
                serialized = json.loads(serialized)
            
            previous_theme = serialized.get('uiSettings', {}).get('theme', {})
            previous_design = {
                'canvasBackgroundColor': previous_theme.get('canvasBackgroundColor', {}).get('light', '#FAFAFB'),
                'widgetBackgroundColor': previous_theme.get('widgetBackgroundColor', {}).get('light', '#FFFFFF'),
                'widgetBorderColor': previous_theme.get('widgetBorderColor', {}).get('light', '#E0E0E0'),
                'fontColor': previous_theme.get('fontColor', {}).get('light', '#11171C'),
                'visualizationColors': previous_theme.get('visualizationColors', []),
                'fontFamily': previous_theme.get('fontFamily', 'Arial')
            }
            
            # Show validation section
            validation_style = {'display': 'block'}
            
            return (
                "",  # Don't show analysis display
                reasoning_display,
                validation_style,
                analysis_txt,
                reasoning_txt,
                ui_settings,
                prompt_text,  # Store original prompt
                previous_design,  # Store previous design
                "",  # Clear status
                no_update,  # Don't update preview yet
                no_update,  # Don't close modal yet
                no_update  # Don't update config yet
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = dbc.Alert([
                html.Strong("❌ Error during design generation"),
                html.Br(),
                html.Small(f"Error: {str(e)}")
            ], color="danger")
            return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
    
    # No valid trigger
    return "", "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update


@callback(
    [Output('dashboard-preview', 'children', allow_duplicate=True),
     Output('deployed-dashboard-id', 'data', allow_duplicate=True),
     Output('current-dashboard-config', 'data', allow_duplicate=True),
     Output('infusion-modal', 'is_open', allow_duplicate=True),
     Output('post-gen-infusion-prompt', 'value', allow_duplicate=True),
     Output('new-dashboard-design-validation-section', 'style', allow_duplicate=True),
     Output('post-gen-infusion-status', 'children', allow_duplicate=True)],
    Input('new-dashboard-validate-design-btn', 'n_clicks'),
    [State('new-dashboard-design-generated-ui-settings', 'data'),
     State('deployed-dashboard-id', 'data'),
     State('current-dashboard-config', 'data'),
     State('current-dashboard-name', 'data')],
    prevent_initial_call=True
)
def apply_validated_design_to_new_dashboard(n_clicks, ui_settings, dashboard_id, dashboard_config, dashboard_name):
    """Apply the validated design to the new dashboard"""
    if not n_clicks or not ui_settings or not dashboard_id:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    try:
        import copy
        
        print(f"✅ [VALIDATION] Applying validated design to NEW dashboard {dashboard_id}")
        
        # Extract serialized_dashboard
        serialized = dashboard_config.get('serialized_dashboard', {})
        if isinstance(serialized, str):
            serialized = json.loads(serialized)
        
        updated_config = copy.deepcopy(serialized)
        
        # Remove old uiSettings and apply new one
        if 'uiSettings' in updated_config:
            del updated_config['uiSettings']
        
        updated_config['uiSettings'] = ui_settings['uiSettings']
        print(f"✅ uiSettings applied to config")
        
        # Update dashboard
        print(f"🔄 Updating dashboard...")
        updated_dashboard_id = dashboard_manager.update_dashboard(dashboard_id, updated_config)
        new_embed_url = dashboard_manager.get_embed_url(updated_dashboard_id)
        
        # Add cache-busting
        cache_buster = f"?_refresh={int(time.time() * 1000)}"
        new_embed_url_with_refresh = new_embed_url + cache_buster
        
        # Construct dashboard URL
        workspace_url = workspace_client.config.host
        dashboard_url = f"{workspace_url}/dashboardsv3/{updated_dashboard_id}"
        
        # Create preview
        preview_card = dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H4(f"✅ Dashboard Updated: {dashboard_name}"),
                        html.A(
                            "🔗 Open Dashboard in New Tab",
                            href=dashboard_url,
                            target="_blank",
                            className="text-muted small d-block mt-1"
                        )
                    ], width=7),
                    dbc.Col([
                        dbc.Button("Apply Infusion", id="apply-infusion-btn", color="primary", size="sm", className="me-2"),
                        dbc.Button("Delete Dashboard", id="delete-dashboard-btn", color="danger", size="sm")
                    ], width=5, className="text-end")
                ], align="center")
            ]),
            dbc.CardBody([
                html.Iframe(
                    src=new_embed_url_with_refresh,
                    style={
                        'width': '100%',
                        'height': '800px',
                        'border': '1px solid #ddd',
                        'borderRadius': '5px'
                    }
                )
            ])
        ])
        
        # Store updated config
        full_updated_config = {
            'serialized_dashboard': updated_config,
            'display_name': dashboard_name
        }
        
        success_msg = dbc.Alert("✅ Design applied successfully!", color="success")
        
        # Close modal, clear prompt, hide validation section
        return preview_card, updated_dashboard_id, full_updated_config, False, "", {'display': 'none'}, success_msg
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = dbc.Alert(f"❌ Error applying design: {str(e)}", color="danger")
        return no_update, no_update, no_update, no_update, no_update, no_update, error_msg


@callback(
    Output('new-dashboard-refinement-collapse', 'is_open'),
    Input('new-dashboard-refine-design-btn', 'n_clicks'),
    State('new-dashboard-refinement-collapse', 'is_open'),
    prevent_initial_call=True
)
def toggle_new_dashboard_refinement(n_clicks, is_open):
    """Toggle the refinement input section for new dashboard"""
    if n_clicks:
        return not is_open
    return is_open


@callback(
    [Output('new-dashboard-design-reasoning-display', 'children', allow_duplicate=True),
     Output('new-dashboard-design-reasoning-text', 'data', allow_duplicate=True),
     Output('new-dashboard-design-generated-ui-settings', 'data', allow_duplicate=True),
     Output('new-dashboard-refinement-collapse', 'is_open', allow_duplicate=True),
     Output('post-gen-infusion-status', 'children', allow_duplicate=True)],
    Input('new-dashboard-apply-refinement-btn', 'n_clicks'),
    [State('new-dashboard-design-refinement-prompt', 'value'),
     State('new-dashboard-original-design-prompt', 'data'),
     State('new-dashboard-design-reasoning-text', 'data'),
     State('new-dashboard-previous-design-data', 'data'),
     State('current-dashboard-config', 'data')],
    prevent_initial_call=True
)
def apply_design_refinement_to_new_dashboard(n_clicks, feedback, original_prompt, previous_reasoning, previous_design, dashboard_config):
    """Refine design based on user feedback for new dashboard"""
    if not n_clicks or not feedback or not feedback.strip():
        return no_update, no_update, no_update, no_update, no_update
    
    try:
        print(f"🔄 [REFINEMENT] Applying feedback for NEW dashboard: {feedback[:50]}...")
        
        # Call refinement function
        refined_reasoning, refined_ui_settings, refined_txt = refine_design_from_feedback(
            original_prompt,
            feedback,
            previous_reasoning,
            previous_design,
            dashboard_config,
            llm_client
        )
        
        if not refined_ui_settings or 'uiSettings' not in refined_ui_settings:
            error_msg = dbc.Alert("⚠️ Failed to refine design", color="warning")
            return error_msg, no_update, no_update, no_update, ""
        
        print(f"✅ Design refined successfully for NEW dashboard")
        
        success_msg = dbc.Alert("✅ Design refined! Review and validate or refine again.", color="info")
        
        # Update reasoning display, close refinement section
        return refined_reasoning, refined_txt, refined_ui_settings, False, success_msg
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = dbc.Alert(f"❌ Refinement error: {str(e)}", color="danger")
        return error_msg, no_update, no_update, no_update, ""


# ============================================================================
# REGISTER EXISTING DASHBOARD PAGE CALLBACKS
# ============================================================================

print("📋 Registering new dashboard page callbacks...")
register_new_dashboard_callbacks(app, datasets, llm_client, dashboard_manager, ai_progress_store, ai_results_store, workspace_client, WAREHOUSE_ID, UNITY_CATALOG, UNITY_SCHEMA)
print("✅ New dashboard page callbacks registered")

print("📋 Registering existing dashboard page callbacks...")
register_existing_dashboard_callbacks(app, dashboard_manager, workspace_client, WAREHOUSE_ID)
print("✅ Existing dashboard page callbacks registered")

print("📋 Registering manual dashboard configuration callbacks...")
register_manual_config_callbacks(app, datasets, dashboard_manager)
print("✅ Manual dashboard configuration callbacks registered")

print("📋 Registering test function page callbacks...")
register_test_function_callbacks(app, llm_client)
print("✅ Test function page callbacks registered")


# ============================================================================
# SIDEBAR NAVIGATION CALLBACK
# ============================================================================

@callback(
    [Output('page-content', 'children'),
     Output('active-page', 'data'),
     Output('nav-new-dashboard', 'className'),
     Output('nav-existing-dashboard', 'className'),
     Output('nav-layout-analyzer', 'className')],
    [Input('nav-new-dashboard', 'n_clicks'),
     Input('nav-existing-dashboard', 'n_clicks'),
     Input('nav-layout-analyzer', 'n_clicks')],
    [State('active-page', 'data')],
    prevent_initial_call=False
)
def navigate_pages(new_clicks, existing_clicks, analyzer_clicks, active_page):
    """Handle sidebar navigation"""
    from dash import callback_context
    
    # Default to new dashboard on initial load
    if not callback_context.triggered:
        return (
            get_new_dashboard_layout(UNITY_CATALOG, UNITY_SCHEMA),
            'new-dashboard',
            'w-100 text-start mb-2 nav-link-btn active',
            'w-100 text-start mb-2 nav-link-btn',
            'w-100 text-start mb-2 nav-link-btn'
        )
    
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'nav-new-dashboard':
        return (
            get_new_dashboard_layout(UNITY_CATALOG, UNITY_SCHEMA),
            'new-dashboard',
            'w-100 text-start mb-2 nav-link-btn active',
            'w-100 text-start mb-2 nav-link-btn',
            'w-100 text-start mb-2 nav-link-btn'
        )
    elif trigger_id == 'nav-existing-dashboard':
        return (
            get_existing_dashboard_layout(),
            'existing-dashboard',
            'w-100 text-start mb-2 nav-link-btn',
            'w-100 text-start mb-2 nav-link-btn active',
            'w-100 text-start mb-2 nav-link-btn'
        )
    elif trigger_id == 'nav-layout-analyzer':
        return (
            get_test_function_layout(),
            'layout-analyzer',
            'w-100 text-start mb-2 nav-link-btn',
            'w-100 text-start mb-2 nav-link-btn',
            'w-100 text-start mb-2 nav-link-btn active'
        )
    
    # Fallback (shouldn't happen)
    return no_update, no_update, no_update, no_update, no_update

print("✅ Sidebar navigation callback registered")


# Expose the Flask server for WSGI deployment (Databricks Apps, Gunicorn, etc.)
server = app.server

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Starting Dash development server...")
    print("=" * 60)
    app.run_server(debug=True, host="0.0.0.0", port=8050)