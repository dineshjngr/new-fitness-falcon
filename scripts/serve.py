#!/usr/bin/env python3
"""Preview grouped pages locally, including legacy URL redirects."""
import argparse, json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parent.parent
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
    def send_head(self):
        parts=urlsplit(self.path)
        redirects=json.loads((ROOT/'audit/routes.json').read_text())['redirects']
        if parts.path in redirects:
            self.send_response(301)
            self.send_header('Location',redirects[parts.path]+('?' + parts.query if parts.query else ''))
            self.send_header('Content-Length','0')
            self.end_headers()
            return None
        return super().send_head()
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    print(f'Preview: http://127.0.0.1:{args.port}')
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
