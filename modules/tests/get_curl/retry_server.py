#!/usr/bin/env python3
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts-file", required=True)
    parser.add_argument("--pid-file", required=True)
    parser.add_argument("--port-file", required=True)
    parser.add_argument("--port", type=int, default=0)
    return parser.parse_args()


args = parse_args()
counts = {}


class RetryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        counts[path] = counts.get(path, 0) + 1
        with open(args.counts_file + ".tmp", "w") as counts_file:
            json.dump(counts, counts_file)
        os.replace(args.counts_file + ".tmp", args.counts_file)

        if path == "/404":
            status, body = 404, b"not found"
        elif path == "/500-then-200" and counts[path] == 1:
            status, body = 500, b"try again"
        elif path == "/always-500":
            status, body = 500, b"still broken"
        else:
            status, body = 200, b"success\n"

        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


server = HTTPServer(("127.0.0.1", args.port), RetryHandler)
with open(args.pid_file, "w") as pid_file:
    pid_file.write(str(os.getpid()))
with open(args.port_file, "w") as port_file:
    port_file.write(str(server.server_port))

try:
    server.serve_forever()
finally:
    server.server_close()
