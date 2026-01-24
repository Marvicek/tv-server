# -*- coding: utf-8 -*-
from bottle import Bottle, static_file
from pathlib import Path

picons_app = Bottle()
_ASSETS = Path(__file__).resolve().parent / "assets"

@picons_app.get("/<service>/<filename:re:.*\.png>")
def picon(service, filename):
    root = _ASSETS / service
    return static_file(filename, root=str(root))
