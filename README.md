
# ČT IPTV Server

Self-healing IPTV backend for Česká televize.

## Features
- Auto-discovery of channels from HBBTV
- DASH-first playback
- Playlist output for VLC / Kodi / Tvheadend
- Picon generator support

## Run
```bash
pip install bottle requests pillow
python3 server.py
```

Playlist:
http://127.0.0.1:8080/ct/playlist/ct_playlist.m3u
