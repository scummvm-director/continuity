channelCount = 24
reservedChannelCount = 6
tempoChannel = -5
paletteChannel = -4
transitionChannel = -3
soundChannel1 = -2
soundChannel2 = -1
scriptChannel = 0

castBitmap = 1
castFilmLoop = 2
castText = 3
castPalette = 4
castPicture = 5
castSound = 6
castButton = 7
castShape = 8
castMovie = 9
castDigitalVideo = 10
castScript = 11

class Movie:
	def __init__(self):
		self.castInfo = {}
		self.labels = []
		self.cast = {}

class Frame:
	def __init__(self):
		self.sprites = {}

class Label:
	pass

class Sprite:
	def __init__(self):
		self.enabled = True
		self.castId = -1

class CastInfo:
	pass

class CastMember:
	pass

class Action:
	pass
