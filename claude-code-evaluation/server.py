#!/usr/bin/env python3
"""Tiny dev server: serves static files and handles PUT /results.json to persist edits."""

import json
from http.server import HTTPServer, SimpleHTTPRequestHandler


class Handler(SimpleHTTPRequestHandler):
    def do_PUT(self):
        if self.path in ('/results.json', '/models.json', '/skills.json'):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            # Validate JSON before writing
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, 'Invalid JSON')
                return
            with open(self.path.lstrip('/'), 'w') as f:
                json.dump(data, f, indent=2)
                f.write('\n')
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_error(405)


if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), Handler)
    print('Serving on http://localhost:8000')
    server.serve_forever()
