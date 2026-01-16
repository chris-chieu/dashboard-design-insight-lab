"""
Metrics Discovery Callbacks for Existing Dashboard Page

Handles callbacks for analyzing dashboard metrics and providing explanations
of how each metric is calculated using LLM.
"""

import json
from dash import callback, Output, Input, State, no_update, html, callback_context, dcc
import dash_bootstrap_components as dbc


def analyze_dashboard_metrics(dashboard_config, llm_client):
    """
    Analyze dashboard widgets and explain how each metric is calculated.
    
    Args:
        dashboard_config: Dashboard configuration dictionary
        llm_client: OpenAI LLM client
        
    Returns:
        tuple: (display_component, analysis_text)
    """
    try:
        # Extract serialized dashboard
        if isinstance(dashboard_config, dict):
            if 'serialized_dashboard' in dashboard_config:
                serialized = dashboard_config['serialized_dashboard']
            else:
                serialized = dashboard_config
        else:
            serialized = dashboard_config
        
        # Ensure serialized is a dict (parse if it's a string)
        if isinstance(serialized, str):
            serialized = json.loads(serialized)
        
        # Debug: Print the top-level structure
        print(f"DEBUG: Dashboard config type: {type(serialized)}")
        print(f"DEBUG: Dashboard config keys: {list(serialized.keys()) if isinstance(serialized, dict) else 'Not a dict'}")
        
        # Extract all pages and datasets
        pages = serialized.get('pages', [])
        datasets = serialized.get('datasets', [])
        
        print(f"DEBUG: Found {len(pages)} pages and {len(datasets)} datasets")
        
        # Build analysis prompt
        widget_summaries = []
        
        print(f"Analyzing dashboard: {len(pages)} pages, {len(datasets)} datasets")
        
        for page_idx, page in enumerate(pages):
            print(f"DEBUG: Page {page_idx} keys: {list(page.keys())}")
            page_name = page.get('displayName', f'Page {page_idx + 1}')
            layouts = page.get('layout', [])
            
            print(f"   Page '{page_name}': {len(layouts)} layout items")
            
            # Debug: check if layouts is a list or something else
            print(f"DEBUG: Layouts type: {type(layouts)}, is list: {isinstance(layouts, list)}")
            
            for widget_idx, layout in enumerate(layouts):
                # Debug: check layout structure
                print(f"DEBUG: Layout {widget_idx} type: {type(layout)}, keys: {list(layout.keys()) if isinstance(layout, dict) else 'Not a dict'}")
                
                widget = layout.get('widget', {})
                position = layout.get('position', {})
                
                # Debug: print widget keys to see what's available
                widget_keys = list(widget.keys()) if isinstance(widget, dict) else []
                print(f"      Widget {widget_idx}: has widget={widget is not None}, widget keys = {widget_keys}")
                
                # CRITICAL: Extract the queries array (contains actual SQL expressions)
                widget_queries = widget.get('queries', [])
                query_fields = []
                for query in widget_queries:
                    query_def = query.get('query', {})
                    fields = query_def.get('fields', [])
                    for field in fields:
                        query_fields.append({
                            'name': field.get('name'),
                            'expression': field.get('expression')
                        })
                
                print(f"      Widget {widget_idx} query fields: {query_fields}")
                
                # Extract widget spec (the display configuration)
                widget_spec = widget.get('spec', {})
                widget_type_raw = widget_spec.get('widgetType', 'unknown')
                frame = widget_spec.get('frame', {})
                encodings = widget_spec.get('encodings', {})
                
                # Get meaningful title from frame
                widget_title = frame.get('title', f'{widget_type_raw} Widget')
                
                # Determine widget type and extract key information
                if widget_type_raw == 'counter':
                    widget_type = 'Counter (KPI)'
                    value_field = encodings.get('value', {}).get('fieldName')
                    widget_config = {
                        'value_field': value_field,
                        'query_fields': query_fields,
                        'label': widget_title
                    }
                    
                elif widget_type_raw in ['bar', 'line', 'area', 'scatter']:
                    widget_type = f'{widget_type_raw.title()} Chart'
                    x_field = encodings.get('x', {}).get('fieldName')
                    y_field = encodings.get('y', {}).get('fieldName')
                    color_field = encodings.get('color', {}).get('fieldName')
                    
                    widget_config = {
                        'x_field': x_field,
                        'y_field': y_field,
                        'color_field': color_field,
                        'query_fields': query_fields,
                        'encodings': encodings
                    }
                    
                elif widget_type_raw == 'table':
                    widget_type = 'Table'
                    widget_config = {
                        'query_fields': query_fields
                    }
                    
                elif widget_type_raw == 'filter':
                    widget_type = 'Filter'
                    widget_config = {
                        'query_fields': query_fields
                    }
                    
                else:
                    # Unknown widget type
                    widget_name = widget.get('name', f'Widget {widget_idx + 1}')
                    print(f"      ⚠️ Unknown widget type: {widget_type_raw}. Keys: {widget_keys}, Name: {widget_name}")
                    widget_type = f'{widget_type_raw} Widget' if widget_type_raw != 'unknown' else 'Unknown Widget'
                    widget_config = {
                        'query_fields': query_fields,
                        'raw_keys': widget_keys
                    }
                
                # Always add the widget
                widget_info = {
                    'title': widget_title,
                    'page': page_name,
                    'type': widget_type,
                    'config': widget_config
                }
                    
                widget_summaries.append(widget_info)
        
        print(f"✅ Total widgets extracted: {len(widget_summaries)}")
        
        # Check if no widgets found
        if len(widget_summaries) == 0:
            # Dump first 500 chars of serialized config for debugging
            config_preview = str(serialized)[:500] if serialized else "None"
            print(f"ERROR: No widgets found. Config preview: {config_preview}")
            
            error_msg = dbc.Alert([
                html.Strong("⚠️ No widgets found in this dashboard"),
                html.Br(),
                html.Small("The dashboard configuration doesn't contain any recognizable widgets (charts, counters, tables, filters)."),
                html.Br(),
                html.Small("Check the app logs for the dashboard structure."),
                html.Br(),
                html.Small(f"Debug: Found {len(pages)} pages, {len(datasets)} datasets")
            ], color="warning")
            return error_msg, None
        
        # Extract dataset queries
        dataset_queries = []
        for dataset_idx, dataset in enumerate(datasets):
            dataset_name = dataset.get('displayName', dataset.get('name', f'Dataset {dataset_idx}'))
            query_lines = dataset.get('queryLines', [])
            query = ''.join(query_lines) if query_lines else dataset.get('query', '')
            
            dataset_queries.append({
                'index': dataset_idx,
                'name': dataset_name,
                'query': query
            })
        
        # Build LLM prompt focusing on widgets only
        prompt = f"""You are a data analyst expert. Analyze these dashboard widgets and explain what each metric measures and how it is calculated.

**SQL Queries Available:**
"""
        
        for ds in dataset_queries:
            prompt += f"\n**Query {ds['index']}:**\n```sql\n{ds['query']}\n```\n"
        
        prompt += f"\n\n**Dashboard Widgets ({len(widget_summaries)} total):**\n"
        
        for idx, widget in enumerate(widget_summaries, 1):
            prompt += f"\n{idx}. **{widget['title']}** ({widget['type']})\n"
            
            # Extract query fields (the actual SQL expressions/calculations)
            query_fields = widget['config'].get('query_fields', [])
            if query_fields:
                prompt += "   **Calculations:**\n"
                for field in query_fields:
                    field_name = field.get('name', 'N/A')
                    field_expr = field.get('expression', 'N/A')
                    prompt += f"   - `{field_name}` = {field_expr}\n"
            
            # Add widget-specific display configuration
            if widget['type'] == 'Counter (KPI)':
                value_field = widget['config'].get('value_field')
                if value_field:
                    prompt += f"   **Displays:** {value_field}\n"
                    
            elif 'Chart' in widget['type']:
                x_field = widget['config'].get('x_field')
                y_field = widget['config'].get('y_field')
                color_field = widget['config'].get('color_field')
                
                if x_field or y_field:
                    prompt += "   **Axes:**\n"
                    if y_field:
                        prompt += f"   - Y-axis: {y_field}\n"
                    if x_field:
                        prompt += f"   - X-axis: {x_field}\n"
                    if color_field:
                        prompt += f"   - Color by: {color_field}\n"
            
            prompt += "\n"
        
        prompt += """

**Your Task:**
For each widget above, provide a concise explanation using the **SQL expressions provided in "Calculations"**.

**Format (IMPORTANT - follow exactly):**
### [Widget Title]
**Metric:** [What is being measured - use the field names and expressions]

**Calculation:** [Explain the SQL expression in business terms - e.g., "SUM(amount)" = total of all transaction amounts]

**Business Insight:** [One sentence on what users learn from this metric]

---

**Guidelines:**
- Use the actual SQL expressions (e.g., "SUM(amount)", "COUNT(*)", "AVG(price)") to explain what's calculated
- Translate technical expressions to business language (SUM = total, COUNT = number of, AVG = average)
- Reference the base SQL query (Query 0, 1, etc.) to explain what data is being aggregated
- Keep each section on a NEW LINE with a blank line between **Metric**, **Calculation**, and **Business Insight**
- Be concise (3-4 sentences per widget max)
- Skip filters/tables - focus only on metrics (Counters and Charts)"""

        # Call LLM (using Claude Sonnet for better analytical reasoning)
        print(f"Analyzing dashboard metrics with LLM...")
        response = llm_client.chat.completions.create(
            model="databricks-claude-sonnet-4",
            messages=[
                {"role": "system", "content": "You are a data analyst expert who explains dashboard metrics in clear, business-friendly language."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000
        )
        
        analysis_text = response.choices[0].message.content
        
        print(f"✅ Metrics analysis complete!")
        
        # Format the display component (no duplicate header, smaller font, smaller widget titles)
        # Match dashboard height (800px) + card padding
        display_component = html.Div([
            dcc.Markdown(
                analysis_text,
                className="metrics-analysis-content",
                style={
                    'height': '800px',  # Match dashboard iframe height
                    'overflowY': 'auto',
                    'fontSize': '0.875rem',  # Smaller font (14px)
                    'lineHeight': '1.5',
                    'padding': '10px'
                }
            )
        ])
        
        return display_component, analysis_text
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_display = dbc.Alert([
            html.Strong("❌ Error analyzing metrics"),
            html.Br(),
            html.Small(f"Error: {str(e)}")
        ], color="danger")
        
        return error_display, None


def register_metrics_discovery_callbacks(app, llm_client):
    """
    Register callbacks for metrics discovery feature on existing dashboard page.
    
    Args:
        app: Dash app instance
        llm_client: OpenAI LLM client for metrics analysis
    """
    
    @callback(
        Output('metrics-discovery-content', 'children'),
        Input('existing-metrics-discovery-btn', 'n_clicks'),
        State('existing-dashboard-config', 'data'),
        prevent_initial_call=True
    )
    def update_metrics_discovery_panel(n_clicks, dashboard_config):
        """Analyze dashboard metrics and update side panel"""
        
        if not n_clicks:
            return no_update
        
        # Check if dashboard is loaded
        if not dashboard_config:
            return dbc.Alert("⚠️ No dashboard loaded", color="warning")
        
        try:
            # Check if LLM client is available
            if not llm_client:
                return dbc.Alert("⚠️ LLM client not available for metrics analysis", color="warning")
            
            # Analyze dashboard metrics
            display_component, analysis_text = analyze_dashboard_metrics(dashboard_config, llm_client)
            return display_component
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return dbc.Alert([
                html.Strong("❌ Error analyzing metrics"),
                html.Br(),
                html.Small(f"Error: {str(e)}")
            ], color="danger")
    
    
    print("✅ Metrics discovery callbacks registered successfully")

