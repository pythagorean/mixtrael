import os
from claude_api import Client

claude_cookie_file = './.cookies/claude/cookie'


def get_claude_client() -> Client:
    if not os.path.exists(claude_cookie_file):
        print("No cookie file found")
        exit(1)
    cookie = open(claude_cookie_file, 'r').read()
    return Client(cookie)
