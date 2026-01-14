"""
New Dashboard Page Layout

This module contains all the UI components for creating a new dashboard.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def get_new_dashboard_layout(unity_catalog="christophe_chieu", unity_schema="certified_tables"):
    """
    Returns the layout for the New Dashboard page
    
    Args:
        unity_catalog: Unity Catalog name
        unity_schema: Unity Catalog schema name
    """
    UNITY_CATALOG = unity_catalog
    UNITY_SCHEMA = unity_schema
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("Create New Dashboard", className="text-center mb-3 mt-3"),
            ])
        ]),
        
        # Table Inspector Section (NEW)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Unity Catalog Tables")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label(f"Browse tables from {UNITY_CATALOG}.{UNITY_SCHEMA}:", className="fw-bold mb-2"),
                                dcc.Dropdown(
                                    id='uc-table-dropdown',
                                    placeholder="Select a table to inspect...",
                                    className="mb-3"
                                )
                            ], width=6)
                        ]),
                        html.Div(id='uc-table-columns-display')
                    ])
                ], className="mb-4")
            ], width=12)
        ]),
        
        # AI Dashboard Generator Section
        dbc.Row([
            dbc.Col([
                html.Div(id='ai-dashboard-generator-section')
            ], width=12)
        ]),
        
        # Widget Selector Section (appears after columns extracted)
        dbc.Row([
            dbc.Col([
                html.Div(id='widget-selector-section')
            ], width=12)
        ]),
        
        # Table Widget Configuration Section
        dbc.Row([
            dbc.Col([
                html.Div(id='table-widget-section')
            ], width=12)
        ]),
        
        # Table Widget JSON Display
        dbc.Row([
            dbc.Col([
                html.Div(id='widget-json')
            ], width=12)
        ]),
        
        # Filter Widgets Section
        dbc.Row([
            dbc.Col([
                html.Div(id='filter-widget-section')
            ], width=12)
        ]),
        
        # Filter Widgets Display
        dbc.Row([
            dbc.Col([
                html.Div(id='filter-widgets-display')
            ], width=12)
        ]),
        
        # Dataset Filters Display
        dbc.Row([
            dbc.Col([
                html.Div(id='dataset-filters-display')
            ], width=12)
        ]),
        
        # Bar Chart Widgets Section
        dbc.Row([
            dbc.Col([
                html.Div(id='bar-chart-widget-section')
            ], width=12)
        ]),
        
        # Bar Chart Widgets Display
        dbc.Row([
            dbc.Col([
                html.Div(id='bar-chart-widgets-display')
            ], width=12)
        ]),
        
        # Line Chart Widgets Section
        dbc.Row([
            dbc.Col([
                html.Div(id='line-chart-widget-section')
            ], width=12)
        ]),
        
        # Line Chart Widgets Display
        dbc.Row([
            dbc.Col([
                html.Div(id='line-chart-widgets-display')
            ], width=12)
        ]),
        
        # Pivot Widgets Section
        dbc.Row([
            dbc.Col([
                html.Div(id='pivot-widget-section')
            ], width=12)
        ]),
        
        # Pivot Widgets Display
        dbc.Row([
            dbc.Col([
                html.Div(id='pivot-widgets-display')
            ], width=12)
        ]),
        
        # Add to Dashboard button and final config
        dbc.Row([
            dbc.Col([
                html.Div(id='add-widget-section')
            ], width=12)
        ]),
        
        # Final Dashboard Configuration
        dbc.Row([
            dbc.Col([
                html.Div(id='dashboard-config-display')
            ], width=12)
        ]),
        
        # Deploy Dashboard Section
        dbc.Row([
            dbc.Col([
                html.Div(id='deploy-section-wrapper', children=[
                    # Always render the dashboard name input (hidden initially)
                    dbc.Input(id='deploy-dashboard-name', placeholder="Enter dashboard name...", value="My Dashboard", style={'display': 'none'}, className=""),
                    html.Div(id='deploy-section')
                ])
            ], width=12)
        ]),
        
        # Dashboard Preview
        dbc.Row([
            dbc.Col([
                html.Div(id='dashboard-preview')
            ], width=12)
        ])
    ])


def register_new_dashboard_callbacks(app, datasets, llm_client, dashboard_manager, ai_progress_store, ai_results_store, workspace_client, warehouse_id, unity_catalog="christophe_chieu", unity_schema="certified_tables"):
    """
    Register all callbacks for the New Dashboard page
    
    Args:
        app: Dash app instance
        datasets: Dictionary of available datasets
        llm_client: OpenAI client for LLM calls
        dashboard_manager: DashboardManager instance
        ai_progress_store: Shared dict for AI progress tracking
        ai_results_store: Shared dict for AI results
        workspace_client: Databricks workspace client
        warehouse_id: Warehouse ID for SQL execution
        unity_catalog: Unity Catalog name
        unity_schema: Unity Catalog schema name
    """
    import threading
    import uuid
    import time
    from utils.query_permission_checker import test_dashboard_queries_for_permissions
    from dash import callback, Output, Input, State, no_update, html
    import dash_bootstrap_components as dbc
    from widgets import extract_columns_with_llm
    from dashboard_management_functions import generate_dashboard_background
    from table_inspector import list_tables_from_schema, get_table_columns
    
    UNITY_CATALOG = unity_catalog
    UNITY_SCHEMA = unity_schema
    
    # ============================================================================
    # UNITY CATALOG TABLE INSPECTOR CALLBACKS
    # ============================================================================
    
    @callback(
        Output('uc-table-dropdown', 'options'),
        Input('uc-table-dropdown', 'id'),  # Triggered on page load
        prevent_initial_call=False
    )
    def populate_table_dropdown(_):
        """Populate the Unity Catalog table dropdown"""
        try:
            tables = list_tables_from_schema(
                workspace_client,
                catalog=UNITY_CATALOG,
                schema=UNITY_SCHEMA
            )
            return tables
        except Exception as e:
            print(f"Error populating table dropdown: {e}")
            return []
    
    
    @callback(
        Output('uc-table-columns-display', 'children'),
        Input('uc-table-dropdown', 'value'),
        prevent_initial_call=True
    )
    def display_table_columns(selected_table):
        """Display columns for the selected Unity Catalog table"""
        if not selected_table:
            return ""
        
        try:
            columns, sql_query = get_table_columns(workspace_client, selected_table)
            
            if not columns:
                return dbc.Alert("⚠️ Could not retrieve columns from this table", color="warning")
            
            # Create a table displaying column names and types
            column_rows = [
                html.Tr([
                    html.Td(col['name'], style={'fontWeight': 'bold', 'padding': '8px'}),
                    html.Td(
                        dbc.Badge(col['type'], color="info"),
                        style={'padding': '8px'}
                    )
                ])
                for col in columns
            ]
            
            return dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6(f"Columns in {selected_table.split('.')[-1]}")),
                        dbc.CardBody([
                            html.P(f"Total columns: {len(columns)}", className="fw-bold mb-3"),
                            html.Div([
                                dbc.Table([
                                    html.Thead([
                                        html.Tr([
                                            html.Th("Column Name", style={'width': '50%'}),
                                            html.Th("Data Type", style={'width': '50%'})
                                        ])
                                    ]),
                                    html.Tbody(column_rows)
                                ], bordered=True, hover=True, size='sm', style={'fontSize': '13px'})
                            ], style={'maxHeight': '400px', 'overflowY': 'auto'}),
                            html.Hr(),
                            html.Div([
                                dbc.Button(
                                    "Confirm & Proceed to AI Dashboard Generation",
                                    id="uc-table-confirm-btn",
                                    color="success",
                                    size="md",
                                    className="mt-3"
                                )
                            ], className="text-center")
                        ])
                    ], className="mt-3")
                ], width=8)
            ])
            
        except Exception as e:
            print(f"Error displaying columns: {e}")
            return dbc.Alert(f"❌ Error: {str(e)}", color="danger")
    
    
    @callback(
        [Output('extracted-columns', 'data', allow_duplicate=True),
         Output('extracted-columns-types', 'data', allow_duplicate=True),
         Output('uc-dataset-store', 'data'),
         Output('ai-dashboard-generator-section', 'children', allow_duplicate=True)],
        Input('uc-table-confirm-btn', 'n_clicks'),
        State('uc-table-dropdown', 'value'),
        prevent_initial_call=True,
        running=[
            (Output('ai-dashboard-generator-section', 'children'), 
             dbc.Alert([
                 html.Div([
                     dbc.Spinner(size="sm"),
                     html.Span("Checking permissions...", style={"marginLeft": "10px"})
                 ], style={"display": "flex", "alignItems": "center"})
             ], color="info"), 
             "")
        ]
    )
    def confirm_uc_table_selection(n_clicks, selected_table):
        """
        Confirm UC table selection and proceed to AI dashboard generation
        """
        if not n_clicks or not selected_table:
            return no_update, no_update, no_update, no_update
        
        try:
            from table_inspector import create_dataset_from_table
            
            # Get columns with types
            columns_info, sql_query = get_table_columns(workspace_client, selected_table)
            
            if not columns_info:
                error_alert = dbc.Alert("❌ Could not retrieve columns from table", color="danger")
                return no_update, no_update, no_update, error_alert
            
            # TEST QUERY PERMISSIONS: Test if user has access to the table
            print(f"🔒 Testing permissions for table: {selected_table}")
            test_query = f"SELECT * FROM {selected_table} LIMIT 1"
            
            permission_check_success, permission_error_alert = test_dashboard_queries_for_permissions(
                [{'name': selected_table, 'query': test_query}],
                workspace_client,
                warehouse_id
            )
            
            if not permission_check_success:
                # Permission check failed - return error
                print(f"❌ Permission check failed for table: {selected_table}")
                return no_update, no_update, no_update, permission_error_alert
            
            print(f"✅ Permission check passed for table: {selected_table}")
            
            # Extract column names and types
            column_names = [col['name'] for col in columns_info]
            columns_with_types = columns_info  # Store full column info with types
            
            # Create dataset from UC table
            dataset = create_dataset_from_table(workspace_client, selected_table)
            
            # Create AI dashboard generator section
            ai_section = dbc.Card([
                dbc.CardHeader(html.H4("AI-Powered Dashboard Generator")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Alert([
                                html.Strong("Table loaded successfully!"),
                                html.Br(),
                                html.Small(f"Table: {selected_table}"),
                                html.Br(),
                                html.Small(f"Columns detected: {len(column_names)}")
                            ], color="success", className="mb-3")
                        ], width=6)
                    ]),
                    
                    # Design Infusion Section
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.H6("Design Infusion (Optional)", className="mb-0"),
                                            html.Small("Extract colors and fonts from an image or describe your style", className="text-muted")
                                        ], width=8),
                                        dbc.Col([
                                            dbc.Button("Design Options", id="infusion-toggle-btn", color="info", size="sm", outline=True, className="float-end")
                                        ], width=4)
                                    ]),
                                    dbc.Collapse([
                                        # Options Side by Side
                                        dbc.Row([
                                            # Option 1: Upload Image
                                            dbc.Col([
                                                html.Label("Option 1: Upload an Image", className="fw-bold mb-2"),
                                                html.P("Upload a picture and the AI will extract colors and fonts from it.", className="text-muted small mb-2"),
                                                dcc.Upload(
                                                    id='infusion-image-upload',
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
                                                ),
                                                dcc.Loading(
                                                    id="infusion-loading",
                                                    type="default",
                                                    children=html.Div(id='infusion-result', className="mt-2")
                                                )
                                            ], width=6),
                                            
                                            # Option 2: Text Prompt
                                            dbc.Col([
                                                html.Label("Option 2: Describe Your Style", className="fw-bold mb-2"),
                                                html.P("Describe the style you want (e.g., 'Modern minimalist').", className="text-muted small mb-2"),
                                                dbc.Textarea(
                                                    id='pre-generation-infusion-prompt',
                                                    placeholder="Example: Modern and impactful style...",
                                                    style={'width': '100%', 'minHeight': '80px'},
                                                    className="mb-2"
                                                ),
                                                dbc.Button("Generate Design from Prompt", id="pre-generation-design-from-prompt-btn", color="primary", size="sm"),
                                                dcc.Loading(
                                                    id="pre-generation-infusion-loading",
                                                    type="default",
                                                    children=html.Div(id='pre-generation-infusion-result', className="mt-2")
                                                )
                                            ], width=6)
                                        ])
                                    ], id="infusion-collapse", is_open=False, className="mt-3")
                                ])
                            ], className="mb-3", style={'backgroundColor': '#f8f9fa'})
                        ], width=8)
                    ]),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Describe your dashboard needs:", className="fw-bold mb-2"),
                            html.P(
                                "The AI will use the column names and their types to automatically create "
                                "the most relevant dashboard for your needs.",
                                className="text-muted small mb-3"
                            ),
                            dcc.Textarea(
                                id='ai-dashboard-prompt',
                                placeholder='Example: "Create a dashboard showing key metrics and trends for this data"',
                                style={'width': '100%', 'height': '100px'},
                                className="mb-3"
                            )
                        ], width=8)
                    ]),
                    
                    # Display available columns with types
                    html.Details([
                        html.Summary("Available Columns & Types", style={'cursor': 'pointer', 'fontWeight': 'bold'}),
                        html.Div([
                            html.Div([
                                dbc.Badge(f"{col['name']}: {col['type']}", color="light", text_color="dark", className="me-2 mb-2")
                                for col in columns_info
                            ], className="mt-2")
                        ])
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Generate Dashboard",
                                id="generate-ai-dashboard-btn",
                                color="success",
                                size="md"
                            )
                        ], width=8, className="text-center"),
                        dbc.Col([
                            dbc.Button(
                                "Manual Configuration",
                                id="manual-config-btn",
                                color="secondary",
                                size="md"
                            )
                        ], width=4, className="text-center")
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Div(id='ai-generation-status', className="mt-3"),
                            html.Div(id='ai-generation-progress'),  # Progress steps with spinner
                            html.Div(id='ai-generation-reasoning'),  # Separate reasoning display
                            html.Div(id='ai-generation-widgets')  # Separate widget details display
                        ], width=8)
                    ])
                ])
            ], className="mb-4")
            
            return column_names, columns_with_types, dataset, ai_section
            
        except Exception as e:
            print(f"Error confirming UC table: {e}")
            import traceback
            traceback.print_exc()
            error_alert = dbc.Alert(f"❌ Error: {str(e)}", color="danger")
            return no_update, no_update, no_update, error_alert
    
    # ============================================================================
    # DATASET AND COLUMN EXTRACTION CALLBACKS
    # ============================================================================
    
    # NOTE: Dataset selection and column extraction callbacks removed
    # The Unity Catalog Table Inspector now handles column extraction directly
    
    
    @callback(
        [Output('ai-generation-session', 'data'),
         Output('ai-progress-interval', 'disabled'),
         Output('ai-generation-status', 'children', allow_duplicate=True),
         Output('ai-generation-progress', 'children', allow_duplicate=True),
         Output('ai-generation-reasoning', 'children', allow_duplicate=True),
         Output('ai-generation-widgets', 'children', allow_duplicate=True)],
        Input('generate-ai-dashboard-btn', 'n_clicks'),
        [State('ai-dashboard-prompt', 'value'),
         State('extracted-columns', 'data'),
         State('extracted-columns-types', 'data'),
         State('uc-dataset-store', 'data'),
         State('infusion-design-data', 'data')],
        prevent_initial_call=True
    )
    def start_ai_dashboard_generation(n_clicks, prompt, all_columns, columns_types, uc_dataset, infusion_data):
        """Start AI dashboard generation in background thread"""
        import uuid
        
        if not n_clicks or n_clicks == 0:
            return None, True, "", "", "", ""
        
        if not prompt or not prompt.strip():
            error = dbc.Alert("⚠️ Please enter a description of your dashboard needs", color="warning")
            return None, True, error, "", "", ""
        
        if not all_columns:
            error = dbc.Alert("⚠️ Missing columns", color="warning")
            return None, True, error, "", "", ""
        
        # Use Unity Catalog dataset (required)
        if not uc_dataset:
            error = dbc.Alert("⚠️ Please select a Unity Catalog table first", color="warning")
            return None, True, error, "", "", ""
        
        dataset = uc_dataset
        dataset_value = uc_dataset.get('name', 'uc_table')
        
        # Create unique session ID
        session_id = str(uuid.uuid4())
        
        # Initialize progress store immediately
        ai_progress_store[session_id] = {
            'status': 'initializing',
            'steps': ['🚀 Initializing AI dashboard generation...'],
            'reasoning': '',
            'widget_details': []
        }
        
        # Start background thread
        thread = threading.Thread(
            target=generate_dashboard_background,
            args=(
                session_id,
                prompt,
                all_columns,
                columns_types,
                dataset_value,
                dataset,
                llm_client,
                dashboard_manager,
                ai_progress_store,
                ai_results_store,
                infusion_data
            ),
            daemon=True
        )
        thread.start()
        
        # Show initial progress
        initial_progress = dbc.Card([
            dbc.CardBody([
                dbc.Spinner(size="sm", color="primary", spinner_class_name="me-2"),
                html.Span("🚀 Starting AI dashboard generation...", style={"fontSize": "14px"})
            ])
        ], className="mb-2")
        
        # Enable the interval to start polling
        return session_id, False, "", initial_progress, "", ""
    
    
    @callback(
        [Output('ai-generation-status', 'children'),
         Output('ai-generation-progress', 'children'),
         Output('ai-generation-reasoning', 'children'),
         Output('ai-generation-widgets', 'children'),
         Output('dashboard-preview', 'children', allow_duplicate=True),
         Output('deployed-dashboard-id', 'data', allow_duplicate=True),
         Output('ai-progress-interval', 'disabled', allow_duplicate=True),
         Output('ai-last-update', 'data'),
         Output('current-dashboard-config', 'data'),
         Output('current-dashboard-name', 'data')],
        Input('ai-progress-interval', 'n_intervals'),
        [State('ai-generation-session', 'data'),
         State('ai-last-update', 'data'),
         State('ai-generation-reasoning', 'children'),
         State('ai-generation-widgets', 'children')],
        prevent_initial_call=True
    )
    def poll_ai_generation_progress(n_intervals, session_id, last_update, current_reasoning, current_widgets):
        """Poll for AI generation progress and update UI"""
        try:
            # Check for timeout (max_intervals reached)
            if n_intervals and n_intervals >= 300:
                error = dbc.Alert("⚠️ Dashboard generation timed out after 2.5 minutes", color="warning")
                return error, "", no_update, no_update, "", None, True, None, None, None
            
            # Validate session
            if not session_id:
                return "", "", no_update, no_update, no_update, no_update, True, None, None, None
            
            # Check if session exists (might not be initialized yet)
            if session_id not in ai_progress_store:
                # Session not ready yet, keep polling
                return no_update, no_update, no_update, no_update, no_update, no_update, False, last_update, no_update, no_update
            
            progress_data = ai_progress_store.get(session_id, {})
            status_value = progress_data.get('status', 'running')
            
            # Create a hash of current progress to check if anything changed
            current_hash = hash(str(progress_data.get('steps', [])) + str(progress_data.get('reasoning', '')) + str(progress_data.get('widget_details', [])))
            
            # If nothing changed, don't update UI
            if last_update == current_hash and status_value == 'running':
                return no_update, no_update, no_update, no_update, no_update, no_update, False, last_update, no_update, no_update
            
            # Build progress display
            progress_steps = progress_data.get('steps', [])
            reasoning = progress_data.get('reasoning', '')
            widget_details = progress_data.get('widget_details', [])
            
            # Create progress display (only steps with spinner - no reasoning/widgets)
            progress_elements = []
            for idx, step in enumerate(progress_steps):
                progress_elements.append(
                    html.Div(
                        step, 
                        style={
                            "marginBottom": "8px", 
                            "fontSize": "14px",
                            "opacity": "1"
                        }
                    )
                )
            
            progress_container = dbc.Card([
                dbc.CardHeader([
                    dbc.Spinner(size="sm", color="primary", spinner_class_name="me-2"),
                    html.Strong("Generating Dashboard...", style={"fontSize": "15px"})
                ]),
                dbc.CardBody(progress_elements, style={"maxHeight": "300px", "overflowY": "auto"})
            ], className="mb-2")
            
            # Handle reasoning display (only update if new reasoning available)
            reasoning_output = no_update
            if reasoning and (not current_reasoning or not isinstance(current_reasoning, dict)):
                # First time or reasoning changed - create the card
                reasoning_output = dbc.Card([
                    dbc.CardHeader(html.Strong("AI Reasoning", style={"fontSize": "15px"})),
                    dbc.CardBody([
                        html.P(reasoning, style={"fontSize": "13px", "color": "#555", "margin": "0", "lineHeight": "1.6"})
                    ])
                ], className="mb-2", style={"marginTop": "10px"})
            
            # Handle widget details display (append-style)
            widgets_output = no_update
            if widget_details:
                # Check if we have new widget details to append
                current_count = 0
                if current_widgets and isinstance(current_widgets, dict) and current_widgets.get('children'):
                    try:
                        # Get count of existing items
                        card_body = current_widgets['children'][1] if len(current_widgets['children']) > 1 else {}
                        ul = card_body.get('props', {}).get('children', [{}])[0]
                        if isinstance(ul, dict) and ul.get('props', {}).get('children'):
                            current_count = len(ul['props']['children'])
                    except:
                        current_count = 0
                
                # Only update if we have new items
                if len(widget_details) > current_count:
                    widgets_output = dbc.Card([
                        dbc.CardHeader(html.Strong("Widget Selection Rationale", style={"fontSize": "15px"})),
                        dbc.CardBody([
                            html.Ul([
                                html.Li(detail, style={"fontSize": "13px", "lineHeight": "1.6"}) 
                                for detail in widget_details
                            ], style={"marginBottom": "0"})
                        ])
                    ], className="mb-2", style={"marginTop": "10px"})
            
            # Check if completed or errored
            if status_value == 'completed':
                # Get results and disable polling
                results = ai_results_store.get(session_id, {})
                # Clean up stores
                if session_id in ai_progress_store:
                    del ai_progress_store[session_id]
                if session_id in ai_results_store:
                    del ai_results_store[session_id]
                return results.get('status', ""), "", no_update, no_update, results.get('preview', ""), results.get('dashboard_id'), True, None, results.get('dashboard_config'), results.get('dashboard_name')
            
            elif status_value == 'error':
                # Get error message and disable polling
                results = ai_results_store.get(session_id, {})
                # Clean up stores
                if session_id in ai_progress_store:
                    del ai_progress_store[session_id]
                if session_id in ai_results_store:
                    del ai_results_store[session_id]
                return results.get('status', ""), "", no_update, no_update, "", None, True, None, None, None
            
            # Still running - show progress and keep polling
            return "", progress_container, reasoning_output, widgets_output, no_update, no_update, False, current_hash, no_update, no_update
        
        except Exception as e:
            # Log error but don't crash - keep polling
            print(f"Error in poll callback: {e}")
            import traceback
            traceback.print_exc()
            return no_update, no_update, no_update, no_update, no_update, no_update, False, last_update, no_update, no_update
    
    
    @callback(
        [Output('dashboard-preview', 'children'),
         Output('deployed-dashboard-id', 'data')],
        Input('deploy-btn', 'n_clicks'),
        [State('dashboard-config', 'data'),
         State('deploy-dashboard-name', 'value')],
        prevent_initial_call=True
    )
    def deploy_dashboard(n_clicks, config, dashboard_name):
        if not n_clicks or n_clicks == 0:
            return "", None
        if not config or not dashboard_name:
            return dbc.Alert("Missing configuration or name", color="warning"), None
        
        try:
            # Create dashboard in Databricks
            dashboard_id = dashboard_manager.create_dashboard(config, dashboard_name)
            
            # Get embed URL
            embed_url = dashboard_manager.get_embed_url(dashboard_id)
            
            # Display dashboard in iframe with delete button
            preview_card = dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H4(f"Dashboard Deployed: {dashboard_name}"),
                            html.Small(f"Dashboard ID: {dashboard_id}", className="text-muted")
                        ], width=8),
                        dbc.Col([
                            dbc.Button("Delete Dashboard", id="delete-dashboard-btn", color="danger", size="sm", className="float-end")
                        ], width=4)
                    ], align="center")
                ]),
                dbc.CardBody([
                    html.Iframe(
                        src=embed_url,
                        style={
                            'width': '100%',
                            'height': '800px',
                            'border': '1px solid #ddd',
                            'borderRadius': '5px'
                        }
                    )
                ])
            ])
            
            return preview_card, dashboard_id
            
        except Exception as e:
            return dbc.Alert(f"❌ Error deploying dashboard: {str(e)}", color="danger"), None
    
    
    @callback(
        [Output('dashboard-preview', 'children', allow_duplicate=True),
         Output('deployed-dashboard-id', 'data', allow_duplicate=True),
         Output('ai-generation-status', 'children', allow_duplicate=True),
         Output('ai-generation-reasoning', 'children', allow_duplicate=True),
         Output('ai-generation-widgets', 'children', allow_duplicate=True),
         Output('ai-generation-progress', 'children', allow_duplicate=True)],
        Input('delete-dashboard-btn', 'n_clicks'),
        [State('deployed-dashboard-id', 'data'),
         State('deploy-dashboard-name', 'value')],
        prevent_initial_call=True
    )
    def delete_dashboard_callback(n_clicks, dashboard_id, dashboard_name):
        """Callback to delete dashboard from Databricks (New Dashboard page)"""
        # Only proceed if button was actually clicked
        if not n_clicks or n_clicks < 1:
            from dash.exceptions import PreventUpdate
            raise PreventUpdate
        
        if not dashboard_id:
            return dbc.Alert("No dashboard to delete", color="warning"), None, "", "", "", ""
        
        # Delete dashboard from Databricks only (no Unity Catalog)
        success, message = dashboard_manager.delete_dashboard(
            dashboard_id=dashboard_id,
            dashboard_name=None  # Don't attempt Unity Catalog deletion
        )
        
        # Return appropriate message and clear the stored ID, success message, reasoning, and widgets
        if success:
            return dbc.Alert(f"✅ {message}", color="success", dismissable=True), None, "", "", "", ""
        else:
            return dbc.Alert(f"❌ {message}", color="danger", dismissable=True), None, "", "", "", ""
    