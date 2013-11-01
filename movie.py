channelCount = 24
reservedChannelCount = 6
tempoChannel = -5
paletteChannel = -4
transitionChannel = -3
soundChannel1 = -2
soundChannel2 = -1
scriptChannel = 0

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
