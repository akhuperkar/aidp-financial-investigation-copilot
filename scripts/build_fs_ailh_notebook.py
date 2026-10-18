"""Append a self-contained AILH publication appendix without changing original cells."""
import copy
import hashlib
import json
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "notebooks/financial_services_medallion_architecture_demo.ipynb"
OUTPUT = ROOT / "notebooks/financial_services_medallion_architecture_demo_ailh.ipynb"
original = json.loads(SOURCE.read_text())
revised = copy.deepcopy(original)


def add(kind, text):
    cell = {"cell_type": kind, "metadata": {},
            "source": textwrap.dedent(text).strip().splitlines(keepends=True)}
    if kind == "code":
        cell.update(execution_count=None, outputs=[])
    revised["cells"].append(cell)


add("markdown", r'''
    # Optional extension: publish Finance Gold tables to AILH

    This appendix uses the **existing `aidp_external_catalog.gold`** connection.
    It publishes independent native Oracle tables from the two `finance.gold` Delta
    tables. It does not create another external catalog or require its password.
    All 29 preceding cells, including their saved outputs, are preserved unchanged.
    Those outputs are historical; the exported appendix cells have cleared outputs.
    Use the result of your current publication run to establish target status.

    | Source Delta table | Default AILH table | Query access pattern |
    |---|---|---|
    | `finance.gold.transaction_analytics_gold` | `aidp_external_catalog.gold.TRANSACTION_ANALYTICS_GOLD` | Account and reporting month |
    | `finance.gold.fraud_detection_model_gold` | `aidp_external_catalog.gold.FRAUD_DETECTION_MODEL_GOLD` | Account and transaction date |

    **Execution:** run this appendix on an AIDP Spark cluster after the Gold tables
    exist. You can run the appendix against existing Gold tables without rerunning
    the original synthetic-data generation or ML training. Start with `enabled=True`,
    `dry_run=True` to inspect the source versions, physical Oracle owner and plan.
    Set `dry_run=False` only when ready to publish. With `enabled=False`, the appendix
    only prints configuration and DDL; it makes no Spark or database calls.

    ### Storage and layout decisions

    - Liquid clustering belongs to **Delta**, not native Oracle tables. The extension
      can adjust existing clustered source keys to `(account_id, month_year)` and
      `(account_id, transaction_date)`. It reports and skips unclustered sources:
      this instance rejects retrofitting them with `ALTER ... CLUSTER BY`. No source
      table is rebuilt as a side effect of publication. `OPTIMIZE`
      is separately configurable and off by default. No `ZORDER`, partitions or
      Delta `CLUSTER BY` clauses are sent to AILH.
    - AILH table/index DDL below uses Oracle types and account/month or account/date
      B-tree indexes. These indexes are access-path choices, not liquid clustering.
      They suit account investigation; reassess column order for month-wide reporting
      on larger data. The catalog writer creates tables but does not execute index DDL.
    - Spark maps are serialized as deterministic JSON and stored in native Oracle
      JSON columns. Readback canonicalizes JSON object key order before comparison. Amounts
      are rounded/cast to `DECIMAL(15,2)`. Average risk score is normalized to
      `DECIMAL(38,10)` before writing and readback comparison, matching the live
      connector's Oracle `NUMBER(38,10)` mapping. This rounds that published
      aggregate to ten decimal places; the source Gold value is unchanged.
      Overflow or invalid casts stop publication.
      Missing `created_timestamp` is published as NULL, rather than inventing a time.
    - The synthetic rule `is_fraud = (risk_score > 60)` is a screening label, not
      confirmed fraud or a calibrated probability. ML predictions are not published.
      No currency conversion or currency column is added.

    ### Privileges and repeat runs

    The external catalog's stored database user needs source read access and target
    create/write privileges (Oracle documents `DWROLE` for this write path). The
    destination schema must already exist. No users, schemas or grants are created.
    New target names/columns default to uppercase to avoid quoted lowercase names.

    The default `existing_table_action="replace"` refreshes only the two configured
    target tables. An existing target is reused without rewriting only after a full
    row comparison proves it is identical to the normalized source (even when the
    general `verify_full_rows` switch is off). It does not append duplicates.
    Existing target column contracts
    are checked before any writes; automatic drop-and-recreate is disabled. Choose
    `create_only` to refuse an existing target. No transaction ID/primary key is
    invented, and repeated transaction rows are retained.

    **The two connector writes are not one atomic transaction.** A failed distributed
    write can leave partial target data. The notebook reports progress, fails on a
    mismatch and does not automatically retry or claim rollback. Stop concurrent
    target writers during publication; rerun replacement after resolving a failure.
''')

