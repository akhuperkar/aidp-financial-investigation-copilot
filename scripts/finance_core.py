"""Shared source embedded in both self-contained AIDP notebooks by build_package.py."""
import hashlib
import json
import re
from datetime import datetime
from html import escape

from pyspark.sql import functions as F
from pyspark.sql import types as T

RULE_VERSION = "FS-TRIAGE-1.1"
RISK_THRESHOLD = 60                 # Matches the supplied Gold construction: strictly greater.
HIGH_VALUE_USD = 5000.0             # Fictional demo policy; source has no currency column.
P1_ACCOUNT_EXPOSURE_USD = 10000.0
VERY_HIGH_SCORE = 85
CURRENCY_ASSUMPTION = "USD"

SOURCE_CONTRACTS = {
    "transaction_analytics_gold": {
        "account_id", "month_year", "total_transactions", "total_amount", "avg_amount",
        "avg_risk_score", "high_risk_transactions", "transaction_types", "merchant_categories",
    },
    "fraud_detection_model_gold": {
        "account_id", "transaction_date", "transaction_type", "amount", "merchant_category",
        "location", "risk_score", "month", "day_of_week", "hour", "is_fraud",
    },
}


def read_gold(spark, catalog):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", catalog):
        raise ValueError("CATALOG must be a simple catalog identifier")
    frames = {}
    for short, required in SOURCE_CONTRACTS.items():
        name = f"{catalog}.gold.{short}"
        try:
            df = spark.table(name)
        except Exception as exc:
            raise RuntimeError(f"Cannot read {name}; run the financial-services medallion notebook and check grants") from exc
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"{name}: missing columns {sorted(missing)}; inspected actual write schema, not just DDL")
        for field in df.schema.fields:
            if field.name in {"amount", "risk_score", "total_transactions", "total_amount", "avg_amount", "avg_risk_score", "high_risk_transactions", "is_fraud"}:
                if not isinstance(field.dataType, T.NumericType):
                    raise ValueError(f"{name}.{field.name} must be numeric, found {field.dataType}")
        if not df.take(1):
            raise ValueError(f"{name} is empty")
        frames[short] = df
    tx, monthly = frames["fraud_detection_model_gold"], frames["transaction_analytics_gold"]
    if not isinstance(tx.schema["transaction_date"].dataType, T.TimestampType):
        raise ValueError("transaction_date must be a Spark timestamp")
    bad_tx = tx.filter(
        F.col("account_id").isNull() | ~F.col("account_id").rlike(r"^ACC[0-9]{8}$") |
        F.col("transaction_date").isNull() | F.col("amount").isNull() |
        F.isnan(F.col("amount").cast("double")) | (F.abs(F.col("amount")) == float("inf")) |
        F.col("risk_score").isNull() | ~F.col("risk_score").between(0, 100) |
        F.isnan(F.col("risk_score").cast("double")) | F.col("is_fraud").isNull() |
        (F.col("is_fraud") != F.when(F.col("risk_score") > RISK_THRESHOLD, 1).otherwise(0))
    )
    if bad_tx.take(1):
        raise ValueError("Gold transaction contract failed: keys, amounts, risk range or synthetic is_fraud label")
    if monthly.filter(
        F.col("account_id").isNull() | F.col("month_year").isNull() |
        ~F.col("month_year").rlike(r"^[0-9]{4}-(0[1-9]|1[0-2])$") |
        F.col("total_transactions").isNull() | (F.col("total_transactions") <= 0) |
        F.col("high_risk_transactions").isNull() |
        ~F.col("high_risk_transactions").between(0, F.col("total_transactions")) |
        F.col("total_amount").isNull() | F.col("avg_amount").isNull() |
        F.col("avg_risk_score").isNull() | ~F.col("avg_risk_score").between(0, 100) |
        F.isnan(F.col("total_amount").cast("double")) | F.isnan(F.col("avg_amount").cast("double")) |
        F.isnan(F.col("avg_risk_score").cast("double"))
    ).take(1):
        raise ValueError("Gold account-month contract failed: period, keys, counts or measures")
    if monthly.groupBy("account_id", "month_year").count().filter("count > 1").take(1):
        raise ValueError("Duplicate Gold account-month rows; aggregation would double-count")
    tx = (tx.withColumn("month_year", F.date_format("transaction_date", "yyyy-MM"))
          .withColumn("period_key", F.date_format("transaction_date", "yyyyMM").cast("int"))
          .withColumn("gross_amount_usd", F.abs("amount").cast("double"))
          .withColumn("rule_flag", (F.col("risk_score") > RISK_THRESHOLD).cast("int")))
    return tx, monthly


