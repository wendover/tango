import logging

from src.controllers.event import EventController
from src.controllers.main import MainController
from src.controllers.qrcode import QRCodeController
from flask import render_template, request
from flask.json import jsonify
from http import HTTPStatus


class Routing(object):
    def __init__(self, app):
        # general
        app.before_request(before_request)
        app.after_request(after_request)

        # api
        app.add_url_rule(
            "/",
            view_func=MainController.as_view("main_controller"),
        )
        app.add_url_rule(
            "/event", view_func=EventController.as_view("event_controller")
        )
        app.add_url_rule(
            "/event_code", view_func=QRCodeController.as_view("qrcode_controller")
        )

        # error
        app.register_error_handler(HTTPStatus.BAD_REQUEST, error_handler_400)
        app.register_error_handler(HTTPStatus.NOT_FOUND, error_handler_404)
        app.register_error_handler(HTTPStatus.INTERNAL_SERVER_ERROR, error_handler_500)


def before_request():
    logger = logging.getLogger(__name__)
    logger.info(request)
    logger.info(request.headers)
    logger.info(request.get_data(as_text=True))


def after_request(response):
    logger = logging.getLogger(__name__)
    logger.info(response)
    return response


def error_handler_400(error):
    logger = logging.getLogger(__name__)
    logger.error(error)
    return render_template("httpstatus400.html")


def error_handler_404(error):
    logger = logging.getLogger(__name__)
    logger.error(error)
    return render_template("httpstatus404.html")


def error_handler_500(error):
    logger = logging.getLogger(__name__)
    logger.error(error)
    return render_template("httpstatus500.html")
