"""Customer branding must update presentation without changing agent context."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')

class BrandingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'PAF_HISTORY_DB': self.temp.name+'/paf.sqlite3',
            'AIDP_HISTORY_DB': self.temp.name+'/aidp.sqlite3', 'COPILOT_CUSTOMER_NAME':'Demo Customer', 'PAF_AGENT_ID':'fixture-agent', 'PAF_ORIGIN':'https://paf.example.com', 'AIDP_ENDPOINT':'https://gateway.example.com/agentendpoint/fixture-agent/a2a'})
        self.env.start()

    def tearDown(self):
        self.env.stop(); self.temp.cleanup()

    def test_customer_editor_is_inside_each_providers_connection_settings(self):
        app = AppTest.from_file(APP).run()
        settings = {x.label:x for x in app.sidebar.expander}['Connection settings']
        self.assertIn('Customer name', [x.label for x in settings.text_input])
        {x.label:x for x in app.selectbox}['Agent provider'].select('Oracle AIDP').run()
        settings = {x.label:x for x in app.sidebar.expander}['AIDP connection settings']
        self.assertIn('Customer name', [x.label for x in settings.text_input])
        self.assertEqual(len(app.exception), 0)

    def test_applied_name_is_embedded_as_sidebar_heading_and_reset_restores_default(self):
        app = AppTest.from_file(APP).run()
        self.assertIn('Demo Customer', [x.value for x in app.sidebar.subheader],
            'The applied customer name must be a heading beneath the Oracle logo.')
        {x.label:x for x in app.text_input}['Customer name'].set_value('Seer Bank').run()
        self.assertIn('Demo Customer', [x.value for x in app.sidebar.subheader])
        self.assertEqual(app.title[0].value, 'Demo Customer Agent Factory Copilot')
        {x.label:x for x in app.button}['Apply'].click().run()
        self.assertIn('Seer Bank', [x.value for x in app.sidebar.subheader])
        self.assertEqual(app.title[0].value, 'Seer Bank Agent Factory Copilot')
        {x.label:x for x in app.button}['Reset'].click().run()
        self.assertIn('Demo Customer', [x.value for x in app.sidebar.subheader])
        self.assertEqual({x.label:x for x in app.text_input}['Customer name'].value, 'Demo Customer')
        self.assertEqual(len(app.exception), 0)

    def test_customer_and_provider_derive_titles_before_connection(self):
        app = AppTest.from_file(APP).run()
        inputs = {x.label:x for x in app.text_input}
        self.assertIn('Customer name', inputs, 'Customer branding input is missing.')
        self.assertEqual(app.title[0].value, 'Demo Customer Agent Factory Copilot')
        inputs['Customer name'].set_value('Meridian Bank').run()
        {x.label:x for x in app.button}['Apply'].click().run()
        self.assertEqual(app.title[0].value, 'Meridian Bank Agent Factory Copilot')
        {x.label:x for x in app.selectbox}['Agent provider'].select('Oracle AIDP').run()
        self.assertEqual(app.title[0].value, 'Meridian Bank AIDP Agent Copilot')
        {x.label:x for x in app.text_input}['Customer name'].set_value('   ').run()
        {x.label:x for x in app.button}['Apply'].click().run()
        self.assertEqual(app.title[0].value, 'Demo Customer AIDP Agent Copilot')
        self.assertEqual(len(app.exception), 0)

    def test_paf_custom_title_survives_customer_change_without_disconnect(self):
        app = AppTest.from_file(APP).run()
        inputs = {x.label:x for x in app.text_input}
        self.assertIn('Customer name', inputs, 'Customer branding input is missing.')
        inputs['API key'].set_value('test-only')
        inputs['Assistant title (optional)'].set_value('Risk Investigation Desk')
        {x.label:x for x in app.button}['Connect / apply settings'].click().run()
        scope = app.session_state['scope']
        app.session_state['room_id'] = 'existing-room'
        {x.label:x for x in app.text_input}['Customer name'].set_value('Meridian Bank').run()
        {x.label:x for x in app.button}['Apply'].click().run()
        self.assertEqual(app.title[0].value, 'Risk Investigation Desk')
        self.assertEqual(app.session_state['room_id'], 'existing-room')
        self.assertEqual(app.session_state['scope'], scope)
        self.assertFalse(app.chat_input[0].disabled)
        self.assertEqual(len(app.exception), 0)

    def test_connected_aidp_uses_live_customer_default_instead_of_card_name(self):
        app = AppTest.from_file(APP).run()
        self.assertIn('Customer name', {x.label:x for x in app.text_input}, 'Customer branding input is missing.')
        {x.label:x for x in app.selectbox}['Agent provider'].select('Oracle AIDP').run()
        {x.label:x for x in app.selectbox}['AIDP authentication'].select('OAuth bearer token').run()
        {x.label:x for x in app.text_input}['OAuth bearer token'].set_value('test-only')
        with patch('aidp_client.AIDPClient.preflight', return_value={'name':'Old Agent Name'}):
            {x.label:x for x in app.button}['Connect / verify AIDP'].click().run()
        self.assertEqual(app.title[0].value, 'Demo Customer AIDP Agent Copilot')
        scope = app.session_state['scope']
        {x.label:x for x in app.text_input}['Customer name'].set_value('North Star').run()
        {x.label:x for x in app.button}['Apply'].click().run()
        self.assertEqual(app.title[0].value, 'North Star AIDP Agent Copilot')
        self.assertEqual(app.session_state['scope'], scope)
        self.assertFalse(app.chat_input[0].disabled)
        self.assertEqual(len(app.exception), 0)

if __name__ == '__main__': unittest.main()
