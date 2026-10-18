import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {'PAF_HISTORY_DB': str(Path(self.temp.name)/'history.sqlite3'), 'PAF_AGENT_ID': 'fixture-agent', 'PAF_ORIGIN': 'https://paf.example.com'})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def test_chat_followup_reset_and_failed_reconnect(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(app.chat_input[0].disabled)
        inputs = {x.label: x for x in app.text_input}
        inputs['API key'].set_value('unit-test-only')
        app.checkbox[0].uncheck()
        {x.label:x for x in app.button}['Connect / apply settings'].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertFalse(app.chat_input[0].disabled)
        with patch('paf_client.PAFClient.send', return_value={'response':'Test response', 'roomId':'room-test'}) as send:
            app.chat_input[0].set_value('first').run()
            send.assert_called_with('first', None)
            app.chat_input[0].set_value('followup').run()
            send.assert_called_with('followup', 'room-test')
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.chat_message), 4)
        {x.label:x for x in app.button}['New chat'].click().run()
        self.assertIsNone(app.session_state['room_id'])
        self.assertEqual(len(app.chat_message), 0)
        inputs = {x.label: x for x in app.text_input}
        inputs['API key'].set_value('')
        {x.label:x for x in app.button}['Connect / apply settings'].click().run()
        self.assertTrue(app.chat_input[0].disabled)
        self.assertEqual(len(app.exception), 0)

    def test_browser_sessions_do_not_share_room(self):
        first=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
        second=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
        first.session_state['room_id']='private-room'
        self.assertIsNone(second.session_state['room_id'])

    def test_local_profile_login_and_external_settings_preserved(self):
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
        inputs={x.label:x for x in app.text_input}
        inputs['PAF origin'].set_value('https://external.example.com')
        inputs['API key'].set_value('external-test-key')
        {x.label:x for x in app.button}['Connect / apply settings'].click().run()
        app.radio[0].set_value('Local MacBook').run()
        self.assertTrue(app.chat_input[0].disabled)
        inputs={x.label:x for x in app.text_input}
        self.assertEqual(inputs['PAF origin'].value,'https://localhost:8080')
        self.assertEqual(inputs['API key'].value,'')
        self.assertEqual(inputs['Agent ID'].value,'')
        inputs['PAF origin'].set_value('https://localhost:8080/agentFactory/#/home/gettingStarted')
        inputs['Agent ID'].set_value('local-agent')
        inputs['Username'].set_value('local-user')
        inputs['App password'].set_value('local-fixture-password')
        app.checkbox[0].check()
        with patch('paf_client.PAFClient.login') as login:
            {x.label:x for x in app.button}['Connect / apply settings'].click().run()
            login.assert_called_once_with('local-user','local-fixture-password')
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.session_state['client'].endpoint,'https://localhost:8080/agentFactory/v1/knowledge/run/local-agent')
        self.assertTrue(app.session_state['client'].insecure_local)
        app.radio[0].set_value('External server').run()
        inputs={x.label:x for x in app.text_input}
        self.assertEqual(inputs['PAF origin'].value,'https://external.example.com')
        self.assertEqual(inputs['API key'].value,'external-test-key')
        self.assertNotIn('Local demo: skip TLS certificate verification',[c.label for c in app.checkbox])
        self.assertTrue(app.chat_input[0].disabled)
        {x.label:x for x in app.button}['Connect / apply settings'].click().run()
        self.assertFalse(app.session_state['client'].insecure_local)
        self.assertEqual(len(app.exception),0)

    def test_data_views_and_persistent_history_deletion(self):
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
        inputs={x.label:x for x in app.text_input}
        inputs['API key'].set_value('history-test-key')
        inputs['Assistant title (optional)'].set_value('Retail Banking Data Analysis Agent')
        {x.label:x for x in app.selectbox}['Agent type (cookie route)'].select('dataAnalysis')
        {x.label:x for x in app.button}['Connect / apply settings'].click().run()
        raw={'message':{'text':'In **March**, the value was 1088.955.','data':[{'MONTH':'March','VALUE':1088.955}], 'query':'SELECT ...','status':True},'roomId':'r1'}
        with patch('paf_client.PAFClient.send',return_value=raw) as send:
            app.chat_input[0].set_value('Monthly result?').run()
            self.assertEqual(send.call_count,1)
        self.assertEqual(app.title[0].value,'Retail Banking Data Analysis Agent')
        self.assertTrue(any('1088.955' in m.value for m in app.markdown))
        {x.label:x for x in app.radio}['Response view'].set_value('Table').run()
        self.assertEqual(app.dataframe[0].value.iloc[0]['VALUE'],1088.955)
        {x.label:x for x in app.radio}['Response view'].set_value('Visualization').run()
        self.assertEqual(len(app.exception),0)
        self.assertTrue(any('Only one row' in m.value for m in app.info))
        chat_id=app.session_state['conversation']['id']
        {x.label:x for x in app.button}['New chat'].click().run()
        picker={x.label:x for x in app.selectbox}['Saved interaction']
        picker.select(chat_id).run()
        {x.label:x for x in app.button}['Open interaction'].click().run()
        self.assertEqual(len(app.chat_message),2)
        {x.label:x for x in app.button}['Delete prompt + reply'].click().run()
        self.assertEqual(len(app.chat_message),0)
        self.assertIsNone(app.session_state['room_id'])
        self.assertTrue(app.session_state['conversation']['context_reset'])
        # Stored interaction survives a new Streamlit browser session for the same endpoint/key.
        other=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
        {x.label:x for x in other.text_input}['API key'].set_value('history-test-key')
        {x.label:x for x in other.button}['Connect / apply settings'].click().run()
        {x.label:x for x in other.selectbox}['Saved interaction'].select(chat_id).run()
        {x.label:x for x in other.checkbox}['Confirm deletion from this app'].check().run()
        {x.label:x for x in other.button}['Delete interaction'].click().run()
        self.assertEqual(len(other.exception),0)
        self.assertEqual(len({x.label:x for x in other.selectbox}['Saved interaction'].options),1)

if __name__=='__main__': unittest.main()
