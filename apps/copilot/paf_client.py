"""Small synchronous REST client. Python standard library; no PAF SDK required."""
import base64
import http.cookiejar
from http.client import HTTPException
import json
import ipaddress
import socket
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPSHandler, HTTPCookieProcessor, HTTPRedirectHandler, ProxyHandler


class PAFError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward credentials or replay agent actions after redirects.


def is_loopback(hostname):
    if hostname == 'localhost':
        return True
    try:
        return ipaddress.ip_address(hostname or '').is_loopback
    except ValueError:
        return False


def normalize_origin(value):
    parts = urlsplit(value.strip())
    if (parts.scheme != 'https' or not parts.hostname or parts.username or parts.password
            or parts.query or parts.path.rstrip('/') not in ('', '/agentFactory')):
        raise ValueError('Use a PAF HTTPS origin such as https://localhost:8080 (no API path or credentials).')
    # A pasted PAF UI URL is accepted; the browser-only #/... route is discarded.
    if parts.fragment and not parts.path.startswith('/agentFactory'):
        raise ValueError('Use the PAF origin without a fragment.')
    _ = parts.port  # Validate port syntax early.
    return f'{parts.scheme}://{parts.netloc}'


def field(data, path):
    for part in path.split('.'):
        if not isinstance(data, dict) or part not in data:
            return None
        data = data[part]
    return data


def answer_text(data, path=''):
    if path:
        selected = field(data, path)
        if selected is not None:
            return selected if isinstance(selected, str) else json.dumps(selected, indent=2)
    # Convenience only: actual response schema must be confirmed on the target build.
    for key in ('response', 'answer', 'message', 'text', 'output'):
        value = data.get(key) if isinstance(data, dict) else None
        if isinstance(value, str) and value.strip():
            return value
    return json.dumps(data, indent=2, ensure_ascii=False)


