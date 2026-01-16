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
    from pages.existing_dashboard.existing_dashboard_infusion_callbacks import register_existing_dashboard_infusion_callbacks
    from pages.existing_dashboard.metrics_discovery_callbacks import register_metrics_discovery_callbacks
    from pages.new_dashboard.new_dashboard_infusion_callbacks import register_new_dashboard_infusion_callbacks
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
DATABRICKS_TOKEN = '<insert your token here>'
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
                
                # Dynamic content area - Initial page loaded on startup
                html.Div(
                    id='page-content',
                    children=[  # Initial content for first load
                        get_new_dashboard_layout(UNITY_CATALOG, UNITY_SCHEMA)
                    ]
                )
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


# ============================================================================
# ALL PAGE-SPECIFIC CALLBACKS HAVE BEEN MOVED TO THEIR RESPECTIVE MODULES
# ============================================================================

# NOTE: Existing dashboard callbacks moved to:
# pages/existing_dashboard/existing_dashboard_page.py
#   - retrieve_existing_dashboard (retrieve and display)
#   - delete_existing_dashboard (deletion)

# NOTE: Existing dashboard infusion callbacks moved to:
# pages/existing_dashboard/existing_dashboard_infusion_callbacks.py
#   - generate_design_for_existing_dashboard (main generation callback)
#   - apply_validated_design_to_existing (validation callback)
#   - toggle_existing_refinement (toggle refinement section)
#   - apply_design_refinement_to_existing (refinement callback)
#   - open_existing_infusion_modal (modal control)
#   - close_existing_infusion_modal (modal control)

# NOTE: New dashboard infusion callbacks moved to:
# pages/new_dashboard/new_dashboard_infusion_callbacks.py
#   - generate_design_for_new_dashboard (main generation callback)
#   - apply_validated_design_to_new_dashboard (validation callback)
#   - toggle_new_dashboard_refinement (toggle refinement section)
#   - apply_design_refinement_to_new_dashboard (refinement callback)
#   - open_infusion_modal (modal control)
#   - close_infusion_modal (modal control)

# NOTE: New dashboard pre-generation infusion callbacks moved to:
# pages/new_dashboard/new_dashboard_page.py
#   - toggle_infusion (collapse toggle)
#   - process_infusion_upload (image upload processing)
#   - process_pre_generation_infusion_prompt (prompt processing)


# ============================================================================
# REGISTER ALL CALLBACKS
# ============================================================================

print("📋 Registering new dashboard page callbacks...")
register_new_dashboard_callbacks(app, datasets, llm_client, dashboard_manager, ai_progress_store, ai_results_store, workspace_client, WAREHOUSE_ID, UNITY_CATALOG, UNITY_SCHEMA)
print("✅ New dashboard page callbacks registered")

print("📋 Registering existing dashboard page callbacks...")
register_existing_dashboard_callbacks(app, dashboard_manager, workspace_client, WAREHOUSE_ID)
print("✅ Existing dashboard page callbacks registered")

print("📋 Registering existing dashboard infusion callbacks...")
register_existing_dashboard_infusion_callbacks(app, dashboard_manager, workspace_client, llm_client)
print("✅ Existing dashboard infusion callbacks registered")

print("📋 Registering metrics discovery callbacks...")
register_metrics_discovery_callbacks(app, llm_client)
print("✅ Metrics discovery callbacks registered")

print("📋 Registering new dashboard infusion callbacks...")
register_new_dashboard_infusion_callbacks(app, dashboard_manager, workspace_client, llm_client)
print("✅ New dashboard infusion callbacks registered")

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
    
    try:
        # Default to new dashboard on initial load
        if not callback_context.triggered:
            print("🔄 Navigation: Initial page load - showing New Dashboard")
            return (
                get_new_dashboard_layout(UNITY_CATALOG, UNITY_SCHEMA),
                'new-dashboard',
                'w-100 text-start mb-2 nav-link-btn active',
                'w-100 text-start mb-2 nav-link-btn',
                'w-100 text-start mb-2 nav-link-btn'
            )
        
        trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        print(f"🔄 Navigation: User clicked {trigger_id}")
        
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
        print("⚠️ Navigation: No matching trigger, using no_update")
        return no_update, no_update, no_update, no_update, no_update
        
    except Exception as e:
        print(f"❌ Navigation callback error: {e}")
        import traceback
        traceback.print_exc()
        # Return no_update on error to prevent breaking the UI
        return no_update, no_update, no_update, no_update, no_update

print("✅ Sidebar navigation callback registered")


# Expose the Flask server for WSGI deployment (Databricks Apps, Gunicorn, etc.)
server = app.server

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Starting Dash development server...")
    print("=" * 60)
    app.run_server(debug=True, host="0.0.0.0", port=8050)