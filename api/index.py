from http.server import BaseHTTPRequestHandler
from server import Handler

class handler(BaseHTTPRequestHandler):
    do_GET = Handler.do_GET
    do_POST = Handler.do_POST
    reply = Handler.reply
    send_bytes = Handler.send_bytes
    log_message = Handler.log_message
