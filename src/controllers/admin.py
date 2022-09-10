import json
import logging
import os

from flask.views import MethodView
from flask import abort, jsonify, render_template, request
from http import HTTPStatus
from psycopg2.extras import Json
from src.utils.postgres import Postgres
from werkzeug.exceptions import Forbidden, InternalServerError


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
            val["status"] = "1"
            query = "UPDATE customer SET val = %s WHERE id = %s"

            postgres.execute(query, (Json(val), email))

            # TODO ここで登録完了メール送るといいかも？


        return (jsonify({"result": "OK"}), HTTPStatus.OK)