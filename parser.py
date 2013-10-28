import struct
from dutils import *
from riffarchive import *
from resourcefork import *
import movie

def hexify(data):
	s = ""
	allzeros = True
	for n in data:
		if ord(n) != 0:
			allzeros = False
	if allzeros:
		return ""
	for n in range(len(data)):
		if n != 0:
			s = s + " "
		s = s + ("%02x" % ord(data[n]))
	return s

class DirectorParser:
	def parse(self, myfile, resources):
		self.movie = movie.Movie()
		self.movie.resources = resources
		self.myfile = myfile
		if 'VER ' in resources:
			self.parseVersion(resources['VER '][0])
		if 'VER.' in resources:
			self.parseVersion(resources['VER.'][0])
		if 'MCNM' in resources:
			# only present (and mandatory) on Windows
			self.parseMacName(resources['MCNM'][0])
		assert 'VWCF' in resources
		self.parseMovieConfig(resources['VWCF'][0])
		assert 'VWCR' in resources
		self.parseMovieCastRecord(resources['VWCR'][0])
		if 'VWCI' in resources:
			for i in resources['VWCI']:
				self.parseCastInfo(i)
		if 'VWSC' in resources:
			self.parseScore(resources['VWSC'][0])
		if 'VWTC' in resources:
			pass # FIXME
		if 'VWLB' in resources:
			self.parseLabels(resources['VWLB'][0])
		if 'VWAC' in resources:
			self.parseActions(resources['VWAC'][0])
		if 'VWFI' in resources:
			pass # FIXME
		if 'VWFM' in resources:
			self.parseFontMap(resources['VWFM'][0])
		if 'VWTL' in resources:
			pass # FIXME
		if 'STXT' in resources:
			for i in resources['STXT']:
				pass # FIXME
		# FIXME: stupid hack for dibs
		self.movie.dibs = {}
		if 'DIB ' in resources:
			for i in resources['DIB ']:
				self.movie.dibs[i.rid] = i
		return self.movie

	def parseMovieConfig(self, data):
		if self.myfile.version > 36:
			assert data.size >= 30, data.size
		else:
			assert data.size >= 28, data.size
		unk = read16(data)
		version1 = read16(data)
		self.movie.movieRect = readRect(data)
		self.movie.castArrayStart = read16(data)
		self.movie.castArrayEnd = read16(data)
		self.movie.initialFrameRate = read8(data)
		# FIXME: probably this is actually another variable which should be skipped
		if self.myfile.version > 36:
			print hexify(data.read(9)) # skipped
		else:
			print hexify(data.read(7)) # skipped
		self.movie.stageColor = read16(data)
		self.movie.colorDepth = read16(data)
		print "config: unk %d, ver %x, rect %s, cast array %d-%d, framerate %d, stage color %d, depth %d" % (unk, version1, self.movie.movieRect, self.movie.castArrayStart, self.movie.castArrayEnd, self.movie.initialFrameRate, self.movie.stageColor, self.movie.colorDepth)
		if data.size > 30:
			unk1f = read8(data)
			unk20 = read8(data)
			print hexify(data.read(4)) # skipped?
			print "config: unk2f %d, unk20 %d" % (unk1f, unk20)
			if data.size > 36:
				version2 = read16(data)
				print "config: ver2 %d" % version2
				print "%x %x %x %x %x %x" % (read16(data), read16(data), read16(data), read16(data), read16(data), read16(data))
		# FIXME: sanity-check colorDepth, set version2 to 0x404 if a VWFI is present, etc etc

	def parseScore(self, data):
		self.movie.frames = []
		size = read32(data)
		assert size == data.size
		size = size - 4
		frameId = 0
		scoreData = bytearray('\x00' * 16 * 26)
		while size:
			frameId = frameId + 1
			frameSize = read16(data)

			print "score frame %d (size %d)" % (frameId, frameSize)

			assert frameSize <= size
			size = size - frameSize
			assert frameSize >= 2
			frameSize = frameSize - 2
			while frameSize:
				assert frameSize >= 2
				frameSize = frameSize - 2

				channelSize = read8(data) * 2
				channelOffset = read8(data) * 2

				assert channelSize <= frameSize
				frameSize = frameSize - channelSize

				channelData = data.read(channelSize)
				#print " diff at offset %d, size %d, data %s" % (channelOffset, channelSize, repr(channelData))

				assert channelOffset + channelSize <= len(scoreData)
				scoreData[channelOffset:channelOffset+channelSize] = channelData

			assert size >= 0
			frame = self.dumpScoreData(scoreData)
			self.movie.frames.append(frame)

	def dumpScoreData(self, score):
		frame = movie.Frame()
		data = StringIO.StringIO(score)
		# header:
		print " header:",
		print "unk %s," % hexify(data.read(2)),
		frame.transFlags = read8(data)
		frame.transData1 = read8(data)
		frame.tempo = read8(data)
		frame.transData2 = read8(data)
		frame.sound = read16(data)
		print "trans %d (%d/%d), tempo %d, sound %d," % (frame.transFlags, frame.transData1, frame.transData2, frame.tempo, frame.sound),
		print "unk %s," % hexify(data.read(8)),
		print
		# palette:
		frame.palette = read16(data)
		print " palette %d:" % frame.palette,
		print "unk %s," % hexify(data.read(2))
		print read8(data), # palette data1
		print read8(data), # palette data2
		print read16(data), # palette id 2
		print read16(data),
		print "unk %s," % hexify(data.read(6)),
		print
		# cast:
		print " cast:",
		frame.cast = []
		for i in range(24):
			entry = movie.CastEntry()
			x1 = data.read(1)
			entry.enabled = read8(data)
			x2 = data.read(3)
			entry.unk3 = read8(data)
			entry.castId = read16(data)
			entry.y = read16(data)
			entry.x = read16(data)
			entry.height = read16(data)
			entry.width = read16(data)
			frame.cast.append(entry)
			print "%03d(%d)[%s,%s,%d]," % (entry.castId, entry.enabled, hexify(x1), hexify(x2), entry.unk3),
		print
		return frame

	def parseMovieCastRecord(self, data):
		currId = self.movie.castArrayStart
		while currId <= self.movie.castArrayEnd:
			if data.tell() == data.size:
				print "(warning: cast record ran out early)"
				break
			entrySize = read8(data)
			entryType = 0
			entryData = ''
			if entrySize > data.tell() + data.size:
				print "(warning: cast record ran out, wanted %d more bytes)" % entrySize
				break
			if entrySize:
				entryType = read8(data)
				entrySize = entrySize - 1
				if entryType == 1:
					flags = read8(data)
					someFlaggyThing = read16(data)
					initialRect = readRect(data)
					boundingRect = readRect(data)
					u1 = read16(data)
					u2 = read16(data)
					entrySize = entrySize - 23
					if (someFlaggyThing & 0x8000):
						u7 = read16(data)
						u8 = read16(data)
						entrySize = entrySize - 4
					assert entrySize == 0
				assert entrySize >= 0
				entryData = data.read(entrySize)
			print "cast member: id %d, type %d (size %d, %s)" % (currId, entryType, entrySize, hexify(entryData))
			if entryType == 1:
				print "  flag %02x/%04x, %s, %s, unk %04x %04x" % (flags, someFlaggyThing, initialRect, boundingRect, u1, u2)
				if (someFlaggyThing & 0x8000):
					print "  unk %04x %04x" % (u7, u8)
			currId = currId + 1

	def parseCastInfo(self, data):
		entry = movie.CastEntry()
		ci_offset = read32(data)
		unk2 = read32(data) # not int!
		unk3 = read32(data) # not int!
		# when unk3 is 1, data is script. otherwise 0: name.
		entryType = read32(data)
		data.seek(ci_offset)
		count = read16(data) + 1
		entries = []
		for i in range(count):
			entries.append(read32(data))
		if unk3 == 0 and (data.tell() < data.size):
			entry.name = readString(data)
			entry.data = ""
		else:
			entry.name = ""
			entry.data = data.read()
		print "VWCI: id %d, type %d, name %s, data %s, entries %s, unk %08x/%08x" % (data.rid, entryType, repr(entry.name), repr(entry.data), str(entries), unk2, unk3)
		self.movie.cast[data.rid] = entry

	def parseMacName(self, data):
		if data.size:
			dirname = readString(data)
		else:
			dirname = ""
		print "mac name: %s, directory %s" % (repr(data.name), repr(dirname))

	def parseVersion(self, data):
		self.versionMinor = data.rid & 0xffff
		self.versionMajor = data.rid >> 16
		print "version: %d.%d" % (self.versionMajor, self.versionMinor)
		assert self.versionMajor <= 3
		if self.versionMajor == 0:
			assert self.versionMinor >= 0x21
		elif self.versionMajor == 3:
			assert self.versionMinor < 0x100

	def parseFontMap(self, data):
		count = read16(data)
		fontmaps = []
		for i in range(count):
			fontmaps.append([read16(data), None])
		for i in range(count):
			fontmaps[i][1] = readString(data)
		print "VWFM: " + str(fontmaps)
		self.movie.fontMaps = fontmaps

	# TODO: duplicates code below
	def parseActions(self, data):
		# FIXME: unverified
		count = read16(data) + 1
		labels = []
		for i in range(count):
			# pairs of ((id, usually 1, sometimes higher; or 0/0), string start pos)
			labels.append([[read8(data), read8(data)], read16(data)])
		stringdata = data.read()
		print "VWAC actions:",
		for i in range(count - 1):
			s = stringdata[labels[i][1]:labels[i+1][1]]
			print "%d/%d %s," % (labels[i][0][0], labels[i][0][1], repr(s)),
		print
		# last entry is just a terminator
		assert labels[-1][0][1] == 0
		assert labels[-1][1] == len(stringdata)

	def parseLabels(self, data):
		self.movie.labels = []
		count = read16(data) + 1
		labels = []
		for i in range(count):
			# pairs of (frame id, string start pos)
			labels.append([read16(data), read16(data)])
		stringdata = data.read()
		print "VWLB labels:",
		for i in range(count - 1):
			s = stringdata[labels[i][1]:labels[i+1][1]]
			print "frame %d %s," % (labels[i][0], repr(s)),
			mylabel = movie.Label()
			mylabel.frame = labels[i][0]
			mylabel.text = s
			self.movie.labels.append(mylabel)
		print
		# last entry is just a terminator
		assert labels[-1][0] == 0

def parseFile(filename):
	myfile = open(filename)
	d = DirectorParser()
	if ("mmm" in filename) or ("MMM" in filename):
		a = RiffArchive(myfile)
		d.mac = False
		movie = d.parse(a, a.resources)
	else:
		a = ResourceFork(myfile)
		d.mac = True
		a.version = 36 # FIXME: hack
		movie = d.parse(a, a.get_all_resources())
	return movie

if __name__ == '__main__':
	import sys
	movie = parseFile(sys.argv[1])
	print movie.__dict__
