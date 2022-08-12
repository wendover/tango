import logging
import os
import smtplib

from email.mime.text import MIMEText
from email.utils import formatdate
from flask.views import MethodView
from flask import render_template, request


MAIL_TITLE = "【予約受付メール】 東京ミロンガ倶楽部"


class EventController(MethodView):
    def get(self):
        return render_template("event.html")

    def post(self):
        name = request.form["name"]
        address = request.form["address"]
        if not address:
            address = "未入力"
        phone = request.form["phone"]
        if not phone:
            phone = "未入力"
        email = request.form["email"]

        from_address = os.environ.get("ADMIN_MAIL")
        bcc = os.environ.get("ADMIN_MAIL")
        subject = MAIL_TITLE

        with open("resources/templates/mail_book.txt", mode="r", encoding="UTF-8") as f:
            body = f.read()
        body = body.format(name, address, email)
        print(body)
        message = self._create_message(from_address, email, bcc, subject, body)
        self._send(from_address, email, message)
        return render_template("httpstatus200.html")

    
    def _create_message(self, from_addr: str, to_addr: str, bcc_addrs: list, subject: str, body: str):
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Bcc"] = bcc_addrs
        msg["Date"] = formatdate()

        return msg
    
    def _send(self, from_addr: str, to_addrs: str, body: MIMEText):
        _logger = logging.getLogger(__name__)
        _logger.info("From: %s" % from_addr)
        _logger.info("To: %s" % to_addrs)
        _logger.info("Body: %s" % body.as_string())

        smtpobj = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        smtpobj.starttls()
        smtpobj.login(from_addr, os.environ.get("GMAIL_APP_PASS"))
        smtpobj.sendmail(from_addr, to_addrs, body.as_string())
        smtpobj.close()

