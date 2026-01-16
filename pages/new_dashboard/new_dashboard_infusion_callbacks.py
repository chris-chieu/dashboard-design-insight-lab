"""
NEW DASHBOARD INTELLIGENT INFUSION CALLBACKS
============================================
Handles post-generation design infusion for new dashboards, including:
- Image-based design extraction and application
- Prompt-based intelligent design generation with analysis and reasoning
- Design validation and refinement
"""

from dash import callback, Output, Input, State, no_update, callback_context, html
import dash_bootstrap_components as dbc
import json
import time
import copy

from dashboard_management_functions.design_infusion import (
    extract_design_from_image,
    generate_design_with_analysis,
    refine_design_from_feedback
)


def register_new_dashboard_infusion_callbacks(app, dashboard_manager, workspace_client, llm_client):
    """
    Register all infusion callbacks for the new dashboard page (post-generation).
    
    Args:
        app: Dash app instance
        dashboard_manager: DashboardManager instance
        workspace_client: Databricks WorkspaceClient instance
        llm_client: LLM client for design generation
    """
    
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
                
                updated_config = copy.deepcopy(serialized)
                if 'uiSettings' in updated_config:
                    del updated_config['uiSettings']
                
                updated_config['uiSettings'] = design_data['uiSettings']
                
                # Update dashboard
                dashboard_manager.update_dashboard(dashboard_id, updated_config)
                new_embed_url = dashboard_manager.get_embed_url(dashboard_id)
                
                # Add cache-busting
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
    
    
    print("✅ New dashboard infusion callbacks registered successfully")

