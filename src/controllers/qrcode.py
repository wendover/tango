from flask.views import MethodView
from flask import render_template


class QRCodeController(MethodView):
    def get(self):
        return render_template("qrcode.html")
