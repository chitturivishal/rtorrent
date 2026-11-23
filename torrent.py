import hashlib
import sys

from bencode import decode, encode


def load_torrent(path):
    with open(path, "rb") as f:
        meta = decode(f.read())
    info = meta[b"info"]
    info_hash = hashlib.sha1(encode(info)).digest()
    return meta, info, info_hash


if __name__ == "__main__":
    path = sys.argv[1]
    meta, info, info_hash = load_torrent(path)

    if b"length" in info:
        total = info[b"length"]
    else:
        total = sum(f[b"length"] for f in info[b"files"])

    print("Name:", info[b"name"].decode())
    print("Tracker:", meta.get(b"announce", b"(none)").decode())
    print("Total size (MB):", round(total / 1024 / 1024, 1))
    print("Piece length:", info[b"piece length"])
    print("Number of pieces:", len(info[b"pieces"]) // 20)
    print("Info hash:", info_hash.hex())