class PAFClient:
    def __init__(self, endpoint, *, api_key='', session_cookie='', ca_bundle='', timeout=180, insecure_local=False):
        parts = urlsplit(endpoint)
        if (parts.scheme != 'https' or not parts.hostname or parts.username or parts.password
                or parts.query or parts.fragment):
            raise ValueError('Use an HTTPS endpoint without credentials, query parameters, or fragment.')
        if api_key and session_cookie:
            raise ValueError('Choose API key or session authentication, not both.')
        if any(c in api_key + session_cookie for c in '\r\n') or ';' in session_cookie:
            raise ValueError('Invalid credential format.')
        if insecure_local and not is_loopback(parts.hostname):
            raise ValueError('Certificate verification may be skipped only for a loopback host.')
        if insecure_local and ca_bundle:
            raise ValueError('Choose a CA bundle with verification, or local bypass; not both.')
        self.insecure_local = insecure_local
        self.endpoint = endpoint
        self.origin = f'{parts.scheme}://{parts.netloc}'
        self.api_key = api_key
        self.session_cookie = session_cookie
        self.timeout = timeout
        self.jar = http.cookiejar.CookieJar()
        context = ssl.create_default_context(cafile=ca_bundle or None)
        if insecure_local:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        handlers = [HTTPSHandler(context=context), HTTPCookieProcessor(self.jar), NoRedirect()]
        if is_loopback(parts.hostname):
            handlers.append(ProxyHandler({}))  # Keep local PAF traffic out of corporate HTTP(S) proxies.
        self.opener = build_opener(*handlers)

    def _open(self, request, stage='agent request'):
        if self.insecure_local and not is_loopback(urlsplit(request.full_url).hostname):
            raise PAFError('Local TLS bypass cannot be used for a non-loopback request.')
        try:
            return self.opener.open(request, timeout=self.timeout)
        except HTTPError as exc:
            advice = {400: 'Check payload and custom-workflow publication.',
                      401: 'Check credentials, session expiry, or API-key expiry.',
                      403: 'Check agent access, key binding, and Origin/Referer.',
                      404: 'Check the API route, agent ID, and deployed build.',
                      502: 'Check Apache connectivity to the PAF upstream.',
                      504: 'Check upstream processing and proxy timeout.'}.get(exc.code, 'Inspect PAF and proxy logs.')
            if 300 <= exc.code < 400:
                advice = 'Redirect blocked. Use the final external URL; check SSO/proxy routing.'
            raise PAFError(f'HTTP {exc.code} during {stage}. {advice}') from None
        except (URLError, TimeoutError, OSError) as exc:
            reason = exc.reason if isinstance(exc, URLError) else exc
            if isinstance(reason, ssl.SSLCertVerificationError):
                detail = ('TLS certificate verification failed. Supply a trusted CA bundle matching the host certificate. '
                          'For local PAF only, you can explicitly enable the local demo TLS bypass.')
            elif isinstance(reason, ssl.SSLError):
                detail = 'TLS handshake failed. Check that the target port serves HTTPS and the TLS configuration is valid.'
            elif isinstance(reason, ConnectionRefusedError):
                detail = 'Connection refused. Check that PAF is running and its HTTPS port is exposed to the machine running Streamlit.'
            elif isinstance(reason, socket.gaierror):
                detail = 'DNS lookup failed. Check the PAF hostname.'
            elif isinstance(reason, (TimeoutError, socket.timeout)):
                detail = f'Timed out during {stage}. Check the host, port and network path.'
                if stage != 'login':
                    detail += ' The agent may still be running; no automatic retry was made.'
            else:
                detail = 'Connection failed. Check the PAF host, port, local container port mapping, or external network/proxy path.'
            raise PAFError(f'{stage.capitalize()}: {detail}') from None

    def login(self, username, password):
        """Basic Auth bootstraps a cookie; it is not sent to the agent endpoint."""
        if self.api_key or self.session_cookie:
            raise ValueError('Login is only for a new cookie-authenticated client.')
        auth = base64.b64encode(f'{username}:{password}'.encode()).decode()
        request = Request(self.origin + '/agentFactory/v1/loginValidation',
                          headers={'Authorization': 'Basic ' + auth, 'Origin': self.origin}, method='GET')
        with self._open(request, stage='login') as response:
            if response.status != 200:
                raise PAFError(f'Login returned HTTP {response.status}.')
        if not any(c.name == 'agent_factory_session' for c in self.jar):
            raise PAFError('Login did not return agent_factory_session. Check app-password/SSO policy and cookie rewriting.')

    def send(self, message, room_id=None):
        if not message.strip():
            raise ValueError('Enter a message.')
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                   'Origin': self.origin, 'Referer': self.origin + '/agentFactory/'}
        if self.api_key:
            headers['Authorization'] = 'Bearer ' + self.api_key
        elif self.session_cookie:
            headers['Cookie'] = 'agent_factory_session=' + self.session_cookie
        elif not any(c.name == 'agent_factory_session' for c in self.jar):
            raise PAFError('Sign in before sending a message.')
        payload = {'message': message}
        if room_id is not None and room_id != '':
            payload['roomId'] = room_id
        request = Request(self.endpoint, data=json.dumps(payload).encode(), headers=headers, method='POST')
        with self._open(request) as response:
            if response.status == 202:
                raise PAFError('HTTP 202: asynchronous execution requires the build-specific status API. This demo handles synchronous replies.')
            kind = response.headers.get('Content-Type', '').lower()
            if 'html' in kind:
                raise PAFError('Received HTML instead of JSON. Check SSO, authentication, and proxy routing.')
            if 'event-stream' in kind:
                raise PAFError('Received an event stream. This demo requires the synchronous JSON route from your build.')
            try:
                data = json.loads(response.read())
            except (TimeoutError, OSError, HTTPException):
                raise PAFError('Response transfer failed or timed out. The agent may still be running; no automatic retry was made.') from None
            except (ValueError, UnicodeError):
                raise PAFError('Response was not JSON. Inspect the response in Postman and confirm the API contract.') from None
        if isinstance(data, dict) and (data.get('error') or data.get('success') is False):
            raise PAFError('PAF returned an application error in HTTP 200. Inspect the response in Postman.')
        return data