def account_metrics(tx):
    return (tx.groupBy("month_year", "period_key", "account_id").agg(
        F.count("*").alias("transaction_count"),
        F.sum("amount").cast("double").alias("net_amount_usd"),
        F.sum("gross_amount_usd").alias("gross_amount_usd"),
        F.sum(F.when(F.col("amount") > 0, F.col("amount")).otherwise(0)).cast("double").alias("positive_amount_usd"),
        F.sum(F.when(F.col("amount") < 0, -F.col("amount")).otherwise(0)).cast("double").alias("negative_magnitude_usd"),
        F.avg("risk_score").alias("avg_risk_score"),
        F.max("risk_score").alias("max_risk_score"),
        F.sum("rule_flag").alias("flagged_count"),
        F.sum(F.when(F.col("rule_flag") == 1, F.col("gross_amount_usd")).otherwise(0)).alias("flagged_gross_usd"),
        F.sum(F.when((F.col("rule_flag") == 1) & (F.col("gross_amount_usd") >= HIGH_VALUE_USD), 1).otherwise(0)).alias("high_value_flagged_count"),
        F.sum(F.when((F.col("risk_score") >= VERY_HIGH_SCORE) & (F.col("gross_amount_usd") >= HIGH_VALUE_USD), 1).otherwise(0)).alias("very_high_value_count"),
    ).withColumn("flagged_rate_pct", 100.0 * F.col("flagged_count") / F.col("transaction_count"))
     .withColumn("priority", F.when((F.col("flagged_gross_usd") >= P1_ACCOUNT_EXPOSURE_USD) |
                                    (F.col("very_high_value_count") > 0), "P1")
                 .when(F.col("flagged_count") > 0, "P2").otherwise("P3")))


def portfolio_metrics(accounts):
    return (accounts.groupBy("month_year", "period_key").agg(
        F.count("*").alias("active_accounts"),
        *[F.sum(c).alias(c) for c in ["transaction_count", "net_amount_usd", "gross_amount_usd",
             "positive_amount_usd", "negative_magnitude_usd", "flagged_count", "flagged_gross_usd", "high_value_flagged_count"]],
        (F.sum(F.col("avg_risk_score") * F.col("transaction_count")) / F.sum("transaction_count")).alias("avg_risk_score"),
        F.sum(F.when(F.col("priority") == "P1", 1).otherwise(0)).alias("p1_accounts"),
    ).withColumn("flagged_rate_pct", 100.0 * F.col("flagged_count") / F.col("transaction_count")))


def reconciliation_checks(tx, monthly):
    expected = account_metrics(tx).select("account_id", "month_year", "transaction_count", "net_amount_usd", "avg_risk_score", "flagged_count")
    joined = expected.alias("e").join(monthly.alias("m"), ["account_id", "month_year"], "full")
    # Currency totals in source may have DECIMAL(15,2) rounding. Risk averages are not rounded.
    bad = joined.filter(
        F.col("e.transaction_count").isNull() | F.col("m.total_transactions").isNull() |
        (F.col("e.transaction_count") != F.col("m.total_transactions")) |
        (F.abs(F.col("e.net_amount_usd") - F.col("m.total_amount")) > 0.02) |
        (F.abs(F.col("e.net_amount_usd") / F.col("e.transaction_count") - F.col("m.avg_amount")) > 0.02) |
        (F.abs(F.col("e.avg_risk_score") - F.col("m.avg_risk_score")) > 1e-8) |
        (F.col("e.flagged_count") != F.col("m.high_risk_transactions"))
    )
    if bad.take(1):
        raise ValueError("Gold tables do not reconcile by account-month; rerun Gold from the same Silver snapshot")
    # Check distributions by category as well as total counts, without exploding both maps together.
    for column, dimension in [("transaction_types", "transaction_type"), ("merchant_categories", "merchant_category")]:
        stored = monthly.select("account_id", "month_year", F.explode_outer(column).alias(dimension, "stored_count"))
        observed = tx.groupBy("account_id", "month_year", dimension).count()
        mismatch = observed.join(stored, ["account_id", "month_year", dimension], "full").filter(
            F.col("count").isNull() | F.col("stored_count").isNull() | (F.col("count") != F.col("stored_count")))
        if mismatch.take(1):
            raise ValueError(f"Gold map {column} does not reconcile to transaction-level Gold")
    return {"account_month_grain": "PASS", "counts_amounts_risk": "PASS", "category_maps": "PASS"}


def content_fingerprint(tx, monthly):
    parts = []
    for df, short in [(tx, "fraud_detection_model_gold"), (monthly, "transaction_analytics_gold")]:
        cols = sorted(SOURCE_CONTRACTS[short])
        # Commutative multiset checksum includes duplicate multiplicity; not a source commit ID.
        row = df.agg(F.count("*").alias("n"), F.sum(
            F.xxhash64(F.to_json(F.struct(*cols))).cast("decimal(38,0)" )).alias("checksum")).first()
        parts.append([short, int(row["n"]), str(row["checksum"])])
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:24]


def rows(df, limit=20):
    return [r.asDict(recursive=True) for r in df.limit(limit).collect()]


def usd(value):
    return "—" if value is None else f"USD {float(value):,.2f}"


def table_html(data, columns):
    headers = "".join(f"<th>{escape(label)}</th>" for key, label in columns)
    body = "".join("<tr>" + "".join(f"<td>{escape(str(row.get(key, '—')))}</td>" for key, label in columns) + "</tr>" for row in data)
    return ("<div style='overflow:auto'><table style='border-collapse:collapse;width:100%'><thead><tr>" +
            headers + "</tr></thead><tbody>" + body + "</tbody></table></div>")
