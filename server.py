#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bottle import Bottle, run

from services.ivysilani.routes import ivysilani_app
from services.picons.routes import picons_app

app = Bottle()
app.mount("/ivysilani", ivysilani_app)
app.mount("/picon", picons_app)

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8080, reloader=False)
