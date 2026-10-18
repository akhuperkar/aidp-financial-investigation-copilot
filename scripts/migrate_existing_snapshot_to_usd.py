"""Migrate the EXISTING agent-serving snapshot to USD without reading Gold.

Prerequisites: existing Spark session; new setup-definition cells have initialized
SQL_TOOLS, RAG_DOCUMENTS, PROMPTS, ACCEPTANCE_CASES. Do not run setup Gold-read or
materialization cells. Stop concurrent setup writers before running this cell.

This is a denomination/schema migration, never FX conversion or data regeneration.
Original prepared_at_utc values and every non-metadata value are preserved. Delta
rollback copies are retained. Multi-table publication is sequential, not atomic;
the PREPARING metadata gate prevents NEW normal tool queries from seeing the swap,
but cannot revoke an in-flight request's already-read context. Start fresh sessions.
On a failure after gating, leave PREPARING and inspect/retry; never force READY.
"""

import hashlib as _usd_hashlib
import json as _usd_json
import re as _usd_re
from datetime import datetime as _usd_datetime, timezone as _usd_timezone
from pyspark.sql import functions as _usd_F


def migrate_existing_snapshot_to_usd(spark_session, sql_tools, rag_documents,
                                     prompts, acceptance_cases,
                                     schema="finance.agent_demo_fs"):
    if not _usd_re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", schema):
        raise ValueError("schema must be a simple catalog.schema identifier")
    rule, currency = "FS-TRIAGE-1.1", "USD"
    suffix = "pre_usd_20261018"
    stage_suffix = "stage_usd_20261018"
    data_tables = ["portfolio_monthly_sql", "account_risk_monthly_sql",
                   "transaction_evidence_sql", "exposure_mix_monthly_sql"]
    metadata_table = "snapshot_metadata_sql"
    migration_time = _usd_datetime.now(_usd_timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    phase = "preflight"

    def name(short):
        if not _usd_re.fullmatch(r"[a-z_0-9]+", short):
            raise ValueError("Invalid table identifier")
        return schema + "." + short

    def quoted(short):
        # Identifiers are restricted above. AIDP's external catalog bridge treats
        # individually quoted catalog parts as literal names for DESCRIBE HISTORY.
        return name(short)

    def exists(short):
        # Permission/connection errors propagate; they are never treated as missing.
        return spark_session.catalog.tableExists(name(short))

    def version(short):
        row = spark_session.sql("DESCRIBE HISTORY " + quoted(short) + " LIMIT 1").first()
        if row is None or "version" not in row.asDict():
            raise RuntimeError(name(short) + " has no readable Delta version")
        return int(row["version"])

    def pinned(short, value):
        return spark_session.sql("SELECT * FROM " + quoted(short) + " VERSION AS OF " + str(value))

    def write(df, short, mode="overwrite"):
        (df.write.format("delta").mode(mode).option("overwriteSchema", "true")
           .saveAsTable(name(short)))

    def parity(expected, actual, label):
        if expected.columns != actual.columns:
            raise AssertionError(label + ": ordered columns differ")
        types_expected = [(f.name, f.dataType.simpleString()) for f in expected.schema.fields]
        types_actual = [(f.name, f.dataType.simpleString()) for f in actual.schema.fields]
        if types_expected != types_actual:
            raise AssertionError(label + ": column types differ")
        expected_count, actual_count = expected.count(), actual.count()
        if expected_count != actual_count:
            raise AssertionError(label + ": row counts differ")
        # Full row multiset equality includes nulls and duplicate multiplicities.
        if expected.exceptAll(actual).limit(1).count() or actual.exceptAll(expected).limit(1).count():
            raise AssertionError(label + ": complete-row parity failed")
        return actual_count

    def one_record(df, label):
        rows = df.limit(2).collect()
        if len(rows) != 1:
            raise RuntimeError(label + " must contain exactly one metadata row")
        return rows[0].asDict()

    def distinct_value(df, column, wanted, label):
        if column not in df.columns:
            raise RuntimeError(label + ": missing " + column)
        values = [r[0] for r in df.select(column).distinct().limit(2).collect()]
        if values != [wanted]:
            raise RuntimeError(label + ": inconsistent " + column)

    # Validate all definitions before mutating any live table or backup.
    if len(sql_tools) != 7 or len(rag_documents) != 8 or not prompts or not acceptance_cases:
        raise ValueError("Expected seven SQL tools, eight policy documents and nonempty prompt/test definitions")
    for document in rag_documents:
        if document.get("version") != "1.1" or f"[{document['document_id']} v1.1 §" not in document.get("content", ""):
            raise ValueError("Load version-1.1 RAG_DOCUMENTS before migration")
    definitions_text = _usd_json.dumps([sql_tools, rag_documents, prompts, acceptance_cases], ensure_ascii=False)
    if _usd_re.search(r"INR|_inr|_INR|₹|FS-TRIAGE-1\.0", definitions_text):
        raise ValueError("Load USD-only SQL_TOOLS, RAG_DOCUMENTS, PROMPTS and ACCEPTANCE_CASES before migration")

    registry_manifest = []
    for document in rag_documents:
        content = document["content"].encode("utf-8")
        registry_manifest.append({key: document[key] for key in ("document_id", "filename", "version", "effective_from")} |
                                 {"sha256": _usd_hashlib.sha256(content).hexdigest(), "bytes": len(content)})
    registry_specs = [
        ("sql_tool_registry", "tool_name", sql_tools),
        ("rag_document_manifest", "document_id", registry_manifest),
        ("prompt_registry", "name", prompts),
        ("demo_acceptance_catalog", "test_id", acceptance_cases),
    ]
    registry_frames = {}
    for short, key, items in registry_specs:
        keys = [item[key] for item in items]
        if len(keys) != len(set(keys)):
            raise ValueError(short + ": duplicate definition keys")
        registry_frames[short] = spark_session.createDataFrame(
            [(item[key], _usd_json.dumps(item, sort_keys=True, ensure_ascii=False)) for item in items],
            key + " string, configuration_json string")

    for short in data_tables + [metadata_table]:
        if not exists(short):
            raise RuntimeError("Required existing serving table is missing: " + name(short))

    live_versions = {short: version(short) for short in data_tables + [metadata_table]}
    registry_versions = {short: version(short) for short in registry_frames if exists(short)}
    metadata_backup = metadata_table + "_" + suffix
    if exists(metadata_backup):
        original_metadata = spark_session.table(name(metadata_backup))
    else:
        original_metadata = pinned(metadata_table, live_versions[metadata_table])
    baseline = one_record(original_metadata, "Original snapshot metadata")
    if baseline.get("status") != "READY":
        raise RuntimeError("Original snapshot was not READY; resolve the existing setup failure first")
    if baseline.get("rule_version") not in ("FS-TRIAGE-1.0", rule) or baseline.get("currency_assumption") not in ("INR", currency):
        raise RuntimeError("Unrecognized original rule/currency contract; review before changing its meaning")
    fingerprint = baseline.get("source_fingerprint")
    old_snapshot = baseline.get("snapshot_id")
    if not isinstance(fingerprint, str) or not fingerprint or not old_snapshot:
        raise RuntimeError("Original fingerprint/snapshot metadata is unavailable")
    new_snapshot = _usd_hashlib.sha256((fingerprint + rule + currency).encode()).hexdigest()[:24]
    current_metadata = one_record(pinned(metadata_table, live_versions[metadata_table]), "Current snapshot metadata")
    if (current_metadata.get("source_fingerprint") != fingerprint or
            current_metadata.get("snapshot_id") not in (old_snapshot, new_snapshot)):
        raise RuntimeError("Rollback copies belong to another serving snapshot; refuse to replace newer data")

    # Backups are write-once. If a prior attempt stopped, use the original backups,
    # never replace them with a partly migrated live table.
    phase = "backing_up"
    if not exists(metadata_backup):
        write(original_metadata, metadata_backup, "errorifexists")
    parity(original_metadata, spark_session.table(name(metadata_backup)), metadata_backup)
    originals = {}
    backup_versions = {}
    for short in data_tables:
        backup = short + "_" + suffix
        if exists(backup):
            original = spark_session.table(name(backup))
        else:
            original = pinned(short, live_versions[short])
            # A missing backup must not be synthesized from a partly migrated table.
            distinct_value(original, "snapshot_id", old_snapshot, short)
            write(original, backup, "errorifexists")
        originals[short] = spark_session.table(name(backup))
        parity(original, originals[short], backup + ": backup copy")
        distinct_value(originals[short], "snapshot_id", old_snapshot, backup)
        for column in ("rule_version", "currency_assumption"):
            distinct_value(originals[short], column, baseline.get(column), backup)
        for column, wanted in (("risk_threshold_exclusive", 60), ("high_value_inr", 5000.0),
                               ("p1_account_exposure_inr", 10000.0), ("very_high_score_inclusive", 85)):
            if column in originals[short].columns:
                distinct_value(originals[short], column, wanted, backup)
        if originals[short].count() == 0:
            raise RuntimeError(backup + " is empty")
        if not exists(metadata_table):
            raise RuntimeError("Metadata disappeared during backup")
        backup_versions[backup] = version(backup)

    for short, start_version in registry_versions.items():
        backup = short + "_" + suffix
        if not exists(backup):
            write(pinned(short, start_version), backup, "errorifexists")

    def transform(df):
        result = df
        for column in df.columns:
            if column.endswith("_inr"):
                replacement = column[:-4] + "_usd"
                if replacement in df.columns:
                    raise RuntimeError("Currency-column collision: " + column)
                result = result.withColumnRenamed(column, replacement)
            elif column.endswith("_INR"):
                replacement = column[:-4] + "_USD"
                if replacement in df.columns:
                    raise RuntimeError("Currency-column collision: " + column)
                result = result.withColumnRenamed(column, replacement)
        for column, value in (("snapshot_id", new_snapshot), ("rule_version", rule), ("currency_assumption", currency)):
            if column not in result.columns:
                raise RuntimeError("Required semantic metadata column missing: " + column)
            result = result.withColumn(column, _usd_F.lit(value))
        return result

    phase = "staging"
    counts = {}
    expected_frames = {}
    for short in data_tables:
        expected = transform(originals[short])
        current = pinned(short, live_versions[short])
        current_ids = [row[0] for row in current.select("snapshot_id").distinct().limit(2).collect()]
        if current_ids == [old_snapshot]:
            parity(originals[short], current, short + ": unchanged original live snapshot")
        elif current_ids == [new_snapshot]:
            parity(expected, current, short + ": resumed USD live snapshot")
        else:
            raise RuntimeError(short + ": live rows belong to another or mixed snapshot")
        stage = short + "_" + stage_suffix
        write(expected, stage)
        actual = spark_session.table(name(stage))
        counts[short] = parity(expected, actual, stage)
        expected_frames[short] = expected
        # All original column values except the three explicit metadata substitutions
        # must match after inverse renaming, including exact signed monetary values.
        preserved = [column for column in originals[short].columns
                     if column not in ("snapshot_id", "rule_version", "currency_assumption")]
        projected = actual.select(*[_usd_F.col(column[:-4] + "_usd" if column.endswith("_inr") else
                                             column[:-4] + "_USD" if column.endswith("_INR") else column).alias(column)
                                    for column in preserved])
        parity(originals[short].select(*preserved), projected, short + ": preserved original values")

    for short, df in registry_frames.items():
        write(df, short + "_" + stage_suffix)
        parity(df, spark_session.table(name(short + "_" + stage_suffix)), short + ": staged registry")

    ready = (transform(original_metadata)
             .withColumn("status", _usd_F.lit("READY"))
             .withColumn("denomination_migrated_at_utc", _usd_F.lit(migration_time))
             .withColumn("denomination_migration", _usd_F.lit("USD interpretation; numeric values unchanged; no FX conversion")))
    preparing = ready.withColumn("status", _usd_F.lit("PREPARING"))
    write(preparing, metadata_table + "_" + stage_suffix)
    # Refuse concurrent updates rather than blending any newer serving snapshot.
    for short, start_version in (live_versions | registry_versions).items():
        if version(short) != start_version:
            raise RuntimeError("Concurrent writer detected for " + name(short) + "; live swap has not started")
    for short, start_version in backup_versions.items():
        if version(short) != start_version:
            raise RuntimeError("Rollback copy changed during staging: " + name(short))
    for short in registry_frames:
        if short not in registry_versions and exists(short):
            raise RuntimeError("Concurrent registry creation detected: " + name(short))

    phase = "gating"
    write(spark_session.table(name(metadata_table + "_" + stage_suffix)), metadata_table)
    parity(preparing, spark_session.table(name(metadata_table)), "PREPARING gate")
    try:
        phase = "publishing"
        for short in data_tables:
            # Independent staging sources avoid Spark's read-and-overwrite-same-table restriction.
            write(spark_session.table(name(short + "_" + stage_suffix)), short)
            parity(expected_frames[short], spark_session.table(name(short)), short + ": live parity")
        for short, df in registry_frames.items():
            write(spark_session.table(name(short + "_" + stage_suffix)), short)
            parity(df, spark_session.table(name(short)), short + ": live registry parity")
        for short in data_tables:
            current = spark_session.table(name(short))
            for column, wanted in (("snapshot_id", new_snapshot), ("rule_version", rule), ("currency_assumption", currency)):
                distinct_value(current, column, wanted, short)
        # Gate stayed closed throughout all data and registry replacements.
        parity(preparing, spark_session.table(name(metadata_table)), "Gate before READY")
        phase = "publishing_ready"
        write(ready, metadata_table + "_" + stage_suffix)
        write(spark_session.table(name(metadata_table + "_" + stage_suffix)), metadata_table)
        parity(ready, spark_session.table(name(metadata_table)), "Final READY metadata")
    except Exception:
        # Never auto-restore old READY over a mixed currency/schema state. Backups
        # and staging tables remain for inspection. Rerun after fixing the cause.
        try:
            # Also close the gate if final READY committed but its read-back check failed.
            write(preparing, metadata_table + "_" + stage_suffix)
            write(spark_session.table(name(metadata_table + "_" + stage_suffix)), metadata_table)
        except Exception as gate_error:
            print("Could not reconfirm PREPARING gate: " + type(gate_error).__name__ + ". Stop consumers and inspect metadata before retrying.")
        print("USD migration failed during " + phase + ". Inspect live metadata; do not force READY. Original rollback copies remain under *_" + suffix)
        raise

    result = {"status": "READY", "currency_assumption": currency, "rule_version": rule,
              "old_snapshot_id": old_snapshot, "snapshot_id": new_snapshot,
              "source_fingerprint_preserved": fingerprint, "counts": counts,
              "row_parity": "PASS: full exact row multisets and inverse-mapped original values",
              "numeric_rescaling": False, "gold_read_or_generation": False,
              "prepared_at_utc_preserved": baseline.get("prepared_at_utc"),
              "denomination_migrated_at_utc": migration_time,
              "registry_rows": {short: len(items) for short, _, items in registry_specs},
              "rollback_suffix": suffix, "staging_suffix": stage_suffix,
              "atomicity": "Sequential tables behind PREPARING gate; no cross-table transaction or in-flight revocation"}
    print(_usd_json.dumps(result, indent=2))
    return result


usd_migration_result = migrate_existing_snapshot_to_usd(
    spark, SQL_TOOLS, RAG_DOCUMENTS, PROMPTS, ACCEPTANCE_CASES,
    schema=globals().get("AGENT_SCHEMA", "finance.agent_demo_fs"))
