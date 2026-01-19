# Intelligent Embedded Dashboard

An AI-powered Dash application that automatically generates Databricks AI/BI dashboards using LLMs. Create beautiful, data-driven dashboards with natural language prompts.

## Problem Statement

Business users often depend on technical teams to create dashboards, creating bottlenecks that slow decision-making and limit agility. This app **empowers non-technical users** to independently create and manage their own dashboards using natural language and domain expertise—**no coding or technical knowledge required**.

---

**🌟 Open Source Project** 

This project is open source. Contributions, feedback, and suggestions are welcome!

## Features

✨ **AI-Powered Dashboard Generation**: Describe your dashboard needs in natural language, and the AI will automatically:
- Select appropriate widget types (tables, charts, filters, counters, pivots)
- Choose relevant columns and aggregations
- Create optimized visualizations
- Apply intelligent layouts
- Support for Unity Catalog tables and Databricks Metric Views

🎨 **Design Infusion**: Customize dashboard appearance by:
- Uploading a reference image to extract colors and fonts
- Describing a style (e.g., "Corporate specialised in tech style")

🤖 **Databricks Genie AI Integration**: Enable intelligent natural language querying:
- Toggle Genie Space on/off for any dashboard
- Empower users to ask questions in natural language
- Get AI-powered insights from your dashboard data

📈 **Metrics Discovery**: Automatically analyze existing dashboards to:
- Discover and list all metrics/KPIs used
- Extract widget types and visualizations
- Understand data sources and aggregations
- Get insights into dashboard structure

📊 **Unity Catalog Integration**:
- Browse and select tables directly from Unity Catalog
- View table and column descriptions
- Search through available columns
- Automatic support for Metric Views with measure/dimension detection

📊 **Supported Widgets**:
- Tables with customizable columns
- Bar charts with aggregations
- Line charts for time series
- Pie charts for distributions
- Counter KPIs
- Pivot tables
- Interactive filters

## Project Structure

```
intelligent-embedded-dashboard/
├── app.py                                    # Main Dash application (includes configuration)
│
├── dashboard_management_functions/           # All dashboard-related modules
│   ├── dashboard_manager.py                  # Unified dashboard operations
│   ├── dashboard_creation.py                 # Dashboard creation logic
│   ├── dashboard_deployment.py               # Publishing and embed URLs
│   ├── dashboard_deletion.py                 # Deletion operations
│   ├── dashboard_catalog_operations.py       # Unity Catalog persistence
│   ├── ai_dashboard_generator.py             # AI-powered generation
│   ├── manual_dashboard_config.py            # Manual configuration callbacks
│   ├── design_infusion.py                    # Design extraction & generation
│   └── monitor_dashboard_traces.py           # MLflow monitoring
│
├── pages/                                     # Page layouts and callbacks
│   ├── new_dashboard/
│   │   ├── new_dashboard_page.py             # New dashboard creation UI
│   │   └── new_dashboard_infusion_callbacks.py  # Design infusion for new dashboards
│   └── existing_dashboard/
│       ├── existing_dashboard_page.py        # Dashboard retrieval & management
│       ├── existing_dashboard_infusion_callbacks.py  # Design infusion for existing dashboards
│       ├── metrics_discovery_callbacks.py    # Metrics discovery feature
│       └── genie_space_callbacks.py          # Genie AI toggle feature
│
├── widgets/                                   # Widget generation modules
│   ├── table_widget.py                       # Table widgets
│   ├── filter_widget.py                      # Filter widgets
│   ├── bar_chart_widget.py                   # Bar chart widgets
│   ├── line_chart_widget.py                  # Line chart widgets
│   ├── pivot_widget.py                       # Pivot table widgets
│   ├── counter.py                            # Counter KPI widgets
│   └── pie_chart.py                          # Pie chart widgets
│
├── utils/                                     # Utility modules
│   ├── table_inspector.py                    # Unity Catalog table inspection & metadata
│   └── query_permission_checker.py           # User permission validation
│
├── example_datasets/                          # Example datasets for testing
│   └── datasets.py                           # Sample dataset configurations
│
├── assets/                                    # Static assets (CSS, etc.)
├── dataset_filter.py                          # Dataset filtering utilities
├── requirements.txt                           # Python dependencies
├── app.yaml                                   # Databricks Apps configuration
└── README.md                                  # This file
```

