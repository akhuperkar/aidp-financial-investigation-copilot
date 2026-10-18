"""Run: streamlit run app.py"""
import os
import time
import uuid
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from history_store import HistoryStore, history_scope
from response_view import parse_response
from response_ui import render_reply
from urllib.parse import urlsplit
import streamlit as st
from branding import ORACLE_WORDMARK, ORACLE_SYMBOL, DEFAULT_CUSTOMER, copilot_title, render_customer_editor
from aidp_client import AIDPError
from aidp_ui import configure_aidp, save_settings as save_aidp_settings
from paf_client import PAFClient, PAFError, answer_text, field, normalize_origin, is_loopback

st.set_page_config(page_title='Agent Copilot', page_icon=str(ORACLE_SYMBOL), layout='centered')

def config(name, default=''):
    try:
        return str(st.secrets.get(name, os.getenv(name, default)))
    except st.errors.StreamlitSecretNotFoundError:
        return os.getenv(name, default)

for key, value in [('client', None), ('messages', []), ('room_id', None), ('raw', None), ('elapsed', None), ('conversation', None), ('scope', None), ('agent_kind', 'knowledge'), ('assistant_title', 'Agent Factory Copilot'), ('assistant_title_override', '')]:
    if key not in st.session_state:
        st.session_state[key] = value

if 'customer_name' not in st.session_state:
    st.session_state.customer_name = config('COPILOT_CUSTOMER_NAME', DEFAULT_CUSTOMER).strip() or DEFAULT_CUSTOMER
# Preserve an applied name entered in the previous version's widget.
st.session_state.customer_name = st.session_state.customer_name
if 'customer_name_draft' not in st.session_state:
    st.session_state.customer_name_draft = st.session_state.customer_name


# Profiles are stored separately for this browser session. Existing server config
# continues to use PAF_*; optional local defaults use PAF_LOCAL_*.
profile_fields = ['origin', 'agent_id', 'mode', 'kind', 'override', 'api_key',
                  'username', 'password', 'cookie', 'ca', 'timeout', 'response_path',
                  'room_path', 'insecure', 'display_name', 'rows_path', 'sources_path', 'structured']
if 'profile_values' not in st.session_state:
    st.session_state.profile_values = {}

def switch_profile():
    old = st.session_state.get('active_profile', 'External server')
    st.session_state.profile_values[old] = {
        name: st.session_state[f'{old}:{name}'] for name in profile_fields
        if f'{old}:{name}' in st.session_state
    }
    st.session_state.update(client=None, messages=[], room_id=None, raw=None, elapsed=None, conversation=None, scope=None)

def switch_provider():
    if st.session_state.get('active_provider', 'Private Agent Factory') == 'Private Agent Factory':
        switch_profile()
    else:
        save_aidp_settings()
        st.session_state.update(client=None, messages=[], room_id=None, raw=None, elapsed=None, conversation=None, scope=None)

