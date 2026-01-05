#!/bin/bash

echo "🔍 Diagnosing intelligent-embedded-dashboard..."
echo "================================================"
echo ""

# Check Python version
echo "1. Python version:"
python3 --version
echo ""

# Check if all required files exist
echo "2. Checking files:"
for file in app.py ai_dashboard_generator.py dashboard_manager.py table_widget.py filter_widget.py bar_chart_widget.py line_chart_widget.py pivot_widget.py datasets.py; do
    if [ -f "$file" ]; then
        echo "   ✅ $file exists"
    else
        echo "   ❌ $file MISSING"
    fi
done
echo ""

# Check syntax
echo "3. Checking Python syntax:"
python3 -m py_compile app.py 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ app.py syntax OK"
else
    echo "   ❌ app.py has syntax errors"
    exit 1
fi

python3 -m py_compile ai_dashboard_generator.py 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ ai_dashboard_generator.py syntax OK"
else
    echo "   ❌ ai_dashboard_generator.py has syntax errors"
    exit 1
fi
echo ""

# Test imports
echo "4. Testing imports:"
python3 test_import.py
echo ""

# Check if dependencies are installed
echo "5. Checking key dependencies:"
python3 -c "import dash" 2>&1 && echo "   ✅ dash installed" || echo "   ❌ dash NOT installed"
python3 -c "import dash_bootstrap_components" 2>&1 && echo "   ✅ dash_bootstrap_components installed" || echo "   ❌ dash_bootstrap_components NOT installed"
python3 -c "import openai" 2>&1 && echo "   ✅ openai installed" || echo "   ❌ openai NOT installed"
python3 -c "import mlflow" 2>&1 && echo "   ✅ mlflow installed" || echo "   ❌ mlflow NOT installed"
python3 -c "from databricks.sdk import WorkspaceClient" 2>&1 && echo "   ✅ databricks-sdk installed" || echo "   ❌ databricks-sdk NOT installed"
echo ""

echo "================================================"
echo "Diagnosis complete!"
echo ""
echo "If all checks passed, try running: python3 app.py"
echo "If you see errors, please share the output above"

