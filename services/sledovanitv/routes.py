# -*- coding: utf-8 -*-
from bottle import Bottle

sledovanitv_app = Bottle()

@sledovanitv_app.get("/")
def index():
    return {
        "service": "sledovanitv",
        "status": "stub",
        "note": "Sem přijde napojení na tvůj script/provider."
    }
