#!/usr/bin/env python3
"""Loopback-only development preview of explicitly listed generated artifacts."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[2]
ROUTES = {
    '/management': ('apps/dashboard/public/index.html', 'text/html; charset=utf-8'),
    '/snapshot.json': ('apps/dashboard/public/snapshot.json', 'application/json; charset=utf-8'),
    '/': ('specs/ai-pms-dashboard/evidence/dashboard.html', 'text/html; charset=utf-8'),
    '/specs/ai-pms-dashboard/evidence/dashboard.html': ('specs/ai-pms-dashboard/evidence/dashboard.html', 'text/html; charset=utf-8'),
    '/empty': ('specs/ai-pms-dashboard/evidence/empty.html', 'text/html; charset=utf-8'),
    '/report': ('reports/ai-pms-eli20/index.html', 'text/html; charset=utf-8'),
}
for name in ('specs/ai-pms-dashboard/README.md', 'specs/ai-pms-dashboard/acceptance-evidence.json', 'specs/ai-pms-dashboard/evidence/browser-observation.md', 'PRODUCT-CLARIFICATION.md', 'specs/ai-pms-dashboard/spec.md'):
    ROUTES['/' + name] = (name, 'application/json; charset=utf-8' if name.endswith('.json') else 'text/plain; charset=utf-8')

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = ROUTES.get(self.path.split('?')[0])
        if not route:
            self.send_error(404)
            return
        try:
            payload = (ROOT / route[0]).read_bytes()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', route[1])
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def log_message(self, *args):
        pass
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=21931)
    args = parser.parse_args()
    server = HTTPServer(('127.0.0.1', args.port), Handler)
    print('Preview http://127.0.0.1:' + str(args.port), flush=True)
    server.serve_forever()