with st.sidebar:
    st.image(str(ORACLE_WORDMARK), width=164)
    customer = st.session_state.customer_name
    st.subheader(customer)
    st.divider()
    st.subheader('Connection')
    provider = st.selectbox('Agent provider', ['Private Agent Factory', 'Oracle AIDP'],
                            key='provider_choice', on_change=switch_provider)
    st.session_state.active_provider = provider
    if provider == 'Oracle AIDP':
        configure_aidp(config)
    else:
        profile = st.radio('Connection profile', ['External server', 'Local MacBook'],
                           key='profile_choice', on_change=switch_profile)
        st.session_state.active_profile = profile
        local = profile == 'Local MacBook'
        saved = st.session_state.profile_values.get(profile, {})
        prefix = 'PAF_LOCAL_' if local else 'PAF_'
        def value(name, env, default=''):
            return saved.get(name, config(prefix + env, default))
        def key(name):
            return f'{profile}:{name}'
        st.caption('Use the origin only, e.g. https://localhost:8080. Pasted PAF home URLs are normalized.')
        if local:
            st.caption('Use the agent ID from this local PAF installation. Login obtains the cookie automatically.')
        with st.expander('Connection settings', expanded=st.session_state.client is None):
            with st.form('connection'):
                origin = st.text_input('PAF origin', value('origin', 'ORIGIN', 'https://localhost:8080' if local else 'https://paf.example.com'), key=key('origin'))
                agent_id = st.text_input('Agent ID', value('agent_id', 'AGENT_ID', ''), key=key('agent_id'))
                modes = ['API key', 'Username / app password', 'Session cookie']
                selected_mode = saved.get('mode', 'Username / app password' if local else 'API key')
                mode = st.selectbox('Authentication', modes, index=modes.index(selected_mode), key=key('mode'))
                kinds = ['knowledge', 'agentBuilder', 'dataAnalysis', 'deepResearch']
                kind = st.selectbox('Agent type (cookie route)', kinds, index=kinds.index(saved.get('kind', 'knowledge')), key=key('kind'))
                display_name = st.text_input('Assistant title (optional)', value('display_name', 'DISPLAY_NAME'), key=key('display_name'),
                    placeholder=copilot_title(customer, provider), help='Leave blank to use the customer and provider title.')
                override = st.text_input('Full endpoint override (optional)', value('override', 'ENDPOINT'), key=key('override'))
                api_key = st.text_input('API key', value('api_key', 'API_KEY'), type='password', key=key('api_key'))
                username = st.text_input('Username', value('username', 'USERNAME'), key=key('username'))
                password = st.text_input('App password', saved.get('password', ''), type='password', key=key('password'))
                cookie = st.text_input('Session cookie value', saved.get('cookie', ''), type='password', key=key('cookie'))
                ca = st.text_input('CA bundle path (optional)', value('ca', 'CA_BUNDLE'), key=key('ca'))
                insecure = False
                if local:
                    insecure = st.checkbox('Local demo: skip TLS certificate verification', value=saved.get('insecure', False), key=key('insecure'))
                    st.caption('Use only for your local self-signed PAF certificate. The client blocks this option for remote hosts.')
                timeout = st.number_input('Request timeout (seconds)', min_value=10, max_value=900, value=int(saved.get('timeout', 180)), key=key('timeout'))
                response_path = st.text_input('Answer JSON path (optional)', value('response_path', 'ANSWER_PATH'), key=key('response_path'))
                room_path = st.text_input('Room ID JSON path', value('room_path', 'ROOM_PATH', 'roomId'), key=key('room_path'))
                rows_path = st.text_input('Data rows JSON path (optional)', value('rows_path', 'ROWS_PATH'), key=key('rows_path'))
                sources_path = st.text_input('Citations JSON path (optional)', value('sources_path', 'SOURCES_PATH'), key=key('sources_path'))
                structured = st.checkbox('Request structured Markdown (non-data agents)', value=saved.get('structured', True), key=key('structured'))
                connect = st.form_submit_button('Connect / apply settings')
            render_customer_editor()
        if connect:
            st.session_state.profile_values[profile] = {
                name: st.session_state[key(name)] for name in profile_fields if key(name) in st.session_state
            }
            st.session_state.update(client=None, messages=[], room_id=None, raw=None, elapsed=None, conversation=None, scope=None)
            try:
                origin = normalize_origin(origin)
                if not agent_id.strip() and not override.strip():
                    raise ValueError('Copy the Agent ID from this PAF installation, or supply its full run endpoint.')
                endpoint = override.strip() or (f'{origin}/agentFactory/v1/integrations/agents/{agent_id.strip()}/run'
                           if mode == 'API key' else f'{origin}/agentFactory/v1/{kind}/run/{agent_id.strip()}')
                if local and (not is_loopback(urlsplit(origin).hostname) or not is_loopback(urlsplit(endpoint).hostname)):
                    raise ValueError('The Local MacBook profile requires localhost or a loopback IP. Use External server for remote PAF.')
                if mode == 'API key':
                    if not api_key.strip():
                        raise ValueError('Provide an API key generated for this agent.')
                    client = PAFClient(endpoint, api_key=api_key.strip(), ca_bundle=ca.strip(), timeout=timeout, insecure_local=insecure)
                else:
                    if mode == 'Session cookie' and not cookie.strip():
                        raise ValueError('Provide the session cookie value.')
                    client = PAFClient(endpoint, session_cookie=cookie.strip() if mode == 'Session cookie' else '',
                                       ca_bundle=ca.strip(), timeout=timeout, insecure_local=insecure)
                    if mode == 'Username / app password':
                        if not username or not password:
                            raise ValueError('Provide your username and application password.')
                        client.login(username, password)
                identity = username.strip() if mode == 'Username / app password' else (api_key.strip() if mode == 'API key' else cookie.strip())
                st.session_state.update(client=client, answer_path=response_path.strip(), room_path=room_path.strip() or 'roomId',
                    rows_path=rows_path.strip(), sources_path=sources_path.strip(), structured=structured, agent_kind=kind,
                    scope=history_scope(endpoint,mode,identity), assistant_title_override=display_name.strip(),
                    assistant_title=copilot_title(customer, provider, display_name))
                st.success('Login succeeded; session cookie obtained. Send a question to test the agent.' if mode == 'Username / app password'
                           else 'Settings applied. Send a question to verify agent access.')
            except (ValueError, OSError, PAFError) as exc:
                st.error(str(exc))
    if st.button('New chat'):
        st.session_state.update(messages=[], room_id=None, raw=None, elapsed=None, conversation=None)
    if st.button('Disconnect'):
        st.session_state.update(client=None, messages=[], room_id=None, raw=None, elapsed=None, conversation=None, scope=None)
    if st.session_state.client:
        st.caption('Active endpoint: ' + st.session_state.client.endpoint)
        if st.session_state.client.insecure_local:
            st.warning('Local demo only: certificate verification is disabled for this loopback connection.')
    st.caption('External connections always verify TLS. Switching providers or profiles disconnects and starts a fresh chat.')