## Workflow

### Create New Dashboard with AI

1. **Select Unity Catalog Table** → Browse and select from Unity Catalog:
   - View table and column descriptions
   - Search through available columns
   - See column types (including measure/dimension for Metric Views)
   - Automatic detection of Metric Views

2. **Generate Dashboard with AI** → Enter a natural language prompt:
   - *Example*: "I am a customer support manager, create me a dashboard with KPIs relevant to my domain"
   - *Example*: "Create a sales dashboard with revenue trends and top products"

3. **AI Processing** → The AI automatically:
   - Selects relevant widgets (tables, charts, filters, counters)
   - Chooses appropriate columns and aggregations
   - Creates visualizations with proper handling of Metric Views
   - Generates intelligent layouts
   - Deploys to Databricks

4. **Design Infusion** (Optional) → Customize the dashboard appearance:
   - Upload an image to extract colors and fonts
   - OR describe a style (e.g., "corporate blue theme", "Van Gogh style")

5. **Enable Genie AI** (Optional) → Toggle on Databricks Genie Space:
   - Allow natural language queries on your dashboard
   - Empower users to ask questions in plain English

6. **View Dashboard** → Dashboard displays in an embedded iframe with:
   - Clickable URL link to open in Databricks
   - Dashboard ID for reference
   - Genie toggle to enable/disable AI querying
   - Your custom design (if applied)

### Manage Existing Dashboards

1. **Enter Dashboard ID** → Input the ID of an existing dashboard

2. **Retrieve Dashboard** → View the dashboard in an embedded iframe with:
   - Clickable URL link to open in Databricks
   - Dashboard name and ID
   - Current Genie Space status

3. **Metrics Discovery** → Automatically analyze the dashboard:
   - View all metrics and KPIs used
   - See widget types and their configurations
   - Understand data sources and aggregations
   - Export metrics list for documentation

4. **Genie AI Toggle** → Enable or disable Databricks Genie Space:
   - Toggle on to allow natural language queries
   - Toggle off to disable AI querying
   - Changes reflect immediately in the dashboard view

5. **Apply New Design** (Optional) → Use design infusion to update the look and feel

6. **Delete Dashboard** (Optional) → Remove the dashboard from Databricks

## Key Features in Detail

### 🤖 Databricks Genie AI Integration

**What is Genie?**
Databricks Genie Space is an AI-powered conversational interface that allows users to ask questions about their data in natural language.

**How to Use:**
- Enable Genie toggle when creating a new dashboard or viewing an existing one
- Users can then ask questions like:
  - "What were the top 5 products by revenue last quarter?"
  - "Show me the trend of customer complaints over time"
  - "Which region has the highest sales growth?"
- Genie AI interprets the question and generates appropriate queries and visualizations

**Benefits:**
- Democratizes data access for non-technical users
- Reduces dependency on SQL knowledge
- Enables ad-hoc analysis without dashboard modifications

### 📈 Metrics Discovery

**What is Metrics Discovery?**
An intelligent analysis feature that automatically examines existing dashboards to extract and catalog all metrics, KPIs, and visualizations.

**What It Discovers:**
- **Metrics & KPIs**: All numerical measures and aggregations
- **Widget Types**: Tables, charts, filters, counters, etc.
- **Data Sources**: Unity Catalog tables and datasets used
- **Aggregations**: SUM, AVG, COUNT, and other calculations
- **Dimensions**: Grouping and filtering columns

**Use Cases:**
- **Documentation**: Auto-generate dashboard documentation
- **Audit**: Understand what metrics are being tracked
- **Migration**: Identify metrics before recreating dashboards
- **Discovery**: Learn from existing dashboards to create new ones

