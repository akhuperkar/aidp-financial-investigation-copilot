import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

BASE = 'https://gateway.aidp.us-chicago-1.oci.oraclecloud.com/agentendpoint/00000000-0000-4000-8000-000000000001/a2a'

class AIDPAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'PAF_HISTORY_DB': self.temp.name+'/paf.sqlite3',
            'AIDP_HISTORY_DB': self.temp.name+'/aidp.sqlite3', 'AIDP_ENDPOINT': BASE, 'PAF_AGENT_ID': 'fixture-agent', 'PAF_ORIGIN': 'https://paf.example.com'})
        self.env.start()

    def tearDown(self):
        self.env.stop(); self.temp.cleanup()

    def app(self):
        return AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run()

    def aidp(self, app):
        {x.label:x for x in app.selectbox}['Agent provider'].select('Oracle AIDP').run()
        {x.label:x for x in app.selectbox}['AIDP authentication'].select('OAuth bearer token').run()
        {x.label:x for x in app.text_input}['OAuth bearer token'].set_value('aidp-test-only')

    def test_switch_disconnects_and_restores_paf_profile_without_mixing_credentials(self):
        app = self.app()
        {x.label:x for x in app.text_input}['API key'].set_value('paf-test-only')
        {x.label:x for x in app.button}['Connect / apply settings'].click().run()
        self.assertFalse(app.chat_input[0].disabled)
        self.aidp(app)
        self.assertTrue(app.chat_input[0].disabled)
        self.assertNotIn('PAF origin', [x.label for x in app.text_input])
        with patch('aidp_client.AIDPClient.preflight', return_value={'name':'FS Investigation Copilot'}):
            {x.label:x for x in app.button}['Connect / verify AIDP'].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state['client'].endpoint, BASE)
        self.assertNotIn('paf-test-only', str(app.session_state['client'].headers))
        {x.label:x for x in app.selectbox}['Agent provider'].select('Private Agent Factory').run()
        self.assertTrue(app.chat_input[0].disabled)
        self.assertEqual({x.label:x for x in app.text_input}['API key'].value, 'paf-test-only')
        self.assertIsNone(app.session_state['room_id'])

    def test_aidp_markdown_rows_context_and_failing_preflight(self):
        app = self.app(); self.aidp(app)
        with patch('aidp_client.AIDPClient.preflight', return_value={'name':'FS Investigation Copilot'}):
            {x.label:x for x in app.button}['Connect / verify AIDP'].click().run()
        self.assertFalse(app.chat_input[0].disabled)
        result = {'response':'## Evidence\n\nUSD 12.50', 'rows':[{'account':'ACC1', 'amount':12.5}], 'roomId':'ctx-1'}
        with patch('aidp_client.AIDPClient.send', return_value=result) as send:
            app.chat_input[0].set_value('first').run()
            self.assertEqual(send.call_args.args[1], None)
            app.chat_input[0].set_value('next').run()
            self.assertEqual(send.call_args.args[1], 'ctx-1')
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any('USD 12.50' in x.value for x in app.markdown))
        self.assertEqual(app.session_state['room_id'], 'ctx-1')
        self.assertNotIn('aidp-test-only', Path(self.temp.name+'/aidp.sqlite3').read_bytes().decode(errors='ignore'))
        with patch('aidp_client.AIDPClient.preflight', side_effect=ValueError('Fixture access denied')):
            {x.label:x for x in app.button}['Connect / verify AIDP'].click().run()
        self.assertTrue(app.chat_input[0].disabled)
        self.assertTrue(any('Fixture access denied' in x.value for x in app.error))
        self.assertEqual(len(app.exception), 0)

if __name__ == '__main__': unittest.main()
