from http.server import BaseHTTPRequestHandler, HTTPServer

class MovieChatbot(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"AI Movie Recommendation Chatbot is running")

server = HTTPServer(("0.0.0.0", 8000), MovieChatbot)
print("Movie Chatbot server started", flush=True)
server.serve_forever()
