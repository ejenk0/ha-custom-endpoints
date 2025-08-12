import os
from threading import Thread, Event
import requests
from imapclient import IMAPClient
import email
import time
import ssl
from dotenv import load_dotenv

load_dotenv()

stop_evt = Event()


def mail_listener():
    host, port = os.getenv("IMAP_HOST", "127.0.0.1"), int(os.getenv("IMAP_PORT", 1143))
    user, password = os.getenv("IMAP_USER"), os.getenv("IMAP_PASSWORD")
    api_url = os.getenv("EMAIL_PROCESSING_API_URL")
    if not user or not password:
        print("IMAP_USER and IMAP_PASSWORD must be set in the environment variables.")
        return
    if not api_url:
        print("EMAIL_PROCESSING_API_URL must be set in the environment variables.")
        return
    print(f"Connecting to IMAP server at {host}:{port} as {user}")
    while not stop_evt.is_set():
        try:
            with IMAPClient(host=host, port=port, ssl=False) as c:
                c.starttls(ssl_context=ssl.create_default_context())
                c.login(user, password)
                c.select_folder("INBOX")
                last_uid = max(c.search("ALL") or [0])
                while not stop_evt.is_set():
                    c.idle()
                    try:
                        if c.idle_check(timeout=30):
                            uids = c.search(f"UID {last_uid + 1}:*")
                            if uids:
                                for uid, data in c.fetch(uids, ["RFC822"]).items():
                                    msg = email.message_from_bytes(data[b"RFC822"])
                                    print(
                                        f"New email received: {msg['Subject']} from {msg['From']}"
                                    )
                                    # Send the email content to API
                                    requests.post(
                                        api_url,
                                        json={
                                            "subject": msg["Subject"],
                                            "from": msg["From"],
                                            "body": msg.get_payload(),
                                        },
                                    )
                                    last_uid = max(last_uid, uid)
                    finally:
                        c.idle_done()
        except Exception:
            time.sleep(5)  # backoff and reconnect


listener_thread = None


def start_mail_listener_once():
    global listener_thread
    if listener_thread and listener_thread.is_alive():
        return
    listener_thread = Thread(target=mail_listener, daemon=True)
    listener_thread.start()
