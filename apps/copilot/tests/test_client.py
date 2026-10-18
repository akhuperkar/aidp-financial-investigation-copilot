import io
import json
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError
from paf_client import PAFClient, PAFError, field, answer_text


def reply(data, status=200, content_type='application/json'):
    response = Mock()
    response.status = status
    response.headers = {'Content-Type': content_type}
    response.read.return_value = json.dumps(data).encode()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    return response


class ClientTests(unittest.TestCase):
    def client(self, **kw):
        return PAFClient('https://paf.example/agentFactory/v1/knowledge/run/ABC', **kw)

    def test_first_request_and_followup(self):
        c = self.client(api_key='secret')
        c.opener = Mock()
        c.opener.open.return_value = reply({'response': 'answer', 'roomId': 'r1'})
        first = c.send('hello')
        request = c.opener.open.call_args.args[0]
        self.assertEqual(json.loads(request.data), {'message': 'hello'})
        self.assertEqual(request.get_header('Authorization'), 'Bearer secret')
        c.send('followup', first['roomId'])
        request = c.opener.open.call_args.args[0]
        self.assertEqual(json.loads(request.data)['roomId'], 'r1')

    def test_cookie_requests_include_external_origin(self):
        c = self.client(session_cookie='secret')
        c.opener = Mock()
        c.opener.open.return_value = reply({'message': 'ok'})
        c.send('hello')
        req = c.opener.open.call_args.args[0]
        self.assertEqual(req.get_header('Origin'), 'https://paf.example')
        self.assertEqual(req.get_header('Cookie'), 'agent_factory_session=secret')
        self.assertEqual(req.get_header('Referer'), 'https://paf.example/agentFactory/')
        self.assertIsNone(req.get_header('Authorization'))

    def test_rejects_unsafe_or_ambiguous_urls(self):
        for url in ['http://paf.example/run', 'https://user:pass@paf.example/run',
                    'https://paf.example/run?token=secret', 'https://paf.example/run#x']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                PAFClient(url, api_key='secret')

    def test_html_login_page_is_not_an_agent_answer(self):
        c = self.client(api_key='secret')
        c.opener = Mock()
        c.opener.open.return_value = reply('login', content_type='text/html')
        with self.assertRaisesRegex(PAFError, 'HTML'):
            c.send('hello')

    def test_no_automatic_retry_or_secret_in_error(self):
        c = self.client(api_key='secret')
        c.opener = Mock()
        c.opener.open.side_effect = HTTPError(c.endpoint, 401, 'bad', {}, io.BytesIO(b'secret'))
        with self.assertRaisesRegex(PAFError, '401') as error:
            c.send('hello')
        self.assertNotIn('secret', str(error.exception))
        self.assertEqual(c.opener.open.call_count, 1)

    def test_async_response_not_reported_as_final(self):
        c = self.client(api_key='secret')
        c.opener = Mock()
        c.opener.open.return_value = reply({'job': '123'}, status=202)
        with self.assertRaisesRegex(PAFError, '202'):
            c.send('hello')

    def test_explicit_response_mapping(self):
        data = {'result': {'text': 'hello', 'roomId': 'r2'}, 'unknown': [1]}
        self.assertEqual(field(data, 'result.roomId'), 'r2')
        self.assertEqual(answer_text(data, 'result.text'), 'hello')
        self.assertIsNone(field(data, 'missing.roomId'))
        self.assertIn('unknown', answer_text(data))

    def test_timeout_while_reading_body_is_actionable(self):
        c = self.client(api_key='secret')
        c.opener = Mock()
        response = reply({})
        response.read.side_effect = TimeoutError()
        c.opener.open.return_value = response
        with self.assertRaisesRegex(PAFError, 'still be running'):
            c.send('hello')


if __name__ == '__main__':
    unittest.main()
