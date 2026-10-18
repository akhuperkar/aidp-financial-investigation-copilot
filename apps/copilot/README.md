# Local agent client

Run from this directory so Streamlit loads `.streamlit/config.toml` and local secrets. Install `../../requirements/oci.txt` for OCI profile authentication or `../../requirements/app.txt` for an OAuth-only connection. No credentials are bundled.

The client keeps AIDP A2A and PAF endpoint transports separate. Select a provider before connecting. Switching providers clears the active connection; history scopes include the endpoint and local identity. This is a single-presenter local client, not a multiuser access-control service.

Customer name **Apply / Reset** sits in configuration settings. The applied name appears below the sidebar Oracle logo. The main title defaults to `<Customer> AIDP Agent Copilot` or `<Customer> Agent Factory Copilot`; an explicit **Assistant title (optional)** overrides it. Default customer is **Demo Customer**. Light/dark themes use the included Redwood palette.

See the [full integration guide](../../docs/user-guide.md#8-run-the-dual-provider-streamlit-app-on-port-8501) and [hosted acceptance](../../docs/hosted-acceptance.md). A successful HTTP response alone does not establish that generated evidence reconciles.