add("code", r'''
    # AILH connection = existing AIDP external catalog; no catalog password here.
    AILH_CONNECTION = {
        "catalog": "aidp_external_catalog",
        "catalog_schema": "gold",       # spelling shown in AIDP Master Catalog
        "oracle_schema": None,          # auto-resolve physical owner; set if ambiguous
    }
    AILH_PUBLICATION = {
        "enabled": False,               # True enables read-only preflight
        "dry_run": True,                # False enables publication and optional DDL
        "source_catalog": "finance",
        "source_schema": "gold",
        "existing_table_action": "replace",   # replace | create_only (no append)
        "write_batch_size": 1000,
        "write_partitions": 2,          # limit concurrent database writers
        "align_source_liquid_clustering": True,  # adjust existing clustered tables only
        "optimize_source_gold": False, # incremental OPTIMIZE; can be expensive
        "verify_full_rows": True,      # multiset comparison, including duplicate rows
        "refresh_catalog_metadata": True,
    }
    AILH_TARGET_TABLES = {
        "transaction_analytics_gold": "TRANSACTION_ANALYTICS_GOLD",
        "fraud_detection_model_gold": "FRAUD_DETECTION_MODEL_GOLD",
    }

    # Optional native DDL execution. Default publication uses catalog credentials.
    # Enable ONLY if explicit table/index DDL is wanted from this notebook.
    # Otherwise copy the generated DDL into an authorized Oracle SQL client.
    AILH_NATIVE_DDL = {
        "execute": False,
        "create_indexes": True,
        "dsn_env": "FS_AILH_DSN",                 # TNS alias or TCPS connect string
        "user_env": "FS_AILH_USER",
        "password_env": "FS_AILH_PASSWORD",
        "config_dir_env": "FS_AILH_TNS_ADMIN",    # optional tnsnames.ora directory
        "wallet_dir_env": "FS_AILH_WALLET_DIR",  # optional extracted PEM wallet
        "wallet_password_env": "FS_AILH_WALLET_PASSWORD",
    }
''')

add("markdown", r'''
    ## 1. Define the native table contract and generate idempotent DDL

    AIDP external catalog SQL does **not** support arbitrary DDL. Do not run
    `spark.sql("CREATE TABLE ...")` against the external catalog and do not send DDL
    via the connector's `pushdown.sql` option. That option is used below for bounded
    metadata SELECTs only.

    There are two supported routes:

    1. **Default, existing catalog credentials:** the three-part external-catalog
       `saveAsTable` write path supplies AIDP's catalog and staging context. It creates
       an absent table (`write.mode=CREATE`), or replaces data in a compatible existing
       table (`OVERWRITE`). A create-only override selects native JSON for the two
       map payloads; standard Spark strings, decimals and timestamps use
       connector mappings. Their actual schema is checked on readback. The native
       DDL route below provides explicit text lengths and native types when needed.
       The existence check supplies create-if-absent behavior without Spark DDL.
    2. **Explicit Oracle DDL:** run the generated `CREATE TABLE IF NOT EXISTS` and
       optional `CREATE INDEX IF NOT EXISTS` statements in a native Oracle client,
       or enable the optional `python-oracledb` helper below. This helper requires its
       own authorized connection; AIDP does not expose the catalog password to Python.
       Native execution here requires Oracle 23ai/26ai or later compatible syntax.

    The preview uses an uppercase owner if the physical owner has not been resolved
    yet. The enabled preflight resolves the owner from the existing catalog and
    prints the final DDL. `IF NOT EXISTS` does not migrate incompatible existing tables.
''')

