import struct
from StringIO import StringIO
from dutils import *

class RiffResource:
	def read(self, f):
		if self.tag == "CFTC":
			return None
		f.seek(self.offset, 0)
		assert f.read(4).upper() == self.tag
		assert read32(f, True) == self.size
		assert read32(f, True) == self.rid
		name = None
		self.size = self.size - 4
		name = readString(f)
		if len(name):
			print self.rid, self.tag, name
		self.size = self.size - len(name) - 1
		if ((f.tell() - self.offset) & 1) != 0:
			f.read(1) # padding
			self.size = self.size - 1
		sio = StringIO(f.read(self.size))
		sio.tag = self.tag
		sio.rid = self.rid
		sio.name = name
		sio.size = self.size
		return sio

class RiffArchive:
	def __init__(self, f):
		f.seek(0, 2)
		fileLength = f.tell()
		f.seek(0, 0)
		tag = f.read(4)
		assert tag == "RIFF", tag
		fileSize = read32(f, True)
		if not (fileSize == fileLength or fileSize == fileLength - 8):
			print "file sizes don't match: claims size %d, is size %d" % (fileSize, fileLength)
		tag = f.read(4).upper()
		assert tag == "RMMP", tag
		tag = f.read(4).upper()
		assert tag == "CFTC", tag

		f.read(8) # don't care

		resources = {}

		self.version = -1

		while True:
			r = RiffResource()
			r.tag = f.read(4)
			if r.tag == "\x00\x00\x00\x00":
				break
			r.tag = r.tag.upper()
			r.size = read32(f, True)
			r.rid = read32(f, True)
			r.offset = read32(f, True)

			if r.tag == "VER " or r.tag == "VER.":
				self.version = r.rid

			print "entry %s: id %d, size %d, offset %d" % (r.tag, r.rid, r.size, r.offset)
			if r.offset >= fileSize:
				print "bad entry %s: id %d, size %d, offset %d, file size %d" % (r.tag, r.rid, r.size, r.offset, fileSize)

			if not (r.tag in resources):
				resources[r.tag] = []
			resources[r.tag].append(r)

		print "version", self.version
		global version
		version = self.version

		for i in resources.values():
			for j in range(len(i)):
				i[j] = i[j].read(f)

		self.resources = resources

