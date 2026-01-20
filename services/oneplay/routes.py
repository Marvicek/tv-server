# -*- coding: utf-8 -*-
from bottle import Bottle

oneplay_app = Bottle()

@oneplay_app.get("/")
def index():
    return {
        "service": "oneplay",
        "status": "stub",
        "note": "Sem přijde napojení na tvůj script/provider."
    }
