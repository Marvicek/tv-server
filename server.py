#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bottle import Bottle, run

from core.playlist import playlist_app
from services.picons.routes import picons_app
from services.logs.routes import logs_app

from services.ivysilani.routes import ivysilani_app, start_background_updater
from services.sledovanitv.routes import sledovanitv_app
from services.oneplay.routes import oneplay_app

app = Bottle()

app.mount("/", playlist_app)
app.mount("/picon", picons_app)
app.mount("/logs", logs_app)

app.mount("/ivysilani", ivysilani_app)
app.mount("/sledovanitv", sledovanitv_app)
app.mount("/oneplay", oneplay_app)

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8080, reloader=True)


# background fetch každých 30 min
start_background_updater()
