import socket
import sys
from concurrent.futures import ThreadPoolExecutor

from torrent import load_torrent
from tracker import PEER_ID, get_all_peers, total_size

PROTOCOL = b"BitTorrent protocol"


def recv_exactly(sock, n):
    """TCP can hand us the bytes in pieces, so keep reading until we have n."""
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Peer closed the connection")
        data += chunk
    return data


def build_handshake(info_hash):
    return bytes([len(PROTOCOL)]) + PROTOCOL + bytes(8) + info_hash + PEER_ID


def handshake(ip, port, info_hash, timeout=5):
    """Connect to a peer and shake hands. Returns (socket, peer_id)."""
    sock = socket.create_connection((ip, port), timeout=timeout)
    try:
        sock.sendall(build_handshake(info_hash))
        reply = recv_exactly(sock, 68)
        if reply[0] != 19 or reply[1:20] != PROTOCOL:
            raise ValueError("Not a BitTorrent peer")
        if reply[28:48] != info_hash:
            raise ValueError("Peer sent a different info hash")
        return sock, reply[48:68]
    except Exception:
        sock.close()
        raise


def try_peer(args):
    ip, port, info_hash = args
    try:
        sock, peer_id = handshake(ip, port, info_hash)
        sock.close()
        return ip, port, peer_id, None
    except Exception as e:
        return ip, port, None, e


if __name__ == "__main__":
    meta, info, info_hash = load_torrent(sys.argv[1])
    total = total_size(info)

    peers = get_all_peers(meta, info_hash, total)
    print("Got", len(peers), "unique peers")

    if not peers:
        print("No peers found. Try again in a minute.")
        sys.exit(1)

    jobs = [(ip, port, info_hash) for ip, port in peers[:40]]
    ok = 0
    with ThreadPoolExecutor(max_workers=20) as pool:
        for ip, port, peer_id, error in pool.map(try_peer, jobs):
            if error is None:
                ok += 1
                tag = peer_id[:8].decode(errors="replace")
                print(f"OK    {ip}:{port}  client={tag}")
            else:
                print(f"fail  {ip}:{port}  ({type(error).__name__})")

    print(f"\nHandshake worked with {ok} of {len(jobs)} peers")