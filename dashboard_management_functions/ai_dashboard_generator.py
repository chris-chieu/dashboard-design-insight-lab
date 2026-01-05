"""
AI-Powered Dashboard Generator Module

This module contains the logic for automatically generating dashboards
based on natural language prompts using an LLM.

"""

import json
import random
import string
import time
import sys
import mlflow
from dash import html
import dash_bootstrap_components as dbc
from widgets import (
    create_table_widget,
    create_filter_widget,
    create_bar_chart_widget,
    create_line_chart_widget,
    create_pivot_widget,
    create_counter_widget,
    create_pie_chart_widget
)

# Prevent direct execution
if __name__ == "__main__":
    print("=" * 70)
    print("❌ ERROR: This is a module, not a standalone application!")
    print("=" * 70)
    print("")
    print("This file (ai_dashboard_generator.py) is a module that should be")
    print("imported by app.py, not run directly.")
    print("")
    print("To run the application, execute:")
    print("  python app.py")
    print("")
    print("=" * 70)
    sys.exit(1)


@mlflow.trace
def generate_dashboard_background(
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
    infusion_data=None
):
    """
    Background function to generate dashboard using AI and update progress
    
    Args:
        session_id: Unique session identifier
        prompt: User's natural language request
        all_columns: List of available column names
        dataset_value: Dataset identifier
        dataset: Dataset configuration dict
        llm_client: OpenAI client instance
        dashboard_manager: DashboardManager instance
        ai_progress_store: Shared dict for progress tracking
        ai_results_store: Shared dict for results
        infusion_data: Optional design infusion data with uiSettings
        
    Returns:
        dict: Status and dashboard details
    """
    
    try:
        # Add MLflow trace metadata
        print(f"🔍 MLflow Trace: Starting dashboard generation for session {session_id}")
        mlflow.update_current_trace(
            metadata={
                "mlflow.trace.session": session_id,
                "operation": "ai_dashboard_generation",
                "dataset": dataset_value,
                "num_columns": len(all_columns),
                "user_prompt": prompt[:200] if len(prompt) > 200 else prompt
            }
        )
        print(f"✅ MLflow Trace: Metadata updated")
        
        # Small delay to ensure UI is ready
        time.sleep(0.2)
        
        # Step 1: Analyzing request
        ai_progress_store[session_id] = {
            'status': 'running',
            'steps': ['🔍 Step 1: Analyzing your request with AI...'],
            'reasoning': '',
            'widget_details': []
        }
        time.sleep(0.3)
        
        # Build LLM prompt to analyze user request and suggest widgets
        # Format columns with types if available
        if columns_types and isinstance(columns_types, list):
            columns_with_types_str = ', '.join([f"{col['name']} ({col['type']})" for col in columns_types])
            columns_info = f"Available columns with types: {columns_with_types_str}\n\nIMPORTANT: Use the column types to help you decide which columns to use for aggregations, filters, and visualizations. For example, use numerical types (bigint, double, decimal) for SUM/AVG aggregations, timestamp/date types for time-based charts, and string/categorical types for grouping and filtering."
        else:
            columns_info = f"Available columns: {', '.join(all_columns)}"
        
        system_prompt = f"""You are a data dashboard expert. Based on the user's request and available columns, suggest the MOST RELEVANT widgets.

{columns_info}

Provide your response in JSON format with the following structure:
{{
    "reasoning": "Explain your thought process: what the user needs, why you selected each widget, and what insights they will provide",
    "counters": [
        {{
            "value_column": "column_to_aggregate",
            "aggregation": "COUNT (for any column) | SUM|AVG|MAX|MIN (ONLY if numerical)",
            "label": "REQUIRED: Short descriptive title (e.g., 'Total Revenue', 'Avg Resolution Time', 'Ticket Count')",
            "reason": "Why this KPI helps the user"
        }}
    ] OR [],
    
    IMPORTANT for counters: Do NOT use timestamp, date, or datetime columns as value_column for counter widgets. Only use numerical columns (bigint, double, decimal, int) or any column for COUNT aggregation.
    "filter": {{
        "column": "categorical_column_for_filtering",
        "reason": "Why this filter helps the user"
    }} OR null,
    "table": {{
        "columns": ["column1", "column2", ...],
        "reason": "Why this table helps the user"
    }} OR null,
    "bar_chart": {{
        "x_column": "column_to_aggregate",
        "y_column": "categorical_grouping_column",
        "aggregation": "COUNT (for any column) | SUM|AVG|MAX|MIN (ONLY if x_column is numerical like revenue, amount)",
        "color_column": "optional_categorical_column_or_null",
        "title": "REQUIRED: Descriptive title (e.g., 'Tickets by Status', 'Revenue by Region')",
        "reason": "Why this chart helps the user"
    }} OR null,
    "line_chart": {{
        "x_column": "temporal_date_column",
        "y_column": "column_to_aggregate",
        "aggregation": "COUNT (for any column) | SUM|AVG|MAX|MIN (ONLY if y_column is numerical like revenue, fare_amount)",
        "time_granularity": "YEAR|QUARTER|MONTH|WEEK|DAY|HOUR",
        "color_column": "optional_categorical_column_or_null",
        "title": "REQUIRED: Descriptive title (e.g., 'Revenue Trend Over Time', 'Ticket Volume by Month')",
        "reason": "Why this chart helps the user"
    }} OR null,
    "pie_chart": {{
        "value_column": "column_to_aggregate",
        "aggregation": "COUNT (for any column) | SUM|AVG|MAX|MIN (ONLY if value_column is numerical)",
        "category_column": "categorical_column_for_slices",
        "title": "REQUIRED: Descriptive title (e.g., 'Revenue by Region', 'Tickets by Priority')",
        "reason": "Why this pie chart helps the user"
    }} OR null,
    "pivot": {{
        "row_columns": ["dimension1", "dimension2"],
        "value_column": "column_to_aggregate",
        "aggregation": "COUNT (for any column) | SUM|AVG|MAX|MIN (ONLY for numerical columns like revenue, amount, price)",
        "title": "REQUIRED: Descriptive title (e.g., 'Sales Analysis by Region and Product', 'Ticket Breakdown')",
        "reason": "Why this pivot helps the user"
    }} OR null,
    "dashboard_name": "descriptive name for dashboard"
}}

WIDGET SELECTION GUIDELINES:
- ONLY include widgets that are relevant to the user's request
- Set unused widgets to null (or empty array for counters)
- Counter: Use for key metrics/KPIs (single aggregated values like total revenue, average resolution time, ticket count)
- Filter: Use for interactive filtering by categorical dimensions (status, priority, category, region)
- Table: Use for detailed record-level data viewing
- Bar Chart: Use for comparing categories or groups
- Line Chart: Use for trends over time or temporal analysis
- Pie Chart: Use for showing proportions/distribution across categories (market share, regional breakdown, status distribution)
- Pivot: Use for multi-dimensional aggregation and business intelligence reporting

WIDGET RULES:

Counter (KPI):
- value_column: Column to aggregate for the KPI
- aggregation: COUNT (for any column) | SUM|AVG|MAX|MIN (ONLY for numerical columns)
- label: REQUIRED - Generate a clear, business-friendly title that describes what the KPI shows
  * Good examples: "Total Revenue", "Avg Resolution Time", "Open Tickets", "Customer Count", "Success Rate"
  * Bad examples: "count(ticket_id)", "revenue", "avg(time)" - these are too technical
  * Format: Title Case, no underscores, human-readable
- Use counters to highlight important metrics at the top of dashboards
- You can include multiple counters (2-4) for different KPIs
- ALWAYS provide a meaningful label for each counter

Filter:
- column: Select a categorical/dimension column that users would want to filter by (status, priority, country, category)
- Filters enhance interactivity and allow users to drill down into data

Table:
- columns: Select the most relevant columns for the user's needs

CRITICAL AGGREGATION RULES (applies to ALL widgets):
⚠️ NUMERICAL columns (revenue, amount, count, quantity, price, age, duration) can use: COUNT, SUM, AVG, MAX, MIN
⚠️ TEXT/CATEGORICAL columns (status, priority, country, name, type, resolution_type, sla_status) can ONLY use: COUNT
⚠️ Examples of TEXT columns that look numeric but are categorical: "SLA Violated", "High Priority", "Resolved", "ticket_id"

Bar charts:
- x_column: Column to aggregate (revenue, amount, tickets)
- y_column: CATEGORICAL/DIMENSION column for grouping (status, priority, country)
- aggregation: 
  * If x_column is TEXT/CATEGORICAL (ticket_id, status, resolution, sla_type): use ONLY "COUNT"
  * If x_column is NUMERICAL (revenue, amount, quantity, price): use COUNT, SUM, AVG, MAX, MIN

Line charts:
- x_column: TEMPORAL/DATE column (created_time, date, timestamp, pickup_datetime)
- y_column: Column to aggregate
- aggregation: 
  * If y_column is TEXT/CATEGORICAL (ticket_id, status, resolution): use ONLY "COUNT"
  * If y_column is NUMERICAL (revenue, fare_amount, trip_distance): use SUM, AVG, MAX, MIN
- time_granularity: MONTH (default), DAY (detailed), YEAR (long-term)

Pie charts:
- value_column: Column to aggregate for slice sizes
- category_column: CATEGORICAL column for pie slices (status, country, priority, region)
- aggregation:
  * If value_column is TEXT/CATEGORICAL (ticket_id, status): use ONLY "COUNT"
  * If value_column is NUMERICAL (revenue, amount, fare_amount): use COUNT, SUM, AVG, MAX, MIN
- title: REQUIRED - Generate a clear title like "Revenue by Region", "Tickets by Status", "Market Share by Product"
- Perfect for showing proportions and distributions (limited to ~8 categories for readability)

Pivot:
- row_columns: One or more CATEGORICAL dimensions ["priority", "status", "region"]
- value_column: Column to aggregate
- aggregation: 
  * If value_column is TEXT/CATEGORICAL (ticket_id, status, sla_status): use ONLY "COUNT"
  * If value_column is NUMERICAL (revenue, amount, fare_amount, trip_count): use COUNT, SUM, AVG, MAX, MIN
  * NEVER use AVG/SUM/MAX/MIN on columns with text values like "SLA Violated", "High", "Resolved"

Counter:
- value_column: Column to aggregate
- aggregation:
  * If value_column is TEXT/CATEGORICAL (ticket_id, status): use ONLY "COUNT"
  * If value_column is NUMERICAL (revenue, resolution_time, amount): use COUNT, SUM, AVG, MAX, MIN
- Perfect for top-level KPIs

EXAMPLES:
- "Customer support manager": 
  counters[{{"value_column": "ticket_id", "aggregation": "COUNT", "label": "Total Tickets"}}, 
           {{"value_column": "resolution_time", "aggregation": "AVG", "label": "Avg Resolution Time"}}]
  + filter + table + bar_chart + line_chart
  
- "Revenue trend over time": 
  counters[{{"value_column": "revenue", "aggregation": "SUM", "label": "Total Revenue"}}, 
           {{"value_column": "order_id", "aggregation": "COUNT", "label": "Order Count"}}]
  + line_chart(SUM of revenue over time)
  
- "Ticket counts by priority": 
  counters[{{"value_column": "ticket_id", "aggregation": "COUNT", "label": "Open Tickets"}}]
  + filter + bar_chart(COUNT of ticket_id by priority)
  
- "Market share by region":
  counters[{{"value_column": "revenue", "aggregation": "SUM", "label": "Total Revenue"}}]
  + pie_chart(value: SUM revenue, category: region, title: "Revenue by Region")
  + table
  
- "SLA violations by priority": 
  counters[{{"value_column": "ticket_id", "aggregation": "COUNT", "label": "Total Tickets"}}] 
  + pivot(row: priority, value: COUNT of ticket_id) - NOT AVG of "SLA Violated"!"""
        
        # Update progress: calling LLM
        ai_progress_store[session_id]['steps'].append('🤖 Step 2: Calling LLM to analyze requirements...')
        time.sleep(0.3)
        
        response = llm_client.chat.completions.create(
            model="databricks-gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        
        # Parse AI response
        ai_suggestion = json.loads(response.choices[0].message.content)
        
        # Extract reasoning
        reasoning = ai_suggestion.get('reasoning', 'AI is building your dashboard based on your requirements.')
        
        # Log to MLflow trace as tags
        suggested_widgets = []
        if ai_suggestion.get('counters'): suggested_widgets.append('counters')
        suggested_widgets.extend([k for k in ['filter', 'table', 'bar_chart', 'line_chart', 'pie_chart', 'pivot'] if ai_suggestion.get(k)])
        
        mlflow.set_tags({
            "ai_reasoning": reasoning[:250],
            "widgets_suggested": ", ".join(suggested_widgets)
        })
        
        # Update progress: received AI response
        ai_progress_store[session_id]['steps'].append('✅ Step 3: Received AI analysis')
        ai_progress_store[session_id]['reasoning'] = reasoning
        time.sleep(0.4)
        
        # Step 4: Build dashboard layout
        layout = []
        current_y = 0
        chart_count = 0
        widget_list = []
        table_widget_data = None  # Store table widget to add at the end
        
        # Step 4A: Create filter widget if suggested (top left position at x=0)
        filter_config = ai_suggestion.get('filter')
        has_filter = False
        if filter_config and isinstance(filter_config, dict):
            ai_progress_store[session_id]['steps'].append('🔍 Step 4: Creating filter widget...')
            if filter_config.get('reason'):
                ai_progress_store[session_id]['widget_details'].append(f"🔍 Filter: {filter_config.get('reason')}")
            time.sleep(0.3)
            
            filter_column = filter_config.get('column', all_columns[0])
            filter_widget = create_filter_widget(
                filter_column=filter_column,
                dataset_name=dataset['name']
            )
            layout.append({
                "widget": filter_widget,
                "position": {"x": 0, "y": 0, "width": 2, "height": 2}
            })
            has_filter = True
            widget_list.append(f"🔍 Filter on {filter_column}")
            ai_progress_store[session_id]['steps'].append(f'✅ Filter widget created for {filter_column}')
        
        # Step 5: Create counter widgets if suggested (KPIs in 2x2 grid starting at x=2, y=0)
        counters_config = ai_suggestion.get('counters', [])
        counter_rows = 0
        if counters_config and isinstance(counters_config, list) and len(counters_config) > 0:
            ai_progress_store[session_id]['steps'].append(f'📊 Step 5: Creating {len(counters_config)} counter widget(s)...')
            time.sleep(0.3)
            
            counter_width = 2  # Each counter takes 2 units of width
            counter_height = 2  # Each counter takes 2 units of height
            for idx, counter in enumerate(counters_config):
                if counter.get('reason'):
                    ai_progress_store[session_id]['widget_details'].append(f"📊 Counter: {counter.get('reason')}")
                
                counter_widget = create_counter_widget(
                    value_column=counter.get('value_column', all_columns[0]),
                    aggregation=counter.get('aggregation', 'COUNT'),
                    dataset_name=dataset['name'],
                    title=counter.get('label', None)
                )
                
                # Position counters in 2x2 grid starting at x=2, y=0 (leaving left for filter)
                # Pattern: (2,0), (4,0), (2,2), (4,2), (2,4), (4,4), etc.
                x_position = 2 + (idx % 2) * counter_width  # Alternates between x=2 and x=4
                y_position = (idx // 2) * counter_height  # New row every 2 counters
                
                layout.append({
                    "widget": counter_widget,
                    "position": {
                        "x": x_position,
                        "y": y_position,
                        "width": counter_width,
                        "height": counter_height
                    }
                })
                
                label = counter.get('label', f"{counter.get('aggregation')} of {counter.get('value_column')}")
                widget_list.append(f"📊 Counter: {label}")
                ai_progress_store[session_id]['steps'].append(f'✅ Counter created: {label}')
            
            # Calculate how many rows of counters we have
            counter_rows = (len(counters_config) - 1) // 2 + 1
            time.sleep(0.3)
        
        # Update current_y to account for filter and counter area (whichever is taller)
        # Filter is 2 units tall (if exists), counters are counter_rows * 2 units tall
        filter_height = 2 if has_filter else 0
        counter_height_total = counter_rows * 2
        current_y = max(filter_height, counter_height_total)
        
        # Step 6: Prepare table widget if suggested (will be added at the bottom)
        table_config = ai_suggestion.get('table')
        if table_config and isinstance(table_config, dict):
            ai_progress_store[session_id]['steps'].append('📋 Step 6: Preparing table widget...')
            if table_config.get('reason'):
                ai_progress_store[session_id]['widget_details'].append(f"📋 Table: {table_config.get('reason')}")
            time.sleep(0.3)
            
            table_columns = table_config.get('columns', all_columns[:5])
            table_widget = create_table_widget(
                title="Data Overview",
                visible_columns=table_columns,
                dataset_name=dataset['name'],
                all_columns=all_columns
            )
            # Store table widget data to add at the bottom later
            table_widget_data = {
                "widget": table_widget,
                "columns_count": len(table_columns)
            }
            widget_list.append(f"📋 Table with {len(table_columns)} columns")
            ai_progress_store[session_id]['steps'].append(f'✅ Table widget prepared with {len(table_columns)} columns')
        
        # Step 8: Create bar chart widget if suggested
        bar_config = ai_suggestion.get('bar_chart')
        if bar_config and isinstance(bar_config, dict):
            ai_progress_store[session_id]['steps'].append('📊 Step 7: Creating bar chart widget...')
            if bar_config.get('reason'):
                ai_progress_store[session_id]['widget_details'].append(f"📊 Bar Chart: {bar_config.get('reason')}")
            time.sleep(0.3)
            
            # Handle color_column - ensure it's None if null or invalid
            color_col = bar_config.get('color_column')
            if color_col == "null" or not color_col:
                color_col = None
            
            bar_chart_widget = create_bar_chart_widget(
                x_column=bar_config.get('x_column', all_columns[0]),
                y_column=bar_config.get('y_column', all_columns[1]),
                y_aggregation=bar_config.get('aggregation', 'COUNT'),
                color_column=color_col,
                dataset_name=dataset['name'],
                title=bar_config.get('title', None)
            )
            layout.append({
                "widget": bar_chart_widget,
                "position": {
                    "x": (chart_count % 2) * 3,
                    "y": current_y + (chart_count // 2) * 6,
                    "width": 3,
                    "height": 6
                }
            })
            chart_count += 1
            widget_list.append(f"📊 Bar chart: {bar_config.get('aggregation', 'COUNT')} of {bar_config.get('x_column', 'N/A')} by {bar_config.get('y_column', 'N/A')}")
            ai_progress_store[session_id]['steps'].append(f"✅ Bar chart created: {bar_config.get('aggregation', 'COUNT')} by {bar_config.get('y_column', 'N/A')}")
        
        # Step 9: Create line chart widget if suggested
        line_config = ai_suggestion.get('line_chart')
        if line_config and isinstance(line_config, dict):
            ai_progress_store[session_id]['steps'].append('📈 Step 8: Creating line chart widget...')
            if line_config.get('reason'):
                ai_progress_store[session_id]['widget_details'].append(f"📈 Line Chart: {line_config.get('reason')}")
            time.sleep(0.3)
            
            # Handle color_column - ensure it's None if null or invalid
            color_col = line_config.get('color_column')
            if color_col == "null" or not color_col:
                color_col = None
            
            line_chart_widget = create_line_chart_widget(
                x_column=line_config.get('x_column', all_columns[0]),
                y_column=line_config.get('y_column', all_columns[1]),
                y_aggregation=line_config.get('aggregation', 'COUNT'),
                time_granularity=line_config.get('time_granularity', 'MONTH'),
                color_column=color_col,
                dataset_name=dataset['name'],
                title=line_config.get('title', None)
            )
            layout.append({
                "widget": line_chart_widget,
                "position": {
                    "x": (chart_count % 2) * 3,
                    "y": current_y + (chart_count // 2) * 6,
                    "width": 3,
                    "height": 6
                }
            })
            chart_count += 1
            widget_list.append(f"📈 Line chart: {line_config.get('aggregation', 'COUNT')} of {line_config.get('y_column', 'N/A')} over {line_config.get('x_column', 'N/A')}")
            ai_progress_store[session_id]['steps'].append(f"✅ Line chart created: {line_config.get('aggregation', 'COUNT')} over time")
        
        # Step 10: Create pie chart widget if suggested
        pie_config = ai_suggestion.get('pie_chart')
        if pie_config and isinstance(pie_config, dict):
            ai_progress_store[session_id]['steps'].append('🥧 Step 9: Creating pie chart widget...')
            if pie_config.get('reason'):
                ai_progress_store[session_id]['widget_details'].append(f"🥧 Pie Chart: {pie_config.get('reason')}")
            time.sleep(0.3)
            
            pie_chart_widget = create_pie_chart_widget(
                value_column=pie_config.get('value_column', all_columns[0]),
                aggregation=pie_config.get('aggregation', 'COUNT'),
                category_column=pie_config.get('category_column', all_columns[1]),
                dataset_name=dataset['name'],
                title=pie_config.get('title', None)
            )
            layout.append({
                "widget": pie_chart_widget,
                "position": {
                    "x": (chart_count % 2) * 3,
                    "y": current_y + (chart_count // 2) * 6,
                    "width": 3,
                    "height": 6
                }
            })
            chart_count += 1
            widget_list.append(f"🥧 Pie chart: {pie_config.get('aggregation', 'COUNT')} of {pie_config.get('value_column', 'N/A')} by {pie_config.get('category_column', 'N/A')}")
            ai_progress_store[session_id]['steps'].append(f"✅ Pie chart created: {pie_config.get('title', 'distribution')}")
        
        # Step 11: Create pivot widget if suggested
        pivot_config = ai_suggestion.get('pivot')
        if pivot_config and isinstance(pivot_config, dict):
            ai_progress_store[session_id]['steps'].append('🔢 Step 10: Creating pivot table widget...')
            if pivot_config.get('reason'):
                ai_progress_store[session_id]['widget_details'].append(f"🔢 Pivot: {pivot_config.get('reason')}")
            time.sleep(0.3)
            
            pivot_widget = create_pivot_widget(
                row_columns=pivot_config.get('row_columns', [all_columns[0]]),
                value_column=pivot_config.get('value_column', all_columns[1]),
                aggregation=pivot_config.get('aggregation', 'SUM'),
                dataset_name=dataset['name'],
                title=pivot_config.get('title', None)
            )
            layout.append({
                "widget": pivot_widget,
                "position": {
                    "x": (chart_count % 2) * 3,
                    "y": current_y + (chart_count // 2) * 6,
                    "width": 3,
                    "height": 6
                }
            })
            chart_count += 1
            row_cols = ', '.join(pivot_config.get('row_columns', []))
            widget_list.append(f"🔢 Pivot: {pivot_config.get('aggregation', 'SUM')} of {pivot_config.get('value_column', 'N/A')} by {row_cols}")
            ai_progress_store[session_id]['steps'].append(f"✅ Pivot created: {pivot_config.get('aggregation', 'SUM')} by {row_cols}")
        
        # Update current_y to account for all chart rows (max 2 charts per row, each 6 units tall)
        if chart_count > 0:
            current_y += ((chart_count - 1) // 2 + 1) * 6
        
        # Step 11: Add table widget at the bottom if it was prepared
        if table_widget_data:
            ai_progress_store[session_id]['steps'].append('📋 Step 11: Adding table widget at bottom...')
            layout.append({
                "widget": table_widget_data["widget"],
                "position": {"x": 0, "y": current_y, "width": 6, "height": 8}
            })
            ai_progress_store[session_id]['steps'].append(f'✅ Table widget added at bottom with {table_widget_data["columns_count"]} columns')
            time.sleep(0.3)
        
        # Check if at least one widget was created
        if not layout:
            ai_progress_store[session_id]['status'] = 'error'
            ai_progress_store[session_id]['steps'].append('❌ No widgets were suggested by AI')
            ai_results_store[session_id] = {
                'status': dbc.Alert("⚠️ AI did not suggest any widgets for this request. Please try rephrasing your prompt.", color="warning"),
                'progress': "",
                'preview': "",
                'dashboard_id': None
            }
            return {
                "status": "no_widgets_suggested",
                "error": "AI did not suggest any widgets"
            }
        
        # Step 12: Build dashboard configuration
        ai_progress_store[session_id]['steps'].append('🔧 Step 12: Building dashboard configuration...')
        time.sleep(0.3)
        
        dashboard_config = {
            "datasets": [dataset],
            "pages": [{
                "name": "ab333341",
                "displayName": "Overview",
                "layout": layout,
                "pageType": "PAGE_TYPE_CANVAS"
            }]
        }
        
        # Add uiSettings from design infusion if available
        if infusion_data and isinstance(infusion_data, dict) and 'uiSettings' in infusion_data:
            dashboard_config['uiSettings'] = infusion_data['uiSettings']
            ai_progress_store[session_id]['steps'].append('🎨 Applied design infusion theme')
            time.sleep(0.2)
        
        # Step 13: Generate random dashboard name or use AI suggestion
        dashboard_name = ai_suggestion.get('dashboard_name', 'AI Generated Dashboard')
        # Add random suffix to ensure uniqueness
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        dashboard_name = f"{dashboard_name} ({random_suffix})"
        
        ai_progress_store[session_id]['steps'].append(f'📝 Dashboard name: {dashboard_name}')
        time.sleep(0.3)
        
        # Step 14: Deploy dashboard
        ai_progress_store[session_id]['steps'].append('🚀 Step 13: Deploying dashboard to Databricks...')
        time.sleep(0.3)
        
        dashboard_id = dashboard_manager.create_dashboard(dashboard_config, dashboard_name)
        embed_url = dashboard_manager.get_embed_url(dashboard_id)
        
        ai_progress_store[session_id]['steps'].append('✅ Step 14: Dashboard deployed successfully!')
        
        # Create preview
        preview_card = dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H4(f"✅ AI Generated Dashboard: {dashboard_name}"),
                        html.Small(f"Dashboard ID: {dashboard_id}", className="text-muted")
                    ], width=7),
                    dbc.Col([
                        dbc.Button("🎨 Infusion", id="apply-infusion-btn", color="primary", size="sm", className="me-2"),
                        dbc.Button("🗑️ Delete Dashboard", id="delete-dashboard-btn", color="danger", size="sm")
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
                )
            ])
        ])
        
        # Build success message
        status_items = [
            html.Strong("🎉 Dashboard generated successfully!"),
            html.Br(),
            html.Small(f"Created: {dashboard_name}"),
            html.Br(),
            html.Small(f"Widgets included: {len(widget_list)}")
        ]
        
        for widget_desc in widget_list:
            status_items.extend([
                html.Br(),
                html.Small(widget_desc)
            ])
        
        success_alert = dbc.Alert(status_items, color="success", dismissable=True)
        
        # Mark as complete and store results
        ai_progress_store[session_id]['status'] = 'completed'
        ai_results_store[session_id] = {
            'status': success_alert,
            'progress': "",
            'preview': preview_card,
            'dashboard_id': dashboard_id,
            'dashboard_config': dashboard_config,
            'dashboard_name': dashboard_name
        }
        
        # Log final results to MLflow trace
        mlflow.set_tags({
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard_name,
            "widgets_created": len(widget_list),
            "widget_list": ", ".join(widget_list),
            "status": "success"
        })
        
        # Return meaningful output for MLflow trace
        return {
            "status": "success",
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard_name,
            "reasoning": reasoning,
            "widgets_created": widget_list,
            "ai_suggestion": ai_suggestion
        }
        
    except json.JSONDecodeError as e:
        ai_progress_store[session_id]['status'] = 'error'
        ai_progress_store[session_id]['steps'].append(f'❌ Failed to parse AI response: {str(e)}')
        error_msg = dbc.Alert([
            html.Strong("❌ Failed to parse AI response"),
            html.Br(),
            html.Small(f"Error: {str(e)}")
        ], color="danger")
        ai_results_store[session_id] = {
            'status': error_msg,
            'progress': "",
            'preview': "",
            'dashboard_id': None
        }
        # Log error to MLflow trace
        mlflow.set_tags({
            "status": "failed_json_parse",
            "error_type": "JSONDecodeError",
            "error_message": str(e)[:200]
        })
        
        return {
            "status": "failed",
            "error_type": "JSONDecodeError",
            "error_message": str(e)
        }
        
    except Exception as e:
        ai_progress_store[session_id]['status'] = 'error'
        ai_progress_store[session_id]['steps'].append(f'❌ Error: {str(e)}')
        error_msg = dbc.Alert([
            html.Strong("❌ Failed to generate dashboard"),
            html.Br(),
            html.Small(f"Error: {str(e)}")
        ], color="danger")
        ai_results_store[session_id] = {
            'status': error_msg,
            'progress': "",
            'preview': "",
            'dashboard_id': None
        }
        # Log error to MLflow trace
        mlflow.set_tags({
            "status": "failed",
            "error_type": type(e).__name__,
            "error_message": str(e)[:200]
        })
        
        return {
            "status": "failed",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }

