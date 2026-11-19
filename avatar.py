"""Create a branded Telegram avatar as a PNG using only the Python standard library."""
import math
import struct
import zlib


def line_distance(x, y, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / max(1.0, dx * dx + dy * dy)))
    return math.hypot(x - (x1 + dx * t), y - (y1 + dy * t))


def render(size=320):
    """A dark cyan/violet AI circuits, download arrow and tray icon."""
    scale = size / 320
    lines = [
        (85, 131, 111, 96), (111, 96, 143, 96), (235, 131, 209, 96),
        (209, 96, 177, 96), (77, 154, 108, 154), (108, 154, 140, 185),
        (243, 154, 212, 154), (212, 154, 180, 185),
        (88, 193, 118, 172), (232, 193, 202, 172),
    ]
    nodes = [(106, 96), (214, 96), (78, 154), (242, 154), (88, 193), (232, 193)]
    rows = []
    for py in range(size):
        y = (py + 0.5) / scale
        row = bytearray([0])
        for px in range(size):
            x = (px + 0.5) / scale
            radius = math.hypot(x - 160, y - 160)
            light = min(1.0, math.exp(-((radius - 141) / 4.3) ** 2) * 0.9)
            glow = max(0.0, math.exp(-((radius - 141) / 15.0) ** 2) * 0.25)
            for x1, y1, x2, y2 in lines:
                d = line_distance(x, y, x1, y1, x2, y2)
                light = max(light, max(0.0, 1.0 - d / 3.6) * 0.93)
                glow = max(glow, max(0.0, 1.0 - d / 8.0) * 0.18)
            for nx, ny in nodes:
                d = math.hypot(x - nx, y - ny)
                light = max(light, max(0.0, 1.0 - d / 7.5))
            # Bold download arrow with a shaft and tapered head.
            arrow = (143 <= x <= 177 and 94 <= y <= 209) or (
                196 <= y <= 246 and abs(x - 160) <= (248 - y) * 1.32)
            tray = ((103 <= x <= 217 and 265 <= y <= 274) or
                    (99 <= x <= 110 and 244 <= y <= 269) or
                    (210 <= x <= 221 and 244 <= y <= 269))
            if arrow or tray:
                light = 1.0
            purple = max(0.0, (y - 178) / 145)
            r = min(255, int(6 + 34 * glow + light * (7 + 69 * purple)))
            g = min(255, int(13 + 72 * glow + light * (227 - 115 * purple)))
            b = min(255, int(29 + 95 * glow + light * 246))
            row += bytes((r, g, b))
        rows.append(bytes(row))
    raw = b"".join(rows)
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw, level=6)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    from pathlib import Path
    Path("avatar.png").write_bytes(render())
