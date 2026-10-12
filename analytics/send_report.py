#!/usr/bin/env python3
"""Email the weekly report from Ryan's Gmail through Gmail SMTP.

  python3 analytics/send_report.py <to> <subject> <body.txt> <attachment.pdf> [--dry-run]

Plain-text body plus the PDF as an ordinary attachment. Apple Mail's scripting wraps any
message with an attachment in a quote block ("> " on every line), so it is not used.
The Gmail app password lives in the macOS Keychain, never in this repo:
  security add-generic-password -a rdelahunt1@gmail.com -s campaign-report-gmail -w
"""
import smtplib
import subprocess
import sys
from email.message import EmailMessage
from datetime import datetime
from email.utils import format_datetime, make_msgid
from pathlib import Path
from zoneinfo import ZoneInfo

SENDER = "rdelahunt1@gmail.com"
KEYCHAIN_SERVICE = "campaign-report-gmail"


def app_password():
    r = subprocess.run(["security", "find-generic-password", "-a", SENDER, "-s", KEYCHAIN_SERVICE, "-w"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"SEND FAILED: no Keychain item '{KEYCHAIN_SERVICE}' for {SENDER}")
    return r.stdout.strip()


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    if len(args) != 4:
        sys.exit(__doc__)
    to, subject, body_path, pdf_path = args
    pdf = Path(pdf_path)
    msg = EmailMessage()
    msg["From"] = f"Ryan Delahunt <{SENDER}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = format_datetime(datetime.now(ZoneInfo("America/Chicago")))
    msg["Message-ID"] = make_msgid(domain="gmail.com")
    msg.set_content(Path(body_path).read_text())
    msg.add_attachment(pdf.read_bytes(), maintype="application", subtype="pdf", filename=pdf.name)
    if "--dry-run" in sys.argv:
        print(msg.as_string()[:600])
        print(f"... {len(msg.as_bytes())} bytes total")
        return
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as s:
        s.login(SENDER, app_password())
        s.send_message(msg)
    print(f"sent to {to}")
    print(f"message-id: {msg['Message-ID']}")


if __name__ == "__main__":
    main()
