# IPTV Web Server (Bottle)

Lokální IPTV utility webserver (Python + Bottle) s modulárními službami:
- Playlist (M3U) + /play redirect
- Picon renderer (master 1024×1024) + downscale pomocí `?size=`
- Logy (ingest + recent)
- Providery: iVysílání / SledovaniTV / OnePlay (zatím stub)

## Start
```bash
pip install -r requirements.txt
python server.py
```

## Ověření
- http://127.0.0.1:8080/
- http://127.0.0.1:8080/playlist.m3u
- http://127.0.0.1:8080/picon/ct1.png
- http://127.0.0.1:8080/picon/ct1.png?size=256
- http://127.0.0.1:8080/logs/recent?n=10
