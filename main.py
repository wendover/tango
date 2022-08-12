import os
import logging.config

from flask import Flask
from routing import Routing


app = Flask(__name__, template_folder="templates")
Routing(app)


def settings():
    app.config.from_pyfile(os.path.join(os.getcwd(), "settings.cfg"), silent=True)
    config = app.config.get("LOG_CONFIG")
    if config:
        logging.config.fileConfig(config)


if __name__ == "__main__":

    settings()
    app.run(debug=False)
