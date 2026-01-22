# -*- coding: utf-8 -*-
from bottle import Bottle

ivysilani_app = Bottle()

@ivysilani_app.get("/")
def index():
    return {
        "service": "ivysilani",
        "status": "stub",
        "note": "Sem přijde napojení na tvůj script/provider."
    }
