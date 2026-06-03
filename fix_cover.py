import os, struct, zlib

os.makedirs('app/static/uploads', exist_ok=True)

def create_png(width, height, color):
    def chunk(name, data):
        c = struct.pack('>I', len(data)) + name + data
        return c + struct.pack('>I', zlib.crc32(c[4:]) & 0xffffffff)
    raw = b''
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            raw += bytes(color)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw))
    png += chunk(b'IEND', b'')
    return png

with open('app/static/uploads/default_cover.png', 'wb') as f:
    f.write(create_png(200, 280, [26, 35, 126]))

print('Default cover created!')