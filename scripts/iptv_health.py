#!/usr/bin/env python3
"""IPTV health check: stream playback + EPG coverage for an M3U playlist.

Python port of the bash health check, same conventions:
  - root is $GITHUB_WORKSPACE on GitHub Actions, /workspace otherwise
  - reads <root>/OpenIPTVItaly.m3u, writes <root>/health_report.txt
  - channels matching --skip are reported as [SKIP]
  - Mediaset / .mpd URLs get the browser User-Agent and Mediaset headers

Added on top of the bash version:
  - per-channel User-Agent from #EXTVLCOPT:http-user-agent (fallback: generic UA)
  - a single -headers option (ffmpeg keeps only the last one if repeated)
  - audio-only streams (radio TV channels) are not reported as DOWN
  - failure reason in the report (the bash version discarded stderr)
  - parallel tests
  - EPG check from the playlist's x-tvg-url
"""
import argparse
import gzip
import io
import json
import os
import re
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
GENERIC_UA = "Mozilla/5.0 (X11; Linux x86_64; IPTV-Health-Check)"
MEDIASET_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
MEDIASET_HEADERS = ("Referer: https://www.mediasetplay.mediaset.it/\r\n"
                    "Origin: https://www.mediasetplay.mediaset.it\r\n"
                    "Accept-Language: it-IT,it;q=0.9\r\n")


# --------------------------------------------------------------------------
# Playlist parsing
# --------------------------------------------------------------------------
def parse_m3u(text):
    """Return (epg_url, channels). Only the first URL after each #EXTINF is kept."""
    epg_url = None
    channels = []
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#EXTM3U"):
            m = re.search(r'x-tvg-url="([^"]+)"', line)
            epg_url = m.group(1) if m else None
        elif line.startswith("#EXTINF"):
            head, _, name = line.rpartition(",")
            attrs = dict(ATTR_RE.findall(head))
            cur = {
                "chno": attrs.get("tvg-chno", ""),
                "tvg_id": attrs.get("tvg-id", ""),
                "name": name.strip() or attrs.get("tvg-name", ""),
                "user_agent": None,
                "url": None,
            }
        elif line.startswith("#EXTVLCOPT:") and cur is not None:
            key, _, value = line[len("#EXTVLCOPT:"):].partition("=")
            if key == "http-user-agent":
                cur["user_agent"] = value
        elif line.startswith("#"):
            continue
        elif cur is not None:
            cur["url"] = line
            channels.append(cur)
            cur = None
    return epg_url, channels


# --------------------------------------------------------------------------
# Stream check
# --------------------------------------------------------------------------
def run(cmd, timeout):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, stdin=subprocess.DEVNULL)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return None, "", "timeout"


def last_line(text, default=""):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return (lines[-1] if lines else default)[:140]


def net_options(ch, timeout):
    url = ch["url"]
    if "mediaset" in url or url.endswith(".mpd"):
        opts = ["-user_agent", MEDIASET_UA, "-headers", MEDIASET_HEADERS]
    else:
        opts = ["-user_agent", ch["user_agent"] or GENERIC_UA]
    return opts + ["-rw_timeout", str(timeout * 1_000_000)]


def check_stream(ch, timeout, sample):
    """Return (status, detail, elapsed_ms). status: OK | DOWN | SKIP."""
    url = ch["url"]
    if re.search(r"(youtube\.com|youtu\.be)/", url):
        return "SKIP", "YouTube URL (needs yt-dlp)", 0

    t0 = time.time()
    net = net_options(ch, timeout)

    rc, out, err = run(
        ["ffprobe", "-v", "error", *net,
         "-show_entries", "stream=codec_type,codec_name,width,height",
         "-of", "json", url],
        timeout * 6,
    )
    ms = lambda: int((time.time() - t0) * 1000)  # noqa: E731
    if rc != 0:
        return "DOWN", "probe: " + last_line(err, "no output"), ms()
    try:
        streams = json.loads(out).get("streams", [])
    except json.JSONDecodeError:
        streams = []
    if not streams:
        return "DOWN", "probe: no streams found", ms()

    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    info = []
    if video:
        info.append(f"{video.get('codec_name')} {video.get('width')}x{video.get('height')}")
    if audio:
        info.append(audio.get("codec_name", "audio"))
    detail = " + ".join(info) or "streams found"

    rc, _, err = run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", *net,
         "-i", url, "-t", str(sample), "-f", "null", "-"],
        timeout * 6 + sample,
    )
    if rc != 0:
        return "DOWN", "decode: " + last_line(err, "failed"), ms()
    return "OK", detail, ms()


# --------------------------------------------------------------------------
# EPG check
# --------------------------------------------------------------------------
def parse_xmltv_time(value):
    if not value:
        return None
    value = value.strip()
    fmt = "%Y%m%d%H%M%S %z" if " " in value else "%Y%m%d%H%M%S"
    try:
        dt = datetime.strptime(value, fmt)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def load_epg(url):
    """Return (channel_ids, stats); stats[id] = [count, airing_now, last_stop]."""
    req = urllib.request.Request(url, headers={"User-Agent": GENERIC_UA})
    data = urllib.request.urlopen(req, timeout=180).read()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)

    now = datetime.now(timezone.utc)
    channel_ids, stats = set(), {}
    for _, el in ET.iterparse(io.BytesIO(data), events=("end",)):
        if el.tag == "channel":
            channel_ids.add(el.get("id"))
            el.clear()
        elif el.tag == "programme":
            st = stats.setdefault(el.get("channel"), [0, False, None])
            start = parse_xmltv_time(el.get("start"))
            stop = parse_xmltv_time(el.get("stop"))
            st[0] += 1
            if start and stop and start <= now < stop:
                st[1] = True
            if stop and (st[2] is None or stop > st[2]):
                st[2] = stop
            el.clear()
    return channel_ids, stats


