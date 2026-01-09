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
    from datasets import DATASETS as datasets
    from dataset_filter import apply_simple_filter_to_dataset, get_dataset_filters_summary
    print("✅ Dashboard modules imported")
    
    print("📦 Importing AI dashboard generator...")
    from dashboard_management_functions import generate_dashboard_background
    print("✅ AI dashboard generator imported successfully")
    
    print("📦 Importing design infusion module...")
    from dashboard_management_functions import extract_design_from_image, generate_design_from_prompt
    print("✅ Design infusion module imported successfully")
    
    print("📦 Importing page layouts...")
    from pages import (
        get_new_dashboard_layout, 
        get_existing_dashboard_layout,
        register_existing_dashboard_callbacks, 
        register_new_dashboard_callbacks,
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
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Suppress callback exceptions for dynamically generated components
app.config.suppress_callback_exceptions = True
print("✅ Dash app created")

# Configuration - Update these values for your environment
DATABRICKS_TOKEN = '<databricks_token>'
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


app.layout = dbc.Container([
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
    
    # Separate stores for EXISTING DASHBOARD PAGE
    dcc.Store(id='existing-dashboard-id', data=None),  # Store for existing dashboard ID
    dcc.Store(id='existing-dashboard-config', data=None),  # Store for existing dashboard config
    dcc.Store(id='existing-dashboard-name', data=None),  # Store for existing dashboard name
    
    dcc.Interval(id='ai-progress-interval', interval=500, disabled=True, n_intervals=0, max_intervals=300),  # Poll every 500ms, max 2.5 mins
    
    dbc.Row([
        dbc.Col([
            html.H1("Dashboard Design & Insight Lab", className="text-center mb-4 mt-4"),
            html.Hr()
        ])
    ]),
    
    # Tabs for New Dashboard vs Existing Dashboard
    dbc.Tabs([
        # Tab 1: New Dashboard
        dbc.Tab(label="📝 New Dashboard", tab_id="tab-new", children=[
            get_new_dashboard_layout(UNITY_CATALOG, UNITY_SCHEMA)
        ]),
        
        # Tab 2: Existing Dashboard
        dbc.Tab(label="📂 Existing Dashboard", tab_id="tab-existing", children=[
            get_existing_dashboard_layout()
        ])
    ], id="main-tabs", active_tab="tab-new"),
    
    # Modal for applying infusion to existing dashboard (shared between tabs)
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("🎨 Apply Design Infusion")),
        dbc.ModalBody([
            html.P("Choose how you want to generate your design:", className="mb-3"),
            
            # Option 1: Upload Image
            dbc.Card([
                dbc.CardBody([
                    html.H6("📷 Option 1: Upload an Image", className="mb-3"),
                    html.P("Upload a picture and the AI will extract colors and fonts from it.", className="text-muted small mb-3"),
                    dcc.Upload(
                        id='dashboard-infusion-upload',
                        children=html.Div([
                            '📷 Drag and Drop or ',
                            html.A('Select Image', style={'cursor': 'pointer', 'textDecoration': 'underline'})
                        ]),
                        style={
                            'width': '100%',
                            'height': '80px',
                            'lineHeight': '80px',
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
            ], className="mb-3"),
            
            # Option 2: Text Prompt
            dbc.Card([
                dbc.CardBody([
                    html.H6("✍️ Option 2: Describe Your Design", className="mb-3"),
                    html.P("Describe the style you want (e.g., 'Van Gogh painting style', 'Modern minimalist').", className="text-muted small mb-3"),
                    dbc.Textarea(
                        id='dashboard-infusion-prompt',
                        placeholder="Example: I would like the dashboard to have the same style as Van Gogh's paintings...",
                        style={'width': '100%', 'minHeight': '100px'},
                        className="mb-2"
                    ),
                    dbc.Button("✨ Generate Design", id="generate-design-from-prompt-btn", color="primary", size="sm")
                ])
            ], className="mb-3"),
            
            dcc.Loading(
                id="dashboard-infusion-loading",
                type="default",
                children=html.Div(id='dashboard-infusion-status', className="mt-3")
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-infusion-modal", color="secondary", size="sm")
        ])
    ], id="infusion-modal", size="lg", is_open=False),
    
    # Separate Modal for Existing Dashboard Page
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("🎨 Apply Design Infusion")),
        dbc.ModalBody([
            html.P("Choose how you want to generate your design:", className="mb-3"),
            
            # Option 1: Upload Image
            dbc.Card([
                dbc.CardBody([
                    html.H6("📷 Option 1: Upload an Image", className="mb-3"),
                    html.P("Upload a picture and the AI will extract colors and fonts from it.", className="text-muted small mb-3"),
                    dcc.Upload(
                        id='existing-dashboard-infusion-upload',
                        children=html.Div([
                            '📷 Drag and Drop or ',
                            html.A('Select Image', style={'cursor': 'pointer', 'textDecoration': 'underline'})
                        ]),
                        style={
                            'width': '100%',
                            'height': '80px',
                            'lineHeight': '80px',
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
            ], className="mb-3"),
            
            # Option 2: Text Prompt
            dbc.Card([
                dbc.CardBody([
                    html.H6("✍️ Option 2: Describe Your Design", className="mb-3"),
                    html.P("Describe the style you want (e.g., 'Van Gogh painting style', 'Modern minimalist').", className="text-muted small mb-3"),
                    dbc.Textarea(
                        id='existing-dashboard-infusion-prompt',
                        placeholder="Example: I would like the dashboard to have the same style as Van Gogh's paintings...",
                        style={'width': '100%', 'minHeight': '100px'},
                        className="mb-2"
                    ),
                    dbc.Button("✨ Generate Design", id="existing-generate-design-from-prompt-btn", color="primary", size="sm")
                ])
            ], className="mb-3"),
            
            dcc.Loading(
                id="existing-dashboard-infusion-loading",
                type="default",
                children=html.Div(id='existing-dashboard-infusion-status', className="mt-3")
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-existing-infusion-modal", color="secondary", size="sm")
        ])
    ], id="existing-infusion-modal", size="lg", is_open=False)
    
], fluid=True, className="p-4")


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
            _, design_data = extract_design_from_image(contents, filename, llm_client)
        else:  # generate-design-from-prompt-btn
            print(f"✍️ Generating design from prompt: {prompt_text[:50]}...")
            _, design_data = generate_design_from_prompt(prompt_text, llm_client)
        
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
        
        # Update dashboard in place using Lakeview API
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
                        dbc.Button("🎨 Infusion", id="apply-infusion-btn", color="primary", size="sm", className="me-2"),
                            dbc.Button("🗑️ Delete Dashboard", id="delete-dashboard-btn", color="danger", size="sm")
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
    [Output('existing-dashboard-infusion-status', 'children'),
     Output('existing-dashboard-preview', 'children', allow_duplicate=True),
     Output('existing-dashboard-id', 'data', allow_duplicate=True),
     Output('existing-dashboard-config', 'data', allow_duplicate=True),
     Output('existing-dashboard-name', 'data', allow_duplicate=True),
     Output('existing-infusion-modal', 'is_open'),
     Output('existing-dashboard-infusion-upload', 'contents'),
     Output('existing-dashboard-infusion-prompt', 'value')],
    [Input('existing-dashboard-infusion-upload', 'contents'),
     Input('existing-generate-design-from-prompt-btn', 'n_clicks')],
    [State('existing-dashboard-infusion-upload', 'filename'),
     State('existing-dashboard-infusion-prompt', 'value'),
     State('existing-dashboard-id', 'data'),
     State('existing-dashboard-config', 'data'),
     State('existing-dashboard-name', 'data')],
    prevent_initial_call=True
)
def apply_infusion_to_existing_dashboard(contents, prompt_btn_clicks, filename, prompt_text, dashboard_id, dashboard_config, dashboard_name):
    """Process uploaded image OR text prompt and apply design infusion to EXISTING dashboard (from Existing Dashboard page)"""
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
    if trigger_id == 'existing-dashboard-infusion-upload' and not contents:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    if trigger_id == 'existing-generate-design-from-prompt-btn' and (not prompt_text or not prompt_text.strip()):
        error_msg = dbc.Alert("⚠️ Please enter a design description", color="warning")
        return error_msg, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    try:
        # Extract/Generate design based on input type
        import copy
        
        print(f"🎨 [EXISTING PAGE] Processing design infusion for dashboard {dashboard_id}")
        
        # Handle different input types
        if trigger_id == 'existing-dashboard-infusion-upload':
            print(f"📷 Processing image upload")
            _, design_data = extract_design_from_image(contents, filename, llm_client)
        else:  # existing-generate-design-from-prompt-btn
            print(f"✍️ Generating design from prompt: {prompt_text[:50]}...")
            _, design_data = generate_design_from_prompt(prompt_text, llm_client)
        
        if not design_data or 'uiSettings' not in design_data:
            error_msg = dbc.Alert("⚠️ Failed to extract/generate design elements", color="warning")
            return error_msg, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        print(f"✅ New design extracted/generated successfully")
        
        # Extract the serialized_dashboard from the config (for retrieved dashboards)
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
        
        # Remove old uiSettings if exists, then add new one
        if 'uiSettings' in updated_config:
            print(f"🔄 Replacing existing design with new infused design")
            del updated_config['uiSettings']
        
        updated_config['uiSettings'] = design_data['uiSettings']
        print(f"✅ New uiSettings applied to config")
        
        # Update dashboard in place using Lakeview API
        print(f"🔄 Updating dashboard {dashboard_id} with infused design")
        updated_dashboard_id = dashboard_manager.update_dashboard(dashboard_id, updated_config)
        new_embed_url = dashboard_manager.get_embed_url(updated_dashboard_id)
        
        # Add cache-busting parameter to force iframe refresh
        cache_buster = f"?_refresh={int(time.time() * 1000)}"
        new_embed_url_with_refresh = new_embed_url + cache_buster
        
        # Create new preview
        preview_card = dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H4(f"✅ Dashboard Updated with Design Infusion: {dashboard_name}"),
                        html.Small(f"Dashboard ID: {updated_dashboard_id}", className="text-muted")
                    ], width=7),
                    dbc.Col([
                        dbc.Button("🎨 Infusion", id="existing-apply-infusion-btn", color="primary", size="sm", className="me-2"),
                        dbc.Button("🗑️ Delete Dashboard", id="existing-delete-dashboard-btn", color="danger", size="sm")
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
        
        # Store the updated config with serialized_dashboard wrapper for future infusions
        full_updated_config = {
            'serialized_dashboard': updated_config
        }
        
        # Close modal and clear both upload and prompt after success
        return success_msg, preview_card, updated_dashboard_id, full_updated_config, dashboard_name, False, None, ""
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = dbc.Alert([
            html.Strong("❌ Error applying infusion"),
            html.Br(),
            html.Small(f"Error: {str(e)}")
        ], color="danger")
        return error_msg, no_update, no_update, no_update, no_update, no_update, no_update, no_update


# ============================================================================
# REGISTER DASHBOARD PAGE CALLBACKS
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


# Expose the Flask server for WSGI deployment (Databricks Apps, Gunicorn, etc.)
server = app.server

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Starting Dash development server...")
    print("=" * 60)
    app.run_server(debug=True, host="0.0.0.0", port=8050)

