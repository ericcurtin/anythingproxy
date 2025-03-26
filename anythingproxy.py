#!/usr/bin/env python3

import http.server
import socketserver
import urllib.request
import sys

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.copy_request_to_target()

    def do_POST(self):
        self.copy_request_to_target()

    def do_PUT(self):
        self.copy_request_to_target()

    def do_DELETE(self):
        self.copy_request_to_target()

    def copy_request_to_target(self):
        target_url = self.server.target_url + self.path
        method = self.command
        headers = self.headers
        data = None

        if 'Content-Length' in headers:
            length = int(headers['Content-Length'])
            data = self.rfile.read(length)
        
        request = urllib.request.Request(target_url, data=data, headers=dict(headers), method=method)
        
        try:
            with urllib.request.urlopen(request) as response:
                self.send_response(response.status)
                for key, value in response.getheaders():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
        except urllib.error.URLError as e:
            self.send_response(500)
            self.end_headers()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: anythingproxy <receiver> <target>")
        sys.exit(1)

    receiver = sys.argv[1]
    target = sys.argv[2]

    receiver_host, receiver_port = receiver.replace("http://", "").split(":")

    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True

    with ThreadedTCPServer((receiver_host, int(receiver_port)), ProxyHandler) as httpd:
        httpd.target_url = target
        print(f"Proxying from {receiver} to {target}")
        httpd.serve_forever()