add("code", r'''
    import hashlib as _ailh_hashlib
    import json as _ailh_json
    import re as _ailh_re

    # (name, Spark projection type, native Oracle type, max text length or None)
    AILH_SPECS = {
        "transaction_analytics_gold": {
            "cluster": ("account_id", "month_year"),
            "totals": ("TOTAL_TRANSACTIONS", "TOTAL_AMOUNT", "HIGH_RISK_TRANSACTIONS"),
            "json_maps": ("transaction_types", "merchant_categories"),
            "columns": [
                ("ACCOUNT_ID", "string", "VARCHAR2(32 CHAR)", 32),
                ("MONTH_YEAR", "string", "VARCHAR2(7 CHAR)", 7),
                ("TOTAL_TRANSACTIONS", "decimal(19,0)", "NUMBER(19,0)", None),
                ("TOTAL_AMOUNT", "decimal(15,2)", "NUMBER(15,2)", None),
                ("AVG_AMOUNT", "decimal(15,2)", "NUMBER(15,2)", None),
                ("AVG_RISK_SCORE", "decimal(38,10)", "NUMBER(38,10)", None),
                ("HIGH_RISK_TRANSACTIONS", "decimal(19,0)", "NUMBER(19,0)", None),
                ("TRANSACTION_TYPES", "string", "JSON", None),
                ("MERCHANT_CATEGORIES", "string", "JSON", None),
                ("CREATED_TIMESTAMP", "timestamp", "TIMESTAMP(6)", None),
            ],
        },
        "fraud_detection_model_gold": {
            "cluster": ("account_id", "transaction_date"),
            "totals": ("AMOUNT", "IS_FRAUD"),
            "json_maps": (),
            "columns": [
                ("ACCOUNT_ID", "string", "VARCHAR2(32 CHAR)", 32),
                ("TRANSACTION_DATE", "timestamp", "TIMESTAMP(6)", None),
                ("TRANSACTION_TYPE", "string", "VARCHAR2(32 CHAR)", 32),
                ("AMOUNT", "decimal(15,2)", "NUMBER(15,2)", None),
                ("MERCHANT_CATEGORY", "string", "VARCHAR2(128 CHAR)", 128),
                ("LOCATION", "string", "VARCHAR2(128 CHAR)", 128),
                ("RISK_SCORE", "decimal(10,0)", "NUMBER(10,0)", None),
                ("MONTH", "decimal(10,0)", "NUMBER(10,0)", None),
                ("DAY_OF_WEEK", "decimal(10,0)", "NUMBER(10,0)", None),
                ("HOUR", "decimal(10,0)", "NUMBER(10,0)", None),
                ("IS_FRAUD", "decimal(10,0)", "NUMBER(10,0)", None),
                ("CREATED_TIMESTAMP", "timestamp", "TIMESTAMP(6)", None),
            ],
        },
    }

    def _ailh_identifier(value):
        # Restrict identifiers before constructing Spark or native Oracle SQL.
        if not isinstance(value, str) or not _ailh_re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,127}", value):
            raise ValueError("Use a simple identifier: letter followed by letters, digits or underscores.")
        return value

    def _ailh_spark_name(*parts):
        # AIDP's catalog bridge misresolves quoted multipart namespaces.
        # Every component is restricted to simple identifiers before joining.
        return ".".join(_ailh_identifier(p) for p in parts)

    def _ailh_oracle_name(*parts):
        return ".".join('"' + _ailh_identifier(p) + '"' for p in parts)

    def _ailh_validate_config():
        for key in ("catalog", "catalog_schema"):
            _ailh_identifier(AILH_CONNECTION[key])
        if AILH_CONNECTION["oracle_schema"] is not None:
            _ailh_identifier(AILH_CONNECTION["oracle_schema"])
        for key in ("source_catalog", "source_schema"):
            _ailh_identifier(AILH_PUBLICATION[key])
        if AILH_PUBLICATION["existing_table_action"] not in ("replace", "create_only"):
            raise ValueError("existing_table_action must be replace or create_only; append duplicates are not supported.")
        for key in ("enabled", "dry_run", "align_source_liquid_clustering", "optimize_source_gold",
                    "verify_full_rows", "refresh_catalog_metadata"):
            if type(AILH_PUBLICATION[key]) is not bool:
                raise ValueError(key + " must be Python True or False, not a string.")
        for key in ("execute", "create_indexes"):
            if type(AILH_NATIVE_DDL[key]) is not bool:
                raise ValueError("Native DDL " + key + " must be Python True or False.")
        if AILH_NATIVE_DDL["execute"] and AILH_PUBLICATION["existing_table_action"] == "create_only":
            raise ValueError("Native pre-creation requires replace mode; create_only refuses all existing tables.")
        for key, maximum in (("write_batch_size", 100000), ("write_partitions", 16)):
            value = AILH_PUBLICATION[key]
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError(f"{key} must be an integer from 1 to {maximum}.")
        if set(AILH_TARGET_TABLES) != set(AILH_SPECS):
            raise ValueError("Provide exactly the two Finance Gold table mappings.")
        targets = [_ailh_identifier(v) for v in AILH_TARGET_TABLES.values()]
        if len({v.casefold() for v in targets}) != len(targets):
            raise ValueError("Target table names must be distinct, including case-insensitive matches.")
        if any(t != t.upper() for t in targets):
            raise ValueError("Use uppercase target names so native Oracle casing stays unambiguous.")
        if AILH_PUBLICATION["source_catalog"].casefold() == AILH_CONNECTION["catalog"].casefold():
            raise ValueError("Source and external target catalogs must be different.")

    def _ailh_ddl(owner, include_indexes=True):
        statements = []
        for source, spec in AILH_SPECS.items():
            target = AILH_TARGET_TABLES[source]
            name = _ailh_oracle_name(owner, target)
            columns = ",\n".join("    " + _ailh_oracle_name(c[0]) + " " + c[2] for c in spec["columns"])
            statements.append(f"CREATE TABLE IF NOT EXISTS {name} (\n{columns}\n)")
            if include_indexes:
                # Stable, <=30-character index name that changes with owner/table/keys.
                signature = owner + "." + target + ":" + ",".join(spec["cluster"])
                index = "FS_" + _ailh_hashlib.sha256(signature.encode()).hexdigest()[:18].upper() + "_IX"
                keys = ", ".join(_ailh_oracle_name(c.upper()) for c in spec["cluster"])
                statements.append(f"CREATE INDEX IF NOT EXISTS {_ailh_oracle_name(owner, index)} ON {name} ({keys})")
        return statements

    def _ailh_plan():
        _ailh_validate_config()
        return [{"source": ".".join((AILH_PUBLICATION["source_catalog"], AILH_PUBLICATION["source_schema"], source)),
                 "target": ".".join((AILH_CONNECTION["catalog"], AILH_CONNECTION["catalog_schema"], target)),
                 "existing_table_action": AILH_PUBLICATION["existing_table_action"]}
                for source, target in AILH_TARGET_TABLES.items()]

    print(_ailh_json.dumps(_ailh_plan(), indent=2))
    _preview_owner = AILH_CONNECTION["oracle_schema"] or AILH_CONNECTION["catalog_schema"].upper()
    print("DDL PREVIEW: physical Oracle owner must be verified by the enabled preflight.")
    print(";\n\n".join(_ailh_ddl(_preview_owner, AILH_NATIVE_DDL["create_indexes"])) + ";")
''')

