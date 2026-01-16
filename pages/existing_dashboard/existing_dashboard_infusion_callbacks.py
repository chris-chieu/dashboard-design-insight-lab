"""
Callbacks for intelligent design infusion workflow on existing dashboard page.
Handles design generation with analysis, validation, and refinement.
"""

import json
import time
from dash import callback, Output, Input, State, no_update, html
import dash_bootstrap_components as dbc
from dashboard_management_functions.design_infusion import (
    extract_design_from_image,
    generate_design_with_analysis,
    refine_design_from_feedback
)


def register_existing_dashboard_infusion_callbacks(app, dashboard_manager, workspace_client, llm_client):
    """
    Register callbacks for intelligent design infusion on existing dashboard page.
    
    Args:
        app: Dash app instance
        dashboard_manager: Dashboard manager instance
        workspace_client: Databricks workspace client
        llm_client: OpenAI LLM client for design generation
    """
    
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
        """Generate design with analysis and reasoning (INTELLIGENT WORKFLOW - doesn't apply immediately)"""
        from dash import callback_context
        
        # Check what triggered the callback
        if not callback_context.triggered:
            return "", "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
        
        trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        
        # Validate that we have dashboard data
        if not dashboard_id or not dashboard_config:
            error_msg = dbc.Alert("⚠️ Missing dashboard data", color="warning")
            return error_msg, "", {'display': 'none'}, None, None, None, None, None, "", no_update, no_update, no_update
        
        # Handle image upload path separately (direct application)
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
                
                # Apply the design immediately
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
                cache_buster = f"?_refresh={int(time.time() * 1000)}"
                new_embed_url_with_refresh = new_embed_url + cache_buster
                
                # Create updated preview card
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
                
                # Call the intelligent function
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
    # MODAL CONTROL CALLBACKS
    # ============================================================================
    
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
    
    
    print("✅ Existing dashboard infusion callbacks registered successfully (including modal controls)")