**How to Use:**
1. Navigate to "Existing Dashboard" page
2. Enter a dashboard ID and retrieve it
3. Click "Discover Metrics" button
4. View the comprehensive analysis in the side panel

### 📊 Unity Catalog & Metric Views Support

**Unity Catalog Integration:**
- Browse catalogs and schemas directly in the app
- Select tables with rich metadata (descriptions, column comments)
- Search and filter columns by name
- View column types and descriptions

**Metric Views Support:**
The app intelligently handles Databricks Metric Views:
- **Automatic Detection**: Identifies metric views vs. regular tables
- **Measure Columns**: Correctly applies `MEASURE()` function for pre-aggregated metrics
- **Dimension Columns**: Uses for grouping and filtering
- **Visual Distinction**: Measure columns are marked with an orange badge in the UI

**Benefits:**
- Seamless integration with your governed data
- No need to manually write SQL queries
- Proper handling of different table types
- Metadata-rich column selection

## Configuration

### App Configuration
Update these values in `app.py`:
```python
DATABRICKS_TOKEN = 'your_token_here'
DATABRICKS_HOST = "https://your-workspace.cloud.databricks.com"
WAREHOUSE_ID = "your_warehouse_id"
```

### MLflow Experiment Path
The app automatically logs AI generation traces to:
```python
"/Users/your-email@databricks.com/intelligent-dashboard-generator"
```

## Setup & Configuration

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Your Environment

Edit `app.py` (lines 64-70) with your Databricks credentials and settings:

```python
# Configuration - Update these values for your environment
DATABRICKS_TOKEN = '<insert your token here>'
DATABRICKS_HOST = "https://your-workspace.cloud.databricks.com"
WAREHOUSE_ID = "<your_warehouse_id>"
UNITY_CATALOG = "<your_catalog_name>"
UNITY_SCHEMA = "<your_schema_name>"
LLM_MODEL = "databricks-gpt-5"
VISION_MODEL = "databricks-gpt-5"
```

**Important Configuration Values:**

| Variable | Description | How to Get |
|----------|-------------|------------|
| `DATABRICKS_TOKEN` | Personal Access Token | User Settings > Developer > Access Tokens > Generate New Token |
| `DATABRICKS_HOST` | Workspace URL | Copy from your browser address bar |
| `WAREHOUSE_ID` | SQL Warehouse ID | SQL Warehouses > Select warehouse > Copy ID from URL |
| `UNITY_CATALOG` | Catalog name | The catalog containing your tables |
| `UNITY_SCHEMA` | Schema name | The schema containing your tables |
| `LLM_MODEL` | LLM model for dashboard generation | Default: `databricks-gpt-5` |
| `VISION_MODEL` | Vision model for design infusion | Default: `databricks-gpt-5` |

## Running the App

### Local Development
```bash
python app.py
```

The app will be available at `http://0.0.0.0:8050`

### Deploy to Databricks Apps

1. Update configuration in `app.py` with your credentials (lines 64-70)

2. Ensure `app.yaml` is configured:
```yaml
command: ["python", "app.py"]
```

