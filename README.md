# IPTV Web Server (simple)

## Endpoints
- Picon: `/picon/<service>/<channel>.png`
- Playlist: `/playlist/<service>.m3u`
- Play redirect: `/play/<service>/<channel>`
- Logs: `/logs`

## Install (Ubuntu APT)
```bash
sudo apt install python3-bottle python3-requests python3-pil
```

## Run
```bash
python3 server.py
```

## Try
- http://127.0.0.1:8080/picon/ivysilani/ct1.png
- http://127.0.0.1:8080/picon/ivysilani/ct1.png?size=256
- http://127.0.0.1:8080/playlist/ivysilani.m3u

### Další kanály
- http://127.0.0.1:8080/picon/ivysilani/ct2.png
- http://127.0.0.1:8080/picon/ivysilani/ct24.png
- http://127.0.0.1:8080/picon/ivysilani/ctart.png
- http://127.0.0.1:8080/picon/ivysilani/ctd.png
- http://127.0.0.1:8080/picon/ivysilani/ctsport.png