st.session_state.assistant_title = copilot_title(customer, provider,
    st.session_state.get('assistant_title_override', '') if st.session_state.client else '')
st.image(str(ORACLE_WORDMARK), width=190)
st.title(st.session_state.assistant_title)
is_aidp = st.session_state.get('provider_choice') == 'Oracle AIDP'
st.caption('Your agents · One workspace · Oracle AIDP' if is_aidp else 'Your agents · One workspace · Powered by Private Agent Factory')

try:
    store = HistoryStore(config('AIDP_HISTORY_DB' if is_aidp else 'PAF_HISTORY_DB', str(Path(__file__).resolve().parent / '.data' / ('aidp_history.sqlite3' if is_aidp else 'history.sqlite3'))))
except (OSError, sqlite3.Error):
    st.error('Cannot open local history. Set '+('AIDP_HISTORY_DB' if is_aidp else 'PAF_HISTORY_DB')+' to a writable file path, then restart.')
    st.stop()

def save_conversation(doc):
    try:
        store.save(st.session_state.scope, doc)
    except (OSError, sqlite3.Error):
        st.warning('The response is visible in this session, but could not be saved to local history.')

if st.session_state.client:
    try:
        histories = store.load(st.session_state.scope)
    except (sqlite3.Error, ValueError):
        histories = []
        st.warning('Saved history could not be read. Current chat remains available.')
    with st.sidebar:
        st.subheader('Interaction history')
        st.caption('Saved on this machine, for the connected agent and login. App deletion does not delete server-side history or memory.')
        options = [''] + [h['id'] for h in histories]
        labels = {h['id']: h['title'] for h in histories}
        selected = st.selectbox('Saved interaction', options, format_func=lambda v: labels.get(v, 'Choose an interaction'), key='history_picker_'+st.session_state.scope)
        if st.button('Open interaction', disabled=not selected):
            doc = next(h for h in histories if h['id']==selected)
            st.session_state.update(conversation=doc, room_id=doc.get('room_id'))
            st.rerun()
        confirm = st.checkbox('Confirm deletion from this app')
        if st.button('Delete interaction', disabled=not (selected and confirm)):
            store.delete(st.session_state.scope, selected)
            if st.session_state.conversation and st.session_state.conversation['id']==selected:
                st.session_state.update(conversation=None, room_id=None)
            st.rerun()

