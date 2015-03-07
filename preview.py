from PySide.QtCore import *
from PySide.QtGui import *
from dutils import *
from movie import *

class Preview(QWidget):
	def __init__(self, parent, movie):
		QWidget.__init__(self, parent)
		parent.setBackgroundRole(QPalette.Dark)
		self.movie = movie
		self.resize(self.movie.movieRect.width(), self.movie.movieRect.height())
		self.parent().parent().parent().parent().selectionChanged.connect(self.selectionChanged)

	def selectionChanged(self):
		self.update()

	def paintEvent(self, ev):
		if self.movie.currFrame == -1:
			return

		painter = QPainter(self)

		palette = getPaletteFor(self.movie.currFrame, self.movie)
		bgcol = self.movie.stageColor & (2**self.movie.colorDepth - 1)
		if bgcol < len(palette)/4: # TODO: ??
			painter.setBrush(QBrush(QColor(ord(palette[4*bgcol+2]), ord(palette[4*bgcol+1]), ord(palette[4*bgcol]))))
		painter.drawRect(0, 0, self.movie.movieRect.width(), self.movie.movieRect.height())
		painter.setBrush(QBrush())

		for i in range(channelCount):
			info = self.movie.frames[self.movie.currFrame].sprites[i+1]
			if not info.enabled:
				continue
			castinfo = None
			if info.castId in self.movie.cast:
				castinfo = self.movie.cast[info.castId]
			myId = 1024 + info.castId
			mystr = str(info.castId)
			img = None
			wasDib = False
			if myId in self.movie.dibs:
				dib = self.movie.dibs[myId]
				dib.seek(0)
				data = dib.read()
				imgdata = imageFromDIB(data, palette)
				img = QImage.fromData(imgdata, "bmp")
				wasDib = True
			elif myId in self.movie.bitmaps:
				bitmap = self.movie.bitmaps[myId]
				bitmap.seek(0)
				data = bitmap.read()
				data = unPackBits(data)
				if castinfo:
					rect = castinfo.initialRect
					width = rect.width()
					height = rect.height()
				else:
					# TODO
					width = info.width
					height = info.height
				img = QImage(QSize(width, height), QImage.Format_Indexed8)
				alignedwidth = width
				if width & 1:
					alignedwidth = width + 1
				mypal = []
				for i in range(256):
					# flip the stupid palette to mac order..
					#n = 255 - i
					n = i
					mypal.append(qRgb(ord(palette[n*4]),ord(palette[n*4+1]),ord(palette[n*4+2])))
				img.setColorTable(mypal)
				for y in range(height):
					scanline = memoryview(img.scanLine(y))
					ourline = data[alignedwidth*y:alignedwidth*(y+1)]
					ourline = ourline + '\x00' * (len(scanline) - len(ourline))
					scanline[0:width] = ourline[0:width]
			if img:
				pixmap = QPixmap.fromImage(img)
				ink = info.flags & 0x3f
				mask = None
				if ink == 8: # matte
					mask = img.createHeuristicMask()
				if ink == 0x24: # background transparent
					depth = 0
					if wasDib:
						depth = ord(data[14])
					if depth == 1:
						if qGray(img.color(0)) >= qGray(img.color(1)):
							# qt's bmp decoder deliberately sabotages the image in this case!
							# see the swapPixel01 call in qbmphandler.cpp
							colorkey = 0
						else:
							colorkey = 1
					elif depth == 4:
						colorkey = 15
					else:
						colorkey = 255
					if not wasDib:
						depth = 8
						colorkey = 0
					mask = QImage(img.size(), QImage.Format_Mono)
					for x in range(img.size().width()):
						for y in range(img.size().height()):
							if img.pixelIndex(x, y) == colorkey:
								mask.setPixel(x, y, 1)
							else:
								mask.setPixel(x, y, 0)
				if mask:
					bitmask = QBitmap.fromImage(mask)
					pixmap.setMask(bitmask)
				offx = info.x - castinfo.regX
				offy = info.y - castinfo.regY
				if castinfo:
					offx = offx + castinfo.initialRect.left
					offy = offy + castinfo.initialRect.top
				painter.drawPixmap(offx, offy, pixmap)
		if self.movie.currChannel != None and self.movie.currChannel > 0:
			info = self.movie.frames[self.movie.currFrame].sprites[self.movie.currChannel]
			pen = QPen("black")
			pen.setStyle(Qt.PenStyle.DashDotLine)
			painter.setPen(pen)
			painter.setBackgroundMode(Qt.OpaqueMode)
			castinfo = self.movie.cast[info.castId]
			offx = info.x
			offy = info.y
			if castinfo.castType == castBitmap:
				offx = offx + castinfo.initialRect.left - castinfo.regX
				offy = offy + castinfo.initialRect.top - castinfo.regY
			painter.drawRect(offx, offy, info.width, info.height)

		return True