add("markdown", r'''
    ## 2. Optional native DDL connection

    Skip this connection route when using automatic connector creation. If you enable
    `AILH_NATIVE_DDL["execute"]`, supply the named environment variables through your
    AIDP compute's secret/environment mechanism and make `python-oracledb` available
    in its Python environment. Do not put passwords or wallet contents into this notebook.
    The direct connection must point to the **same AILH database** as the external
    catalog and have DDL privileges in the resolved owner schema. With mTLS, use an
    extracted wallet directory containing the PEM wallet; a wallet ZIP path is not a
    `python-oracledb` wallet directory. TLS server identity checks remain enabled.

    DDL auto-commits. The helper is called only by an enabled, non-dry-run publication.
    It does not grant privileges, migrate existing tables or ignore SQL errors.
''')

add("code", r'''
    def _ailh_execute_native_ddl(owner):
        if not AILH_NATIVE_DDL["execute"]:
            return
        import os
        try:
            import oracledb
        except ImportError as exc:
            raise RuntimeError("Optional native DDL requires python-oracledb in the AIDP Python environment.") from exc
        def env_value(key, required=False):
            value = os.environ.get(AILH_NATIVE_DDL[key], "")
            if required and not value:
                raise ValueError("Missing required connection environment variable: " + AILH_NATIVE_DDL[key])
            return value
        options = {"dsn": env_value("dsn_env", True), "user": env_value("user_env", True),
                   "password": env_value("password_env", True), "ssl_server_dn_match": True}
        for key, option in (("config_dir_env", "config_dir"), ("wallet_dir_env", "wallet_location"),
                            ("wallet_password_env", "wallet_password")):
            value = env_value(key)
            if value:
                options[option] = value
        with oracledb.connect(**options) as connection:
            if int(connection.version.split(".")[0]) < 23:
                raise RuntimeError("This native IF NOT EXISTS DDL route requires Oracle 23ai/26ai or newer.")
            with connection.cursor() as cursor:
                for statement in _ailh_ddl(owner, AILH_NATIVE_DDL["create_indexes"]):
                    cursor.execute(statement)  # no trailing semicolon in the Python driver
        print("Native table/index DDL completed. Existing compatible objects were retained.")
''')

add("markdown", r'''
    ## 3. Read pinned Gold snapshots and validate the publication contract

    Every run pins each Delta table's version independently, materializes both source
    projections and validates existing target schemas before writing either table.
    This keeps an individual source stable while publishing; it does not establish
    a cross-table transaction or prove that both source versions came from one batch.
    Run after the upstream Gold pipeline has completed, with no concurrent Gold refresh.

    Validation rejects missing required columns, numeric overflow, text truncation,
    blank strings that Oracle would turn into NULL, unsupported map types and empty
    source tables. The JSON columns retain the two map distributions. The optional
    `created_timestamp` column remains NULL when absent in the persisted source.
''')

