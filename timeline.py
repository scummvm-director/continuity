from PySide.QtCore import *
from PySide.QtGui import *
from dutils import *

gridSizeX = 25
gridSizeY = 25
oldX = -1
oldY = -1

class Timeline(QWidget):
	def __init__(self, parent, movie):
		QWidget.__init__(self, parent)
		self.setAutoFillBackground(True)
		self.setMouseTracking(True)
		self.movie = movie
		self.movie.currFrame = -1
		self.movie.currChannel = -1
		self.resize((len(self.movie.frames) + 1) * gridSizeX + 2, (2 + 3 + 24) * gridSizeY + 2) # +2 to make edges visible
		self.parent().parent().parent().selectionChanged.connect(self.selectionChanged)

	def selectionChanged(self):
		if self.movie.currFrame != -1 and self.movie.currChannel == -1:
			self.parent().parent().ensureVisible((self.movie.currFrame + 1) * gridSizeX, gridSizeY, 150, 50)
		self.update()

        def event(self, ev):
                if ev.type() != QEvent.ToolTip:
                        return QWidget.event(self, ev)
		ev.ignore()
		return True

	def mousePressEvent(self, ev):
		valid = True
		chanValid = True
		x = ev.x() - gridSizeX
		y = ev.y() - gridSizeY*2
		if x < 0:
			valid = False
		if y < 0:
			chanValid = False
			y = -1
		x = x / gridSizeX
		y = y / gridSizeY
		if (not valid) or x >= len(self.movie.frames) or (chanValid and y >= len(self.movie.frames[x].sprites)):
			valid = False
		info = None
		if chanValid:
			info = self.movie.frames[x].sprites[y]
		if (not valid) or (info and not info.enabled):
			self.movie.currFrame = -1
			self.movie.currChannel = -1
		else:
			self.movie.currFrame = x
			self.movie.currChannel = y
		self.parent().parent().parent().parent().selectionChanged.emit()
		self.update()
		return True

	def mouseMoveEvent(self, ev):
		x = ev.x() - gridSizeX
		y = ev.y() - gridSizeY*2
		if x < 0 or y < 0:
			oldX = -1
			QToolTip.hideText()
			return True
		x = x / gridSizeX
		y = y / gridSizeY
		global oldX, oldY
		if oldX == x and oldY == y:
			return True
		oldX = x
		oldY = y
		if x >= len(self.movie.frames) or y >= len(self.movie.frames[x].sprites):
			oldX = -1
			QToolTip.hideText()
			return True
		info = self.movie.frames[x].sprites[y]
		#QToolTip.hideText()
		if not info.enabled:
			QToolTip.hideText()
			return True
		myId = 1024 + info.castId
		mystr = str(info.castId)
		if myId in self.movie.castInfo:
			mystr = "%s (%s)" % (mystr, self.movie.castInfo[myId].name)
		if "BITD" in self.movie.resources:
			for p in self.movie.resources["BITD"]:
				if p.rid != myId:
					continue
				p.seek(0)
				# TODO
		if myId in self.movie.dibs:
			dib = self.movie.dibs[myId]
			dib.seek(0)
			data = dib.read()
			imgdata = imageFromDIB(data, x, self.movie)
			img = QImage.fromData(imgdata, "bmp")

			ba = QByteArray()
			buf = QBuffer(ba)
			buf.open(QIODevice.WriteOnly)
			img.save(buf, "PNG")
			mystr = mystr + "<img src=\"data:image/png;base64,%s\">" % buf.data().toBase64()
			mystr = mystr + str(img.size())
		if info.height:
			mystr = "%s<br>at (%d, %d), size (%d, %d)" % (mystr, info.x, info.y, info.width, info.height)
		QToolTip.showText(ev.globalPos(), mystr, self)
		return True

	def paintEvent(self, ev):
		painter = QPainter(self)

		myfont = QFont()
		myfont.setPointSize(6)
		painter.setFont(myfont)

		# labels
		for i in self.movie.labels:
			xpos = i.frame * gridSizeX + gridSizeX/2
			# triangle
			painter.drawLine(xpos, gridSizeY - 5, xpos - 3, 13)
			painter.drawLine(xpos, gridSizeY - 5, xpos + 3, 13)
			painter.drawLine(xpos - 3, 13, xpos + 3, 13)
			# text
			painter.drawText(xpos+10, gridSizeY - 5, i.text)

		# ruler
		painter.setPen(QPen("gray"))
		for n in range(4, len(self.movie.frames), 5):
			xpos = (n+1) * gridSizeX + gridSizeX/2
			painter.drawText(xpos-gridSizeX, gridSizeY+2, gridSizeX*2, gridSizeY, Qt.AlignHCenter, str(n + 1))
		for n in range(len(self.movie.frames)):
			xpos = (n+1) * gridSizeX + gridSizeX/2
			if self.movie.currFrame == n and self.movie.currChannel == -1:
				painter.setPen(QPen("red"))
			if n % 5 == 4:
				painter.drawLine(xpos, gridSizeY + 17, xpos, gridSizeY*2)
			else:
				painter.drawLine(xpos, gridSizeY + 20, xpos, gridSizeY*2)
			if self.movie.currFrame == n and self.movie.currChannel == -1:
				painter.setPen(QPen("gray"))

		for n in range(24):
			ypos = gridSizeY * (2 + n)
			painter.drawText(0, ypos, gridSizeX, gridSizeY, Qt.AlignVCenter | Qt.AlignRight, str(n + 1))
		painter.drawText(0, gridSizeY * (2 + 24), gridSizeX, gridSizeY, 0x82, "pal")
		painter.drawText(0, gridSizeY * (3 + 24), gridSizeX, gridSizeY, 0x82, "snd1")
		painter.drawText(0, gridSizeY * (4 + 24), gridSizeX, gridSizeY, 0x82, "snd2")

		# grid
		painter.setPen(QPen("darkGray"))
		rect = self.rect()
		if rect.left() < gridSizeX:
			rect.setLeft(gridSizeX)
		if rect.top() < gridSizeY * 2: # notes, ruler
			rect.setTop(gridSizeY * 2)
		left = int(rect.left()) - (int(rect.left()) % gridSizeX)
		top = int(rect.top()) - (int(rect.top()) % gridSizeY)
		lines = []
		for x in range(left, int(rect.right()), gridSizeX):
			lines.append(QLineF(x, rect.top(), x, rect.bottom()))
		for y in range(top, int(rect.bottom()), gridSizeY):
			lines.append(QLineF(rect.left(), y, rect.right(), y))
		painter.drawLines(lines)

		# stupid hack
		for x in range(len(self.movie.frames)):
			xpos = (x+1) * gridSizeX
			frame = self.movie.frames[x]
			for y in range(len(frame.sprites)):
				entry = frame.sprites[y]
				if not entry.enabled:
					continue
				ypos = (y + 2) * gridSizeY
				if self.movie.currFrame == x and self.movie.currChannel == y:
					painter.setBrush(QBrush("red", Qt.SolidPattern))
				elif self.movie.currFrame == x:
					painter.setBrush(QBrush("pink", Qt.SolidPattern))
				else:
					painter.setBrush(QBrush("darkGray", Qt.SolidPattern))
				painter.setPen(QPen("darkGray"))
				painter.drawRect(xpos, ypos, gridSizeX, gridSizeY)
				painter.setPen(QPen("gray"))
				painter.drawLine(xpos, ypos, xpos+gridSizeX, ypos)
				painter.drawLine(xpos, ypos+gridSizeY, xpos+gridSizeX, ypos+gridSizeY)
		seenEntries = {}
		for x in range(len(self.movie.frames)):
			xpos = (x+1) * gridSizeX
			frame = self.movie.frames[x]
			for y in range(len(frame.sprites)):
				entry = frame.sprites[y]
				oldEntry = None
				if y in seenEntries:
					oldEntry = seenEntries[y]
				seenEntries[y] = entry.castId
				ypos = (y + 2) * gridSizeY
				if oldEntry and (not entry.enabled or entry.castId != oldEntry):
					# draw a line at the end of the OLD one
					painter.setPen(QPen("gray"))
					painter.drawLine(xpos, ypos, xpos, ypos+gridSizeY)
				if not entry.enabled:
					del seenEntries[y]
					continue
				if entry.castId != oldEntry:
					text = "(" + str(entry.castId) + ")"
					if ((1024 + entry.castId) in self.movie.castInfo) and len(text):
						text = self.movie.castInfo[1024 + entry.castId].name
					path = QPainterPath()
					painter.setPen(QPen("black"))
					painter.setBrush(QBrush("red", Qt.SolidPattern))
					painter.drawText(xpos, ypos + 18, text)
					painter.drawPath(path)

