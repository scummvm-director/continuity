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
	def getResourceById(self, tag, idd):
		if not (tag in self.movie.resources):
			return None
		for i in self.movie.resources[tag]:
			if i.rid == idd:
				return i
		return None

	def parse(self, myfile, resources):
		self.movie = movie.Movie()
		self.movie.mac = self.mac
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
		if myfile.version < 0xf000:
			assert 'VWCR' in resources
			self.parseMovieCastRecord(resources['VWCR'][0])
		if 'VWCI' in resources:
			for i in resources['VWCI']:
				self.parseCastInfo(i)
		if 'CASt' in resources:
			for i in resources['CASt']:
				self.parseCastData(i)
		if 'VWSC' in resources:
			self.parseScore(self.getResourceById('VWSC', 1024))
		if 'VWTC' in resources:
			pass # FIXME
		if 'VWLB' in resources:
			self.parseLabels(self.getResourceById('VWLB', 1024))
		if 'VWAC' in resources:
			self.parseActions(self.getResourceById('VWAC', 1024))
		if 'VWFI' in resources:
			self.parseFileInfo(self.getResourceById('VWFI', 1024))
		else:
			self.movie.script = ""
			self.movie.changedBy = ""
			self.movie.createdBy = ""
			self.movie.flags = 0
			self.movie.whenLoadCast = -1
		if 'VWFM' in resources:
			self.parseFontMap(self.getResourceById('VWFM', 1024))
		if 'VWTL' in resources:
			pass # FIXME
		if 'STXT' in resources:
			for i in resources['STXT']:
				self.parseText(i)
		# FIXME: stupid hack for dibs,bitmaps
		self.movie.dibs = {}
		if 'DIB ' in resources:
			for i in resources['DIB ']:
				self.movie.dibs[i.rid] = i
		self.movie.bitmaps = {}
		if 'BITD' in resources:
			for i in resources['BITD']:
				self.movie.bitmaps[i.rid] = i
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
		if self.myfile.version < 0xf000: # d3
			assert size == data.size, (size, data.size) # FIXME: ??
		size = size - 4
		if self.myfile.version >= 0xf000:
			unk1 = read32(data)
			assert unk1 == 0x14
			unk2 = read32(data)
			# unk2 can be zero, the frame count, or something odd: e.g. unk2==200, frames==975
			#assert unk2 == 0
			unk3 = read16(data)
			assert unk3 == 4 or unk3 == 7, unk2 # 7 is d5
			unk4 = read16(data)
			assert unk4 == 0x14 or unk4 == 0x18, unk4 # d4 is 0x14, d5 is 0x18: frame size?
			unk5 = read16(data)
			assert unk5 == 0x32
			unk6 = read16(data)
			assert unk6 == 0x100 or unk6 == 0, unk6 # 0 is d5
			size = size - 16

		frameId = 0
		frameSize = 16
		if self.myfile.version >= 0xf000:
			frameSize = 20
		if self.myfile.version >= 0xf4c1: # d5
			frameSize = 24
		# FIXME: probably bad (like this since d3 frames are 16*26)
		#scoreData = bytearray('\x00' * frameSize * 26)
		scoreData = bytearray('\x00' * frameSize * 50)

		while size:
			frameId = frameId + 1
			frameSize = read16(data)

			print "score frame %d (size %d)" % (frameId, frameSize)

			assert frameSize <= size
			size = size - frameSize
			assert frameSize >= 2
			frameSize = frameSize - 2
			while frameSize:
				if self.myfile.version < 0xf000:
					assert frameSize >= 2
					frameSize = frameSize - 2
					channelSize = read8(data) * 2
					channelOffset = read8(data) * 2
				else:
					assert frameSize >= 4
					frameSize = frameSize - 4
					channelSize = read16(data)
					channelOffset = read16(data)

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
		if self.myfile.version < 0xf000:
			print "unk %s," % hexify(data.read(3)),
		else:
			frame.sound2 = read16(data)
			frame.soundType2 = read8(data)
		frame.skipFrameFlags = read8(data)
		print "skip frame flags %d," % frame.skipFrameFlags # 3 = on, 2 = off
		frame.blend = read8(data)
		print "blend %d," % frame.blend,
		if self.myfile.version < 0xf000:
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
		if self.myfile.version >= 0xf000:
			print "unk2 %s, " % hexify(data.read(11))
			if self.myfile.version >= 0xf4c1: # d5
				print "unk3 %s, " % hexify(data.read(7))
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
			x3 = ""
			frame.sprites[i+1] = entry
			print "%03d(%d)[%s,%s,%04x,%d/%d/%d/%d]," % (entry.castId, entry.enabled, hexify(x1), hexify(x2), entry.flags, entry.x, entry.y, entry.width, entry.height),
			if self.myfile.version >= 0xf000:
				scriptId = read16(data)
				flags2 = read8(data) # 0x40 editable, 0x80 moveable
				unk2 = read8(data)
				print "[%04x,%02x,%02x]"  % (scriptId, flags2, unk2),
				if self.myfile.version >= 0xf4c1: # d5
					data.read(4)
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

	def parseSubstrings(self, data, hasHeader=True):
		if hasHeader:
			ci_offset = read32(data)
			unk2 = read32(data) # not int!
			unk3 = read32(data) # not int!
			entryType = read32(data)
			data.seek(ci_offset)
		else:
			unk2 = 0
			unk3 = 0
			entryType = 0

		count = read16(data) + 1
		entries = []
		for i in range(count):
			entries.append(read32(data))
		rawdata = data.read(entries[-1])
		assert entries[0] == 0
		assert entries[-1] == len(rawdata)

		strings = []
		for i in range(count-1):
			strings.append(rawdata[entries[i]:entries[i+1]])

		return (strings, unk2, unk3, entryType)

	def parseCastInfo(self, data):
		# d3 variant
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

	def parseCastData(self, data):
		# d4+ variant
		if data.size == 0:
			return
		if data.size < 26:
			# FIXME: wtf?
			return

		info = movie.CastInfo()
		member = movie.CastMember()
		self.movie.cast[data.rid - 1024] = member

		if self.myfile.version < 0xf4c1: # d4
			size1 = read16(data)
			size2 = read32(data)
			size3 = 0
			member.castType = read8(data)
			blob = data.read(3)
		else: # d5
			# FIXME: only the cast type and the strings are good
			member.castType = read32(data)
			size2 = read32(data)
			size3 = read32(data)
			size1 = read32(data)
			assert size1 == 0x14
			size1 = 0
			blob = ""
		member.initialRect = readRect(data)
		member.boundingRect = readRect(data)
		member.regX = 0 # FIXME: HACK
		member.regY = 0 # FIXME: HACK
		print "%04x: cast type 0x%02x:" % (data.rid, member.castType), str(member.initialRect), str(member.boundingRect), hexify(blob), ",",
		print hexify(data.read(size1)),
		if size2:
			strings = self.parseSubstrings(data, False)[0]
			print strings
			strings.extend([""]*5) # FIXME: HACK
			info.script = strings[0]
			info.name = getString(strings[1])
			info.extDirectory = getString(strings[2])
			info.extFilename = getString(strings[3])
			info.extType = strings[4]

			self.movie.castInfo[data.rid] = info
		if size3:
			print hexify(data.read(size3))

	def parseFileInfo(self, data):
		ss,unk2,unk3,flags = self.parseSubstrings(data)
		self.movie.script = ss[0]
		self.movie.changedBy = getString(ss[1])
		self.movie.createdBy = getString(ss[2])
		self.movie.flags = flags
		self.movie.directory = getString(ss[3]) # d4+
		if ss[4]:
			assert len(ss[4]) == 2
			self.movie.whenLoadCast = struct.unpack(">H", ss[4])[0]
			assert self.movie.whenLoadCast in [0,1,2]
		else:
			self.movie.whenLoadCast = None
		if self.myfile.version < 0xf4c1 and len(ss) == 7: # d3/d4
			assert ss[5] == ""
			assert ss[6] == ""
		elif len(ss) == 5: # d4?
			pass
		else: # some d5?
			# TODO: three uint16s in ss[5]/ss[6]/ss[7]
			pass
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
		if data.size == 0: # v4 moved this into a text file
			return
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
		d.mac = True
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
