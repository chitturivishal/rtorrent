def decode(data: bytes):
    value, _ = _decode_next(data, 0)
    return value


def _decode_next(data: bytes, i: int):
    char = data[i:i + 1]

    # Integer: i42e
    if char == b"i":
        end = data.index(b"e", i)
        return int(data[i + 1:end]), end + 1

    # List: l ... e
    if char == b"l":
        i += 1
        items = []
        while data[i:i + 1] != b"e":
            item, i = _decode_next(data, i)
            items.append(item)
        return items, i + 1

    # Dictionary: d ... e
    if char == b"d":
        i += 1
        result = {}
        while data[i:i + 1] != b"e":
            key, i = _decode_next(data, i)
            value, i = _decode_next(data, i)
            result[key] = value
        return result, i + 1

    # String: 4:spam
    if char.isdigit():
        colon = data.index(b":", i)
        length = int(data[i:colon])
        start = colon + 1
        return data[start:start + length], start + length

    raise ValueError(f"Invalid bencode at position {i}")


def encode(value) -> bytes:
    if isinstance(value, int):
        return b"i" + str(value).encode() + b"e"
    if isinstance(value, bytes):
        return str(len(value)).encode() + b":" + value
    if isinstance(value, str):
        return encode(value.encode())
    if isinstance(value, list):
        return b"l" + b"".join(encode(v) for v in value) + b"e"
    if isinstance(value, dict):
        result = b"d"
        for key in sorted(value):
            result += encode(key) + encode(value[key])
        return result + b"e"
    raise TypeError(f"Cannot encode {type(value)}")
