"""A2A boundary fixtures, independent of a live agent or real credentials."""
import unittest
from unittest.mock import Mock, patch
import requests

try:
    import aidp_client
except ModuleNotFoundError:
    aidp_client = None

BASE = 'https://gateway.aidp.us-chicago-1.oci.oraclecloud.com/agentendpoint/00000000-0000-4000-8000-000000000001'
ANSWER = '## Evidence\n\n| Account | INR |\n|---|---:|\n| ACC00003604 | 28,845.44 |'


class Reply:
    def __init__(self, result=None, status=200, content_type='application/json', error=None):
        self.status_code = status
        self.headers = {'Content-Type': content_type, 'opc-request-id': 'safe-request-id'}
        self.body = {'jsonrpc': '2.0', 'id': 'fixture'}
        self.body.update({'error': error} if error else {'result': result})

    def json(self):
        return self.body


def task(state='completed', text=ANSWER):
    return {'kind': 'task', 'id': 'task-1', 'contextId': 'ctx-returned',
            'status': {'state': state, 'message': {'kind': 'message', 'role': 'agent',
                'messageId': 'progress-1', 'parts': [{'kind': 'text', 'text': 'Working…'}]}},
            'artifacts': [{'artifactId': 'answer-1', 'parts': [{'kind': 'text', 'text': text}]}] if state == 'completed' else []}


