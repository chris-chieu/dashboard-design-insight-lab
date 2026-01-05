# Dashboard Design Insight Lab

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

🎨 **Design Infusion**: Customize dashboard appearance by:
- Uploading a reference image to extract colors and fonts
- Describing a style (e.g., "Corporate specialised in tech style")

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
│   │   └── new_dashboard_page.py             # New dashboard creation UI
│   └── existing_dashboard/
│       └── existing_dashboard_page.py        # Dashboard retrieval & management
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
├── datasets.py                                # Dataset configurations
├── dataset_filter.py                          # Dataset filtering utilities
├── requirements.txt                           # Python dependencies
└── README.md                                  # This file
```

## Workflow

### Create New Dashboard with AI

1. **Select Dataset** → Choose from available datasets (e.g., Customer Support, NYC Taxi)

2. **Extract Columns with LLM** → AI analyzes SQL query and extracts available columns

3. **Generate Dashboard with AI** → Enter a natural language prompt:
   - *Example*: "I am a customer support manager, create me a dashboard with KPIs relevant to my domain"
   - *Example*: "Create a sales dashboard with revenue trends and top products"

4. **AI Processing** → The AI automatically:
   - Selects relevant widgets (tables, charts, filters, counters)
   - Chooses appropriate columns and aggregations
   - Creates visualizations
   - Generates intelligent layouts
   - Deploys to Databricks

5. **Design Infusion** (Optional) → Customize the dashboard appearance:
   - Upload an image to extract colors and fonts
   - OR describe a style (e.g., "corporate blue theme", "Van Gogh style")

6. **View Dashboard** → Dashboard displays in an embedded iframe with your custom design

### Manage Existing Dashboards

1. **Enter Dashboard ID** → Input the ID of an existing dashboard

2. **Retrieve Dashboard** → View the dashboard in an embedded iframe

3. **Apply New Design** (Optional) → Use design infusion to update the look and feel

4. **Delete Dashboard** (Optional) → Remove the dashboard from Databricks

## Configuration

### App Configuration
Set up in the `App Configuration`: 
Edit > Configure Resources > User Authorization > Add Scope > Manage your model serving endpoints
(More information [here](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth#add-scopes-to-an-app))

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

3. Deploy using Databricks Apps UI or CLI

## Key Components

### DashboardManager
Unified interface for all dashboard operations:
- Create and publish dashboards
- Update existing dashboards
- Generate embed URLs
- Delete dashboards

### AI Dashboard Generator
Intelligent dashboard creation:
- Natural language understanding
- Automatic widget selection
- Column and aggregation inference
- Layout optimization

### Design Infusion
Customize dashboard appearance:
- **Image-based**: Upload a reference image to extract design elements
- **Prompt-based**: Describe desired style for AI generation
- Extracts: background colors, font colors, visualization colors, borders, fonts

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
