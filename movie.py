class Movie:
	def __init__(self):
		self.cast = {}
		self.labels = []

		self.channels = {}
		for i in range(24):
			self.channels[i] = Channel()

class Frame:
	pass

class Channel:
	pass

class Label:
	pass

class CastEntry:
	pass
