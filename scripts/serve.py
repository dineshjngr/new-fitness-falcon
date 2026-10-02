#!/usr/bin/env python3
"""Preview grouped pages locally, including legacy URL redirects."""
import argparse, json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
ROOT = Path(__file__).resolve().parent.parent
REDIRECTS = json.loads((ROOT / 'audit/routes.json').read_text())['redirects']

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_head(self):
        parts = urlsplit(self.path)
        if parts.path in ('/404.html', '/404'):
            self.send_error(404)
            return None
        if parts.path in REDIRECTS:
            self.send_response(301)
            self.send_header('Location', REDIRECTS[parts.path] + ('?' + parts.query if parts.query else ''))
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None
        return super().send_head()

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            err_file = ROOT / '404.html'
            if err_file.exists():
                content = err_file.read_bytes()
                self.send_response(404, 'Not Found')
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Connection', 'close')
                self.end_headers()
                if self.command != 'HEAD':
                    self.wfile.write(content)
                return
        super().send_error(code, message, explain)
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    print(f'Preview: http://127.0.0.1:{args.port}')
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
