from bencode import decode, encode

print(decode(b"i42e"))
print(decode(b"4:spam"))
print(decode(b"l4:spami42ee"))
print(decode(b"d3:cow3:moo4:spam4:eggse"))

# Round trip: encoding what we decoded should give the original bytes
original = b"d3:cow3:moo4:spam4:eggse"
print(encode(decode(original)) == original)