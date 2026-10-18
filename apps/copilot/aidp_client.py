"""Authenticated Oracle AIDP adapter for the published A2A 0.3 JSON-RPC endpoint.

PAF transport is intentionally independent. No invocation retries: a timed-out
submission may already be running remotely. Only accepted tasks are polled.
"""
import re
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests


class AIDPError(Exception):
    pass


def normalize_aidp_endpoint(value):
    value = value.strip()
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or
            parsed.password or parsed.query or parsed.fragment or
            any(c.isspace() for c in value)):
        raise ValueError('Use the deployed AIDP HTTPS endpoint without credentials, query parameters or fragments.')
    match = re.fullmatch(r'(/agentendpoint/[A-Za-z0-9_-]+)(?:/chat|/a2a(?:/agent-card\.json)?)?/?', parsed.path)
    if not match:
        raise ValueError('Copy the AIDP deployment Chat, A2A or Agent card endpoint URL.')
    return urlunsplit(('https', parsed.netloc, match.group(1) + '/a2a', '', ''))


def oci_profile_signer(profile='DEFAULT', config_file='~/.oci/config', security_token=False):
    """Load only the explicitly selected local profile; never copy key material."""
    try:
        import oci
    except ImportError:
        raise ValueError('OCI authentication needs the optional OCI SDK. Install requirements-aidp.txt in this venv.') from None
    try:
        file_path = str(Path(config_file).expanduser())
        cfg = oci.config.from_file(file_path, profile)
        if security_token:
            token_path = cfg.get('security_token_file')
            if not token_path:
                raise ValueError('The selected profile has no security_token_file. Run OCI session authenticate or select API key authentication.')
            token = Path(token_path).expanduser().read_text().strip()
            key = oci.signer.load_private_key_from_file(str(Path(cfg['key_file']).expanduser()), cfg.get('pass_phrase'))
            signer = oci.auth.signers.SecurityTokenSigner(token, key)
        else:
            signer = oci.signer.Signer(cfg['tenancy'], cfg['user'], cfg['fingerprint'],
                                      str(Path(cfg['key_file']).expanduser()), cfg.get('pass_phrase'))
        # Identity scopes history, not authorization. The SDK performs signing.
        identity = '|'.join([file_path, profile, str(cfg.get('user', '')), str(cfg.get('fingerprint', '')), str(security_token)])
        return signer, identity
    except ValueError as exc:
        if str(exc).startswith('The selected profile'):
            raise
        raise ValueError('Could not load the selected OCI profile. Check its key, passphrase and authentication type locally.') from None
    except Exception:
        raise ValueError('Could not load the selected OCI profile. Check its config, key path and session expiry locally.') from None


