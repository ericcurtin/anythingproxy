#!/usr/bin/env python3

import http.server
import socketserver
import urllib.request
import sys
import json
from urllib.parse import urlparse

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override to prevent default logging
        return

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

        # Print request details
        self.print_request_details(target_url, method, headers, data)

        request = urllib.request.Request(target_url, data=data, headers=dict(headers), method=method)
        
        try:
            with urllib.request.urlopen(request) as response:
                self.send_response(response.status)

                hop_by_hop_headers = ['connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade']
                for key, value in response.getheaders():
                    if key.lower() in hop_by_hop_headers:
                        continue

                    self.send_header(key, value)

                self.end_headers()
                response_data = ""
                for line in response:
                    self.wfile.write(line)
                    self.wfile.flush()
                    response_data += line.decode("utf-8")

                # Print response details
                self.print_response_details(response, response_data)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            print(f"HTTPError: {e}")
        except urllib.error.URLError as e:
            self.send_response(500)
            self.end_headers()
            print(f"URLError: {e}")

    def print_request_details(self, url, method, headers, data):
        print(f"\n----- Request -----")
        print(f"URL: {url}")
        print(f"Method: {method}")
        print(f"Headers: {dict(headers)}")
        if data:
            try:
                json_data = json.loads(data)
                print(f"Body (JSON): {json.dumps(json_data, indent=4)}")
            except json.JSONDecodeError:
                print(f"Body: {data.decode('utf-8')}")
        else:
            print("Body: None")
        print(f"-------------------\n")

    def print_response_details(self, response, data):
        print(f"\n----- Response -----")
        print(f"Status: {response.status}")
        print(f"Headers: {dict(response.getheaders())}")
        if data:
            try:
                json_data = json.loads(data)
                print(f"Body (JSON): {json.dumps(json_data, indent=4)}")
            except json.JSONDecodeError:
                print(f"Body: {data}")
        else:
            print("Body: None")
        print(f"-------------------\n")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: anythingproxy <receiver> <target>")
        sys.exit(1)

    receiver = sys.argv[1]
    target = sys.argv[2]

    parsed_receiver = urlparse(receiver)
    receiver_host = parsed_receiver.hostname
    receiver_port = parsed_receiver.port

    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True

    with ThreadedTCPServer((receiver_host, receiver_port), ProxyHandler) as httpd:
        httpd.target_url = target
        print(f"Proxying from {receiver} to {target}")
        httpd.serve_forever()


