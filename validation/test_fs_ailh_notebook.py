"""Local contract/failure tests. They do not emulate the AIDP connector or Spark."""
import contextlib
import copy
from decimal import Decimal
import io
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "notebooks/financial_services_medallion_architecture_demo.ipynb"
TARGET = ROOT / "notebooks/financial_services_medallion_architecture_demo_ailh.ipynb"


class AilhNotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads(SOURCE.read_text())
        cls.revised = json.loads(TARGET.read_text())

    def setUp(self):
        self.ns = {}
        with contextlib.redirect_stdout(io.StringIO()):
            for cell in self.revised["cells"][len(self.original["cells"]):]:
                if cell["cell_type"] == "code":
                    exec(compile("".join(cell["source"]), "<ailh appendix>", "exec"), self.ns)

    def test_original_cells_are_preserved_including_outputs(self):
        self.assertEqual(self.revised["cells"][:29], self.original["cells"])
        self.assertEqual(len(self.original["cells"]), 29)

    def test_all_code_cells_compile(self):
        for number, cell in enumerate(self.revised["cells"], 1):
            if cell["cell_type"] == "code":
                compile("".join(cell["source"]), f"cell {number}", "exec")

    def test_identifiers_reject_injection_and_dotted_names(self):
        for value in ('GOLD; DROP TABLE x', 'a.b', 'x"y', 'a`b', '', None, ' gold', 'x\ny'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.ns["_ailh_identifier"](value)
        # AIDP's catalog bridge misresolves quoted namespace components.
        self.assertEqual(self.ns["_ailh_spark_name"]("finance", "gold"), "finance.gold")
        self.assertEqual(self.ns["_ailh_oracle_name"]("GOLD", "TABLE_1"), '"GOLD"."TABLE_1"')

    def test_target_collisions_fail_before_publication(self):
        tables = self.ns["AILH_TARGET_TABLES"]
        tables["fraud_detection_model_gold"] = tables["transaction_analytics_gold"]
        with self.assertRaisesRegex(ValueError, "distinct"):
            self.ns["_ailh_validate_config"]()

    def test_string_false_cannot_enable_publication(self):
        self.ns["AILH_PUBLICATION"]["enabled"] = "False"
        with self.assertRaisesRegex(ValueError, "True or False"):
            self.ns["run_ailh_publication"]()

    def test_append_and_invalid_writer_limits_are_refused(self):
        cfg = self.ns["AILH_PUBLICATION"]
        original = copy.deepcopy(cfg)
        for key, value in (("existing_table_action", "append"), ("write_partitions", 0),
                           ("write_batch_size", True), ("write_partitions", 100)):
            cfg.update(original)
            cfg[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.ns["_ailh_validate_config"]()

    def test_ddl_has_native_json_storage_and_no_delta_layout(self):
        sql = self.ns["_ailh_ddl"]("GOLD")
        self.assertEqual(len(sql), 4)
        tables = [s for s in sql if s.startswith("CREATE TABLE IF NOT EXISTS")]
        self.assertEqual(len(tables), 2)
        self.assertIn('"TRANSACTION_TYPES" JSON', tables[0])
        self.assertIn('"AMOUNT" NUMBER(15,2)', tables[1])
        self.assertTrue(all('USING DELTA' not in s and 'CLUSTER BY' not in s and 'DROP ' not in s for s in sql))
        indexes = [s for s in sql if s.startswith("CREATE INDEX")]
        self.assertIn('("ACCOUNT_ID", "MONTH_YEAR")', indexes[0])
        self.assertIn('("ACCOUNT_ID", "TRANSACTION_DATE")', indexes[1])
        self.assertNotEqual(indexes[0].split(' ON ')[0], indexes[1].split(' ON ')[0])
        self.assertEqual(len(self.ns["_ailh_ddl"]("GOLD", False)), 2)

    def test_incompatible_target_fails_instead_of_being_recreated(self):
        spec = self.ns["AILH_SPECS"]["transaction_analytics_gold"]
        fields = {c[0]: c[1] for c in spec["columns"]}
        self.assertEqual(self.ns["_ailh_schema_errors"](fields, spec), [])
        fields["TOTAL_AMOUNT"] = "decimal(8,2)"
        fields["EXTRA_COLUMN"] = "string"
        errors = self.ns["_ailh_schema_errors"](fields, spec)
        self.assertTrue(any("TOTAL_AMOUNT" in e for e in errors))
        self.assertTrue(any("extra or missing" in e for e in errors))

    def test_count_and_decimal_reconciliation_detects_loss(self):
        expected = {"rows": 10, "TOTAL_AMOUNT": Decimal("1.20")}
        self.assertEqual(self.ns["_ailh_summary_errors"](expected, {"rows": 10, "TOTAL_AMOUNT": Decimal("1.2")}), [])
        errors = self.ns["_ailh_summary_errors"](expected, {"rows": 9, "TOTAL_AMOUNT": Decimal("1.19")})
        self.assertEqual(len(errors), 2)
        self.assertTrue(self.ns["_ailh_summary_errors"](expected, {"rows": 10}))

    def test_risk_average_has_explicit_roundtrip_decimal_precision(self):
        # The live Oracle connector reads its default NUMBER mapping as (38,10).
        # Normalize before writing as well as reading, rather than relaxing checks
        # and silently comparing rounded decimals with original binary doubles.
        spec = self.ns["AILH_SPECS"]["transaction_analytics_gold"]
        score = next(c for c in spec["columns"] if c[0] == "AVG_RISK_SCORE")
        self.assertEqual(score[1:3], ("decimal(38,10)", "NUMBER(38,10)"))
        fields = {c[0]: c[1] for c in spec["columns"]}
        fields["AVG_RISK_SCORE"] = "decimal(38,10)"
        self.assertEqual(self.ns["_ailh_schema_errors"](fields, spec), [])
        fields["AVG_RISK_SCORE"] = "decimal(8,2)"
        self.assertTrue(self.ns["_ailh_schema_errors"](fields, spec))

    def test_disabled_path_makes_no_spark_calls(self):
        spark = Mock()
        with contextlib.redirect_stdout(io.StringIO()):
            result = self.ns["run_ailh_publication"](spark)
        self.assertEqual(result["status"], "disabled")
        self.assertEqual(spark.mock_calls, [])

    def test_metadata_query_supplies_schema_for_live_connector_inference(self):
        # Removing schema recreates observed DATA_ACCESS_LAYER_0013 before JDBC.
        class RecordingReader:
            def __init__(self):
                self.values = {}
            def format(self, value):
                self.values["format"] = value
                return self
            def option(self, key, value):
                self.values[key] = value
                return self
            def load(self):
                return self.values
        class Session:
            read = RecordingReader()
        result = self.ns["_ailh_metadata_query"](Session(), "SELECT USERNAME FROM ALL_USERS")
        self.assertIn("schema", result)
        self.assertEqual(result["schema"], "gold")
        self.assertEqual(result["catalog.id"], "aidp_external_catalog")
        self.assertEqual(result["pushdown.sql"], "SELECT USERNAME FROM ALL_USERS")

    def fake_prepared(self):
        return [{"source": key, "source_name": "finance.gold." + key, "source_version": 7,
                 "target": self.ns["AILH_TARGET_TABLES"][key], "rows": 12, "exists": False,
                 "source_clustering": [], "spec": spec, "frame": Mock()}
                for key, spec in self.ns["AILH_SPECS"].items()]

    def test_unclustered_sources_are_not_rebuilt_or_altered_for_publication(self):
        class Session:
            def __init__(self):
                self.statements = []
            def sql(self, statement):
                self.statements.append(statement)
        session = Session()
        items = self.fake_prepared()
        with contextlib.redirect_stdout(io.StringIO()):
            self.ns["_ailh_align_layout"](session, items)
        self.assertEqual(session.statements, [])

    def test_create_writer_only_overrides_supported_special_oracle_types(self):
        class Writer:
            def __init__(self):
                self.values = {}
            def format(self, value):
                return self
            def options(self, **values):
                self.values.update(values)
                return self
            def save(self):
                pass
            def mode(self, value):
                self.values["spark_mode"] = value
                return self
            def saveAsTable(self, name):
                self.values["destination"] = name
        class Frame:
            write = Writer()
            def coalesce(self, partitions):
                return self
        frame = Frame()
        spec = self.ns["AILH_SPECS"]["transaction_analytics_gold"]
        item = {"target": "TRANSACTION_ANALYTICS_GOLD", "spec": spec, "frame": frame}
        with patch.dict(self.ns, {"_ailh_target_exists": lambda *args: False}):
            self.ns["_ailh_write"](None, "GOLD", item)
        self.assertEqual(frame.write.values["preserve.oracle.column.types"],
                         "TRANSACTION_TYPES JSON, MERCHANT_CATEGORIES JSON")
        self.assertEqual(frame.write.values["write.mode"], "CREATE")
        self.assertEqual(frame.write.values.get("destination"),
                         "aidp_external_catalog.gold.TRANSACTION_ANALYTICS_GOLD")

    def test_dry_run_has_no_ddl_layout_or_write_side_effects(self):
        self.ns["AILH_PUBLICATION"]["enabled"] = True
        items = self.fake_prepared()
        overrides = {"_ailh_resolve_owner": Mock(return_value="GOLD"),
                     "_ailh_prepare": Mock(return_value=items)}
        for name in ("_ailh_write", "_ailh_verify", "_ailh_execute_native_ddl", "_ailh_align_layout"):
            overrides[name] = Mock(side_effect=AssertionError("Mutation during dry run"))
        with patch.dict(self.ns, overrides), contextlib.redirect_stdout(io.StringIO()):
            result = self.ns["run_ailh_publication"](Mock())
        self.assertEqual(result["status"], "dry_run")
        for item in items:
            item["frame"].unpersist.assert_called_once()

    def test_identical_existing_target_is_verified_without_overwrite(self):
        item = self.fake_prepared()[0]
        verify = Mock()
        with patch.dict(self.ns, {"_ailh_target_exists": lambda *a: True,
                                 "_ailh_check_target_schema": Mock(),
                                 "_ailh_target_read": Mock(), "_ailh_verify": verify}), \
                contextlib.redirect_stdout(io.StringIO()):
            action = self.ns["_ailh_write"](None, "GOLD", item)
        self.assertEqual(action, "reused_identical")
        verify.assert_called_once_with(None, "GOLD", item, full_rows=True)
        item["frame"].coalesce.assert_not_called()

    def test_existing_read_failure_does_not_trigger_overwrite(self):
        item = self.fake_prepared()[0]
        with patch.dict(self.ns, {"_ailh_target_exists": lambda *a: True,
                                 "_ailh_check_target_schema": Mock(),
                                 "_ailh_target_read": Mock(),
                                 "_ailh_verify": Mock(side_effect=RuntimeError("connection failed"))}):
            with self.assertRaisesRegex(RuntimeError, "connection failed"):
                self.ns["_ailh_write"](None, "GOLD", item)
        item["frame"].coalesce.assert_not_called()

    def test_changed_target_attempts_replacement_without_recreation(self):
        item = self.fake_prepared()[0]
        mismatch = self.ns.get("_AilhReconciliationError", RuntimeError)
        with patch.dict(self.ns, {"_ailh_target_exists": lambda *a: True,
                                 "_ailh_check_target_schema": Mock(),
                                 "_ailh_target_read": Mock(),
                                 "_ailh_verify": Mock(side_effect=mismatch("different rows"))}):
            action = self.ns["_ailh_write"](None, "GOLD", item)
        self.assertEqual(action, "replaced")
        writer = item["frame"].coalesce.return_value.write
        self.assertEqual(writer.options.call_args.kwargs["overwrite.with.recreate"], "false")
        self.assertEqual(writer.options.call_args.kwargs["write.mode"], "OVERWRITE")

    def test_partial_failure_stops_without_retry_and_releases_both_sources(self):
        self.ns["AILH_PUBLICATION"].update(enabled=True, dry_run=False)
        items = self.fake_prepared()
        write = Mock(side_effect=[None, RuntimeError("write failed")])
        verify = Mock()
        overrides = {"_ailh_resolve_owner": Mock(return_value="GOLD"),
                     "_ailh_prepare": Mock(return_value=items), "_ailh_write": write,
                     "_ailh_verify": verify, "_ailh_execute_native_ddl": Mock(), "_ailh_align_layout": Mock()}
        output = io.StringIO()
        with patch.dict(self.ns, overrides), contextlib.redirect_stdout(output):
            with self.assertRaisesRegex(RuntimeError, "write failed"):
                self.ns["run_ailh_publication"](Mock())
        self.assertEqual(write.call_count, 2)
        self.assertEqual(verify.call_count, 1)
        self.assertIn("may contain partial writes", output.getvalue())
        for item in items:
            item["frame"].unpersist.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
