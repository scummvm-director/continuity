class Movie:
	def __init__(self):
		self.castInfo = {}
		self.labels = []
		self.cast = {}

		self.channels = {}
		for i in range(24):
			self.channels[i] = Channel()

class Frame:
	pass

class Channel:
	pass

class Label:
	pass

class Sprite:
	pass

class CastInfo:
	pass

class CastMember:
	pass