add("code", r'''
    def _ailh_read_options(owner, table):
        return {"catalog.id": AILH_CONNECTION["catalog"], "schema": owner, "table": table}

    def _ailh_metadata_query(spark_session, query):
        return (spark_session.read.format("aidataplatform")
                .option("catalog.id", AILH_CONNECTION["catalog"])
                .option("schema", AILH_CONNECTION["catalog_schema"])
                .option("pushdown.sql", query).load())

    def _ailh_resolve_owner(spark_session):
        configured = AILH_CONNECTION["oracle_schema"]
        value = _ailh_identifier(configured or AILH_CONNECTION["catalog_schema"])
        predicate = f"USERNAME = '{value}'" if configured else f"LOWER(USERNAME) = '{value.lower()}'"
        rows = _ailh_metadata_query(spark_session, "SELECT USERNAME FROM ALL_USERS WHERE " + predicate).collect()
        if len(rows) != 1:
            raise ValueError("Cannot resolve one native Oracle owner. Set AILH_CONNECTION['oracle_schema'] to its exact spelling.")
        return _ailh_identifier(rows[0][0])

    def _ailh_target_exists(spark_session, owner, table):
        _ailh_identifier(owner)
        _ailh_identifier(table)
        sql = f"SELECT TABLE_NAME FROM ALL_TABLES WHERE OWNER = '{owner}' AND TABLE_NAME = '{table}'"
        return bool(_ailh_metadata_query(spark_session, sql).take(1))

    def _ailh_target_read(spark_session, owner, table):
        return (spark_session.read.format("aidataplatform")
                .options(**_ailh_read_options(owner, table)).load())

    def _ailh_normalize(source_df, spec):
        from pyspark.sql import functions as SF
        from pyspark.sql.types import MapType, StringType, LongType, IntegerType
        fields = {f.name: f.dataType for f in source_df.schema.fields}
        required = {c[0].lower() for c in spec["columns"]} - {"created_timestamp"}
        missing = sorted(required - set(fields))
        if missing:
            raise ValueError("Persisted Gold source is missing columns: " + ", ".join(missing))
        expressions, invalid = [], []
        for name, spark_type, _, max_length in spec["columns"]:
            source = name.lower()
            raw = SF.col(source) if source in fields else SF.lit(None)
            if source in spec["json_maps"]:
                dtype = fields[source]
                if not (isinstance(dtype, MapType) and isinstance(dtype.keyType, StringType)
                        and isinstance(dtype.valueType, (LongType, IntegerType))):
                    raise TypeError(source + " must be MAP<STRING, INT/BIGINT>.")
                raw = SF.to_json(SF.map_from_entries(SF.array_sort(SF.map_entries(raw))))
            converted = raw.cast(spark_type)
            invalid.append(raw.isNotNull() & converted.isNull())
            if spark_type.startswith("decimal(") and spark_type.endswith(",0)"):
                invalid.append(raw != converted)  # do not silently truncate fractional counts/labels
            if max_length is not None:
                invalid.append(SF.length(converted) > max_length)
                invalid.append(raw.isNotNull() & (SF.length(SF.trim(converted)) == 0))
            if spark_type == "double":
                invalid.append(SF.isnan(converted) | (SF.abs(converted) == float("inf")))
            expressions.append(converted.alias(name))
        condition = invalid[0]
        for item in invalid[1:]:
            condition = condition | item
        if source_df.where(condition).limit(1).count():
            raise ValueError("Source values violate the target contract (overflow, non-finite value, blank or overlong text).")
        return source_df.select(*expressions)

    def _ailh_schema_errors(actual_types, spec):
        expected = {c[0]: c[1] for c in spec["columns"]}
        errors = []
        if set(actual_types) != set(expected):
            errors.append("Target column names must match the uppercase contract exactly; no extra or missing columns.")
        for column, wanted in expected.items():
            actual = actual_types.get(column)
            if actual is None:
                continue
            if wanted == "timestamp" and actual in ("timestamp", "timestamp_ntz"):
                continue
            if actual != wanted:
                errors.append(f"{column}: expected {wanted}, got {actual}")
        return errors

    def _ailh_check_target_schema(target_df, spec):
        errors = _ailh_schema_errors({f.name: f.dataType.simpleString() for f in target_df.schema.fields}, spec)
        if errors:
            raise ValueError("Incompatible existing AILH table; no automatic recreation. " + "; ".join(errors))

    def _ailh_prepare(spark_session, owner):
        prepared = []
        try:
            for source, spec in AILH_SPECS.items():
                source_name = _ailh_spark_name(AILH_PUBLICATION["source_catalog"], AILH_PUBLICATION["source_schema"], source)
                details = spark_session.sql(f"DESCRIBE DETAIL {source_name}").first().asDict()
                if str(details.get("format", "")).lower() != "delta":
                    raise ValueError("Expected a Delta Gold source: " + source_name)
                version = int(spark_session.sql(f"DESCRIBE HISTORY {source_name} LIMIT 1").first()["version"])
                snapshot = spark_session.sql(f"SELECT * FROM {source_name} VERSION AS OF {version}")
                projected = _ailh_normalize(snapshot, spec).persist()
                item = {"source": source, "source_name": source_name, "source_version": version,
                        "target": AILH_TARGET_TABLES[source], "frame": projected, "spec": spec,
                        "source_clustering": list(details.get("clusteringColumns") or [])}
                prepared.append(item)  # retain handle for cleanup even if the next action fails
                item["rows"] = projected.count()
                if item["rows"] == 0:
                    raise ValueError("Refusing to replace AILH with an empty Gold source: " + source_name)
                item["exists"] = _ailh_target_exists(spark_session, owner, item["target"])
                if item["exists"]:
                    if AILH_PUBLICATION["existing_table_action"] == "create_only":
                        raise ValueError("create_only refuses the existing target: " + item["target"])
                    _ailh_check_target_schema(_ailh_target_read(spark_session, owner, item["target"]), spec)
            return prepared
        except Exception:
            for item in prepared:
                item["frame"].unpersist()
            raise
''')