if not st.session_state.client:
    st.info('Choose a provider and configure its connection in the sidebar to begin. Saved history becomes available after connecting.')
else:
    st.caption('AIDP Agent · A2A 0.3 · Markdown output' if is_aidp else 'Knowledge Agent' if st.session_state.agent_kind=='knowledge' else 'Data Analysis Agent' if st.session_state.agent_kind=='dataAnalysis' else 'PAF Agent')

paths = {'answer_path':st.session_state.get('answer_path',''), 'rows_path':st.session_state.get('rows_path',''),
         'sources_path':st.session_state.get('sources_path',''), 'room_path':st.session_state.get('room_path','roomId')}
doc = st.session_state.conversation
if doc and doc.get('context_reset'):
    st.info('A prompt was removed locally. Subsequent questions use a new '+('AIDP context' if is_aidp else 'PAF room')+'; earlier visible turns are not replayed. Server-side memory may still apply.')
if doc:
    for turn in doc['turns']:
        with st.chat_message('user'):
            st.markdown(turn['prompt'])
            if st.button('Delete prompt + reply', key='delete_'+turn['id']):
                store.delete_turn(st.session_state.scope, doc['id'], turn['id'])
                updated = next((h for h in store.load(st.session_state.scope) if h['id']==doc['id']),None)
                st.session_state.update(conversation=updated, room_id=None)
                st.rerun()
        with st.chat_message('assistant'):
            render_reply(turn, st.session_state.agent_kind, paths)

prompt = st.chat_input('Ask your connected agent a question', disabled=st.session_state.client is None)
if prompt:
    if not doc:
        doc = {'id':uuid.uuid4().hex,'title':prompt[:70],'room_id':None,'turns':[], 'assistant_title':st.session_state.assistant_title}
        st.session_state.conversation=doc
    request = prompt
    if st.session_state.get('structured') and st.session_state.agent_kind != 'dataAnalysis':
        request += '\n\nResponse format: Use Markdown with a short summary and clear headings or bullets where useful. Preserve technical details. Cite supporting sources when available; do not invent citations or scores.'
    turn = {'id':uuid.uuid4().hex,'prompt':prompt,'request':request,'created':datetime.now(timezone.utc).isoformat()}
    start=time.monotonic()
    try:
        with st.spinner('Waiting for your AIDP agent…' if is_aidp else 'Waiting for your PAF agent…'):
            raw=st.session_state.client.send(request, doc.get('room_id'))
        elapsed=time.monotonic()-start
        parsed=parse_response(raw,**paths)
        room=parsed['room_id']
        if isinstance(room,(str,int)) and not isinstance(room,bool) and str(room):
            doc['room_id']=room
        turn.update(raw=raw,elapsed=elapsed)
    except (ValueError, PAFError, AIDPError) as exc:
        turn.update(error=str(exc),elapsed=time.monotonic()-start)
    doc['turns'].append(turn)
    st.session_state.room_id=doc.get('room_id')
    save_conversation(doc)
    st.rerun()
if doc and doc['turns'] and doc.get('room_id') is None:
    st.caption('No AIDP context ID returned. The next question starts a new context.' if is_aidp else 'No active room ID. The next question starts a new PAF conversation; check Room ID JSON path if continuity is expected.')
