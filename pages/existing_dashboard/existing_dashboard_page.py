"""
Existing Dashboard Page Layout and Callbacks

This module contains all the UI components and callbacks for viewing and managing existing dashboards.
"""

from dash import html, dcc, callback, Output, Input, State, no_update, MATCH
import dash_bootstrap_components as dbc
from utils.query_permission_checker import test_dashboard_queries_for_permissions


def get_existing_dashboard_layout():
    """
    Returns the layout for the Existing Dashboard page
    """
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("View Existing Dashboard", className="text-center mb-3 mt-3"),
            ])
        ]),
        
        # Dashboard ID Input
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("🔍 Retrieve Dashboard by ID")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Enter Dashboard ID:", className="fw-bold mb-2"),
                                html.P("You can find the dashboard ID in the URL or from the deployment confirmation.", className="text-muted small mb-3"),
                                dbc.Input(
                                    id='existing-dashboard-id-input',
                                    placeholder="e.g., 01ef5f2a-e7cf-1c1f-9fc3-e06afd4e73f3",
                                    type="text",
                                    className="mb-3"
                                ),
                                dbc.Button("🔍 Retrieve Dashboard", id="retrieve-dashboard-btn", color="primary", className="mb-2"),
                                html.Div(id='retrieve-dashboard-status', className="mt-3")
                            ], width=6)
                        ])
                    ])
                ], className="mb-4")
            ], width=12)
        ]),
        
        # Existing Dashboard Preview
        dbc.Row([
            dbc.Col([
                html.Div(id='existing-dashboard-preview')
            ], width=12)
        ])
    ])


