import logging
import os
import smtplib

from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.utils import formatdate
from flask.views import MethodView
from flask import abort, jsonify, render_template, request
from http import HTTPStatus
from psycopg2.extras import Json
from src.utils.postgres import Postgres
from werkzeug.exceptions import Forbidden, InternalServerError


JST = timezone(timedelta(hours=+9), "JST")

MAIL_TITLE_COMPLETE = "Milonga The World：【予約完了メール】 東京ミロンガ倶楽部"


class AdminController(MethodView):
    def __init__(self):
        self._logger = logging.getLogger()
    
    def _check_header_params(self):
        for header in request.headers:
            expect = os.environ.get("ADMIN_PASSWORD")
            if header[0].upper() == "ADMIN":
                password = header[1]
                if password == expect:
                    return True
        return False

    def get(self):
        
        if self._check_header_params() is False:
            self._logger.error("不正アクセス")
            abort(Forbidden.code)

        ret = []
        with Postgres() as postgres:
            query = "SELECT * FROM customer ORDER BY id"
            cur = postgres.select(query)
            for c in cur:
                record = dict(c)
                val = record.get("val")
                ret.append(
                    [
                        val.get("name"),
                        val.get("email"),
                        val.get("status"),
                    ]
                )
        p = ret
        return render_template("event_books.html", p=p)

    def post(self):
        if self._check_header_params() is False:
            self._logger.error("不正アクセス")
            abort(Forbidden.code)
        email = request.form["email"]
        with Postgres() as postgres:
            query = "SELECT * FROM customer WHERE id = %s"
            cur = postgres.select(query, (email, ))
            record = None
            for c in cur:
                record = dict(c)
            if record is None:
                self._logger.error("データなし id=%s" % email)
                abort(InternalServerError.code)

            val = record.get("val")

            from_address = os.environ.get("ADMIN_MAIL")
            cc = os.environ.get("ADMIN_MAIL")

            db_name = self._get_if_exists(val, "name")
            db_address = self._get_if_exists(val, "address", required=False)
            db_phone = self._get_if_exists(val, "phone", required=False)
            db_email = self._get_if_exists(val, "email")
            db_booking_number = self._get_if_exists(val, "booking_number")
            create_date = self._get_if_exists(val, "create_date")
            if create_date:
                create_date = datetime.fromtimestamp(create_date, tz=JST)
                create_date = create_date.strftime("%Y/%m/%d %H:%M:%S")
            
            val["status"] = 1
            val["update_date"] = self._create_currenttime_as_timestamp()
            query = "UPDATE customer SET val = %s WHERE id = %s"

            postgres.execute(query, (Json(val), email))

        with open("resources/templates/mail_book_complete.txt", mode="r", encoding="UTF-8") as f:
            body = f.read()
        body = body.format(
            name=db_name,
            address=db_address,
            phone=db_phone,
            booking_number=db_booking_number,
            booking_time=create_date
        )
        
        message = self._create_message(from_address, db_email, cc, MAIL_TITLE_COMPLETE, body)

        self._send(from_address, email, message)

        return (jsonify({"result": "OK"}), HTTPStatus.OK)


    def _get_if_exists(self, o, key, required=True):
        if o.get(key):
            return o.get(key)
        elif required:
            raise Exception("Data was not found with the key %s in the data %s" % (key, o))
        return ""

    def _create_currenttime_as_timestamp(self):
        now = datetime.now(JST)
        return datetime.timestamp(now)

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