class AIDPClient:
    def __init__(self, endpoint, *, bearer_token='', signer=None, dh_user_principal='',
                 ca_bundle='', timeout=600, session=None, poll_interval=1):
        self.endpoint = normalize_aidp_endpoint(endpoint)
        if bool(bearer_token) == bool(signer):
            raise ValueError('Select exactly one AIDP authorization method: OCI profile or OAuth bearer token.')
        for header in (bearer_token, dh_user_principal):
            if '\r' in header or '\n' in header:
                raise ValueError('Authentication headers must contain a single line.')
        self.timeout = float(timeout)
        if self.timeout <= 0:
            raise ValueError('Request timeout must be positive.')
        self.insecure_local = False
        self.verify = ca_bundle or True
        self.session = session or requests.Session()
        self.signer = signer
        self.headers = {'Accept': 'application/json', 'Content-Type': 'application/json',
                        'x-session-id': str(uuid.uuid4())}
        if bearer_token:
            self.headers['Authorization'] = 'Bearer ' + bearer_token.strip()
        if dh_user_principal.strip():
            self.headers['dh-user-principal'] = dh_user_principal.strip()
        self.poll_interval = max(0, float(poll_interval))
        self.active_tasks = {}

    def _request(self, method, url, payload=None, deadline=None):
        remaining = self.timeout if deadline is None else deadline - time.monotonic()
        if remaining <= 0:
            raise AIDPError('AIDP task is still pending at the time limit. Check the agent session before submitting again.')
        kwargs = dict(headers=dict(self.headers), auth=self.signer, verify=self.verify,
                      allow_redirects=False, timeout=(min(20, remaining), remaining))
        if payload is not None:
            kwargs['json'] = payload
        try:
            response = self.session.request(method, url, **kwargs)
        except requests.Timeout:
            raise AIDPError('AIDP request timed out. It was not retried; check the agent session before submitting again.') from None
        except requests.RequestException:
            raise AIDPError('AIDP connection failed. Check the endpoint, network and TLS configuration locally.') from None
        status = response.status_code
        if status < 200 or status >= 300:
            hint = (' Check the selected AIDP authorization method and deployment permissions.' if status in (401, 403)
                    else ' Redirects are not followed.' if 300 <= status < 400 else '')
            raise AIDPError(f'AIDP returned HTTP {status}.{hint}')
        if 'json' not in response.headers.get('Content-Type', '').lower():
            raise AIDPError('AIDP returned a non-JSON response. Check the endpoint and authentication type.')
        try:
            result = response.json()
        except ValueError:
            raise AIDPError('AIDP returned invalid JSON.') from None
        if not isinstance(result, dict):
            raise AIDPError('AIDP returned an unexpected response shape.')
        if result.get('error'):
            code = result['error'].get('code') if isinstance(result['error'], dict) else None
            code = str(code) if isinstance(code, int) else 'unknown'
            # Remote error strings can echo credentials or other request data.
            raise AIDPError(f'AIDP JSON-RPC error {code}. Check the server session or audit logs for details.')
        return result

    def preflight(self):
        card = self._request('GET', self.endpoint + '/agent-card.json')
        try:
            matches = normalize_aidp_endpoint(card.get('url', '')) == self.endpoint
        except ValueError:
            matches = False
        if not matches:
            raise AIDPError('Published agent card endpoint does not match the configured endpoint.')
        if card.get('protocolVersion') != '0.3.0' or card.get('preferredTransport', 'JSONRPC') != 'JSONRPC':
            raise AIDPError('This adapter requires an A2A 0.3.0 JSONRPC agent card.')
        return card

    def _rpc(self, method, params, deadline):
        envelope = self._request('POST', self.endpoint,
            {'jsonrpc': '2.0', 'id': str(uuid.uuid4()), 'method': method, 'params': params}, deadline)
        result = envelope.get('result')
        if not isinstance(result, dict):
            raise AIDPError('AIDP JSON-RPC response has no result object.')
        return result

    def send(self, message, room_id=None):
        if not isinstance(message, str) or not message.strip():
            raise ValueError('Enter a non-empty question.')
        deadline = time.monotonic() + self.timeout
        outgoing = {'kind': 'message', 'role': 'user', 'messageId': str(uuid.uuid4()),
                    'parts': [{'kind': 'text', 'text': message}]}
        if room_id:
            outgoing['contextId'] = str(room_id)
            if str(room_id) in self.active_tasks:
                outgoing['taskId'] = self.active_tasks[str(room_id)]
        result = self._rpc('message/send', {'message': outgoing, 'configuration':
            {'acceptedOutputModes': ['text/plain', 'text'], 'blocking': True}}, deadline)
        while result.get('kind') == 'task' and result.get('status', {}).get('state') in ('submitted', 'working'):
            task_id = result.get('id')
            if not task_id:
                raise AIDPError('AIDP pending task has no task ID.')
            if time.monotonic() + self.poll_interval >= deadline:
                raise AIDPError('AIDP task is still pending at the time limit. Check the agent session before submitting again.')
            time.sleep(self.poll_interval)
            result = self._rpc('tasks/get', {'id': task_id}, deadline)
        return self._normalize(result, room_id)

    def _normalize(self, result, previous_context):
        context = result.get('contextId') or previous_context
        kind = result.get('kind')
        state = result.get('status', {}).get('state') if kind == 'task' else None
        if kind == 'task':
            if state not in ('completed', 'input-required'):
                raise AIDPError(f'AIDP task did not complete (state: {state if state in ("failed", "rejected", "canceled", "auth-required") else "unknown"}).')
            parts = [p for artifact in result.get('artifacts', []) for p in artifact.get('parts', [])]
            if state == 'input-required':
                parts = result.get('status', {}).get('message', {}).get('parts', [])
                if context and result.get('id'):
                    self.active_tasks[str(context)] = result['id']
            else:
                self.active_tasks.pop(str(context), None)
                # Some servers return final agent messages in history, without artifacts.
                if not parts:
                    messages = [m for m in result.get('history', []) if m.get('role') == 'agent']
                    parts = messages[-1].get('parts', []) if messages else []
        elif kind == 'message' and result.get('role') == 'agent':
            parts = result.get('parts', [])
        else:
            raise AIDPError('AIDP returned neither an agent message nor a supported task.')
        text = '\n\n'.join(p['text'] for p in parts if p.get('kind') == 'text' and isinstance(p.get('text'), str) and p['text'].strip())
        data = [p['data'] for p in parts if p.get('kind') == 'data' and isinstance(p.get('data'), dict)]
        if not text and not data:
            raise AIDPError('AIDP completed without an answer artifact or agent message.')
        value = {'response': text, 'roomId': context, 'metadata': {'provider': 'AIDP', 'protocol': 'A2A 0.3',
                 'context_id': context, 'task_id': result.get('id'), 'task_state': state or 'message'}}
        # Store only recognized output fields, never remote history or request headers.
        for part in data:
            for source, target in [('rows', 'rows'), ('data', 'rows'), ('citations', 'citations'), ('sources', 'citations')]:
                if isinstance(part.get(source), list):
                    value[target] = part[source]
        return value
