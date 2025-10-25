import sys

while True:
	b = sys.stdin.buffer.read(1)
	if b != "":
		print(hex(ord(b))[1:], end="")