add("markdown", r'''
    ## 4. Align source Delta layout, publish and verify

    Source liquid keys are only altered for an already clustered table when the keys
    differ. An unclustered source is reported and skipped, so publication does not
    depend on a source-table rebuild or unsupported protocol change. Delta documents
    enabling clustering on an existing unclustered table through ALTER for 3.3+;
    the current instance rejected that operation. Optional incremental `OPTIMIZE`
    materializes eligible layout changes. Existing clustered files are not guaranteed
    to be fully rewritten. The result records the actual source layout action.

    Each publication verifies row count and exact decimal totals. With
    `verify_full_rows=True`, it also performs a full bidirectional `exceptAll`
    comparison after type normalization, so dropped/duplicated transaction rows or
    altered JSON/timestamps fail validation. This reads both published Gold tables
    back through the catalog connection; keep the complete check for this demo.

    Existing identical tables are verified and reused. A changed target uses the
    connector's replacement path with recreation disabled. On this instance that
    path rejected an identical TIMESTAMP shape with `DATA_ACCESS_LAYER_0068`.
    If it recurs for changed data, stop and use new configured target names, or
    obtain a reviewed connector/schema fix; this code does not drop tables to
    bypass it. Reusing identical data does not prove changed-data replacement works.

    No automatic append/merge is used because the transaction table has no stable
    transaction key. Target metadata refresh is requested after data verification;
    metadata harvesting can finish asynchronously in AIDP Job Runs.
''')

