#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bottle import Bottle, run
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from services.picons.routes import picons_app
from services.logs.routes import logs_app


app = Bottle()

app.mount("/picon", picons_app)
app.mount("/logs", logs_app)


if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8080, reloader=True)