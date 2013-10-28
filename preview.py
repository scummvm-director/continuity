from PySide.QtCore import *
from PySide.QtGui import *
from dutils import *

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

		for i in range(len(self.movie.frames[self.movie.currFrame].cast)):
			info = self.movie.frames[self.movie.currFrame].cast[i]
			if not info.enabled:
				continue
			myId = 1024 + info.castId
			mystr = str(info.castId)
			if myId in self.movie.dibs:
				dib = self.movie.dibs[myId]
				dib.seek(0)
				data = dib.read()
				depth = ord(data[14])
				if depth == 1:
					colorkey = 1
				elif depth == 4:
					colorkey = 15
				else:
					colorkey = 255
				imgdata = imageFromDIB(data, self.movie.currFrame, self.movie)
				img = QImage.fromData(imgdata, "bmp")
				mask = QImage(img.size(), QImage.Format_Mono)
				for x in range(img.size().width()):
					for y in range(img.size().height()):
						if img.pixelIndex(x, y) == colorkey:
							mask.setPixel(x, y, 1)
						else:
							mask.setPixel(x, y, 0)
				pixmap = QPixmap.fromImage(img)
				bitmask = QBitmap.fromImage(mask)
				pixmap.setMask(bitmask)
				offx = info.width - img.size().width()
				offy = info.height - img.size().height()
				painter.drawPixmap(info.x - info.width/2 + offx/2, info.y - info.height/2 + offy/2, pixmap)
		info = self.movie.frames[self.movie.currFrame].cast[self.movie.currChannel]
		pen = QPen("black")
		pen.setStyle(Qt.PenStyle.DashDotLine)
		painter.setPen(pen)
		painter.drawRect(info.x - info.width/2, info.y - info.height/2, info.width, info.height)

		return True

