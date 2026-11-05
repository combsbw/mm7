#!/usr/bin/env python3
"""Serve this folder over HTTPS on your home network, so an iPhone or iPad can install the Hub (see LOCAL_HTTPS_IOS.md).

usage: python3 serve_https.py CERT.pem KEY.pem [port]        (port defaults to 8443)

The certificate must be one your device trusts (made with mkcert, whose root certificate you have installed and trusted on
the device). Stop with Ctrl-C."""
import http.server, os, socket, ssl, sys

if len(sys.argv) < 3:
    sys.exit(__doc__)
cert, key = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
port = int(sys.argv[3]) if len(sys.argv) > 3 else 8443
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, '.webmanifest': 'application/manifest+json', '.js': 'text/javascript'}

    def end_headers(self):
        if self.path.split('?')[0] in ('/', '/index.html', '/sw.js'):
            self.send_header('Cache-Control', 'no-cache')   # so an update is noticed
        super().end_headers()


ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(cert, key)
srv = http.server.ThreadingHTTPServer(('0.0.0.0', port), Handler)
srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
try:
    ip = socket.gethostbyname(socket.gethostname())
except OSError:
    ip = 'this-computer'
print('Serving over https on port %d. On the iPhone or iPad open: https://%s:%d/' % (port, ip, port))
print('(if that address is wrong, use the computer\'s Wi-Fi IP address, e.g. from System Settings > Wi-Fi > Details)')
srv.serve_forever()
