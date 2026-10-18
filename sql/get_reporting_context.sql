-- First call for structured or hybrid requests. Returns READY source snapshot, period coverage, timezone, fictional rule version and INR assumption. No READY row means setup is not ready.
SELECT * FROM finance.agent_demo_fs.snapshot_metadata_sql WHERE status = 'READY' LIMIT 1
