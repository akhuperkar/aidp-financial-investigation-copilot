"""LOCAL VALIDATION ONLY: catalog names mapped to two-part local Spark databases; Delta writes -> Parquet.
Never import this adapter in AIDP. Product notebooks contain no local validation adapter.
"""
import json
import os
from pathlib import Path
import random
import re
from pyspark.sql import SparkSession
from pyspark.sql.readwriter import DataFrameWriter

root = Path(os.environ["AIDP_PACKAGE_ROOT"])
warehouse = Path(os.environ["AIDP_TEST_WAREHOUSE"])
real_spark = (SparkSession.builder.master("local[2]").appName("finance-notebook-local-validation")
              .config("spark.sql.warehouse.dir", str(warehouse))
              .config("spark.sql.shuffle.partitions", "4")
              .config("spark.driver.bindAddress", "127.0.0.1")
              .config("spark.driver.host", "127.0.0.1")
              .config("spark.ui.enabled", "false")
              .config("spark.sql.session.timeZone", "UTC")
              .getOrCreate())
real_spark.sparkContext.setLogLevel("ERROR")

def local_name(text):
    for schema in ["bronze", "silver", "gold", "agent_demo_fs"]:
        text = text.replace(f"finance.{schema}.", f"finance_{schema}.")
        text = text.replace(f"finance.{schema}", f"finance_{schema}")
    return text

class LocalCatalogAdapter:
    def __init__(self, session):
        self._session = session
    def sql(self, query, *args, **kwargs):
        return self._session.sql(local_name(query), *args, **kwargs)
    def table(self, name):
        return self._session.table(local_name(name))
    def __getattr__(self, name):
        return getattr(self._session, name)

original_format = DataFrameWriter.format
original_save = DataFrameWriter.saveAsTable
def local_format(self, source):
    return original_format(self, "parquet" if source.lower() == "delta" else source)
def local_save(self, name, *args, **kwargs):
    return original_save(self, local_name(name), *args, **kwargs)
DataFrameWriter.format = local_format
DataFrameWriter.saveAsTable = local_save
spark = LocalCatalogAdapter(real_spark)
for schema in ["bronze", "silver", "gold", "agent_demo_fs"]:
    real_spark.sql(f"CREATE DATABASE IF NOT EXISTS finance_{schema}")

# Use the user's exact source generator and transformation code, seeded only for this local test.
# Skip AIDP catalog/Delta CLUSTER DDL and model training; neither notebook consumes model predictions.
source = json.loads((root/"reference/financial_services_medallion_architecture_demo.ipynb").read_text())
random.seed(42)
for cell_index in [5, 6, 9, 11, 15, 16, 17, 18]:
    print(f"Executing reference medallion data cell {cell_index}")
    exec(compile("".join(source["cells"][cell_index]["source"]), f"reference:cell{cell_index}", "exec"), globals())
print("LOCAL FIXTURE READY: seeded original data; Spark 3.5.3; local catalog translation; Parquet substitutes for Delta writes.")
