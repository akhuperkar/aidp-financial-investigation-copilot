"""Customer-facing identity; independent of agent authentication and chat scope."""
from pathlib import Path

ASSETS = Path(__file__).resolve().parent / 'assets'
ORACLE_WORDMARK = ASSETS / 'oracle-wordmark.png'
ORACLE_SYMBOL = ASSETS / 'oracle-symbol.png'
DEFAULT_CUSTOMER = 'Demo Customer'


def copilot_title(customer, provider, override=''):
    customer = customer.strip() or DEFAULT_CUSTOMER
    suffix = 'AIDP Agent Copilot' if provider == 'Oracle AIDP' else 'Agent Factory Copilot'
    return override.strip() or f'{customer} {suffix}'


def _apply_customer_name():
    import streamlit as st
    name = st.session_state.customer_name_draft.strip() or DEFAULT_CUSTOMER
    st.session_state.update(customer_name=name, customer_name_draft=name)


def _reset_customer_name():
    import streamlit as st
    st.session_state.update(customer_name=DEFAULT_CUSTOMER, customer_name_draft=DEFAULT_CUSTOMER)


def render_customer_editor():
    """Render inside provider settings, separate from its connection form."""
    import streamlit as st
    st.markdown('#### Customer branding')
    with st.form('customer_branding', border=False):
        st.text_input('Customer name', key='customer_name_draft', max_chars=80, placeholder=DEFAULT_CUSTOMER)
        apply_column, reset_column = st.columns(2)
        with apply_column:
            st.form_submit_button('Apply', type='primary', on_click=_apply_customer_name)
        with reset_column:
            st.form_submit_button('Reset', on_click=_reset_customer_name)
    st.caption('Applies the name beneath the Oracle logo and to the default copilot title.')
