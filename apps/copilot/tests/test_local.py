import socket
import ssl
import unittest
from unittest.mock import Mock
from urllib.error import URLError
from paf_client import PAFClient, PAFError, normalize_origin

class LocalTests(unittest.TestCase):
    def test_pasted_ui_url_does_not_duplicate_path(self):
        self.assertEqual(normalize_origin('https://localhost:8080/agentFactory/#/home/gettingStarted'), 'https://localhost:8080')
        self.assertEqual(normalize_origin('https://paf.example.com/agentFactory'), 'https://paf.example.com')
        with self.assertRaises(ValueError): normalize_origin('https://paf.example.com/unrelated')

    def test_remote_tls_bypass_rejected(self):
        for host in ['paf.example.com','localhost.example.com','10.0.0.5']:
            with self.subTest(host=host), self.assertRaisesRegex(ValueError,'loopback'):
                PAFClient(f'https://{host}/run', insecure_local=True)

    def test_local_tls_bypass_is_explicit(self):
        for host in ['localhost:8080','127.0.0.1:8080','[::1]:8080']:
            c=PAFClient(f'https://{host}/run',insecure_local=True)
            self.assertTrue(c.insecure_local)
        with self.assertRaisesRegex(ValueError,'CA bundle'):
            PAFClient('https://localhost:8080/run',insecure_local=True,ca_bundle='unused.pem')

    def test_specific_connection_diagnostics(self):
        for reason, expected in [(ssl.SSLCertVerificationError(1,'certificate verify failed'),'certificate verification'),
                                 (ConnectionRefusedError(),'Connection refused'),
                                 (socket.gaierror(),'DNS'), (TimeoutError(),'Timed out during login')]:
            with self.subTest(reason=reason):
                c=PAFClient('https://localhost:8080/run')
                c.opener=Mock()
                c.opener.open.side_effect=URLError(reason)
                with self.assertRaisesRegex(PAFError,expected) as error:
                    c.login('test-user','do-not-display-password')
                self.assertNotIn('do-not-display-password',str(error.exception))
                self.assertNotIn('agent may still',str(error.exception))
