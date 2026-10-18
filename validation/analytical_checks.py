"""Executed after both notebooks, in the local validation notebook kernel."""
from datetime import datetime
import math

def check(name, condition):
    assert condition, name
    analytical_results.append({"check": name, "status": "PASS"})

analytical_results = []
schema = "account_id string, transaction_date timestamp, transaction_type string, amount double, merchant_category string, location string, risk_score int, month int, day_of_week int, hour int, is_fraud int"
records = []
for account, amount, risk in [(1,5000.,60),(1,-5000.,61),(1,-5000.,61),(1,5000.,85),
                               (2,-4999.99,85),(2,1.,0),(3,10000.,60),(4,10000.,61)]:
    records.append((f"ACC{account:08d}", datetime(2024,1,15,12), "Transfer", amount, "Online", "Online", risk, 1, 2, 12, int(risk > 60)))
small = spark.createDataFrame(records, schema).withColumn("month_year", F.lit("2024-01")).withColumn("period_key", F.lit(202401)).withColumn("gross_amount_inr", F.abs("amount")).withColumn("rule_flag", (F.col("risk_score") > 60).cast("int"))
small_accounts = account_metrics(small)
actual = {r["account_id"]:r.asDict() for r in small_accounts.collect()}
a1 = actual["ACC00000001"]
check("exact boundaries and duplicate retention", a1["transaction_count"] == 4 and a1["flagged_count"] == 3)
check("signed cancellation does not hide gross exposure", a1["net_amount_inr"] == 0 and a1["gross_amount_inr"] == 20000 and a1["flagged_gross_inr"] == 15000)
check("high value threshold is inclusive", a1["high_value_flagged_count"] == 3 and a1["very_high_value_count"] == 1)
check("P1 OR conditions", a1["priority"] == "P1" and actual["ACC00000004"]["priority"] == "P1")
check("4999.99 below high value; score 85 alone does not force P1", actual["ACC00000002"]["priority"] == "P2")
check("score 60 is not flagged", actual["ACC00000003"]["priority"] == "P3" and actual["ACC00000003"]["flagged_count"] == 0)
small_portfolio = portfolio_metrics(small_accounts).first().asDict()
check("risk score average is transaction weighted", math.isclose(small_portfolio["avg_risk_score"], sum(r[6] for r in records)/len(records)))
check("portfolio account and transaction denominators", small_portfolio["active_accounts"] == 4 and small_portfolio["transaction_count"] == 8 and small_portfolio["flagged_count"] == 5)

# Verify end-to-end semantic data against independent direct source aggregates.
source_totals = transactions.agg(F.count("*").alias("n"), F.sum("gross_amount_inr").alias("gross"), F.sum("rule_flag").alias("flags")).first()
published_totals = spark.table("finance.agent_demo_fs.portfolio_monthly_sql").agg(F.sum("transaction_count").alias("n"), F.sum("gross_amount_inr").alias("gross"), F.sum("flagged_count").alias("flags")).first()
check("materialized totals equal original source", source_totals["n"] == published_totals["n"] and source_totals["flags"] == published_totals["flags"] and abs(source_totals["gross"]-published_totals["gross"]) < 0.02)
all_tool_results = []
for tool in SQL_TOOLS:
    result = test_query(tool, {"period_key":latest_period_key,"account_number":seed_account_number,"dimension_code":1})
    response = rows(result, tool["max_rows"])
    all_tool_results.append({"tool":tool["tool_name"],"parameters":{"period_key":latest_period_key,"account_number":seed_account_number,"dimension_code":1},"rows":response})
    check(f"{tool['tool_name']} snapshot consistency", all(r["snapshot_id"] == snapshot_id for r in response))

missing_period_tool = next(t for t in SQL_TOOLS if t["tool_name"] == "get_portfolio_snapshot")
check("explicit missing period never falls back", test_query(missing_period_tool,{"period_key":202606}).count() == 0)
trend_tool = next(t for t in SQL_TOOLS if t["tool_name"] == "get_portfolio_trend")
check("trend requires an available ending period", test_query(trend_tool,{"period_key":202606}).count() == 0)
account_tool = next(t for t in SQL_TOOLS if t["tool_name"] == "get_account_snapshot")
check("unknown valid numeric account returns no data", test_query(account_tool,{"period_key":latest_period_key,"account_number":99999999}).count() == 0)
for invalid in ["202401 OR 1=1", "1'; DROP TABLE x;--", 202401.5, True, -1]:
    try:
        test_query(missing_period_tool,{"period_key":invalid})
    except ValueError:
        analytical_results.append({"check":f"local evaluator rejects malformed period {invalid!r}","status":"PASS"})
    else:
        raise AssertionError("Malformed numeric parameter accepted")

# Gold reconciliation must reject corruption, not silently render plausible totals.
corrupted = gold_monthly.withColumn("total_transactions", F.col("total_transactions") + 1)
try:
    reconciliation_checks(transactions, corrupted)
except ValueError:
    analytical_results.append({"check":"corrupted Gold counts rejected","status":"PASS"})
else:
    raise AssertionError("Mismatching Gold accepted")

manifest_disk = json.loads((root/"config/rag_manifest.json").read_text())
check("RAG corpus hashes match manifest", all(hashlib.sha256((root/"rag_corpus"/item["filename"]).read_bytes()).hexdigest() == item["sha256"] for item in manifest_disk))
check("eight documents with durable citation markers", len(RAG_DOCUMENTS)==8 and all(f"[{d['document_id']} v1.0 §" in d["content"] for d in RAG_DOCUMENTS))
check("source snapshot unchanged after tests", content_fingerprint(*read_gold(spark,"finance")) == source_fingerprint)
(root/"validation/local_tool_results.json").write_text(json.dumps(all_tool_results,indent=2,default=str,ensure_ascii=False))
(root/"validation/analytical_results.json").write_text(json.dumps(analytical_results,indent=2))
print(json.dumps({"analytical_checks_passed":len(analytical_results),"source_transactions":int(source_totals['n']),"source_flags":int(source_totals['flags']),"latest_period_key":latest_period_key,"seed_account":seed_account['account_id'],"snapshot_id":snapshot_id},indent=2))
real_spark.stop()
