"""Local HTTPS fixture only; this is not an Oracle PAF server."""
import base64
import json
import shutil
import ssl
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from pathlib import Path
from paf_client import PAFClient, PAFError

@unittest.skipUnless(shutil.which('openssl'), 'openssl is needed for the local TLS fixture')
class HttpsTests(unittest.TestCase):
    def test_login_cookie_roundtrip_and_redirect_block(self):
        with tempfile.TemporaryDirectory() as folder:
            cert=Path(folder)/'cert.pem'
            key=Path(folder)/'key.pem'
            subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
                '-keyout',str(key),'-out',str(cert),'-subj','/CN=localhost',
                '-addext','subjectAltName=DNS:localhost'],check=True,capture_output=True)
            seen=[]
            class Handler(BaseHTTPRequestHandler):
                def log_message(self,*args): pass
                def do_GET(self):
                    if self.path.endswith('loginValidation') and self.headers.get('Authorization') == 'Basic '+base64.b64encode(b'demo:fixture').decode():
                        self.send_response(200)
                        self.send_header('Set-Cookie','agent_factory_session=fixture; Secure; HttpOnly; Path=/agentFactory/')
                        self.end_headers()
                    else:
                        self.send_response(401); self.end_headers()
                def do_POST(self):
                    seen.append((self.path,dict(self.headers),json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                    if self.path.endswith('/redirect'):
                        self.send_response(302)
                        self.send_header('Location','https://other.invalid/should-not-follow')
                        self.end_headers(); return
                    if 'agent_factory_session=fixture' not in self.headers.get('Cookie',''):
                        self.send_response(401); self.end_headers(); return
                    self.send_response(200)
                    self.send_header('Content-Type','application/json')
                    self.end_headers()
                    self.wfile.write(b'{"response":"fixture reply","roomId":"fixture-room"}')
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
            context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert,key)
            server.socket=context.wrap_socket(server.socket,server_side=True)
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            try:
                origin=f'https://localhost:{server.server_port}'
                untrusted=PAFClient(origin+'/agentFactory/v1/knowledge/run/fixture')
                with self.assertRaisesRegex(PAFError, 'certificate verification failed'):
                    untrusted.login('demo','fixture')
                with patch.dict('os.environ', {'https_proxy':'http://127.0.0.1:1', 'HTTPS_PROXY':'http://127.0.0.1:1', 'no_proxy':'', 'NO_PROXY':''}):
                    local=PAFClient(origin+'/agentFactory/v1/knowledge/run/fixture',insecure_local=True)
                    local.login('demo','fixture')
                    result=local.send('local hello')
                    local.send('local follow-up',result['roomId'])
                    self.assertEqual(seen[-1][2]['roomId'],'fixture-room')
                seen.clear()
                client=PAFClient(origin+'/agentFactory/v1/knowledge/run/fixture',ca_bundle=str(cert))
                client.login('demo','fixture')
                data=client.send('hello')
                client.send('follow-up',data['roomId'])
                self.assertEqual(seen[-1][2],{'message':'follow-up','roomId':'fixture-room'})
                self.assertNotIn('Authorization',seen[-1][1])
                client.endpoint=origin+'/agentFactory/redirect'
                with self.assertRaisesRegex(PAFError,'Redirect blocked'):
                    client.send('redirect')
                self.assertEqual(len(seen),3)
            finally:
                server.shutdown(); server.server_close(); thread.join()

if __name__=='__main__': unittest.main()