add("code", r'''
    def _ailh_align_layout(spark_session, prepared):
        for item in prepared:
            keys = item["spec"]["cluster"]
            item["source_layout"] = "unchanged"
            if AILH_PUBLICATION["align_source_liquid_clustering"]:
                if not item["source_clustering"]:
                    item["source_layout"] = "unclustered; not retrofitted"
                    print("Source layout skipped:", item["source_name"],
                          "is unclustered. No ALTER or rebuild was attempted.")
                elif tuple(item["source_clustering"]) != tuple(keys):
                    columns = ", ".join(_ailh_spark_name(c) for c in keys)
                    spark_session.sql(f"ALTER TABLE {item['source_name']} CLUSTER BY ({columns})")
                    item["source_layout"] = "existing clustering keys updated"
                else:
                    item["source_layout"] = "already aligned"
            if AILH_PUBLICATION["optimize_source_gold"]:
                spark_session.sql(f"OPTIMIZE {item['source_name']}")

    def _ailh_summary(frame, spec):
        from pyspark.sql import functions as SF
        expressions = [SF.count(SF.lit(1)).alias("rows")]
        expressions += [SF.sum(SF.col(c)).alias(c) for c in spec["totals"]]
        return frame.agg(*expressions).first().asDict()

    def _ailh_summary_errors(expected, actual):
        return [f"{key}: source={value}, target={actual.get(key)}"
                for key, value in expected.items() if actual.get(key) != value]

    class _AilhReconciliationError(RuntimeError):
        """Data differs; connector/permission failures must not be treated as mismatches."""

    def _ailh_verify(spark_session, owner, item, full_rows=None):
        from pyspark.sql import functions as SF
        remote = _ailh_target_read(spark_session, owner, item["target"])
        _ailh_check_target_schema(remote, item["spec"])
        expressions = []
        for name, dtype, _, _ in item["spec"]["columns"]:
            column = SF.col(name).cast(dtype)
            if name.lower() in item["spec"]["json_maps"]:
                parsed = SF.from_json(column, "MAP<STRING,BIGINT>")
                column = SF.to_json(SF.map_from_entries(SF.array_sort(SF.map_entries(parsed))))
            expressions.append(column.alias(name))
        target = remote.select(*expressions).persist()
        try:
            errors = _ailh_summary_errors(_ailh_summary(item["frame"], item["spec"]),
                                          _ailh_summary(target, item["spec"]))
            if errors:
                raise _AilhReconciliationError("Publication reconciliation failed: " + "; ".join(errors))
            if AILH_PUBLICATION["verify_full_rows"] if full_rows is None else full_rows:
                if (item["frame"].exceptAll(target).limit(1).count()
                        or target.exceptAll(item["frame"]).limit(1).count()):
                    raise _AilhReconciliationError("Full row comparison failed, including duplicate multiplicities.")
        finally:
            target.unpersist()

    def _ailh_write(spark_session, owner, item):
        # Recheck existence/schema immediately before writing; never drop/recreate.
        exists = _ailh_target_exists(spark_session, owner, item["target"])
        if exists:
            if AILH_PUBLICATION["existing_table_action"] == "create_only":
                raise ValueError("Target appeared after preflight; create_only stopped publication.")
            _ailh_check_target_schema(_ailh_target_read(spark_session, owner, item["target"]), item["spec"])
            try:
                _ailh_verify(spark_session, owner, item, full_rows=True)
            except _AilhReconciliationError:
                pass  # Changed data: use the documented replacement path below.
            else:
                print("Existing target fully verified; no rewrite:", item["target"])
                return "reused_identical"
        options = {
            "write.mode": "OVERWRITE" if exists else "CREATE",
            "write.batch.size": str(AILH_PUBLICATION["write_batch_size"]),
            "write.reject.limit": "0",
            "overwrite.with.recreate": "false",
        }
        if not exists:
            # This option accepts special native types, not VARCHAR/NUMBER/TIMESTAMP.
            overrides = [c[0] + " JSON" for c in item["spec"]["columns"] if c[2] == "JSON"]
            if overrides:
                options["preserve.oracle.column.types"] = ", ".join(overrides)
        destination = _ailh_spark_name(AILH_CONNECTION["catalog"],
                                       AILH_CONNECTION["catalog_schema"], item["target"])
        (item["frame"].coalesce(AILH_PUBLICATION["write_partitions"])
         .write.options(**options).mode("overwrite" if exists else "errorifexists")
         .saveAsTable(destination))
        return "replaced" if exists else "created"

    def run_ailh_publication(spark_session=None):
        plan = _ailh_plan()
        if not AILH_PUBLICATION["enabled"]:
            print("AILH publication disabled. No Spark/database calls were made by this appendix.")
            return {"status": "disabled", "plan": plan}
        if spark_session is None:
            raise RuntimeError("Pass the existing AIDP Spark session: run_ailh_publication(spark).")
        owner = _ailh_resolve_owner(spark_session)
        print("Resolved native Oracle owner:", owner)
        print(";\n\n".join(_ailh_ddl(owner, AILH_NATIVE_DDL["create_indexes"])) + ";")
        prepared = _ailh_prepare(spark_session, owner)
        verified, attempted = [], []
        try:
            for item in prepared:
                print(_ailh_json.dumps({k: item[k] for k in ("source", "source_version", "target", "rows", "exists", "source_clustering")}))
            if AILH_PUBLICATION["dry_run"]:
                print("DRY RUN: preflight passed. No source ALTER/OPTIMIZE, native DDL or target writes were executed.")
                return {"status": "dry_run", "owner": owner, "plan": plan}
            _ailh_align_layout(spark_session, prepared)
            _ailh_execute_native_ddl(owner)
            for item in prepared:
                attempted.append(item["target"])
                action = _ailh_write(spark_session, owner, item)
                if action != "reused_identical":
                    _ailh_verify(spark_session, owner, item)
                verified.append({"target": item["target"], "source_version": item["source_version"],
                                 "rows": item["rows"], "write_action": action,
                                 "source_layout": item.get("source_layout", "unchanged"),
                                 "verification": "full_rows" if action == "reused_identical" or AILH_PUBLICATION["verify_full_rows"] else "counts_and_totals"})
                print("Verified:", _ailh_json.dumps(verified[-1]))
            refresh = "not_requested"
            if AILH_PUBLICATION["refresh_catalog_metadata"]:
                try:
                    qualified = _ailh_spark_name(AILH_CONNECTION["catalog"], AILH_CONNECTION["catalog_schema"])
                    spark_session.sql("REFRESH SCHEMA IN EXTERNAL CATALOG " + qualified)
                    refresh = "requested; inspect Job Runs for metadata completion"
                except Exception as exc:
                    refresh = "failed; refresh the external schema in Master Catalog"
                    print("Data verified; metadata refresh failed:", type(exc).__name__)
            return {"status": "verified", "owner": owner, "tables": verified, "metadata_refresh": refresh}
        except Exception:
            print("Publication stopped. Verified targets:", [t["target"] for t in verified])
            print("Attempted targets (may contain partial writes):", attempted)
            print("No cross-table rollback or automatic retry was performed.")
            raise
        finally:
            for item in prepared:
                item["frame"].unpersist()
''')

