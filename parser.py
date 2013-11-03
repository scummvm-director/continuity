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
			self.parseFileInfo(resources['VWFI'][0])
		if 'VWFM' in resources:
			self.parseFontMap(resources['VWFM'][0])
		if 'VWTL' in resources:
			pass # FIXME
		if 'STXT' in resources:
			for i in resources['STXT']:
				self.parseText(i)
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
		# FIXME: the versioning in the stuff below is probably wrong?
		print hexify(data.read(9)) # skipped
		self.movie.stageColor = read16(data)
		if self.myfile.version > 36:
			self.movie.colorDepth = read16(data)
		else:
			self.movie.colorDepth = 8
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
		if self.movie.colorDepth > 8:
			self.movie.colorDepth = 8
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
		frame.actionId = read8(data)
		if frame.actionId:
			frame.sprites[movie.scriptChannel] = movie.Sprite()
		frame.soundType1 = read8(data) # type: 0x17 for sounds (sound is cast id), 0x16 for MIDI (sound is cmd id)
		frame.transFlags = read8(data) # 0x80 is whole stage (vs changed area), rest is duration in 1/4ths of a second
		frame.transChunkSize = read8(data)
		frame.tempo = read8(data)
		if frame.tempo:
			frame.sprites[movie.tempoChannel] = movie.Sprite()
		frame.transType = read8(data)
		if frame.transType:
			frame.sprites[movie.transitionChannel] = movie.Sprite()
		frame.sound1 = read16(data)
		if frame.sound1:
			frame.sprites[movie.soundChannel1] = movie.Sprite()
			frame.sprites[movie.soundChannel1].castId = frame.sound1
		print "action %d, trans %d/%d:%d, tempo %d, sound %d (%02x)," % (frame.actionId, frame.transFlags, frame.transChunkSize, frame.transType, frame.tempo, frame.sound1, frame.soundType1),
		print "unk %s," % hexify(data.read(3)),
		frame.skipFrameFlags = read8(data)
		print "skip frame flags %d," % frame.skipFrameFlags # 3 = on, 2 = off
		frame.blend = read8(data)
		print "blend %d," % frame.blend,
		frame.sound2 = read16(data)
		frame.soundType2 = read8(data)
		if frame.sound2:
			frame.sprites[movie.soundChannel2] = movie.Sprite()
			frame.sprites[movie.soundChannel2].castId = frame.sound2
		print "sound2 %d (%02x)" % (frame.sound2, frame.soundType2),
		print
		# palette:
		frame.palette = read16(data)
		if frame.palette:
			frame.sprites[movie.paletteChannel] = movie.Sprite()
		frame.paletteFirstColor = read8(data) # for cycles. note: these start at 0x80 (for pal entry 0)!
		frame.paletteLastColor = read8(data)
		frame.paletteFlags = read8(data)
		frame.paletteSpeed = read8(data)
		frame.paletteFrameCount = read16(data) # for 'over time'
		frame.paletteCycleCount = read16(data)
		print " palette %d: cycle %d-%d, flags %02x, speed %d, %d frames, %d cycles" % (frame.palette, frame.paletteFirstColor, frame.paletteLastColor, frame.paletteFlags, frame.paletteSpeed, frame.paletteFrameCount, frame.paletteCycleCount)
		print "unk %s," % hexify(data.read(6)),
		print
		# cast:
		print " sprites:",
		for i in range(movie.channelCount):
			entry = movie.Sprite()
			x1 = data.read(1)
			entry.enabled = read8(data)
			x2 = data.read(2)
			entry.flags = read16(data)
			entry.castId = read16(data)
			entry.y = read16(data,True)
			entry.x = read16(data,True)
			entry.height = read16(data,True)
			entry.width = read16(data,True)
			frame.sprites[i+1] = entry
			print "%03d(%d)[%s,%s,%04x]," % (entry.castId, entry.enabled, hexify(x1), hexify(x2), entry.flags),
		print
		return frame

	def parseMovieCastRecord(self, data):
		currId = self.movie.castArrayStart
		while currId <= self.movie.castArrayEnd:
			if data.tell() == data.size:
				print "(warning: cast record ran out early)"
				break
			entrySize = read8(data)
			entryType = -1
			entryData = ''
			if entrySize > data.tell() + data.size:
				print "(warning: cast record ran out, wanted %d more bytes)" % entrySize
				break
			if entrySize:
				entry = movie.CastMember()
				entry.castType = read8(data)
				entrySize = entrySize - 1
				if entry.castType == movie.castBitmap:
					flags = read8(data)
					someFlaggyThing = read16(data)
					entry.initialRect = readRect(data)
					entry.boundingRect = readRect(data)
					# registration point
					entry.regY = read16(data,True)
					entry.regX = read16(data,True)
					entrySize = entrySize - 23
					if (someFlaggyThing & 0x8000):
						u7 = read16(data)
						u8 = read16(data)
						entrySize = entrySize - 4
					assert entrySize == 0
				elif entry.castType == movie.castText or entry.castType == movie.castButton:
					flags = read8(data)
					entry.borderSize = read8(data)
					entry.gutterSize = read8(data)
					entry.boxShadow = read8(data)
					entry.textType = read8(data)
					entry.textAlign = read16(data, True)
					palInfo = data.read(6) # ??? unused?
					unk1 = data.read(4) # TODO: always zeros?
					entry.initialRect = readRect(data)
					entry.textShadow = read8(data)
					entry.textFlags = read8(data)
					unk2 = read16(data) # TODO: always 12?
					entrySize = entrySize - 29
					if entry.castType == 7:
						entry.buttonType = read16(data)
						entrySize = entrySize - 2
					assert entrySize == 0
				elif entry.castType == movie.castShape:
					flags = read8(data)
					unk1 = read8(data)
					entry.shapeType = read8(data)
					entry.initialRect = readRect(data)
					entry.pattern = read16(data)
					entry.fgCol = read8(data)
					entry.bgCol = read8(data)
					entry.fillType = read8(data)
					entry.lineThickness = read8(data)
					entry.lineDirection = read8(data)
					entrySize = entrySize - 18
				assert entrySize >= 0
				entryData = data.read(entrySize)
				self.movie.cast[currId] = entry
			print "cast member: id %d, type %d (size %d, %s)" % (currId, entry.castType, entrySize, hexify(entryData))
			if entry.castType == 1:
				print "  flag %02x/%04x, %s, %s, reg (%d, %d)" % (flags, someFlaggyThing, entry.initialRect, entry.boundingRect, entry.regX, entry.regY)
				if (someFlaggyThing & 0x8000):
					print "  unk %04x %04x" % (u7, u8)
			currId = currId + 1

	def parseSubstrings(self, data):
		ci_offset = read32(data)
		unk2 = read32(data) # not int!
		unk3 = read32(data) # not int!
		entryType = read32(data)
		data.seek(ci_offset)

		count = read16(data) + 1
		entries = []
		for i in range(count):
			entries.append(read32(data))
		rawdata = data.read()
		assert entries[0] == 0
		assert entries[-1] == len(rawdata)

		strings = []
		for i in range(count-1):
			strings.append(rawdata[entries[i]:entries[i+1]])

		return (strings, unk2, unk3, entryType)

	def parseCastInfo(self, data):
		entry = movie.CastInfo()
		strings, unk2, unk3, entryType = self.parseSubstrings(data)
		assert len(strings) == 5

		entry.script = strings[0]
		entry.name = getString(strings[1])
		entry.extDirectory = getString(strings[2])
		entry.extFilename = getString(strings[3])
		entry.extType = strings[4]
		print "VWCI: id %d, type %d, name %s, script %s, unk %08x/%08x" % (data.rid, entryType, repr(entry.name), repr(entry.script), unk2, unk3)
		if entry.extDirectory or entry.extFilename or entry.extType:
			print " file %s/%s(%s)" % (repr(entry.extDirectory), repr(entry.extFilename), repr(entry.extType))
		self.movie.castInfo[data.rid] = entry

	def parseFileInfo(self, data):
		ss,unk2,unk3,flags = self.parseSubstrings(data)
		self.movie.script = ss[0]
		self.movie.changedBy = getString(ss[1])
		self.movie.createdBy = getString(ss[2])
		self.movie.flags = flags
		assert ss[3] == ""
		assert len(ss[4]) == 2
		self.movie.whenLoadCast = struct.unpack(">H", ss[4])[0]
		assert self.movie.whenLoadCast in [0,1,2]
		assert ss[5] == ""
		assert ss[6] == ""
		print 'VWFI data', ss,hex(unk2),hex(unk3),hex(flags)

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
		self.movie.actions = {}
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
			myaction = movie.Action()
			myaction.script = s
			# TODO: can frames have multiple actions..?
			self.movie.actions[labels[i][0][0]] = myaction
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

	def parseText(self, data):
		unk1 = read32(data)
		assert unk1 == 12 # i.e. after header
		strLen = read32(data)
		dataLen = read32(data)
		print 'text %d: ' % data.rid + repr(data.read(strLen)) + ", " + repr(data.read(dataLen))

def parseFile(filename):
	myfile = open(filename)
	hdr = myfile.read(4)
	myfile.seek(0)
	d = DirectorParser()
	if hdr == "RIFF":
		a = RiffArchive(myfile)
		d.mac = False
		movie = d.parse(a, a.resources)
	elif hdr == "RIFX":
		a = RIFXArchive(myfile)
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
