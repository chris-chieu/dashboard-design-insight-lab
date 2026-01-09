# Databricks notebook source
# MAGIC %md
# MAGIC # Dashboard Generation - Production Monitoring
# MAGIC 
# MAGIC This notebook monitors AI-generated dashboard quality using MLflow's built-in **`RelevanceToQuery`** judge.
# MAGIC 
# MAGIC **Features:**
# MAGIC - Fetches recent traces from MLflow experiment
# MAGIC - Evaluates trace quality using MLflow's pre-built LLM judge
# MAGIC - Returns "yes" (relevant) or "no" (not relevant) with rationale
# MAGIC - Logs evaluation results for tracking
# MAGIC - Can be scheduled as a Databricks job
# MAGIC 
# MAGIC **Reference:** [MLflow RelevanceToQuery Judge Documentation](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_context_relevant#relevance-to-query)
# MAGIC 
# MAGIC **Schedule recommendation:** Run daily or after every N dashboard generations

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup and Imports

# COMMAND ----------

import mlflow
from mlflow.tracking import MlflowClient
import pandas as pd
from datetime import datetime, timedelta
import json

# Set tracking URI
mlflow.set_tracking_uri("databricks")

print("✅ MLflow configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Configuration

# COMMAND ----------

# Configuration
EXPERIMENT_NAME = "/Users/christophe.chieu@databricks.com/intelligent-dashboard-generator"
LOOKBACK_HOURS = 24  # How far back to look for traces
MAX_TRACES = 50  # Maximum number of traces to evaluate

# Get experiment
client = MlflowClient()
experiment = client.get_experiment_by_name(EXPERIMENT_NAME)

if experiment is None:
    raise ValueError(f"Experiment '{EXPERIMENT_NAME}' not found")

print(f"✅ Found experiment: {experiment.experiment_id}")
print(f"📊 Looking back: {LOOKBACK_HOURS} hours")
print(f"📈 Max traces to evaluate: {MAX_TRACES}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Import MLflow Built-in RelevanceToQuery Judge
# MAGIC 
# MAGIC Using the pre-built MLflow judge for standardized evaluation.
# MAGIC 
# MAGIC **Note:** The `name` parameter is optional and just labels this judge instance in results.
# MAGIC It doesn't need to match anything in your Databricks Experiment.
# MAGIC 
# MAGIC Reference: https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_context_relevant#relevance-to-query

# COMMAND ----------

from mlflow.genai.scorers import RelevanceToQuery

# Initialize the judge with name matching your Databricks scorer
relevance_judge = RelevanceToQuery(name="RelevanceToQuery")

# Optional: Customize the LLM model used by the judge
# relevance_judge = RelevanceToQuery(name="RelevanceToQuery", model="databricks:/your-model-name")

print("✅ MLflow RelevanceToQuery judge initialized with name='RelevanceToQuery'")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Fetch Recent Traces

# COMMAND ----------

# Calculate time window
end_time = datetime.now()
start_time = end_time - timedelta(hours=LOOKBACK_HOURS)

# Search for traces
print(f"🔍 Searching traces from {start_time} to {end_time}...")

# Get all runs from the experiment in the time window
filter_string = f"attributes.start_time >= {int(start_time.timestamp() * 1000)}"

runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    filter_string=filter_string,
    max_results=MAX_TRACES,
    order_by=["start_time DESC"]
)

print(f"✅ Found {len(runs)} runs in the last {LOOKBACK_HOURS} hours")

# Filter to only runs with traces (those from generate_dashboard_background)
traces_to_evaluate = []

for run in runs:
    # Check if this run has the tags we expect from a trace
    tags = run.data.tags
    
    if "mlflow.trace.session" in tags or "operation" in tags:
        # This is a trace from our AI dashboard generation
        traces_to_evaluate.append({
            "run_id": run.info.run_id,
            "start_time": datetime.fromtimestamp(run.info.start_time / 1000),
            "status": run.info.status,
            "tags": tags
        })

print(f"📊 Found {len(traces_to_evaluate)} dashboard generation traces to evaluate")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Evaluate Traces with MLflow RelevanceToQuery Judge

# COMMAND ----------

evaluation_results = []

for idx, trace_info in enumerate(traces_to_evaluate):
    run_id = trace_info["run_id"]
    
    print(f"\n{'='*60}")
    print(f"Evaluating trace {idx+1}/{len(traces_to_evaluate)}: {run_id}")
    print(f"{'='*60}")
    
    try:
        # Get run details
        run = client.get_run(run_id)
        
        # Extract inputs - MLflow judge expects 'question' or prompt-like key
        user_prompt = run.data.tags.get("user_prompt", "")
        
        # Skip if no user prompt (invalid trace)
        if not user_prompt:
            print("⚠️ Skipping - no user prompt found")
            continue
        
        # Extract outputs - build a response string from available data
        reasoning = run.data.tags.get("ai_reasoning", "")
        widgets_suggested = run.data.tags.get("widgets_suggested", "")
        widget_list = run.data.tags.get("widget_list", "")
        dashboard_name = run.data.tags.get("dashboard_name", "")
        status = run.data.tags.get("status", "unknown")
        
        # Build a response that describes what the AI created
        if status == "success":
            response_text = f"Created dashboard '{dashboard_name}' with widgets: {widget_list}. Reasoning: {reasoning}"
        else:
            response_text = f"Failed to create dashboard. Status: {status}"
        
        print(f"📝 User Prompt: {user_prompt[:100]}...")
        print(f"🎯 Response: {response_text[:100]}...")
        
        # Apply MLflow RelevanceToQuery judge
        # The judge expects inputs and outputs dicts
        assessment = relevance_judge(
            inputs={"question": user_prompt},
            outputs=response_text
        )
        
        # Extract feedback from assessment
        # MLflow judges return Feedback objects with 'value' and 'rationale'
        is_relevant = assessment.value  # "yes" or "no"
        rationale = assessment.rationale
        
        # Convert to numeric score for easier analysis (yes=5, no=1)
        numeric_score = 5 if is_relevant == "yes" else 1
        
        print(f"📊 Relevant: {is_relevant}")
        print(f"💭 Rationale: {rationale}")
        
        # Store result
        evaluation_results.append({
            "run_id": run_id,
            "timestamp": trace_info["start_time"],
            "user_prompt": user_prompt,
            "dataset": run.data.tags.get("dataset", ""),
            "widgets_created": len(widget_list.split(", ")) if widget_list else 0,
            "status": status,
            "is_relevant": is_relevant,
            "relevance_score": numeric_score,
            "rationale": rationale
        })
        
    except Exception as e:
        print(f"❌ Error evaluating trace {run_id}: {e}")
        import traceback
        traceback.print_exc()
        
        evaluation_results.append({
            "run_id": run_id,
            "timestamp": trace_info["start_time"],
            "error": str(e),
            "is_relevant": None,
            "relevance_score": None
        })

print(f"\n✅ Completed evaluation of {len(evaluation_results)} traces")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Analyze Results

# COMMAND ----------

# Create DataFrame for analysis
df_results = pd.DataFrame(evaluation_results)

# Display summary statistics
print("="*60)
print("EVALUATION SUMMARY")
print("="*60)

if len(df_results) > 0:
    # Filter out errors
    df_valid = df_results[df_results['is_relevant'].notna()]
    
    if len(df_valid) > 0:
        print(f"\n📊 Total Traces Evaluated: {len(df_valid)}")
        
        # Count yes/no responses
        relevance_counts = df_valid['is_relevant'].value_counts()
        yes_count = relevance_counts.get('yes', 0)
        no_count = relevance_counts.get('no', 0)
        
        print(f"✅ Relevant (yes): {yes_count} ({yes_count/len(df_valid)*100:.1f}%)")
        print(f"❌ Not Relevant (no): {no_count} ({no_count/len(df_valid)*100:.1f}%)")
        print(f"📊 Relevance Rate: {yes_count/len(df_valid)*100:.1f}%")
        
        # Visual representation
        print("\n📊 Relevance Distribution:")
        yes_bar = "█" * int(yes_count * 40 / len(df_valid)) if yes_count > 0 else ""
        no_bar = "█" * int(no_count * 40 / len(df_valid)) if no_count > 0 else ""
        print(f"  Yes: {yes_bar} ({yes_count} traces)")
        print(f"  No:  {no_bar} ({no_count} traces)")
        
        # Show non-relevant traces (need attention)
        not_relevant = df_valid[df_valid['is_relevant'] == 'no']
        if len(not_relevant) > 0:
            print(f"\n⚠️  {len(not_relevant)} traces marked as NOT RELEVANT (needs attention)")
            print("\nNot relevant traces:")
            display(not_relevant[['timestamp', 'user_prompt', 'is_relevant', 'rationale']].head(10))
        
        # Show relevant traces
        relevant = df_valid[df_valid['is_relevant'] == 'yes']
        print(f"\n✅ {len(relevant)} traces marked as RELEVANT (good quality)")
        
    else:
        print("⚠️ No valid scores to analyze")
else:
    print("⚠️ No evaluation results to analyze")

# Display full results
print("\n" + "="*60)
print("DETAILED RESULTS")
print("="*60)
display(df_results)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Log Evaluation Results to MLflow

# COMMAND ----------

# Log evaluation run
with mlflow.start_run(experiment_id=experiment.experiment_id, run_name=f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}") as run:
    
    # Log parameters
    mlflow.log_param("lookback_hours", LOOKBACK_HOURS)
    mlflow.log_param("traces_evaluated", len(df_results))
    mlflow.log_param("evaluation_timestamp", datetime.now().isoformat())
    
    # Log metrics (if we have valid results)
    if len(df_results) > 0:
        df_valid = df_results[df_results['is_relevant'].notna()]
        
        if len(df_valid) > 0:
            yes_count = len(df_valid[df_valid['is_relevant'] == 'yes'])
            no_count = len(df_valid[df_valid['is_relevant'] == 'no'])
            relevance_rate = yes_count / len(df_valid) if len(df_valid) > 0 else 0
            
            mlflow.log_metric("total_traces_evaluated", len(df_valid))
            mlflow.log_metric("relevant_count", yes_count)
            mlflow.log_metric("not_relevant_count", no_count)
            mlflow.log_metric("relevance_rate", relevance_rate)
            mlflow.log_metric("relevance_rate_percentage", relevance_rate * 100)
    
    # Log results as artifact
    results_csv = "/tmp/evaluation_results.csv"
    df_results.to_csv(results_csv, index=False)
    mlflow.log_artifact(results_csv, "evaluation_results")
    
    # Log summary as text
    summary_text = f"""Dashboard Generation Quality Report
Generated: {datetime.now().isoformat()}

Traces Evaluated: {len(df_results)}
Time Window: Last {LOOKBACK_HOURS} hours

"""
    
    if len(df_valid) > 0:
        yes_count = len(df_valid[df_valid['is_relevant'] == 'yes'])
        no_count = len(df_valid[df_valid['is_relevant'] == 'no'])
        relevance_rate = yes_count / len(df_valid) * 100 if len(df_valid) > 0 else 0
        
        summary_text += f"""Relevant: {yes_count} traces
Not Relevant: {no_count} traces
Relevance Rate: {relevance_rate:.1f}%
"""
    
    with open("/tmp/summary.txt", "w") as f:
        f.write(summary_text)
    mlflow.log_artifact("/tmp/summary.txt", "summary")
    
    print(f"✅ Evaluation results logged to MLflow run: {run.info.run_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Alerts (Optional)

# COMMAND ----------

# Define alert thresholds
ALERT_THRESHOLD_RELEVANCE_RATE = 70.0  # Alert if relevance rate drops below 70%
ALERT_THRESHOLD_NOT_RELEVANT_COUNT = 5  # Alert if more than 5 traces are not relevant

if len(df_valid) > 0:
    yes_count = len(df_valid[df_valid['is_relevant'] == 'yes'])
    no_count = len(df_valid[df_valid['is_relevant'] == 'no'])
    relevance_rate = yes_count / len(df_valid) * 100 if len(df_valid) > 0 else 0
    
    alerts = []
    
    if relevance_rate < ALERT_THRESHOLD_RELEVANCE_RATE:
        alerts.append(f"⚠️  ALERT: Relevance rate ({relevance_rate:.1f}%) is below threshold ({ALERT_THRESHOLD_RELEVANCE_RATE}%)")
    
    if no_count > ALERT_THRESHOLD_NOT_RELEVANT_COUNT:
        alerts.append(f"⚠️  ALERT: {no_count} traces marked as NOT RELEVANT (threshold: {ALERT_THRESHOLD_NOT_RELEVANT_COUNT})")
    
    if alerts:
        print("\n" + "="*60)
        print("🚨 ALERTS TRIGGERED")
        print("="*60)
        for alert in alerts:
            print(alert)
        
        # TODO: Add your notification logic here (Slack, email, PagerDuty, etc.)
        # Example:
        # send_slack_notification(alerts)
    else:
        print("\n✅ No alerts - all metrics within acceptable ranges")
else:
    print("\n⚠️  Cannot check alerts - no valid evaluation results")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Next Steps
# MAGIC 
# MAGIC **To schedule this notebook as a job:**
# MAGIC 1. Go to Workflows → Create Job
# MAGIC 2. Select this notebook
# MAGIC 3. Set schedule (e.g., daily at 9 AM)
# MAGIC 4. Configure notifications for failures
# MAGIC 
# MAGIC **To improve monitoring:**
# MAGIC - Add Slack/email notifications in the Alerts section
# MAGIC - Create a dashboard to visualize trends over time
# MAGIC - Adjust alert thresholds based on your requirements
# MAGIC - Add more MLflow built-in judges (e.g., `AnswerCorrectness`, `Groundedness`)
# MAGIC - Use `mlflow.genai.evaluate()` for batch evaluation
# MAGIC 
# MAGIC **MLflow Judge Documentation:**
# MAGIC - [RelevanceToQuery Judge](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_context_relevant#relevance-to-query)
# MAGIC - [All Built-in Judges](https://docs.databricks.com/en/mlflow3/genai/eval-monitor/concepts/judges/index.html)
# MAGIC - [Custom Judges](https://docs.databricks.com/en/mlflow3/genai/eval-monitor/concepts/judges/custom-llm-judges.html)

