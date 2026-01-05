"""
Manual Dashboard Configuration Module

This module contains all callbacks for manual dashboard configuration,
including widget selection, filter creation, chart creation, and dashboard assembly.
"""

import json
from dash import callback, Output, Input, State, no_update, html, dcc
import dash_bootstrap_components as dbc


def register_manual_config_callbacks(app, datasets, dashboard_manager):
    """
    Register all callbacks for manual dashboard configuration
    
    Args:
        app: Dash app instance
        datasets: Dictionary of available datasets
        dashboard_manager: DashboardManager instance
    """
    from widgets import (
        create_table_widget,
        create_filter_widget,
        create_bar_chart_widget,
        create_line_chart_widget,
        create_pivot_widget
    )
    from dataset_filter import apply_simple_filter_to_dataset, get_dataset_filters_summary
    
    # ============================================================================
    # WIDGET SELECTION & TABLE CONFIGURATION
    # ============================================================================
    
    @app.callback(
        Output('widget-selector-section', 'children'),
        Input('extracted-columns', 'data'),
        Input('manual-config-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def show_widget_selector(extracted_columns, manual_clicks):
        """Show widget selector for manual configuration"""
        if not extracted_columns:
            return ""
        
        # Only show if manual config button was clicked
        if not manual_clicks:
            return ""
        
        return dbc.Card([
            dbc.CardHeader(html.H5("🎯 Step 3: Select Widgets to Configure")),
            dbc.CardBody([
                html.Label("Choose which widgets you want to add to your dashboard:", className="fw-bold mb-3"),
                dcc.Dropdown(
                    id='widget-selector-dropdown',
                    options=[
                        {"label": "📋 Table Widget (Display data in table format)", "value": "table"},
                        {"label": "🔍 Filter Widget (Interactive filters)", "value": "filter"},
                        {"label": "📊 Bar Chart Widget (Visualizations)", "value": "bar_chart"},
                        {"label": "📈 Line Chart Widget (Time series & trends)", "value": "line_chart"},
                        {"label": "🔢 Pivot Table Widget (Aggregate & summarize data)", "value": "pivot"}
                    ],
                    multi=True,
                    placeholder="Select widgets to add to your dashboard...",
                    className="mb-3"
                ),
                html.Div(id='widget-selection-status', className="mt-2")
            ])
        ], className="mb-4")
    
    
    @app.callback(
        Output('selected-widgets', 'data'),
        Output('widget-selection-status', 'children'),
        Input('widget-selector-dropdown', 'value'),
        prevent_initial_call=False
    )
    def update_selected_widgets(selected_widgets):
        """Update the selected widgets store and display status"""
        if not selected_widgets:
            return [], ""
        
        # Create status message
        widget_names = []
        if "table" in selected_widgets:
            widget_names.append("Table Widget")
        if "filter" in selected_widgets:
            widget_names.append("Filter Widget")
        if "bar_chart" in selected_widgets:
            widget_names.append("Bar Chart Widget")
        if "line_chart" in selected_widgets:
            widget_names.append("Line Chart Widget")
        if "pivot" in selected_widgets:
            widget_names.append("Pivot Table Widget")
        
        status = dbc.Alert(
            f"✅ Selected: {', '.join(widget_names)}. Configure them below!",
            color="success"
        )
        
        return selected_widgets, status
    
    
    @app.callback(
        Output('table-widget-section', 'children'),
        Input('selected-widgets', 'data'),
        State('extracted-columns', 'data'),
        prevent_initial_call=False
    )
    def show_table_widget_section(selected_widgets, all_columns):
        """Show table widget configuration section if table is selected"""
        if not selected_widgets or "table" not in selected_widgets or not all_columns:
            return ""
        
        return dbc.Card([
            dbc.CardHeader(html.H5("📋 Step 3.8: Configure Table Widget")),
            dbc.CardBody([
                html.Label("Select columns to display in the table:", className="fw-bold mb-2"),
                dcc.Dropdown(
                    id='column-dropdown',
                    options=[{'label': col, 'value': col} for col in all_columns],
                    value=[],
                    multi=True,
                    placeholder="Select columns...",
                    className="mb-3"
                ),
                dbc.Button("Create Table Widget", id="create-widget-btn", color="primary")
            ])
        ], className="mb-4")
    
    
    @app.callback(
        [Output('widget-json', 'children'),
         Output('current-widget', 'data')],
        Input('create-widget-btn', 'n_clicks'),
        [State('column-dropdown', 'value'),
         State('dataset-dropdown', 'value'),
         State('extracted-columns', 'data')],
        prevent_initial_call=True
    )
    def create_widget_from_selection(n_clicks, selected_columns, dataset_value, all_columns):
        if not n_clicks or n_clicks == 0:
            return "", None
        if not selected_columns or not dataset_value:
            return dbc.Alert("Please select at least one column", color="warning"), None
        
        dataset = datasets.get(dataset_value)
        if not dataset:
            return dbc.Alert("Dataset not found", color="warning"), None
        
        # Create table widget with selected columns and all available columns
        table_widget = create_table_widget(
            title="Support Data Table",
            visible_columns=selected_columns,
            dataset_name=dataset['name'],
            all_columns=all_columns
        )
        
        widget_card = dbc.Card([
            dbc.CardHeader(html.H5("📋 Table Widget JSON Created")),
            dbc.CardBody([
                dbc.Alert(f"✅ Table widget created with {len(selected_columns)} columns", color="success", className="mb-3"),
                html.Pre(
                    json.dumps(table_widget, indent=2),
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
        
        return widget_card, table_widget
    
    
    # ============================================================================
    # FILTER CONFIGURATION
    # ============================================================================
    
    @app.callback(
        Output('filter-widget-section', 'children'),
        Input('current-widget', 'data'),
        Input('selected-widgets', 'data'),
        State('extracted-columns', 'data'),
        prevent_initial_call=False
    )
    def show_filter_section(widget, selected_widgets, all_columns):
        if not widget or not all_columns:
            return ""
        
        # Only show if filter widget is selected
        if not selected_widgets or "filter" not in selected_widgets:
            return ""
        
        return dbc.Card([
            dbc.CardHeader(html.H5("🔍 Step 3.6: Configure Filter Widget")),
            dbc.CardBody([
                dbc.Row([
                    # Filter Widget Option
                    dbc.Col([
                        html.H6("Option 1: Filter Widget", className="mb-3"),
                        html.P("Add interactive filter widgets to your dashboard:", className="text-muted small"),
                        dcc.Dropdown(
                            id='filter-columns-dropdown',
                            options=[{'label': col, 'value': col} for col in all_columns],
                            multi=True,
                            placeholder="Select columns for filter widgets...",
                            className="mb-3"
                        ),
                        dbc.Button("➕ Add Filter Widgets", id="add-filters-btn", color="info", size="sm")
                    ], width=6),
                    
                    # Dataset Filter Option
                    dbc.Col([
                        html.H6("Option 2: Dataset Filter", className="mb-3"),
                        html.P("Add WHERE clause filters directly to the dataset query:", className="text-muted small"),
                        dcc.Dropdown(
                            id='dataset-filter-column-dropdown',
                            options=[{'label': col, 'value': col} for col in all_columns],
                            placeholder="Select column to filter...",
                            className="mb-2"
                        ),
                        dbc.Input(
                            id='dataset-filter-values-input',
                            placeholder="Enter values separated by comma (e.g., Low, Medium, High)",
                            className="mb-3"
                        ),
                        html.Small("Tip: For single value use 'Low', for multiple use 'Low, Medium, High'", className="text-muted d-block mb-2"),
                        dbc.ButtonGroup([
                            dbc.Button("➕ Add Dataset Filter", id="add-dataset-filter-btn", color="success", size="sm"),
                            dbc.Button("🔄 Refresh Dashboard", id="refresh-dashboard-with-filter-btn", color="primary", size="sm", className="ms-2", style={'display': 'none'})
                        ]),
                        html.Div(id='refresh-dashboard-status')
                    ], width=6)
                ])
            ])
        ], className="mb-4")
    
    
    @app.callback(
        [Output('filter-widgets-display', 'children'),
         Output('filter-widgets', 'data')],
        Input('add-filters-btn', 'n_clicks'),
        [State('filter-columns-dropdown', 'value'),
         State('dataset-dropdown', 'value')],
        prevent_initial_call=True
    )
    def create_filter_widgets(n_clicks, filter_columns, dataset_value):
        if not n_clicks or n_clicks == 0:
            return "", []
        if not filter_columns or not dataset_value:
            return dbc.Alert("Please select at least one column for filtering", color="warning"), []
        
        dataset = datasets.get(dataset_value)
        if not dataset:
            return dbc.Alert("Dataset not found", color="warning"), []
        
        # Create filter widgets
        filter_widgets_list = []
        for col in filter_columns:
            filter_widget = create_filter_widget(
                filter_column=col,
                dataset_name=dataset['name']
            )
            filter_widgets_list.append(filter_widget)
        
        filter_card = dbc.Card([
            dbc.CardHeader(html.H5(f"🔍 Filter Widgets Created ({len(filter_widgets_list)})")),
            dbc.CardBody([
                dbc.Alert(f"✅ Created {len(filter_widgets_list)} filter widget(s)", color="success", className="mb-3"),
                html.Pre(
                    json.dumps(filter_widgets_list, indent=2),
                    style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '15px',
                        'borderRadius': '5px',
                        'overflow': 'auto',
                        'maxHeight': '400px',
                        'fontSize': '11px'
                    }
                )
            ])
        ], className="mb-4")
        
        return filter_card, filter_widgets_list
    
    
    @app.callback(
        [Output('dataset-filters-display', 'children'),
         Output('filtered-dataset', 'data'),
         Output('dataset-json', 'children', allow_duplicate=True)],
        Input('add-dataset-filter-btn', 'n_clicks'),
        [State('dataset-filter-column-dropdown', 'value'),
         State('dataset-filter-values-input', 'value'),
         State('dataset-dropdown', 'value'),
         State('filtered-dataset', 'data')],
        prevent_initial_call=True
    )
    def add_dataset_filter(n_clicks, filter_column, filter_values_text, dataset_value, filtered_dataset):
        """Add a WHERE clause filter directly to the dataset"""
        if not n_clicks or n_clicks == 0:
            from dash.exceptions import PreventUpdate
            raise PreventUpdate
        
        if not filter_column or not filter_values_text:
            return dbc.Alert("Please select a column and enter at least one value", color="warning"), None, no_update
        
        # Parse comma-separated values
        filter_values = [v.strip() for v in filter_values_text.split(',') if v.strip()]
        
        if not filter_values:
            return dbc.Alert("Please enter at least one value", color="warning"), None, no_update
        
        if not dataset_value:
            return dbc.Alert("Please select a dataset first", color="warning"), None, no_update
        
        # Get the current dataset (either filtered or original)
        if filtered_dataset:
            dataset = filtered_dataset
        else:
            dataset = datasets.get(dataset_value)
            if not dataset:
                return dbc.Alert("Dataset not found", color="warning"), None, no_update
            import copy
            dataset = copy.deepcopy(dataset)
        
        # Add the filter to the dataset
        updated_dataset = apply_simple_filter_to_dataset(dataset, filter_column, filter_values)
        
        # Get filters summary
        filters_summary = get_dataset_filters_summary(updated_dataset)
        
        # Build filter description
        if len(filter_values) == 1:
            filter_desc = f"{filter_column} = '{filter_values[0]}'"
        else:
            values_list = ', '.join([f"'{v}'" for v in filter_values])
            filter_desc = f"{filter_column} IN ({values_list})"
        
        # Display card with updated dataset
        filter_card = dbc.Card([
            dbc.CardHeader(html.H5(f"🔍 Dataset Filters Applied ({len(filters_summary)})")),
            dbc.CardBody([
                dbc.Alert(f"✅ Added filter: {filter_desc}", color="success", className="mb-3"),
                html.P("Active filters:", className="fw-bold"),
                html.Ul([html.Li(f) for f in filters_summary]) if filters_summary else html.P("No filters detected", className="text-muted"),
                html.Hr(),
                html.P("Updated dataset query:", className="fw-bold mt-3"),
                html.Pre(
                    ''.join(updated_dataset.get('queryLines', [])),
                    style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '15px',
                        'borderRadius': '5px',
                        'overflow': 'auto',
                        'maxHeight': '300px',
                        'fontSize': '11px'
                    }
                )
            ])
        ], className="mb-4")
        
        # Also update the dataset JSON display
        dataset_card = dbc.Card([
            dbc.CardHeader(html.H5("📊 Dataset Configuration (with filters)")),
            dbc.CardBody([
                html.Pre(
                    json.dumps(updated_dataset, indent=2),
                    style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '15px',
                        'borderRadius': '5px',
                        'overflow': 'auto',
                        'maxHeight': '400px',
                        'fontSize': '12px'
                    }
                )
            ])
        ], className="mb-4")
        
        return filter_card, updated_dataset, dataset_card
    
    
    @app.callback(
        Output('refresh-dashboard-with-filter-btn', 'style'),
        [Input('filtered-dataset', 'data'),
         Input('deployed-dashboard-id', 'data')],
        prevent_initial_call=False
    )
    def show_refresh_dashboard_button(filtered_dataset, dashboard_id):
        """Show refresh button when a dataset filter has been added OR dashboard exists"""
        if filtered_dataset or dashboard_id:
            return {'display': 'inline-block'}
        return {'display': 'none'}
    
    
    @app.callback(
        [Output('dashboard-preview', 'children', allow_duplicate=True),
         Output('dashboard-config', 'data', allow_duplicate=True),
         Output('deployed-dashboard-id', 'data', allow_duplicate=True),
         Output('refresh-dashboard-status', 'children')],
        Input('refresh-dashboard-with-filter-btn', 'n_clicks'),
        [State('dataset-filter-column-dropdown', 'value'),
         State('dataset-filter-values-input', 'value'),
         State('original-dataset', 'data'),
         State('current-widget', 'data'),
         State('filter-widgets', 'data'),
         State('bar-chart-widgets', 'data'),
         State('line-chart-widgets', 'data'),
         State('pivot-widgets', 'data'),
         State('deployed-dashboard-id', 'data'),
         State('deploy-dashboard-name', 'value')],
        prevent_initial_call=True
    )
    def refresh_dashboard_with_filter(n_clicks, filter_column, filter_values_text, original_dataset, widget, filter_widgets, bar_chart_widgets, line_chart_widgets, pivot_widgets, dashboard_id, dashboard_name):
        """Refresh: Go back to original dataset, add new filter, update dashboard (or recreate if needed)"""
        if not n_clicks or n_clicks == 0:
            from dash.exceptions import PreventUpdate
            raise PreventUpdate
        
        # Validation - widget is required
        if not widget:
            return no_update, no_update, no_update, dbc.Alert("⚠️ No widget found. Please create a table widget first.", color="warning")
        
        # Use the stored ORIGINAL dataset
        if not original_dataset:
            return no_update, no_update, no_update, dbc.Alert("⚠️ Original dataset not found. Please select a dataset first.", color="warning")
        
        if not filter_column or not filter_values_text:
            return no_update, no_update, no_update, dbc.Alert("⚠️ Please select a column and provide filter values.", color="warning")
        
        # Parse filter values
        filter_vals = [v.strip() for v in filter_values_text.split(',') if v.strip()]
        if not filter_vals:
            return no_update, no_update, no_update, dbc.Alert("⚠️ Please provide at least one filter value", color="warning")
        
        # Build filter description
        if len(filter_vals) == 1:
            filter_desc = f"{filter_column} = '{filter_vals[0]}'"
        else:
            filter_desc = f"{filter_column} = {', '.join(filter_vals)}"
        
        updated_config = None  # Initialize for error handling
        
        try:
            # Apply filter to COPY of original dataset
            import copy
            dataset_copy = copy.deepcopy(original_dataset)
            filtered_dataset_result = apply_simple_filter_to_dataset(dataset_copy, filter_column, filter_vals)
            
            # Build layout with widgets
            layout = [
                {
                    "widget": widget,
                    "position": {
                        "x": 0,
                        "y": 0,
                        "width": 6,
                        "height": 8
                    }
                }
            ]
            
            current_y = 8
            
            # Add filter widgets
            if filter_widgets:
                for idx, filter_widget in enumerate(filter_widgets):
                    layout.append({
                        "widget": filter_widget,
                        "position": {
                            "x": (idx % 6) * 2,
                            "y": current_y + (idx // 6),
                            "width": 2,
                            "height": 1
                        }
                    })
                current_y = current_y + ((len(filter_widgets) - 1) // 6) + 1
            
            # Add bar chart widgets
            if bar_chart_widgets:
                for idx, bar_chart in enumerate(bar_chart_widgets):
                    layout.append({
                        "widget": bar_chart,
                        "position": {
                            "x": (idx % 2) * 3,
                            "y": current_y + (idx // 2) * 6,
                            "width": 3,
                            "height": 6
                        }
                    })
                current_y = current_y + ((len(bar_chart_widgets) - 1) // 2 + 1) * 6
            
            # Add line chart widgets
            if line_chart_widgets:
                for idx, line_chart in enumerate(line_chart_widgets):
                    layout.append({
                        "widget": line_chart,
                        "position": {
                            "x": (idx % 2) * 3,
                            "y": current_y + (idx // 2) * 6,
                            "width": 3,
                            "height": 6
                        }
                    })
                current_y = current_y + ((len(line_chart_widgets) - 1) // 2 + 1) * 6
            
            # Add pivot widgets
            if pivot_widgets:
                for idx, pivot_widget in enumerate(pivot_widgets):
                    layout.append({
                        "widget": pivot_widget,
                        "position": {
                            "x": (idx % 2) * 3,
                            "y": current_y + (idx // 2) * 6,
                            "width": 3,
                            "height": 6
                        }
                    })
            
            # Build full dashboard config with filtered dataset
            updated_config = {
                "datasets": [filtered_dataset_result],
                "pages": [
                    {
                        "name": "ab333341",
                        "displayName": "Overview",
                        "layout": layout,
                        "pageType": "PAGE_TYPE_CANVAS"
                    }
                ]
            }
            
            # Delete existing dashboard if it exists
            if dashboard_id:
                try:
                    success, msg = dashboard_manager.delete_dashboard(dashboard_id)
                    print(f"[DEBUG] Deleted existing dashboard {dashboard_id}: {msg}")
                    # Wait for deletion to be processed
                    import time
                    time.sleep(1)
                except Exception as e:
                    print(f"[DEBUG] Warning: Could not delete dashboard {dashboard_id}: {str(e)}")
            
            # Use default dashboard name if not provided
            if not dashboard_name or not dashboard_name.strip():
                dashboard_name = "Filtered Dashboard"
            
            # Generate new dashboard
            new_dashboard_id = dashboard_manager.create_dashboard(updated_config, dashboard_name)
            print(f"[DEBUG] Created new dashboard {new_dashboard_id}")
            
            # Get embed URL
            embed_url = dashboard_manager.get_embed_url(new_dashboard_id)
            
            # Create iframe
            iframe = html.Iframe(
                src=embed_url,
                style={
                    'width': '100%',
                    'height': '800px',
                    'border': '1px solid #ddd',
                    'borderRadius': '5px'
                }
            )
            
            # Create preview card
            preview_card = dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H4(f"✅ Dashboard Deployed: {dashboard_name}"),
                            html.Small(f"Dashboard ID: {new_dashboard_id}", className="text-muted")
                        ], width=8),
                        dbc.Col([
                            dbc.Button("🗑️ Delete Dashboard", id="delete-dashboard-btn", color="danger", size="sm", className="float-end")
                        ], width=4)
                    ], align="center")
                ]),
                dbc.CardBody([
                    iframe
                ])
            ])
            
            # Create status message
            status = dbc.Alert([
                html.Strong("✅ Filter applied and dashboard regenerated!"),
                html.Br(),
                html.Small(f"Filter: {filter_desc}"),
                html.Br(),
                html.Small(f"Dashboard ID: {new_dashboard_id}")
            ], color="success", dismissable=True)
            
            return preview_card, updated_config, new_dashboard_id, status
            
        except Exception as e:
            # If dashboard generation fails, still return the updated config
            error_msg = dbc.Alert([
                html.Strong("⚠️ Filter applied but dashboard generation failed"),
                html.Br(),
                html.Small(f"Filter: {filter_desc}"),
                html.Br(),
                html.Small(f"Error: {str(e)}")
            ], color="warning")
            
            print(f"[DEBUG] Error refreshing dashboard: {e}")
            import traceback
            traceback.print_exc()
            
            return html.Div(), updated_config if updated_config else no_update, None, error_msg
    
    
    # ============================================================================
    # BAR CHART CONFIGURATION
    # ============================================================================
    
    @app.callback(
        Output('bar-chart-widget-section', 'children'),
        Input('current-widget', 'data'),
        Input('selected-widgets', 'data'),
        State('extracted-columns', 'data'),
        prevent_initial_call=False
    )
    def show_bar_chart_section(widget, selected_widgets, all_columns):
        if not widget or not all_columns:
            return ""
        
        # Only show if bar chart widget is selected
        if not selected_widgets or "bar_chart" not in selected_widgets:
            return ""
        
        return dbc.Card([
            dbc.CardHeader(html.H5("📊 Step 3.7: Configure Bar Chart Widget")),
            dbc.CardBody([
                html.P("Create bar charts to visualize your data:", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("X-Axis (Measure):", className="fw-bold"),
                        dcc.Dropdown(
                            id='bar-x-column',
                            options=[{'label': col, 'value': col} for col in all_columns],
                            placeholder="Select column for X-axis...",
                            className="mb-2"
                        )
                    ], width=4),
                    dbc.Col([
                        html.Label("Aggregation:", className="fw-bold"),
                        dcc.Dropdown(
                            id='bar-aggregation',
                            options=[
                                {'label': 'COUNT', 'value': 'COUNT'},
                                {'label': 'SUM', 'value': 'SUM'},
                                {'label': 'AVG', 'value': 'AVG'},
                                {'label': 'MAX', 'value': 'MAX'},
                                {'label': 'MIN', 'value': 'MIN'}
                            ],
                            value='COUNT',
                            className="mb-2"
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label("Y-Axis (Dimension):", className="fw-bold"),
                        dcc.Dropdown(
                            id='bar-y-column',
                            options=[{'label': col, 'value': col} for col in all_columns],
                            placeholder="Select column for Y-axis...",
                            className="mb-2"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("Color (Optional):", className="fw-bold"),
                        dcc.Dropdown(
                            id='bar-color-column',
                            options=[{'label': col, 'value': col} for col in all_columns],
                            placeholder="Select color column...",
                            className="mb-2"
                        )
                    ], width=3)
                ]),
                dbc.Button("Add Bar Chart", id="add-bar-chart-btn", color="primary", className="mt-3")
            ])
        ], className="mb-4")
    
    
    @app.callback(
        [Output('bar-chart-widgets-display', 'children'),
         Output('bar-chart-widgets', 'data')],
        Input('add-bar-chart-btn', 'n_clicks'),
        [State('bar-x-column', 'value'),
         State('bar-aggregation', 'value'),
         State('bar-y-column', 'value'),
         State('bar-color-column', 'value'),
         State('dataset-dropdown', 'value'),
         State('bar-chart-widgets', 'data')],
        prevent_initial_call=True
    )
    def create_bar_chart(n_clicks, x_col, aggregation, y_col, color_col, dataset_value, existing_charts):
        if not n_clicks or n_clicks == 0:
            return "", []
        if not x_col or not y_col or not dataset_value:
            return dbc.Alert("Please select X and Y columns", color="warning"), existing_charts or []
        
        dataset = datasets.get(dataset_value)
        if not dataset:
            return dbc.Alert("Dataset not found", color="warning"), existing_charts or []
        
        # Create bar chart widget
        bar_chart = create_bar_chart_widget(
            x_column=x_col,
            y_column=y_col,
            y_aggregation=aggregation,
            color_column=color_col if color_col else None,
            dataset_name=dataset['name']
        )
        
        # Add to existing charts
        if not existing_charts:
            existing_charts = []
        existing_charts.append(bar_chart)
        
        chart_card = dbc.Card([
            dbc.CardHeader(html.H5(f"📊 Bar Chart Widgets ({len(existing_charts)})")),
            dbc.CardBody([
                dbc.Alert(f"✅ Created {len(existing_charts)} bar chart(s)", color="success", className="mb-3"),
                html.Pre(
                    json.dumps(existing_charts, indent=2),
                    style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '15px',
                        'borderRadius': '5px',
                        'overflow': 'auto',
                        'maxHeight': '400px',
                        'fontSize': '11px'
                    }
                )
            ])
        ], className="mb-4")
        
        return chart_card, existing_charts
    
    
    # ============================================================================
    # LINE CHART CONFIGURATION
    # ============================================================================
    
    @app.callback(
        Output('line-chart-widget-section', 'children'),
        Input('current-widget', 'data'),
        Input('selected-widgets', 'data'),
        State('extracted-columns', 'data'),
        prevent_initial_call=False
    )
    def show_line_chart_section(widget, selected_widgets, all_columns):
        if not widget or not all_columns:
            return ""
        
        # Only show if line chart widget is selected
        if not selected_widgets or "line_chart" not in selected_widgets:
            return ""
        
        return dbc.Card([
            dbc.CardHeader(html.H5("📈 Step 3.9: Configure Line Chart Widget")),
            dbc.CardBody([
                html.P("Create line charts to visualize trends over time:", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("X-Axis (Time Column):", className="fw-bold"),
                        dcc.Dropdown(
                            id='line-x-column',
                            options=[{'label': col, 'value': col} for col in all_columns],
                            placeholder="Select date/time column...",
                            className="mb-2"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("Time Granularity:", className="fw-bold"),
                        dcc.Dropdown(
                            id='line-time-granularity',
                            options=[
                                {'label': 'Year', 'value': 'YEAR'},
                                {'label': 'Quarter', 'value': 'QUARTER'},
                                {'label': 'Month', 'value': 'MONTH'},
                                {'label': 'Week', 'value': 'WEEK'},
                                {'label': 'Day', 'value': 'DAY'},
                                {'label': 'Hour', 'value': 'HOUR'}
                            ],
                            value='MONTH',
                            className="mb-2"
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label("Y-Axis (Measure):", className="fw-bold"),
                        dcc.Dropdown(
                            id='line-y-column',
                            options=[{'label': col, 'value': col} for col in all_columns],
                            placeholder="Select column for Y-axis...",
                            className="mb-2"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("Aggregation:", className="fw-bold"),
                        dcc.Dropdown(
                            id='line-aggregation',
                            options=[
                                {'label': 'COUNT', 'value': 'COUNT'},
                                {'label': 'SUM', 'value': 'SUM'},
                                {'label': 'AVG', 'value': 'AVG'},
                                {'label': 'MAX', 'value': 'MAX'},
                                {'label': 'MIN', 'value': 'MIN'}
                            ],
                            value='COUNT',
                            className="mb-2"
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label("Color (Optional):", className="fw-bold"),
                        dcc.Dropdown(
                            id='line-color-column',
                            options=[{'label': col, 'value': col} for col in all_columns],
                            placeholder="Multiple lines...",
                            className="mb-2"
                        )
                    ], width=2)
                ]),
                dbc.Button("Add Line Chart", id="add-line-chart-btn", color="success", className="mt-3")
            ])
        ], className="mb-4")
    
    
    @app.callback(
        [Output('line-chart-widgets-display', 'children'),
         Output('line-chart-widgets', 'data')],
        Input('add-line-chart-btn', 'n_clicks'),
        [State('line-x-column', 'value'),
         State('line-time-granularity', 'value'),
         State('line-y-column', 'value'),
         State('line-aggregation', 'value'),
         State('line-color-column', 'value'),
         State('dataset-dropdown', 'value'),
         State('line-chart-widgets', 'data')],
        prevent_initial_call=True
    )
    def create_line_chart(n_clicks, x_col, time_granularity, y_col, aggregation, color_col, dataset_value, existing_charts):
        if not n_clicks or n_clicks == 0:
            return "", []
        if not x_col or not y_col or not dataset_value:
            return dbc.Alert("Please select X and Y columns", color="warning"), existing_charts or []
        
        dataset = datasets.get(dataset_value)
        if not dataset:
            return dbc.Alert("Dataset not found", color="warning"), existing_charts or []
        
        # Create line chart widget
        line_chart = create_line_chart_widget(
            x_column=x_col,
            y_column=y_col,
            y_aggregation=aggregation,
            time_granularity=time_granularity,
            color_column=color_col if color_col else None,
            dataset_name=dataset['name']
        )
        
        # Add to existing charts
        if not existing_charts:
            existing_charts = []
        existing_charts.append(line_chart)
        
        chart_card = dbc.Card([
            dbc.CardHeader(html.H5(f"📈 Line Chart Widgets ({len(existing_charts)})")),
            dbc.CardBody([
                dbc.Alert(f"✅ Created {len(existing_charts)} line chart(s)", color="success", className="mb-3"),
                html.Pre(
                    json.dumps(existing_charts, indent=2),
                    style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '15px',
                        'borderRadius': '5px',
                        'overflow': 'auto',
                        'maxHeight': '400px',
                        'fontSize': '11px'
                    }
                )
            ])
        ], className="mb-4")
        
        return chart_card, existing_charts
    
    
    # ============================================================================
    # PIVOT TABLE CONFIGURATION
    # ============================================================================
    
    @app.callback(
        Output('pivot-widget-section', 'children'),
        Input('current-widget', 'data'),
        Input('selected-widgets', 'data'),
        State('extracted-columns', 'data'),
        prevent_initial_call=False
    )
    def show_pivot_section(widget, selected_widgets, all_columns):
        if not widget or not all_columns:
            return ""
        
        # Only show if pivot widget is selected
        if not selected_widgets or "pivot" not in selected_widgets:
            return ""
        
        return dbc.Card([
            dbc.CardHeader(html.H5("🔢 Step 3.10: Configure Pivot Table Widget")),
            dbc.CardBody([
                html.P("Create pivot tables to aggregate and summarize your data:", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Row Dimensions:", className="fw-bold"),
                        dcc.Dropdown(
                            id='pivot-row-columns',
                            options=[{'label': col, 'value': col} for col in all_columns],
                            placeholder="Select row dimensions...",
                            multi=True,
                            className="mb-2"
                        ),
                        html.Small("Select one or more columns to group by (e.g., priority, status, country)", className="text-muted")
                    ], width=5),
                    dbc.Col([
                        html.Label("Value Column:", className="fw-bold"),
                        dcc.Dropdown(
                            id='pivot-value-column',
                            options=[{'label': col, 'value': col} for col in all_columns],
                            placeholder="Select column to aggregate...",
                            className="mb-2"
                        ),
                        html.Small("Column to aggregate in cells", className="text-muted")
                    ], width=4),
                    dbc.Col([
                        html.Label("Aggregation:", className="fw-bold"),
                        dcc.Dropdown(
                            id='pivot-aggregation',
                            options=[
                                {'label': 'COUNT', 'value': 'COUNT'},
                                {'label': 'SUM', 'value': 'SUM'},
                                {'label': 'AVG', 'value': 'AVG'},
                                {'label': 'MAX', 'value': 'MAX'},
                                {'label': 'MIN', 'value': 'MIN'}
                            ],
                            value='SUM',
                            className="mb-2"
                        )
                    ], width=3)
                ]),
                dbc.Button("Add Pivot Table", id="add-pivot-btn", color="info", className="mt-3")
            ])
        ], className="mb-4")
    
    
    @app.callback(
        [Output('pivot-widgets-display', 'children'),
         Output('pivot-widgets', 'data')],
        Input('add-pivot-btn', 'n_clicks'),
        [State('pivot-row-columns', 'value'),
         State('pivot-value-column', 'value'),
         State('pivot-aggregation', 'value'),
         State('dataset-dropdown', 'value'),
         State('pivot-widgets', 'data')],
        prevent_initial_call=True
    )
    def create_pivot(n_clicks, row_columns, value_column, aggregation, dataset_value, existing_pivots):
        if not n_clicks or n_clicks == 0:
            return "", []
        if not row_columns or not value_column or not dataset_value:
            return dbc.Alert("Please select row dimensions and value column", color="warning"), existing_pivots or []
        
        dataset = datasets.get(dataset_value)
        if not dataset:
            return dbc.Alert("Dataset not found", color="warning"), existing_pivots or []
        
        # Create pivot widget
        pivot_widget = create_pivot_widget(
            row_columns=row_columns if isinstance(row_columns, list) else [row_columns],
            value_column=value_column,
            aggregation=aggregation,
            dataset_name=dataset['name']
        )
        
        # Add to existing pivots
        if not existing_pivots:
            existing_pivots = []
        existing_pivots.append(pivot_widget)
        
        pivot_card = dbc.Card([
            dbc.CardHeader(html.H5(f"🔢 Pivot Table Widgets ({len(existing_pivots)})")),
            dbc.CardBody([
                dbc.Alert(f"✅ Created {len(existing_pivots)} pivot table(s)", color="success", className="mb-3"),
                html.Pre(
                    json.dumps(existing_pivots, indent=2),
                    style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '15px',
                        'borderRadius': '5px',
                        'overflow': 'auto',
                        'maxHeight': '400px',
                        'fontSize': '11px'
                    }
                )
            ])
        ], className="mb-4")
        
        return pivot_card, existing_pivots
    
    
    # ============================================================================
    # DASHBOARD ASSEMBLY
    # ============================================================================
    
    @app.callback(
        Output('add-widget-section', 'children'),
        Input('current-widget', 'data'),
        prevent_initial_call=False
    )
    def show_add_button(widget):
        if not widget:
            return ""
        
        return dbc.Card([
            dbc.CardHeader(html.H5("📌 Step 4: Add to Dashboard")),
            dbc.CardBody([
                html.P("Ready to add all your widgets to the dashboard configuration?", className="mb-3"),
                dbc.Button("➕ Add All Widgets to Dashboard", id="add-to-dashboard-btn", color="success", size="lg", className="w-100")
            ])
        ], className="mb-4")
    
    
    @app.callback(
        [Output('dashboard-config-display', 'children'),
         Output('dashboard-config', 'data')],
        Input('add-to-dashboard-btn', 'n_clicks'),
        [State('current-widget', 'data'),
         State('filter-widgets', 'data'),
         State('bar-chart-widgets', 'data'),
         State('line-chart-widgets', 'data'),
         State('pivot-widgets', 'data'),
         State('dataset-dropdown', 'value'),
         State('filtered-dataset', 'data')],
        prevent_initial_call=True
    )
    def add_widget_to_dashboard(n_clicks, widget, filter_widgets, bar_chart_widgets, line_chart_widgets, pivot_widgets, dataset_value, filtered_dataset):
        if not n_clicks or n_clicks == 0:
            return "", None
        if not widget or not dataset_value:
            return "", None
        
        # Use filtered dataset if available, otherwise use original
        if filtered_dataset:
            dataset = filtered_dataset
        else:
            dataset = datasets.get(dataset_value)
            if not dataset:
                return dbc.Alert("Dataset not found", color="warning"), None
        
        # Create layout with table widget first
        layout = [
            {
                "widget": widget,
                "position": {
                    "x": 0,
                    "y": 0,
                    "width": 6,
                    "height": 8
                }
            }
        ]
        
        # Calculate starting Y position for additional widgets
        current_y = 8
        
        # Add filter widgets below the table
        if filter_widgets:
            for idx, filter_widget in enumerate(filter_widgets):
                layout.append({
                    "widget": filter_widget,
                    "position": {
                        "x": (idx % 6) * 2,
                        "y": current_y + (idx // 6),
                        "width": 2,
                        "height": 1
                    }
                })
            current_y = current_y + ((len(filter_widgets) - 1) // 6) + 1
        
        # Add bar chart widgets
        if bar_chart_widgets:
            for idx, bar_chart in enumerate(bar_chart_widgets):
                layout.append({
                    "widget": bar_chart,
                    "position": {
                        "x": (idx % 2) * 3,
                        "y": current_y + (idx // 2) * 6,
                        "width": 3,
                        "height": 6
                    }
                })
            current_y = current_y + ((len(bar_chart_widgets) - 1) // 2 + 1) * 6
        
        # Add line chart widgets
        if line_chart_widgets:
            for idx, line_chart in enumerate(line_chart_widgets):
                layout.append({
                    "widget": line_chart,
                    "position": {
                        "x": (idx % 2) * 3,
                        "y": current_y + (idx // 2) * 6,
                        "width": 3,
                        "height": 6
                    }
                })
            current_y = current_y + ((len(line_chart_widgets) - 1) // 2 + 1) * 6
        
        # Add pivot widgets
        if pivot_widgets:
            for idx, pivot_widget in enumerate(pivot_widgets):
                layout.append({
                    "widget": pivot_widget,
                    "position": {
                        "x": (idx % 2) * 3,
                        "y": current_y + (idx // 2) * 6,
                        "width": 3,
                        "height": 6
                    }
                })
        
        # Create full dashboard configuration
        dashboard_config = {
            "datasets": [dataset],
            "pages": [
                {
                    "name": "ab333341",
                    "displayName": "Overview",
                    "layout": layout,
                    "pageType": "PAGE_TYPE_CANVAS"
                }
            ]
        }
        
        widget_summary = [
            f"1 table widget",
            f"{len(filter_widgets) if filter_widgets else 0} filter widget(s)",
            f"{len(bar_chart_widgets) if bar_chart_widgets else 0} bar chart(s)",
            f"{len(line_chart_widgets) if line_chart_widgets else 0} line chart(s)",
            f"{len(pivot_widgets) if pivot_widgets else 0} pivot table(s)"
        ]
        
        config_card = dbc.Card([
            dbc.CardHeader(html.H4("🎨 Step 5: Final Dashboard Configuration")),
            dbc.CardBody([
                dbc.Alert(f"✅ Dashboard created with {', '.join(widget_summary)}!", color="success", className="mb-3"),
                html.Pre(
                    json.dumps(dashboard_config, indent=2),
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
        
        return config_card, dashboard_config
    
    
    @app.callback(
        [Output('deploy-section', 'children'),
         Output('deploy-dashboard-name', 'style'),
         Output('deploy-dashboard-name', 'className')],
        Input('dashboard-config', 'data'),
        prevent_initial_call=False
    )
    def show_deploy_button(config):
        if not config:
            return "", {'display': 'none'}, ""
        
        deploy_card = dbc.Card([
            dbc.CardHeader(html.H5("🚀 Step 6: Deploy to Databricks")),
            dbc.CardBody([
                html.Label("Dashboard Name:", className="fw-bold mb-2"),
                html.Div(style={'marginBottom': '1rem'}),  # Placeholder for the input
                dbc.Button("🚀 Deploy Dashboard to Databricks", id="deploy-btn", color="primary", size="lg", className="w-100")
            ])
        ], className="mb-4")
        
        return deploy_card, {'display': 'block'}, 'mb-3'
