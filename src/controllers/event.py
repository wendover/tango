import logging
import os
import smtplib

from email.mime.text import MIMEText
from email.utils import formatdate
from flask.views import MethodView
from flask import abort, render_template, request
from psycopg2.extras import Json
from src.utils.postgres import Postgres
from werkzeug.exceptions import InternalServerError


MAIL_TITLE = "【予約受付メール】 東京ミロンガ倶楽部"


class EventController(MethodView):
    def __init__(self):
        self._logger = logging.getLogger()

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
        body = body.format(name=name, address=address, phone=phone)
        message = self._create_message(from_address, email, bcc, subject, body)

        with Postgres() as postgres:
            status = None
            query = "SELECT * FROM customer WHERE id = %s"
            cur = postgres.select(query, (email, ))
            for c in cur:
                record = dict(c)
                status = record.get("val").get("status")
                
            if status is not None:
                if status == 0:
                    ret = "既に予約依頼が行われています。指定の口座に振込を行うか、当日に直接現地でお支払い下さい。"
                elif status == 1:
                    ret = "既にお支払いが完了しています。予約番号をお控えの上、現地にお越しください。"
                else:
                    self._logger.error("不明なステータス: %s" % status)
                    abort(InternalServerError.code)
            else:
                val = {
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "status": 0
                }
                query = "INSERT INTO customer (id, val) VALUES(%s, %s);"
                postgres.execute(query, (email, Json(val)))
                ret = "ご予約を受け付けました。<br>" \
                    "入力したメールアドレスに今後の流れが記載されているのでご確認ください。<br>" \
                    "しばらく待ってもメールが届かない場合は、お手数ですが再度手続きをお願いいたします。<br>" \
                    "また、迷惑メール等に振り分けられている可能性もございますので再度ご確認ください。"
                

        self._send(from_address, email, message)
        p = {"message": ret}
        return render_template("event_result.html", p=p)

    
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