def register_existing_dashboard_callbacks(app, dashboard_manager, workspace_client, warehouse_id):
    """
    Register all callbacks for the Existing Dashboard page
    
    Args:
        app: Dash app instance
        dashboard_manager: DashboardManager instance
        workspace_client: Databricks workspace client
        warehouse_id: Warehouse ID for SQL execution
    """
    
    # ============================================================================
    # DELETE EXISTING DASHBOARD CALLBACK
    # ============================================================================
    
    @app.callback(
        [Output('existing-dashboard-preview', 'children', allow_duplicate=True),
         Output('existing-dashboard-id', 'data', allow_duplicate=True),
         Output('retrieve-dashboard-status', 'children', allow_duplicate=True)],
        Input('existing-delete-dashboard-btn', 'n_clicks'),
        State('existing-dashboard-id', 'data'),
        prevent_initial_call=True
    )
    def delete_existing_dashboard_callback(n_clicks, dashboard_id):
        """Callback to delete dashboard from Databricks (Existing Dashboard page)"""
        # Only proceed if button was actually clicked
        if not n_clicks or n_clicks < 1:
            from dash.exceptions import PreventUpdate
            raise PreventUpdate
        
        if not dashboard_id:
            return no_update, None, dbc.Alert("No dashboard to delete", color="warning")
        
        # Delete dashboard from Databricks only (no Unity Catalog)
        success, message = dashboard_manager.delete_dashboard(
            dashboard_id=dashboard_id,
            dashboard_name=None  # Don't attempt Unity Catalog deletion
        )
        
        # Return appropriate message and clear the stored ID and preview
        if success:
            return "", None, dbc.Alert(f"✅ {message}", color="success", dismissable=True)
        else:
            return no_update, dashboard_id, dbc.Alert(f"❌ {message}", color="danger", dismissable=True)
    
    
    # ============================================================================
    # RETRIEVE EXISTING DASHBOARD CALLBACK
    # ============================================================================
    
    @app.callback(
        [Output('retrieve-dashboard-status', 'children'),
         Output('existing-dashboard-preview', 'children'),
         Output('existing-dashboard-id', 'data'),
         Output('existing-dashboard-config', 'data'),
         Output('existing-dashboard-name', 'data')],
        Input('retrieve-dashboard-btn', 'n_clicks'),
        State('existing-dashboard-id-input', 'value'),
        prevent_initial_call=True,
        running=[
            (Output('retrieve-dashboard-status', 'children'), 
             dbc.Alert([
                 html.Div([
                     dbc.Spinner(size="sm"),
                     html.Span("🔒 Checking permissions...", style={"marginLeft": "10px"})
                 ], style={"display": "flex", "alignItems": "center"})
             ], color="info"), 
             "")
        ]
    )
    def retrieve_existing_dashboard(n_clicks, dashboard_id):
        """Retrieve and display an existing dashboard by ID"""
        if not n_clicks or not dashboard_id or not dashboard_id.strip():
            warning_msg = dbc.Row([
                dbc.Col([
                    dbc.Alert("⚠️ Please enter a valid dashboard ID", color="warning")
                ], width=6)
            ])
            return warning_msg, "", None, None, None
        
        try:
            dashboard_id = dashboard_id.strip()
            print(f"🔍 Retrieving dashboard: {dashboard_id}")
            
            # Get dashboard configuration
            dashboard_config = dashboard_manager.get_dashboard_config(dashboard_id)
            
            # Extract SQL queries from the dashboard datasets
            import json
            dashboard_queries = []
            try:
                serialized = dashboard_config.get('serialized_dashboard')
                if isinstance(serialized, str):
                    serialized = json.loads(serialized)
                
                datasets = serialized.get('datasets', []) if isinstance(serialized, dict) else []
                print(f"📊 Found {len(datasets)} datasets")
                
                for idx, dataset in enumerate(datasets, 1):
                    if isinstance(dataset, dict):
                        query_lines = dataset.get('queryLines', [])
                        if query_lines:
                            sql_query = ''.join(query_lines).strip()
                            dataset_name = dataset.get('displayName', f'Dataset {idx}')
                            dashboard_queries.append({
                                'name': dataset_name,
                                'query': sql_query
                            })
                            print(f"   Extracted query from: {dataset_name}")
                
                # Store queries in the dashboard config
                dashboard_config['extracted_queries'] = dashboard_queries
                print(f"✅ Extracted {len(dashboard_queries)} queries")
                
            except Exception as e:
                print(f"⚠️ Could not extract queries: {e}")
                dashboard_config['extracted_queries'] = []
            
            # AUTO-TEST QUERIES: Test all queries for permissions before displaying dashboard
            success, error_alert = test_dashboard_queries_for_permissions(
                dashboard_queries, 
                workspace_client, 
                warehouse_id
            )
            
            if not success:
                # Permission check failed - return error alert
                return error_alert, "", None, None, None
            
            # Get the actual dashboard name from config
            dashboard_name = dashboard_config.get('display_name', f'Dashboard {dashboard_id[:8]}')
            print(f"📊 Dashboard name: {dashboard_name}")
            
            # Get embed URL for the dashboard
            embed_url = dashboard_manager.get_embed_url(dashboard_id)
            
            # Create SQL query display section (COMMENTED OUT - queries are auto-tested instead)
            queries_section = []
            # if dashboard_queries:
            #     queries_section = [
            #         html.Hr(),
            #         html.H5("📝 Dashboard SQL Queries", className="mt-3"),
            #         html.P("These are the queries used by this dashboard. Click 'Test Query' to verify you have permissions:", className="text-muted small")
            #     ]
            #     
            #     for idx, query_info in enumerate(dashboard_queries, 1):
            #         queries_section.append(
            #             dbc.Card([
            #                 dbc.CardHeader([
            #                     dbc.Row([
            #                         dbc.Col(html.Strong(f"Query {idx}: {query_info['name']}"), width=9),
            #                         dbc.Col(
            #                             dbc.Button("▶️ Test Query", 
            #                                        id={'type': 'test-query-btn', 'index': idx-1}, 
            #                                        color="info", 
            #                                        size="sm"),
            #                             width=3, 
            #                             className="text-end"
            #                         )
            #                     ])
            #                 ]),
            #                 dbc.CardBody([
            #                     html.Pre(
            #                         query_info['query'], 
            #                         style={
            #                             'backgroundColor': '#f5f5f5', 
            #                             'padding': '10px', 
            #                             'borderRadius': '5px', 
            #                             'fontSize': '12px',
            #                             'whiteSpace': 'pre-wrap',
            #                             'wordBreak': 'break-word'
            #                         }
            #                     ),
            #                     html.Div(id={'type': 'query-test-result', 'index': idx-1})
            #                 ])
            #             ], className="mb-2")
            #         )
            
            # Create preview card with infusion option and queries
            preview_card = dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H4(f"✅ {dashboard_name}"),
                            html.Small(f"Dashboard ID: {dashboard_id}", className="text-muted")
                        ], width=7),
                        dbc.Col([
                            dbc.Button("🎨 Infusion", id="existing-apply-infusion-btn", color="primary", size="sm", className="me-2"),
                            dbc.Button("🗑️ Delete Dashboard", id="existing-delete-dashboard-btn", color="danger", size="sm")
                        ], width=5, className="text-end")
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
                    ),
                    *queries_section
                ])
            ])
            
            success_msg = dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.Strong("✅ Dashboard retrieved successfully!"),
                        html.Br(),
                        html.Small(f"Viewing: {dashboard_name}")
                    ], color="success")
                ], width=6)
            ])
            
            # Store dashboard ID, config, and actual name in SEPARATE stores for existing dashboard page
            return success_msg, preview_card, dashboard_id, dashboard_config, dashboard_name
            
        except Exception as e:
            error_msg = dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.Strong("❌ Error retrieving dashboard"),
                        html.Br(),
                        html.Small(f"Error: {str(e)}"),
                        html.Br(),
                        html.Small("Please verify the dashboard ID is correct and the dashboard exists.")
                    ], color="danger")
                ], width=6)
            ])
            return error_msg, "", None, None, None
    
    
    # ============================================================================
    # TEST QUERY CALLBACK
    # ============================================================================
    
    # Callback to test individual queries (COMMENTED OUT - queries are auto-tested instead)
    # @app.callback(
    #     Output({'type': 'query-test-result', 'index': MATCH}, 'children'),
    #     Input({'type': 'test-query-btn', 'index': MATCH}, 'n_clicks'),
    #     State('existing-dashboard-config', 'data'),
    #     State({'type': 'test-query-btn', 'index': MATCH}, 'id'),
    #     prevent_initial_call=True
    # )
    # def test_query(n_clicks, dashboard_config, button_id):
    #     """Test if user has permissions to run a specific query"""
    #     if not n_clicks or not dashboard_config:
    #         from dash.exceptions import PreventUpdate
    #         raise PreventUpdate
    #     
    #     try:
    #         from databricks.sdk.service.sql import StatementState
    #         
    #         query_index = button_id['index']
    #         queries = dashboard_config.get('extracted_queries', [])
    #         
    #         if query_index >= len(queries):
    #             return dbc.Alert("❌ Query not found", color="danger", className="mt-2")
    #         
    #         query_info = queries[query_index]
    #         sql_query = query_info['query']
    #         
    #         # Add LIMIT 5 to make it fast
    #         if 'LIMIT' not in sql_query.upper():
    #             test_query = f"{sql_query.rstrip(';')} LIMIT 5"
    #         else:
    #             test_query = sql_query
    #         
    #         print(f"🔍 Testing query: {test_query[:100]}...")
    #         
    #         # Execute the query
    #         response = workspace_client.statement_execution.execute_statement(
    #             warehouse_id=warehouse_id,
    #             statement=test_query,
    #             wait_timeout='30s'
    #         )
    #         
    #         if response.status and response.status.state == StatementState.FAILED:
    #             error_msg = str(response.status.error) if response.status.error else "Unknown error"
    #             print(f"❌ Query failed: {error_msg}")
    #             
    #             return dbc.Alert([
    #                 html.Strong("❌ Permission Error"),
    #                 html.Br(),
    #                 html.Small(error_msg)
    #             ], color="danger", className="mt-2")
    #         
    #         elif response.status and response.status.state == StatementState.SUCCEEDED:
    #             row_count = len(response.result.data_array) if response.result and response.result.data_array else 0
    #             print(f"✅ Query succeeded, returned {row_count} rows")
    #             
    #             return dbc.Alert([
    #                 html.Strong("✅ Query Successful!"),
    #                 html.Br(),
    #                 html.Small(f"You have the required permissions. Query returned {row_count} rows.")
    #             ], color="success", className="mt-2")
    #         
    #         else:
    #             return dbc.Alert("⚠️ Query status unknown", color="warning", className="mt-2")
    #             
    #     except Exception as e:
    #         error_msg = str(e)
    #         print(f"❌ Error testing query: {error_msg}")
    #         
    #         if 'INSUFFICIENT_PERMISSIONS' in error_msg or 'does not have' in error_msg.lower():
    #             return dbc.Alert([
    #                 html.Strong("❌ Insufficient Permissions"),
    #                 html.Br(),
    #                 html.Small(error_msg)
    #             ], color="danger", className="mt-2")
    #         else:
    #             return dbc.Alert([
    #                 html.Strong("❌ Error"),
    #                 html.Br(),
    #                 html.Small(error_msg)
    #             ], color="danger", className="mt-2")