add("code", r'''
    # With the default enabled=False this is safe without a Spark session.
    ail_publication_result = run_ailh_publication(globals().get("spark"))
    print(_ailh_json.dumps(ail_publication_result, indent=2))
''')

add("markdown", r'''
    ## 5. Run checklist and troubleshooting

    1. Confirm the original Gold tables already exist. Leave the first 29 cells alone
       if preserving the current demo dataset and model is important.
    2. Review the connection, schema and table mapping cell. The default uses
       `aidp_external_catalog` and schema `gold` from this instance. A native Oracle
       owner is discovered through this catalog; override `oracle_schema` only when
       necessary. Uppercase target table/column names are intentional.
    3. Set `enabled=True`, keep `dry_run=True`, then run the appendix top-to-bottom.
       Check both pinned source versions, row counts, existing target schemas, and
       the resolved DDL. A dry run does not prove writer privileges or connector
       create/type-option support; it only exercises the read/preflight path.
    4. If indexes/explicit DDL are wanted, execute the printed DDL in an authorized
       native Oracle SQL client before publication, or configure the optional native
       helper. If SQL is run outside the notebook, rerun preflight afterwards. The
       default connector creation route does not create the optional indexes.
    5. Set `dry_run=False` and rerun the appendix. A successful run returns
       `status="verified"` with two verified target records. The full check includes
       JSON values and duplicate row multiplicity, not just the displayed totals.
    6. Refresh `aidp_external_catalog.gold` in Master Catalog if needed and wait for
       its metadata Job Run. Read the new tables using their discovered names:
       `spark.table("aidp_external_catalog.gold.TRANSACTION_ANALYTICS_GOLD").show(5)`.

    **Common failures:** missing catalog write grants → ask the owner to grant the
    required privileges; ambiguous owner → set the exact native owner spelling;
    incompatible schema → choose new target names or perform a reviewed migration;
    unsupported create-only native type option → pre-create using the printed DDL
    and rerun, rather than silently falling back to short VARCHAR JSON columns;
    unsupported source `ALTER ... CLUSTER BY` → use a compatible Delta runtime or
    disable source alignment explicitly after checking the existing layout.
    A failed write requires inspection of the attempted target and a clean replacement
    rerun; append is not a recovery strategy.

    ### Validation status and references

    The added code is provided for execution in **AIDP Spark with its ORACLE_ALH
    connector**. The export clears new-cell outputs; live validation observations
    are recorded separately in the accompanying validation report. A current run
    must return two verified targets to establish current publication success.
    The existing historical outputs were kept to preserve the supplied notebook.

    - [Oracle AIDP external catalogs: privileges, casing, DDL limitations and refresh](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/external-catalogs.html)
    - [Oracle's ORACLE_ALH connector examples and option reference](https://github.com/oracle-samples/oracle-aidp-samples/blob/main/data-engineering/ingestion/Read_Write_Oracle_Ecosystem_Connectors/Autonomous_AI_Lakehouse.ipynb)
    - [Oracle sample: execute native AILH SQL with python-oracledb](https://github.com/oracle-samples/oracle-aidp-samples/blob/main/data-engineering/ingestion/Execute%20Oracle%20ALH%20SQL.ipynb)
    - [Delta Lake liquid clustering and OPTIMIZE](https://docs.delta.io/delta-clustering/)
    - [Oracle native CREATE TABLE syntax](https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/CREATE-TABLE.html)
    - [python-oracledb connection configuration](https://python-oracledb.readthedocs.io/en/latest/user_guide/connection_handling.html)
''')

# Preserve original cells; complete standard kernel display metadata and add provenance.
revised["metadata"]["kernelspec"].setdefault("display_name", "AIDP Spark (existing session)")
revised["metadata"]["ailh_publication_extension"] = {
    "original_cell_count": len(original["cells"]),
    "original_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "execution_status": "appendix outputs cleared; live observations recorded separately",
}
assert revised["cells"][:len(original["cells"])] == original["cells"]
OUTPUT.write_text(json.dumps(revised, ensure_ascii=False, indent=1) + "\n")
print(OUTPUT)
print(f"Preserved {len(original['cells'])} original cells; appended {len(revised['cells']) - len(original['cells'])} cells.")
