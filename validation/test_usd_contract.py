"""Currency-release regressions; no cloud calls or data regeneration."""
import ast
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UsdContract(unittest.TestCase):
    def test_frozen_numeric_reference_is_unchanged(self):
        current = json.loads((ROOT / "data/reference-snapshot.json").read_text())
        prior = json.loads((ROOT / "reference/archive-inr-2026-10-18/data/reference-snapshot.json").read_text())
        for key in ("transactions", "account_month_rows", "accounts", "source_delta_version", "december_2024"):
            self.assertEqual(current[key], prior[key], key)
        self.assertEqual(current["top_account"]["flagged_gross_usd"], next(v for k, v in prior["top_account"].items() if k.startswith("flagged_gross_")))
        self.assertEqual(current["currency"], "USD")
        self.assertIn("numeric_verification_date", current)
        self.assertNotIn("verified_on", current)

    def test_rule_threshold_values_are_preserved(self):
        module = ast.parse((ROOT / "scripts/finance_core.py").read_text())
        constants = {n.targets[0].id: ast.literal_eval(n.value) for n in module.body
                     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                     and isinstance(n.value, ast.Constant)}
        self.assertEqual(constants["RULE_VERSION"], "FS-TRIAGE-1.1")
        self.assertEqual(constants["CURRENCY_ASSUMPTION"], "USD")
        self.assertEqual(constants["HIGH_VALUE_USD"], 5000.0)
        self.assertEqual(constants["P1_ACCOUNT_EXPOSURE_USD"], 10000.0)
        self.assertEqual(constants["RISK_THRESHOLD"], 60)

    def test_active_sources_have_one_currency_contract(self):
        obsolete = re.compile("I" + "NR|_" + "inr|_" + "INR|" + chr(0x20b9) + "|FS-TRIAGE-1[.]0")
        for folder in ("notebooks", "scripts", "sql", "agents", "config", "article", "rag_corpus", "agent_card", "slides", "video"):
            for p in (ROOT / folder).rglob("*"):
                if not p.is_file() or p.suffix not in (".py", ".ipynb", ".sql", ".json", ".txt", ".md", ".html", ".svg", ".csv"):
                    continue
                if p.name == "migrate_existing_snapshot_to_usd.py":
                    # The one-time adapter recognizes the old deployment explicitly.
                    continue
                self.assertIsNone(obsolete.search(p.read_text()), str(p.relative_to(ROOT)))
                if p.name in ("dashboard_cells.py", "financial_services_executive_analytics_dashboards_aidp.ipynb"):
                    self.assertNotIn("USD lakh", p.read_text())

    def test_rag_release_and_notebook_match(self):
        documents = json.loads((ROOT / "config/rag_documents.json").read_text())
        self.assertEqual(len(documents), 8)
        for d in documents:
            self.assertEqual(d["version"], "1.1")
            self.assertIn(f'[{d["document_id"]} v1.1 §', d["content"])
            self.assertEqual((ROOT / "rag_corpus" / d["filename"]).read_text(), d["content"])
        nb = json.loads((ROOT / "notebooks/financial_services_multi_agent_demo_setup_aidp.ipynb").read_text())
        cell = next("".join(c["source"]) for c in nb["cells"] if "".join(c["source"]).startswith("RAG_DOCUMENTS = json.loads("))
        embedded = json.loads(ast.literal_eval(ast.parse(cell).body[0].value.args[0]))
        self.assertEqual(embedded, documents)

    def test_reviewed_node_prompts_match_generated_contract(self):
        nodes = json.loads((ROOT / "agents/node-configurations.json").read_text())
        nb = json.loads((ROOT / "notebooks/financial_services_multi_agent_demo_setup_aidp.ipynb").read_text())
        cell = next("".join(c["source"]) for c in nb["cells"] if "".join(c["source"]).startswith("PROMPTS = json.loads("))
        embedded = json.loads(ast.literal_eval(ast.parse(cell).body[0].value.args[0]))
        exported = json.loads((ROOT / "config/prompts.json").read_text()) if (ROOT / "config/prompts.json").exists() else []
        by_name = {p["name"]: p for p in embedded}
        self.assertEqual(embedded, exported)
        for node in nodes:
            prompt = by_name[node["name"]]
            for key, value in node.items():
                self.assertEqual(prompt[key], value, (node["name"], key))
            self.assertEqual(prompt["instructions"], node.get("instructions", node.get("preamble_override")))
            self.assertEqual((ROOT / "agents/prompts" / (node["name"] + ".txt")).read_text().rstrip(), prompt["instructions"].rstrip())
        brief = by_name["compose_investigation_brief"]
        self.assertIn("{{evidence_packet}}", brief["instructions"])
        self.assertNotIn("evidence_json", json.dumps(embedded))
        self.assertIn("Markdown", brief["instructions"])

    def test_source_generator_is_preserved(self):
        original = json.loads((ROOT / "reference/financial_services_medallion_architecture_demo.ipynb").read_text())
        revised = json.loads((ROOT / "notebooks/financial_services_medallion_architecture_demo.ipynb").read_text())
        for index in (5, 6, 9, 11, 15, 16, 17, 18):
            self.assertEqual(original["cells"][index]["source"], revised["cells"][index]["source"], index)


if __name__ == "__main__":
    unittest.main()
