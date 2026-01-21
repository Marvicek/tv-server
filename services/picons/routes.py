
from bottle import Bottle, static_file

picons_app = Bottle()

@picons_app.get("/<name>.png")
def get_picon(name):
    return static_file(name + ".png", root="static/picons")
