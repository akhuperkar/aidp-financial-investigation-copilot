"""AIDP-only sidebar settings. Credentials stay in the browser's app session."""
import streamlit as st
from aidp_client import AIDPClient, AIDPError, oci_profile_signer
from history_store import history_scope
from branding import copilot_title, DEFAULT_CUSTOMER, render_customer_editor

DEFAULT_ENDPOINT = ''
FIELDS = ('endpoint', 'auth', 'profile', 'config_file', 'token', 'principal', 'ca', 'timeout', 'title')


def save_settings():
    st.session_state.aidp_values = {name: st.session_state['AIDP:'+name]
        for name in FIELDS if 'AIDP:'+name in st.session_state}


def configure_aidp(config):
    saved = st.session_state.get('aidp_values', {})
    def value(name, env, default=''):
        return saved.get(name, config('AIDP_'+env, default))
    st.caption('Use a published AIDP endpoint. Connection checks the agent card before enabling chat.')
    modes = ['OCI API key profile', 'OCI security-token profile', 'OAuth bearer token']
    selected = saved.get('auth', config('AIDP_AUTH', modes[0]))
    mode = st.selectbox('AIDP authentication', modes, index=modes.index(selected) if selected in modes else 0, key='AIDP:auth')
    with st.expander('AIDP connection settings', expanded=st.session_state.client is None):
        with st.form('aidp_connection'):
            endpoint = st.text_input('AIDP deployed endpoint', value('endpoint', 'ENDPOINT', DEFAULT_ENDPOINT), key='AIDP:endpoint')
            title = st.text_input('Assistant title', value('title', 'DISPLAY_NAME'), key='AIDP:title',
                placeholder=copilot_title(st.session_state.get('customer_name', DEFAULT_CUSTOMER), 'Oracle AIDP'),
                help='Leave blank to use the customer and provider title.')
            profile = config('AIDP_OCI_PROFILE', 'DEFAULT')
            config_file = config('AIDP_OCI_CONFIG', '~/.oci/config')
            token = ''
            if mode.startswith('OCI'):
                profile = st.text_input('OCI profile', value('profile', 'OCI_PROFILE', 'DEFAULT'), key='AIDP:profile')
                config_file = st.text_input('OCI config file', value('config_file', 'OCI_CONFIG', '~/.oci/config'), key='AIDP:config_file')
            else:
                token = st.text_input('OAuth bearer token', saved.get('token', config('AIDP_BEARER_TOKEN')), type='password', key='AIDP:token')
            principal = st.text_input('AIDP user principal (if required)', value('principal', 'DH_USER_PRINCIPAL'), key='AIDP:principal', type='password',
                help='Use the deployment-approved dh-user-principal value, if required. Do not reuse a PAF cookie.')
            ca = st.text_input('AIDP CA bundle (optional)', value('ca', 'CA_BUNDLE'), key='AIDP:ca')
            timeout = st.number_input('AIDP timeout (seconds)', min_value=30, max_value=1800, value=int(value('timeout', 'TIMEOUT', '600')), key='AIDP:timeout')
            connect = st.form_submit_button('Connect / verify AIDP')
        st.caption('OCI uses your selected local profile. OAuth uses the deployed authorization configuration. TLS verification is required.')
        render_customer_editor()
    if connect:
        save_settings()
        st.session_state.update(client=None, messages=[], room_id=None, raw=None, elapsed=None, conversation=None, scope=None)
        try:
            signer = None
            identity = token.strip()
            if mode.startswith('OCI'):
                signer, identity = oci_profile_signer(profile.strip(), config_file.strip(), security_token=mode == 'OCI security-token profile')
            elif not token.strip():
                raise ValueError('Provide the bearer token issued for this AIDP deployment.')
            client = AIDPClient(endpoint, signer=signer, bearer_token=token.strip(),
                dh_user_principal=principal, ca_bundle=ca.strip(), timeout=timeout)
            with st.spinner('Checking published AIDP agent card…'):
                card = client.preflight()
            st.session_state.update(client=client, answer_path='', room_path='roomId', rows_path='', sources_path='',
                structured=False, agent_kind='aidp', scope=history_scope(client.endpoint, 'AIDP:'+mode, identity+'|'+principal.strip()),
                assistant_title_override=title.strip(),
                assistant_title=copilot_title(st.session_state.get('customer_name', DEFAULT_CUSTOMER), 'Oracle AIDP', title))
            st.success('Agent card verified. Send a question to test invocation and execution permissions.')
        except (ValueError, OSError, AIDPError) as exc:
            st.error(str(exc))
