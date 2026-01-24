# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import threading
import queue
import time
from typing import Optional, List

class StreamHub:
    """Single ffmpeg producer -> fan-out to N subscribers (queues)."""

    def __init__(self, *, channel_id: str, hls_url: str, service_name: str, provider: str = "ivysilani"):
        self.channel_id = channel_id
        self.hls_url = hls_url
        self.service_name = service_name
        self.provider = provider

        self._proc: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_evt = threading.Event()
        self._subs_lock = threading.Lock()
        self._subs: List[queue.Queue[bytes]] = []
        self._started_at = time.time()

    @property
    def started_at(self) -> float:
        return self._started_at

    def subscriber_count(self) -> int:
        with self._subs_lock:
            return len(self._subs)

    def start(self) -> None:
        if self._proc is not None:
            return

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
            "-i", self.hls_url,
            "-c", "copy",
            "-copyts",
            "-metadata", f"service_name={self.service_name}",
            "-metadata", f"service_provider={self.provider}",
            "-f", "mpegts",
            "pipe:1",
        ]

        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )

        self._thread = threading.Thread(target=self._reader_loop, name=f"hub-{self.channel_id}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_evt.set()
        try:
            if self._proc is not None:
                self._proc.kill()
        except Exception:
            pass

        with self._subs_lock:
            for q in self._subs:
                try:
                    q.put_nowait(b"")
                except Exception:
                    pass
            self._subs.clear()

    def subscribe(self, *, max_queue_bytes: int = 2 * 1024 * 1024) -> queue.Queue[bytes]:
        max_items = max(8, max_queue_bytes // (64 * 1024))
        q: queue.Queue[bytes] = queue.Queue(maxsize=max_items)
        with self._subs_lock:
            self._subs.append(q)
        return q

    def unsubscribe(self, q: queue.Queue[bytes]) -> None:
        with self._subs_lock:
            try:
                self._subs.remove(q)
            except ValueError:
                pass

    def _reader_loop(self) -> None:
        stdout = self._proc.stdout if self._proc else None
        if stdout is None:
            self.stop()
            return

        try:
            while not self._stop_evt.is_set():
                chunk = stdout.read(64 * 1024)
                if not chunk:
                    break

                with self._subs_lock:
                    subs = list(self._subs)

                for q in subs:
                    if q.full():
                        try:
                            _ = q.get_nowait()
                        except Exception:
                            pass
                    try:
                        q.put_nowait(chunk)
                    except Exception:
                        pass
        finally:
            self.stop()
