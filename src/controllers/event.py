import logging
import os
import smtplib

from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.utils import formatdate
from flask.views import MethodView
from flask import abort, render_template, request
from psycopg2.extras import Json
from src.utils.postgres import Postgres
from werkzeug.exceptions import InternalServerError


JST = timezone(timedelta(hours=+9), "JST")

MAIL_TITLE = "Milonga The World：【予約受付メール】 東京ミロンガ倶楽部"



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
        booking_number = request.form["booking_number"]

        with Postgres() as postgres:
            status = None
            query = "SELECT * FROM customer WHERE id = %s"
            cur = postgres.select(query, (email, ))
            for c in cur:
                record = dict(c)
                val = record.get("val")
                print(val)
                db_booking_number = val.get("booking_number")
                if db_booking_number != booking_number:
                    status = -1
                else:
                    status = val.get("status")
                
            if status is not None:
                create_date = val.get("create_date")
                create_date = datetime.fromtimestamp(create_date, tz=JST)
                create_date = create_date.strftime("%Y/%m/%d %H:%M:%S")
                if status == 0:
                    ret = "既に予約依頼が行われています。指定の口座に振込を行うか、当日に直接現地でお支払い下さい。<br>" \
                        "受付日時：%s<br>" \
                        "受付番号：%s<br>" \
                        "予約状況：済<br>" \
                        "お支払い状況：未" % (create_date, db_booking_number)
                elif status == 1:
                    ret = "既にお支払いまで完了しています。身分証明書と受付番号をお控えの上、現地にお越しください。<br>" \
                        "受付日時：%s<br>" \
                        "受付番号：%s<br>" \
                        "予約状況：済<br>" \
                        "お支払い状況：済" % (create_date, db_booking_number)
                elif status == -1:
                    ret = "受付番号か、メールアドレスが正しくありません。"
                else:
                    self._logger.error("不明なステータス: %s" % status)
                    abort(InternalServerError.code)
            else:
                from_address = os.environ.get("ADMIN_MAIL")
                cc = os.environ.get("ADMIN_MAIL")

                booking_number = self._create_bokking_number()
                booking_time = self._create_currentdate()

                with open("resources/templates/mail_book.txt", mode="r", encoding="UTF-8") as f:
                    body = f.read()
                body = body.format(
                    name=name,
                    address=address,
                    phone=phone,
                    booking_number=booking_number,
                    booking_time=booking_time.strftime("%Y/%m/%d %H:%M:%S")
                )
                message = self._create_message(from_address, email, cc, MAIL_TITLE, body)

                val = {
                    "name": name,
                    "address": address,
                    "phone": phone,
                    "email": email,
                    "booking_number": booking_number,
                    "create_date": datetime.timestamp(booking_time),
                    "update_date": "",
                    "status": 0
                }
                query = "INSERT INTO customer (id, val) VALUES(%s, %s);"
                postgres.execute(query, (email, Json(val)))

                self._send(from_address, email, message)

                ret = "ご予約を受け付けました。<br>" \
                    "入力したメールアドレスに今後の流れが記載されているのでご確認ください。<br>" \
                    "しばらく待ってもメールが届かない場合は、お手数ですが再度手続きをお願いいたします。<br>" \
                    "また、迷惑メール等に振り分けられている可能性もございますので再度ご確認ください。"

        p = {"message": ret}
        return render_template("event_result.html", p=p)

   
    def _create_bokking_number(self):
        now = datetime.now(JST)
        today = now.strftime("%m%d%H%M%S%f")
        return today[:-3]

    def _create_currentdate(self):
        return datetime.now(JST)

    def _create_message(self, from_addr: str, to_addr: str, cc_addrs: list, subject: str, body: str):
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Cc"] = cc_addrs
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
