import sys
from pylibdmtx import pylibdmtx
from PIL import Image

INPUT = sys.stdin.read().encode()
OUTPUT_FILE = sys.argv[1]

encoded = pylibdmtx.encode(INPUT)
img = Image.frombytes("RGB", (encoded.width, encoded.height), encoded.pixels)

img.save(OUTPUT_FILE)
