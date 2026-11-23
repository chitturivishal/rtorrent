import os
import socket
import struct
import sys
import urllib.parse
import urllib.request

from bencode import decode
from torrent import load_torrent

# Our random ID. "-RT0001-" is a tag meaning rtorrent version 0.0.0.1
PEER_ID = b"-RT0001-" + os.urandom(12)


def get_trackers(meta):
    urls = []
    if b"announce" in meta:
        urls.append(meta[b"announce"].decode())
    for tier in meta.get(b"announce-list", []):
        for u in tier:
            u = u.decode()
            if u not in urls:
                urls.append(u)
    return urls


def total_size(info):
    if b"length" in info:
        return info[b"length"]
    return sum(f[b"length"] for f in info[b"files"])


def parse_peers(peers):
    result = []
    if isinstance(peers, bytes):
        # Compact format: 6 bytes per peer (4 for IP, 2 for port)
        for i in range(0, len(peers) - 5, 6):
            ip = ".".join(str(b) for b in peers[i:i + 4])
            port = struct.unpack(">H", peers[i + 4:i + 6])[0]
            result.append((ip, port))
    else:
        for p in peers:
            result.append((p[b"ip"].decode(), p[b"port"]))
    return result


def parse_peers6(peers):
    result = []
    if isinstance(peers, bytes):
        # IPv6 compact format: 18 bytes per peer (16 for IP, 2 for port)
        for i in range(0, len(peers) - 17, 18):
            ip = socket.inet_ntop(socket.AF_INET6, peers[i:i + 16])
            port = struct.unpack(">H", peers[i + 16:i + 18])[0]
            result.append((ip, port))
    return result


def ask_tracker(url, info_hash, total):
    params = {
        "info_hash": info_hash,
        "peer_id": PEER_ID,
        "port": 6881,
        "uploaded": 0,
        "downloaded": 0,
        "left": total,
        "compact": 1,
        "numwant": 200,
    }
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    full_url = url + ("&" if "?" in url else "?") + query

    with urllib.request.urlopen(full_url, timeout=10) as response:
        reply = decode(response.read())

    if b"failure reason" in reply:
        raise RuntimeError(reply[b"failure reason"].decode())

    found = parse_peers(reply.get(b"peers", b""))
    found += parse_peers6(reply.get(b"peers6", b""))
    return found


def get_all_peers(meta, info_hash, total):
    seen = set()
    for url in get_trackers(meta):
        if not url.startswith(("http://", "https://")):
            print("Skipping (not HTTP yet):", url)
            continue
        try:
            for peer in ask_tracker(url, info_hash, total):
                seen.add(peer)
            print("Tracker OK:", url)
        except Exception as e:
            print("Tracker failed:", url, "-", type(e).__name__)
    return list(seen)


if __name__ == "__main__":
    meta, info, info_hash = load_torrent(sys.argv[1])
    peers = get_all_peers(meta, info_hash, total_size(info))
    print("Got", len(peers), "unique peers")
    for ip, port in peers[:10]:
        print("   ", ip, port)