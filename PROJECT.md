# IPTV Web Server – základní kostra

## Účel
Lokální IPTV webserver (Python + Bottle) pro:
- playlisty (M3U) + /play redirect
- picon renderer (master 1024×1024, downscale `?size=`)
- služby/providery: iVysílání, SledovaniTV, OnePlay (napojení přes tvoje skripty)
- logy (ingest + později generator)

## Architektura
- `server.py` = entrypoint, mount sub-apps
- `services/` = jednotlivé služby (picons, logs, providery…)
- `core/` = sdílené věci (playlist, utils)
- `cache/` = generované soubory (picon PNG, sqlite log DB)

## Picon layout
- velké logo stanice uprostřed (mark)
- kvalita vpravo nahoře (720p / 1080i / 1080p)
- source badge vpravo dole (např. iVysílání)
- vodotisk: MarvicekLogo

## Konvence
- picon endpoint: `/picon/<channel>.png[?src=...&q=...&size=...]`
- master render je vždy 1024×1024
- playlist používá `tvg-logo` z picon endpointu
