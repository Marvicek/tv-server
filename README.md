# tv-server (ivysilani-only)

Minimalistický IPTV server zaměřený výhradně na **iVysílání (Česká televize)**.

## Playlisty
- TS: http://IP:PORT/ivysilani/ivysilani_ts.m3u
- DASH: http://IP:PORT/ivysilani/ivysilani_dash.m3u

## Picony
http://IP:PORT/picon/ivysilani/*.png

## Spuštění
python3 server.py


## iVysilani+ (CH_25+)
- IDs CH_25+ jsou natvrdo.
- Název se best-effort doplní z HbbTV online.json (encoder -> programTitle).
- Lineární CH_1..CH_24 běží v režimu 1 aktivní stream (autoswitch).
