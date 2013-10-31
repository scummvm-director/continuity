import struct
from StringIO import StringIO

def read32(f, le=False):
        x = f.read(4)
	if le:
	        return struct.unpack("<I", x)[0]
	else:
	        return struct.unpack(">I", x)[0]

def read16(f, signed=False):
        x = f.read(2)
	if signed:
	        return struct.unpack(">h", x)[0]
	else:
	        return struct.unpack(">H", x)[0]

def read8(f):
        x = f.read(1)
        return struct.unpack("<B", x)[0]

def readString(f):
	s = read8(f)
	return f.read(s)

def getString(s):
	if len(s) == 0:
		return s
	l = ord(s[0])
	s = s[1:]
	assert l == len(s)
	return s

class Rect:
	def width(self):
		return self.right - self.left

	def height(self):
		return self.bottom - self.top

	def __str__(self):
		return "(%d, %d, %d, %d)" % (self.left, self.top, self.right, self.bottom)

def readRect(f):
	r = Rect()
	r.top = read16(f,True)
	r.left = read16(f,True)
	r.bottom = read16(f,True)
	r.right = read16(f,True)
	return r

import struct
def imageFromDIB(data, pos, movie):
	# fake a stupid BMP (sigh)
	palette = ""
	assert ord(data[0]) == 40 and ord(data[1]) == 0 # size
	depth = ord(data[14])
	width, height = struct.unpack("<Ii", data[4:12])
	assert depth == 1 or depth == 4 or depth == 8
	palentries = ord(data[32]) + (ord(data[33]) << 8)
	if palentries == 0:
#		palentries = 2**depth
		palentries = 256
	else:
		# FIXME
		print "WARNING: palentries %d" % palentries
	palId = 0
	for n in range(pos+1):
		if movie.frames[n].palette != 0:
			palId = movie.frames[n].palette
	if palId != 0 and 'CLUT' in movie.resources:
		for p in movie.resources['CLUT']:
			if p.rid == palId + 1024:
				p.seek(0)
				d = p.read()
				for i in range(len(d)/6):
					l = len(d)/6
					n = l - i - 1
					if i >= palentries:
						break
					palette = palette + d[n*6+4] + d[n*6+2] + d[n*6] + '\x00'
				while len(palette) < 4*palentries:
					palette = palette + '\x00'
	else:
		pf = open("data/mac.pal")
		pf.read(6) # 0:seed,4:flags
		assert read16(pf)+1 == 256 # count
		pf = pf.read()
		n = 0
		for e in range(palentries):
			ee = 255 - e
			# high bytes of uint16s, ignore the first
#			palette = palette + pf[e*8+6] + pf[e*8+4] + pf[e*8+2] + '\x00'
			palette = palette + pf[ee*8+6] + pf[ee*8+4] + pf[ee*8+2] + '\x00'
	totalsize = 14 + len(data) + len(palette)
	offset = 14 + 40 + len(palette)
	rawdata = data[40:]
	if depth == 1:
		# 1bpp handled differently: always top-down
		if height > 0:
			data = data[:8] + struct.pack("<i", -height) + data[12:]
		# 1bpp handled differently: word padding, so we have to expand to dword padding
		oldrawdata = rawdata
		rawdata = ""
		realwidth = ((width+7)/8)
		realwidth = ((realwidth+1)/2)*2
		neededwidth = ((realwidth+3)/4)*4
		for n in range(height):
			rawdata = rawdata + oldrawdata[n*realwidth:n*realwidth+realwidth] + '\x00' * (neededwidth - realwidth)
	dibdata = "BM" + struct.pack("<III", totalsize, 0, offset) + data[:40] + palette + rawdata

	return dibdata


