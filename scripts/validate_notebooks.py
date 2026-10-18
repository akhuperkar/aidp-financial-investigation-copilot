"""Execute both notebooks on seeded original medallion data, with explicit local-only adapters.

Usage: PYTHONPATH=<validation dependencies> <python> scripts/validate_notebooks.py
Requires Java 17 and Spark 3.5.3. Writes cleanly separated executed fixture outputs.
"""
import copy
import json
import os
from pathlib import Path
import tempfile
import time
import nbformat as nbf
from nbclient import NotebookClient
from nbconvert import HTMLExporter

ROOT = Path(__file__).resolve().parents[1]
os.environ["AIDP_PACKAGE_ROOT"] = str(ROOT)
os.environ["AIDP_TEST_WAREHOUSE"] = tempfile.mkdtemp(prefix="aidp-finance-warehouse-")
kernel_root = Path(tempfile.mkdtemp(prefix="aidp-finance-jupyter-"))
kernel = kernel_root/"kernels/aidp-finance-local"
kernel.mkdir(parents=True)
import sys
(kernel/"kernel.json").write_text(json.dumps({"argv":[sys.executable,"-m","ipykernel_launcher","-f","{connection_file}"],"display_name":"AIDP finance LOCAL validation","language":"python"}))
import nbconvert
target_share = Path(nbconvert.__file__).resolve().parent.parent / "share/jupyter"
os.environ["JUPYTER_PATH"] = os.pathsep.join([str(kernel_root), str(target_share)])
os.environ["MPLCONFIGDIR"] = tempfile.mkdtemp(prefix="aidp-mpl-")
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
if os.environ.get("AIDP_JAVA_HOME"):
    os.environ["JAVA_HOME"] = os.environ["AIDP_JAVA_HOME"]
# Otherwise respect JAVA_HOME or Spark's Java discovery on PATH (Java 17 required).
notice = """# LOCAL FIXTURE EXECUTION — NOT YOUR AIDP RESULTS

The exact supplied medallion generator/transforms run with seed 42 in local Spark 3.5.3.
Three-part finance catalog names are translated into local two-part databases, and Delta writes are substituted
with Parquet. These outputs validate PySpark calculations, notebook execution, chart generation and SQL syntax.
They do not validate AIDP catalog/Delta integration, grants, tool parameter substitution, Knowledge Base retrieval,
LLM routing, Guardrails, model availability or Agent Flow deployment. Your unseeded AIDP source totals will differ.
"""
cells = [nbf.v4.new_markdown_cell(notice), nbf.v4.new_code_cell((ROOT/"validation/local_spark_fixture.py").read_text())]
boundaries = {}
for filename in ["financial_services_executive_analytics_dashboards_aidp.ipynb", "financial_services_multi_agent_demo_setup_aidp.ipynb"]:
    source = nbf.read(ROOT/"notebooks"/filename,as_version=4)
    nbf.validate(source)
    start = len(cells)
    cells.extend(copy.deepcopy(source.cells))
    boundaries[filename] = (start,len(cells))
    if filename.startswith("financial_services_executive_"):
        filtered = copy.deepcopy(source.cells)
        for cell in filtered:
            cell.id = "filtered-" + cell.id
        # Reuse a known account returned by the all-account dashboard. Exercise full dashboard scope,
        # not just the aggregation helpers; the production notebook remains parameter-driven.
        for cell in filtered:
            if cell.cell_type == "code" and 'ACCOUNT_IDS = []' in cell.source:
                cell.source = cell.source.replace('ACCOUNT_IDS = []', 'ACCOUNT_IDS = [priority_rows[0]["account_id"]]').replace('TREND_MONTHS = 12', 'TREND_MONTHS = 3')
        cells.append(nbf.v4.new_markdown_cell("# Filtered-scope regression: one existing account and three calendar months"))
        filter_start = len(cells)
        cells.extend(filtered)
        cells.append(nbf.v4.new_code_cell('assert current["active_accounts"] == 1\nassert len(ACCOUNT_IDS) == 1\nassert scope_label == ACCOUNT_IDS[0]\nassert len(trend_rows) == 3\nprint("PASS: full dashboard uses one selected account across all outputs and a three-month window")'))
        boundaries["filtered_scope_dashboard.ipynb"] = (filter_start,len(cells))
cells.append(nbf.v4.new_code_cell((ROOT/"validation/analytical_checks.py").read_text()))
notebook = nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"name":"aidp-finance-local","display_name":"LOCAL Spark fixture","language":"python"}})
client = NotebookClient(notebook,timeout=600,kernel_name="aidp-finance-local",resources={"metadata":{"path":str(ROOT)}})
started = time.time()
try:
    client.execute()
finally:
    nbf.write(notebook, ROOT/"validation/local_fixture_execution.ipynb")
    exporter = HTMLExporter()
    exporter.exclude_input_prompt = True
    body,_ = exporter.from_notebook_node(notebook)
    (ROOT/"validation/local_fixture_execution.html").write_text(body)

for filename,(start,end) in boundaries.items():
    result = nbf.v4.new_notebook(cells=[nbf.v4.new_markdown_cell(notice)] + copy.deepcopy(notebook.cells[start:end]))
    output = ROOT/"validation"/("local_"+filename)
    nbf.write(result,output)
    exporter = HTMLExporter(); exporter.exclude_input = True; exporter.exclude_input_prompt = True
    body,_=exporter.from_notebook_node(result)
    output.with_suffix(".html").write_text(body)
print(json.dumps({"execution":"PASS","duration_seconds":round(time.time()-started,1),"product_notebooks":2,"cell_count":len(cells),"validation_scope":"local Spark; catalog translation and Parquet adapter; no AIDP deployment"},indent=2))
