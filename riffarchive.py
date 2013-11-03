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

		for i in resources.values():
			for j in range(len(i)):
				i[j] = i[j].read(f)

		self.resources = resources

class RIFXResource:
	def read(self, f):
		f.seek(self.offset, 0)
		assert f.read(4) == self.tag
		assert read32(f) == self.size
		sio = StringIO(f.read(self.size))
		sio.tag = self.tag
		sio.rid = self.rid
		sio.size = self.size
		return sio

class RIFXArchive:
	def __init__(self, f):
		self.resources = {}

		f.seek(0, 2)
		fileLength = f.tell()

		# header
		f.seek(0, 0)
		tag = f.read(4)
		assert tag == "RIFX", tag # FIXME: XFIR (LE)
		fileLength2 = read32(f)
		assert fileLength2 <= fileLength - 8, fileLength2
		tag = f.read(4)
		assert tag == "MV93", tag # TODO: APPL..?

		# imap header
		tag = f.read(4)
		assert tag == "imap"
		imapLen = read32(f)
		assert imapLen == 24, imapLen
		unk1 = read32(f)
		assert unk1 == 1, unk1
		offset = read32(f)
		version = read32(f) # 0 for 4.0, 0x4c1 for 5.0, 0x4c7 for 6.0, 0x708 for 8.5, 0x742 for 10.0
		self.version = 0xf000 + version
		unk2 = read32(f)
		assert unk2 == 0, unk2
		unk3 = read32(f)
		assert unk3 == 0, unk3
		unk4 = read32(f)
		assert unk4 == 0, unk4

		print "RIFX: version 0x%08x" % version

		# mmap header
		f.seek(offset, 0)
		tag = f.read(4)
		assert tag == "mmap"
		mmapLen = read32(f)
		unk1 = read16(f) # 18
		unk2 = read16(f) # 14
		numEntries = read32(f)
		numUsefulEntries = read32(f)
		unk3 = read32(f) # 0xffffffff in early files
		unk4 = read32(f) # 0xffffffff in early files
		unk5 = read32(f) # ??
		print "mmap: %d entries (space for %d), unk: %04x, %04x, %08x, %08x, %08x" % (numUsefulEntries, numEntries, unk1, unk2, unk3, unk4, unk5)
		assert numUsefulEntries <= numEntries
		assert mmapLen == (24 + numEntries * 20)

		entries = []
		for i in range(numUsefulEntries):
			r = RIFXResource()
			r.tag = f.read(4)
			r.size = read32(f)
			r.offset = read32(f)
			r.rid = -1
			flags = read16(f)
			unk1 = read16(f)
			unk2 = read32(f)
			entries.append(r)

			print "entry %s: size %d, offset %d, flags %04x, unk %04x, %08x" % (r.tag, r.size, r.offset, flags, unk1, unk2)

			if flags == 0xc:
				assert r.tag == "free"
				continue
			if flags & 0x4:
				assert r.tag == "junk"
				continue
			if flags == 0x1:
				assert r.tag == "RIFX" or r.tag == "XFIR" or r.tag == "imap"
				continue
			if r.tag == "mmap":
				continue

			if not (r.tag in self.resources):
				self.resources[r.tag] = []
			self.resources[r.tag].append(r)

		assert 'KEY*' in self.resources
		assert len(self.resources['KEY*']) == 1
		key = self.resources['KEY*'][0]
		keydata = key.read(f)
		unk1 = read16(keydata)
		unk2 = read16(keydata)
		unk3 = read32(keydata)
		keyCount = read32(keydata)
		for i in range(keyCount):
			n = read32(keydata)
			rid = read32(keydata)
			tag = keydata.read(4)
			assert entries[n].tag == tag
			entries[n].rid = rid
			print "res %d (%s): %d" % (n, tag, rid)

		if 'CAS*' in self.resources:
			assert len(self.resources['CAS*']) == 1
			cas = self.resources['CAS*'][0]
			casdata = cas.read(f)
			cast = self.resources['CASt']
			assert casdata.size == len(cast)*4
			for n in range(len(cast)):
				castId = read32(casdata)
				assert entries[castId].tag == 'CASt'
				cast[n].rid = cas.rid + n + 1 # FIXME
		else:
			assert not ('CASt' in self.resources)

		for i in self.resources.values():
			for j in range(len(i)):
				i[j] = i[j].read(f)