def check_epg(ch, epg):
    """Return (status, detail). status: OK | STALE | EMPTY | NOT_FOUND | NO_ID | SKIP."""
    if epg is None:
        return "SKIP", "EPG not checked"
    channel_ids, stats = epg
    tvg_id = ch["tvg_id"]
    if not tvg_id:
        return "NO_ID", "no tvg-id in playlist"
    if tvg_id not in channel_ids and tvg_id not in stats:
        return "NOT_FOUND", f"'{tvg_id}' not in EPG"
    count, airing, last_stop = stats.get(tvg_id, [0, False, None])
    if count == 0:
        return "EMPTY", "no programmes"
    until = last_stop.astimezone().strftime("%Y-%m-%d %H:%M") if last_stop else "?"
    if not airing:
        return "STALE", f"{count} programmes, none airing now (until {until})"
    return "OK", f"{count} programmes until {until}"


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    root = Path(os.environ.get("GITHUB_WORKSPACE") or "/workspace")
    ap = argparse.ArgumentParser(description="IPTV health check (stream + EPG)")
    ap.add_argument("--playlist", default=str(root / "OpenIPTVItaly.m3u"))
    ap.add_argument("--report", default=str(root / "health_report.txt"))
    ap.add_argument("--json", help="also write a JSON report to this path")
    ap.add_argument("--skip", default="(Teledue)", help="regex of channel names to skip")
    ap.add_argument("--only", help="regex: test only channels whose name matches")
    ap.add_argument("--epg", help="override the XMLTV URL (default: x-tvg-url)")
    ap.add_argument("--skip-epg", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=5, help="network timeout in seconds")
    ap.add_argument("--sample", type=int, default=2, help="seconds of media to decode")
    args = ap.parse_args()

    print(f"Environment root: {root}")
    print(f"Playlist:         {args.playlist}")
    print(f"Report:           {args.report}\n")

    playlist = Path(args.playlist)
    if not playlist.is_file():
        print(f"ERROR: Playlist not found: {playlist}")
        raise SystemExit(1)

    # utf-8-sig drops the BOM, splitlines() handles CRLF: no need to edit the file
    epg_url, channels = parse_m3u(playlist.read_text(encoding="utf-8-sig"))
    epg_url = args.epg or epg_url
    if args.only:
        rx = re.compile(args.only, re.I)
        channels = [c for c in channels if rx.search(c["name"])]
    skip_rx = re.compile(args.skip) if args.skip else None

    epg = None
    if not args.skip_epg and epg_url:
        print(f"Downloading EPG: {epg_url}")
        try:
            epg = load_epg(epg_url)
            print(f"EPG loaded: {len(epg[0])} channels\n")
        except Exception as exc:  # noqa: BLE001
            print(f"EPG download/parse failed: {exc}\n")

    def work(ch):
        if skip_rx and skip_rx.search(ch["name"]):
            return {**ch, "stream": "SKIP", "stream_detail": "skipped by regex",
                    "ms": 0, "epg": "SKIP", "epg_detail": ""}
        status, detail, ms = check_stream(ch, args.timeout, args.sample)
        e_status, e_detail = check_epg(ch, epg)
        r = {**ch, "stream": status, "stream_detail": detail, "ms": ms,
             "epg": e_status, "epg_detail": e_detail}
        reason = f"  {detail}" if status == "DOWN" else ""
        print(f"{status:<5} {ch['name'][:32]:<32} {ms:>6}ms  EPG={e_status}{reason}", flush=True)
        return r

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(work, channels))  # keeps playlist order

    counts = {"OK": 0, "DOWN": 0, "SKIP": 0}
    epg_counts = {}
    lines = ["IPTV Health Dashboard", f"Generated: {datetime.now(timezone.utc):%a %b %d %H:%M:%S UTC %Y}", ""]
    for r in results:
        counts[r["stream"]] += 1
        tag = f"{'[' + r['stream'] + ']':<8}"
        if r["stream"] == "OK":
            epg_counts[r["epg"]] = epg_counts.get(r["epg"], 0) + 1
            lines.append(f"{tag}{r['name']} | {r['ms']}ms | {r['stream_detail']} | EPG: {r['epg']}")
        elif r["stream"] == "DOWN":
            epg_counts[r["epg"]] = epg_counts.get(r["epg"], 0) + 1
            lines.append(f"{tag}{r['name']} | {r['stream_detail']} | EPG: {r['epg']}")
        else:
            lines.append(f"{tag}{r['name']} | {r['stream_detail']}")

    tested = counts["OK"] + counts["DOWN"]
    lines += ["", f"Total tested: {tested}", f"Working:      {counts['OK']}",
              f"Down:         {counts['DOWN']}", f"Skipped:      {counts['SKIP']}"]
    if epg is not None:
        lines.append("EPG (tested channels): " + ", ".join(f"{k}={v}" for k, v in sorted(epg_counts.items())))

    Path(args.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "\n".join(lines[-5:]))
    print(f"\nReport generated at: {args.report}")


if __name__ == "__main__":
    main()