class AIDPClientTests(unittest.TestCase):
    def client(self, replies=None, **kwargs):
        self.assertIsNotNone(aidp_client, 'AIDP provider transport has not been implemented.')
        session = Mock(spec=requests.Session)
        session.request.side_effect = replies or [Reply(task())]
        client = aidp_client.AIDPClient(BASE + '/a2a', bearer_token='fixture-token', session=session, **kwargs)
        return client, session

    def test_aidp_url_normalization_does_not_use_paf_origin_rules(self):
        self.assertIsNotNone(aidp_client, 'AIDP endpoint validation is missing.')
        for suffix in ['/chat', '/a2a', '/a2a/agent-card.json']:
            self.assertEqual(aidp_client.normalize_aidp_endpoint(BASE + suffix), BASE + '/a2a')
        for bad in ['http://gateway.example/a2a', BASE + '/a2a?token=x',
                    'https://u:p@example.com/agentendpoint/x/a2a', 'https://paf.example/agentFactory/v1/knowledge/run/x']:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                aidp_client.normalize_aidp_endpoint(bad)

    def test_send_uses_a2a_schema_and_auth_without_paf_cookie(self):
        client, session = self.client()
        result = client.send('Show evidence')
        call = session.request.call_args
        self.assertEqual(call.args, ('POST', BASE + '/a2a'))
        payload = call.kwargs['json']
        self.assertEqual(payload['method'], 'message/send')
        self.assertEqual(payload['params']['message']['parts'], [{'kind': 'text', 'text': 'Show evidence'}])
        self.assertEqual(payload['params']['message']['role'], 'user')
        self.assertNotIn('roomId', payload)
        self.assertEqual(call.kwargs['headers']['Authorization'], 'Bearer fixture-token')
        self.assertNotIn('Cookie', call.kwargs['headers'])
        self.assertFalse(call.kwargs['allow_redirects'])
        self.assertTrue(call.kwargs['verify'])
        self.assertEqual(result['response'], ANSWER)
        self.assertEqual(result['roomId'], 'ctx-returned')

    def test_completed_task_artifact_wins_over_progress_and_user_history(self):
        result = task()
        result['history'] = [{'role': 'user', 'parts': [{'kind': 'text', 'text': 'User text is not the answer'}]}]
        client, _ = self.client([Reply(result)])
        self.assertEqual(client.send('q')['response'], ANSWER)

    def test_followup_reuses_context_without_restarting_completed_task(self):
        client, session = self.client([Reply(task()), Reply(task())])
        first = client.send('first')
        client.send('followup', first['roomId'])
        message = session.request.call_args.kwargs['json']['params']['message']
        self.assertEqual(message['contextId'], 'ctx-returned')
        self.assertNotIn('taskId', message)

    def test_working_task_is_polled_without_replaying_message(self):
        client, session = self.client([Reply(task('working')), Reply(task())], poll_interval=0)
        result = client.send('q')
        methods = [c.kwargs['json']['method'] for c in session.request.call_args_list]
        self.assertEqual(methods, ['message/send', 'tasks/get'])
        self.assertEqual(session.request.call_args.kwargs['json']['params']['id'], 'task-1')
        self.assertEqual(result['metadata']['task_state'], 'completed')

    def test_input_required_continues_only_that_active_task(self):
        waiting = task('input-required')
        waiting['status']['message']['parts'][0]['text'] = 'Which month?'
        client, session = self.client([Reply(waiting), Reply(task())])
        first = client.send('q')
        self.assertEqual(first['response'], 'Which month?')
        client.send('December', first['roomId'])
        self.assertEqual(session.request.call_args.kwargs['json']['params']['message']['taskId'], 'task-1')

    def test_failed_or_empty_tasks_are_not_successful_answers(self):
        self.assertIsNotNone(aidp_client, 'AIDP error handling is missing.')
        for state in ['failed', 'rejected', 'canceled', 'auth-required']:
            client, _ = self.client([Reply(task(state))])
            with self.subTest(state=state), self.assertRaises(aidp_client.AIDPError):
                client.send('q')
        empty = task(); empty['artifacts'] = []; empty['status'].pop('message')
        client, _ = self.client([Reply(empty)])
        with self.assertRaises(aidp_client.AIDPError):
            client.send('q')

    def test_message_result_and_data_part_are_normalized_for_existing_ui(self):
        result = {'kind': 'message', 'messageId': 'm-1', 'role': 'agent', 'contextId': 'ctx-message',
                  'parts': [{'kind': 'text', 'text': ANSWER}, {'kind': 'data', 'data': {'rows': [{'amount': 12}], 'citations': [{'title': 'actual source'}]}}]}
        client, _ = self.client([Reply(result)])
        value = client.send('q')
        from response_view import parse_response
        parsed = parse_response(value)
        self.assertEqual(parsed['text'], ANSWER)
        self.assertEqual(parsed['room_id'], 'ctx-message')
        self.assertEqual(parsed['rows'], [{'amount': 12}])
        self.assertEqual(parsed['sources'], [{'title': 'actual source'}])

    def test_timeout_is_not_retried_and_does_not_reveal_credentials(self):
        client, session = self.client()
        session.request.side_effect = requests.Timeout('fixture-token')
        with self.assertRaises(aidp_client.AIDPError) as error:
            client.send('q')
        self.assertNotIn('fixture-token', str(error.exception))
        self.assertEqual(session.request.call_count, 1)

    def test_http_and_rpc_errors_are_redacted_not_false_success(self):
        for reply in [Reply(status=401), Reply(status=302), Reply(content_type='text/html'),
                      Reply(error={'code': -32603, 'message': 'fixture-token', 'data': {'secret': 'fixture-token'}})]:
            client, _ = self.client([reply])
            with self.subTest(reply=reply.status_code), self.assertRaises(aidp_client.AIDPError) as error:
                client.send('q')
            self.assertNotIn('fixture-token', str(error.exception))

    def test_preflight_uses_authenticated_card_get_and_ignores_foreign_url(self):
        client, session = self.client()
        reply = Reply(); reply.body = {'name': 'FS Investigation', 'url': 'https://other.example/a2a', 'protocolVersion': '0.3.0', 'preferredTransport': 'JSONRPC', 'skills': []}
        session.request.side_effect = [reply]
        with self.assertRaisesRegex(aidp_client.AIDPError, 'endpoint'):
            client.preflight()
        self.assertEqual(session.request.call_args.args, ('GET', BASE + '/a2a/agent-card.json'))

    def test_no_auth_or_header_injection_rejected_before_request(self):
        self.assertIsNotNone(aidp_client, 'AIDP auth validation is missing.')
        with self.assertRaises(ValueError): aidp_client.AIDPClient(BASE + '/a2a')
        with self.assertRaises(ValueError): aidp_client.AIDPClient(BASE + '/a2a', bearer_token='x\r\ny')
        with self.assertRaises(ValueError): aidp_client.AIDPClient(BASE + '/a2a', bearer_token='x', dh_user_principal='a\nb')


if __name__ == '__main__':
    unittest.main()