3. **Configure App Permissions** (Required):
   - Navigate to your deployed app
   - Click **Edit** > **Configure Resources** > **User Authorization**
   - Click **Add Scope**
   - Select **"Manage your model serving endpoints"**
   - Save configuration
   
   📖 [More information on App Configuration](https://docs.databricks.com/en/dev-tools/auth/oauth-m2m.html)

4. Deploy using Databricks Apps UI or CLI

## Permissions Model

### Service Principal vs. User Permissions

**Backend Operations (Service Principal):**
The app runs with the **Service Principal's credentials** for backend operations:
- ✅ Creating/updating/deleting dashboards (Lakeview API)
- ✅ Calling LLM endpoints (Model Serving APIs)
- ✅ Executing SQL queries for dashboard data
- ✅ Accessing SQL Warehouse

**Required Service Principal Permissions:**
- `CAN MANAGE` on Model Serving Endpoints
- `CAN USE` on SQL Warehouse
- `CREATE` permissions on the dashboard directory (`/Shared`)
- `USE CATALOG` and `USE SCHEMA` on Unity Catalog resources

**User-Level Permissions (Data Access):**
Individual users accessing the app need:
- ✅ **READ** permissions on Unity Catalog tables they want to analyze
- ✅ The app automatically checks user permissions before displaying dashboards
- ❌ Users do NOT need dashboard creation or LLM access (handled by Service Principal)

**Permission Checking:**
- When retrieving existing dashboards, the app tests if the current user can access the underlying data
- If permission checks fail, the dashboard won't be displayed to that user
- This ensures data security while allowing the Service Principal to handle infrastructure operations

## Key Components

### DashboardManager
Unified interface for all dashboard operations:
- Create and publish dashboards
- Update existing dashboards (including Genie Space configuration)
- Generate embed URLs
- Delete dashboards
- Manage dashboard permissions

### AI Dashboard Generator
Intelligent dashboard creation:
- Natural language understanding
- Automatic widget selection
- Column and aggregation inference
- Layout optimization
- Support for Unity Catalog tables and Metric Views
- Intelligent handling of measure vs. dimension columns

### Unity Catalog Integration
Browse and select tables with rich metadata:
- **Table Inspector**: Fetches table and column metadata from Unity Catalog
- **Permission Checker**: Validates user access to tables before dashboard creation
- **Metric View Support**: Automatically detects and handles Databricks Metric Views
- **Column Search**: Filter columns by name for easy selection

### Metrics Discovery
Intelligent dashboard analysis:
- Extracts all metrics and KPIs from existing dashboards
- Identifies widget types and configurations
- Maps data sources and aggregations
- Provides structured insights for documentation and audit

### Genie Space Management
Enable AI-powered natural language querying:
- Toggle Genie Space on/off for any dashboard
- Update dashboard configuration programmatically
- Refresh dashboard view to reflect Genie state
- Seamless integration with Databricks Genie AI

### Design Infusion
Customize dashboard appearance:
- **Image-based**: Upload a reference image to extract design elements
- **Prompt-based**: Describe desired style for AI generation
- **Intelligent Analysis**: AI analyzes dashboard structure before applying design
- Extracts: background colors, font colors, visualization colors, borders, fonts
- Preserves Genie Space settings during design updates

### MLflow Tracing
Monitor AI dashboard generation:
- Trace LLM reasoning and decisions
- Track token usage
- Evaluate with `RelevanceToQuery` judge
- View traces in Databricks Experiments

## Widget Layout Rules

The AI follows intelligent layout rules:
- **Counters**: 2x2 grid in top corner (2x2 size each)
- **Filters**: Top left position
- **Charts**: Maximum 2 per row
- **Tables**: Bottom layer (full width)
- **Pivots**: Treated as charts for layout purposes

## Technology Stack

- **Dash**: Web application framework
- **Dash Bootstrap Components**: UI components
- **OpenAI SDK**: LLM integration (Databricks endpoints)
- **Databricks SDK**: Workspace and Lakeview API access
- **MLflow**: Tracing and monitoring
- **Python 3.8+**

## About This Project

### Open Source & Solo Development

This is an **open source project** developed and maintained by a **single developer**. 

- **Development Status**: Active development
- **Maintenance**: Solo maintainer
- **Contributions**: Welcome! Feel free to fork, submit PRs, or open issues
- **Feedback**: Your suggestions and feedback help improve the project

### Contributing

If you'd like to contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Support

For issues or questions:
- Open an issue on the repository
- Refer to Databricks documentation:
  - [Lakeview Dashboards](https://docs.databricks.com/dashboards/lakeview.html)
  - [MLflow Tracing](https://docs.databricks.com/mlflow/tracking.html)

---

**Made with ❤️ by a solo developer**
