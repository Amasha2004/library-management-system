import struct, zlib, os

def create_png(width, height, pixels):
    def chunk(name, data):
        c = struct.pack('>I', len(data)) + name + data
        return c + struct.pack('>I', zlib.crc32(c[4:]) & 0xffffffff)
    raw = b''
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            raw += bytes(pixels[y][x])
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw))
    png += chunk(b'IEND', b'')
    return png

# 32x32 favicon with book icon style
size = 32
pixels = []
for y in range(size):
    row = []
    for x in range(size):
        # Background circle
        cx, cy = size//2, size//2
        dist = ((x-cx)**2 + (y-cy)**2)**0.5
        if dist <= 15:
            # Purple gradient background
            r = max(99, min(139, 99 + int((x/size)*40)))
            g = max(102, min(102, 102))
            b = max(241, min(246, 241 + int((y/size)*5)))
            # Book shape in white
            bx1, bx2 = 9, 23
            by1, by2 = 8, 24
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                # Book pages
                if x == bx1 or x == bx2 or y == by1 or y == by2:
                    row.append([255, 255, 255])
                elif x == (bx1+bx2)//2:
                    row.append([255, 255, 255])
                elif by1+4 <= y <= by1+5 and bx1+2 <= x <= bx2-2:
                    row.append([255, 255, 255])
                elif by1+8 <= y <= by1+9 and bx1+2 <= x <= bx2-2:
                    row.append([255, 255, 255])
                else:
                    row.append([r, g, b])
            else:
                row.append([r, g, b])
        else:
            row.append([240, 242, 245])
    pixels.append(row)

os.makedirs('app/static', exist_ok=True)
with open('app/static/favicon.png', 'wb') as f:
    f.write(create_png(size, size, pixels))
print('Favicon created!')