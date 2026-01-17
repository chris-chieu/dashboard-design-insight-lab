"""
Genie Space Toggle Callbacks for Existing Dashboard Page

Handles the toggle functionality for enabling/disabling Genie Space on dashboards.
"""

import json
import time
import copy
from dash import callback, Output, Input, State, no_update, html
import dash_bootstrap_components as dbc


def create_dashboard_card_with_genie_toggle(dashboard_id, dashboard_name, embed_url, genie_enabled):
    """
    Create a dashboard preview card with Genie Space toggle
    
    Args:
        dashboard_id: Dashboard ID
        dashboard_name: Dashboard name
        embed_url: Dashboard embed URL
        genie_enabled: Current Genie Space enabled state
        
    Returns:
        dbc.Card: Dashboard preview card with header containing toggle
    """
    preview_card = dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H4(f"{dashboard_name}"),
                    html.Small(f"Dashboard ID: {dashboard_id}", className="text-muted")
                ], width=7),
                dbc.Col([
                    dbc.Button("Metrics Discovery", id="existing-metrics-discovery-btn", color="info", size="sm", className="me-2"),
                    dbc.Button("Infusion", id="existing-apply-infusion-btn", color="primary", size="sm", className="me-2"),
                    dbc.Button("Delete Dashboard", id="existing-delete-dashboard-btn", color="danger", size="sm")
                ], width=5, className="text-end")
            ], align="center"),
            # Genie Space Toggle (second row in header)
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Label("Genie Space:", className="me-2", style={'fontWeight': '600', 'fontSize': '0.875rem'}),
                        dbc.Switch(
                            id='genie-space-toggle',
                            value=genie_enabled,
                            label="",
                            className="d-inline-block",
                            persistence=False  # Prevent persistence to avoid conflicts
                        ),
                        html.Small(
                            " Enabled" if genie_enabled else " Disabled",
                            id='genie-space-status-text',
                            className="text-muted ms-1",
                            style={'fontSize': '0.75rem'}
                        )
                    ], className="d-flex align-items-center")
                ], width=12)
            ], className="mt-2")
        ]),
        dbc.CardBody([
            html.Iframe(
                id='dashboard-iframe',
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
    
    return preview_card


def register_genie_space_callbacks(app, dashboard_manager):
    """
    Register callbacks for Genie Space toggle functionality
    
    Args:
        app: Dash app instance
        dashboard_manager: Dashboard manager instance for updating dashboards
    """
    
    @callback(
        [Output('dashboard-iframe', 'src'),
         Output('genie-space-status-text', 'children'),
         Output('existing-dashboard-config', 'data', allow_duplicate=True)],
        Input('genie-space-toggle', 'value'),
        [State('existing-dashboard-id', 'data'),
         State('existing-dashboard-config', 'data'),
         State('existing-dashboard-name', 'data')],
        prevent_initial_call=True
    )
    def toggle_genie_space(genie_enabled, dashboard_id, dashboard_config, dashboard_name):
        """Toggle Genie Space setting and update dashboard"""
        
        print(f"🔘 Genie Space toggle callback triggered! Value: {genie_enabled}")
        print(f"   Dashboard ID: {dashboard_id}")
        print(f"   Dashboard Name: {dashboard_name}")
        
        if not dashboard_id or not dashboard_config:
            print(f"❌ Missing required data - dashboard_id: {dashboard_id}, dashboard_config: {dashboard_config is not None}")
            return no_update, no_update, no_update
        
        try:
            print(f"🔄 Toggling Genie Space to: {genie_enabled}")
            
            # Extract and update config
            serialized = dashboard_config.get('serialized_dashboard', {})
            if isinstance(serialized, str):
                serialized = json.loads(serialized)
            
            updated_config = copy.deepcopy(serialized)
            
            # genieSpace is inside uiSettings, not at top level!
            if 'uiSettings' not in updated_config:
                updated_config['uiSettings'] = {}
            
            if 'genieSpace' not in updated_config['uiSettings']:
                updated_config['uiSettings']['genieSpace'] = {}
            
            # Update genieSpace setting with correct enablementMode
            updated_config['uiSettings']['genieSpace']['isEnabled'] = genie_enabled
            # Set enablementMode based on toggle state
            if genie_enabled:
                updated_config['uiSettings']['genieSpace']['enablementMode'] = 'ENABLED'
            else:
                updated_config['uiSettings']['genieSpace']['enablementMode'] = 'DISABLED'
            
            print(f"✅ Updated uiSettings.genieSpace: isEnabled={genie_enabled}, enablementMode={'ENABLED' if genie_enabled else 'DISABLED'}")
            
            # Debug: Show what we're about to send
            print(f"📤 Sending to Databricks:")
            print(f"   - uiSettings.genieSpace: {updated_config.get('uiSettings', {}).get('genieSpace')}")
            print(f"   - Config has {len(updated_config)} top-level keys")
            print(f"   - Top-level keys: {list(updated_config.keys())}")
            
            # Update dashboard in Databricks
            print(f"📤 Updating dashboard {dashboard_id} in Databricks...")
            dashboard_manager.update_dashboard(dashboard_id, updated_config)
            print(f"✅ Dashboard update complete")
            
            # Verify the update was persisted
            print(f"🔍 Verifying update was persisted...")
            verified_config = dashboard_manager.get_dashboard_config(dashboard_id)
            verified_serialized = verified_config.get('serialized_dashboard', {})
            if isinstance(verified_serialized, str):
                verified_serialized = json.loads(verified_serialized)
            
            # genieSpace is in uiSettings
            verified_ui_settings = verified_serialized.get('uiSettings', {})
            verified_genie = verified_ui_settings.get('genieSpace', {})
            print(f"✅ Verified uiSettings.genieSpace in Databricks: isEnabled={verified_genie.get('isEnabled')}, enablementMode={verified_genie.get('enablementMode')}")
            
            if verified_genie.get('isEnabled') != genie_enabled:
                print(f"⚠️ WARNING: Expected isEnabled={genie_enabled}, but got {verified_genie.get('isEnabled')}")
            
            new_embed_url = dashboard_manager.get_embed_url(dashboard_id)
            
            # Add cache-busting parameter to force refresh
            cache_buster = f"?_refresh={int(time.time() * 1000)}"
            new_embed_url_with_refresh = new_embed_url + cache_buster
            
            print(f"🔗 New embed URL: {new_embed_url_with_refresh[:100]}...")
            
            # Update stored config
            full_updated_config = {
                'serialized_dashboard': updated_config,
                'display_name': dashboard_name
            }
            
            # Status text to show next to toggle
            status_text = " Enabled" if genie_enabled else " Disabled"
            
            print(f"✅ Dashboard updated with Genie Space = {genie_enabled}")
            return new_embed_url_with_refresh, status_text, full_updated_config
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Error toggling Genie Space: {str(e)}")
            return no_update, no_update, no_update
    
    
    print("✅ Genie Space callbacks registered successfully")

