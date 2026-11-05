#!/usr/bin/env python3
"""Serve this folder on your own computer so the Hub can be opened, installed and used offline.
   usage: python3 serve.py            then open http://localhost:8000  (Chrome or Edge: the address bar offers Install)
   Only this computer can reach it. To use the Hub on a phone or tablet, put this folder on a web host (see README.md)."""
import http.server, os, sys, webbrowser
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))
class H(http.server.SimpleHTTPRequestHandler):
    extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map, **{'.webmanifest': 'application/manifest+json', '.js': 'text/javascript', '.woff2': 'font/woff2'})
    def end_headers(self):
        if self.path.split('?')[0].endswith('sw.js'): self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    def log_message(self, *a): pass
print('The Learning Hub is at http://localhost:%d  (leave this window open; press Ctrl+C to stop)' % PORT)
try: webbrowser.open('http://localhost:%d' % PORT)
except Exception: pass
http.server.ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
