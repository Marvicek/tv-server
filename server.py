
from bottle import Bottle, run
from services.ctstream.routes import ctstream_app, start_ct_updater
from services.picons.routes import picons_app

app = Bottle()
app.mount("/ct", ctstream_app)
app.mount("/picon", picons_app)

start_ct_updater()

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8080, debug=True)
