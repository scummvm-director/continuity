import sys
from PySide.QtCore import *
from PySide.QtGui import *
import timeline
import preview
import parser
from movie import *

class TimelineArea(QScrollArea):
	def __init__(self, parent):
		QScrollArea.__init__(self, parent)

	def keyPressEvent(self, ev):
		if ev.key() == Qt.Key_Space:
			# TODO: bounds checking
			movie.currFrame = movie.currFrame + 1
			self.parent().parent().selectionChanged.emit()
		return QScrollArea.keyPressEvent(self, ev)

class MyMainWindow(QMainWindow):
	selectionChanged = Signal()
	def __init__(self):
		QMainWindow.__init__(self, None)
		self.selectionChanged.connect(self.updateTable)
		vsplitter = QSplitter(self)
		vsplitter.setOrientation(Qt.Vertical)
		mytimelinearea = TimelineArea(vsplitter)
		mytimelinearea.setWidget(timeline.Timeline(mytimelinearea, movie))
		hsplitter = QSplitter(vsplitter)
		mypreviewarea = QScrollArea(hsplitter)
		mypreviewarea.setWidget(preview.Preview(mypreviewarea, movie))
		self.info = QTreeWidget(hsplitter)
		self.info.setColumnCount(2)
		self.info.setHeaderLabels(["Name", "Value"])
		vsplitter.addWidget(mytimelinearea)
		vsplitter.addWidget(hsplitter)
		hsplitter.addWidget(self.info)
		hsplitter.addWidget(mypreviewarea)
		self.setCentralWidget(vsplitter)
		self.updateTable()

	def updateTable(self):
		while self.info.takeTopLevelItem(0):
			pass
		if movie.currFrame == -1:
			item = QTreeWidgetItem(["Movie", ""])
			item.addChild(QTreeWidgetItem(["Created By", movie.createdBy]))
			item.addChild(QTreeWidgetItem(["Changed By", movie.changedBy]))
			scItem = QTreeWidgetItem(["Script", movie.script])
			scItem.setToolTip(1, "<p>"+movie.script.replace("\r", "<br>").replace(" ", "&nbsp;"))
			item.addChild(scItem)
			whenLoadCastNames = {0:"When Needed", 1:"After Frame One", 2:"Before Frame One"}
			item.addChild(QTreeWidgetItem(["Load Cast", whenLoadCastNames[movie.whenLoadCast]]))
			flags = []
			if movie.flags & 0x20:
				flags.append("don't AA")
			if movie.flags & 0x40:
				flags.append("remap palettes")
			item.addChild(QTreeWidgetItem(["Flags", ", ".join(flags)]))
			self.info.addTopLevelItem(item)
			self.info.expandItem(item)

			self.info.resizeColumnToContents(0)
			return
		item = QTreeWidgetItem(["Selection", ""])
		item.addChild(QTreeWidgetItem(["Frame", str(movie.currFrame + 1)]))
		frame = movie.frames[movie.currFrame]
		if movie.currChannel != None:
			info = frame.sprites[movie.currChannel]
			item.addChild(QTreeWidgetItem(["Channel", str(movie.currChannel)]))
		self.info.addTopLevelItem(item)
		self.info.expandItem(item)
		item = None
		if movie.currChannel > 0:
			item = QTreeWidgetItem(["Cast Member", ""])
			item.addChild(QTreeWidgetItem(["Cast ID", str(info.castId)]))
			castType = movie.cast[info.castId].castType
			castTypeNames = {1:"Bitmap",2:"FilmLoop",3:"Text",4:"Palette",5:"Picture",6:"Sound",7:"Button",8:"Shape",9:"Movie",10:"DigitalVideo",11:"Script"}
			if castType in castTypeNames:
				typeName = castTypeNames[castType]
			else:
				typeName = "<unknown> (%02x)" % castType
			item.addChild(QTreeWidgetItem(["Cast Type", typeName]))
			myId = info.castId + 1024
			if myId in movie.castInfo:
				item.addChild(QTreeWidgetItem(["Name", movie.castInfo[myId].name]))
				scItem = QTreeWidgetItem(["Script", movie.castInfo[myId].script])
				scItem.setToolTip(1, "<p>"+movie.castInfo[myId].script.replace("\r", "<br>").replace(" ", "&nbsp;"))
				item.addChild(scItem)
				item.addChild(QTreeWidgetItem(["Filename", movie.castInfo[myId].extFilename]))
				item.addChild(QTreeWidgetItem(["Directory", movie.castInfo[myId].extDirectory]))
				item.addChild(QTreeWidgetItem(["Resource Type", movie.castInfo[myId].extType]))
		elif movie.currChannel == tempoChannel:
			item = QTreeWidgetItem(["Tempo", ""])
			if frame.tempo <= 60:
				item.addChild(QTreeWidgetItem(["Set FPS", str(frame.tempo)]))
			elif frame.tempo >= 161:
				item.addChild(QTreeWidgetItem(["Delay", str(256 - frame.tempo)]))
			elif frame.tempo >= 136:
				item.addChild(QTreeWidgetItem(["Wait For", "Channel " + str(frame.tempo - 136)]))
			elif frame.tempo == 128:
				item.addChild(QTreeWidgetItem(["Wait For", "Click/Key"]))
			elif frame.tempo == 135:
				item.addChild(QTreeWidgetItem(["Wait For", "Sound Channel 1"]))
			elif frame.tempo == 134:
				item.addChild(QTreeWidgetItem(["Wait For", "Sound Channel 2"]))
			else:
				item.addChild(QTreeWidgetItem(["Unknown", str(frame.tempo)]))
		elif movie.currChannel == scriptChannel:
			item = QTreeWidgetItem(["Frame Action", ""])
			text = movie.actions[frame.actionId].script
			scItem = QTreeWidgetItem(["Script", text])
			scItem.setToolTip(1, "<p>"+text.replace("\r", "<br>").replace(" ", "&nbsp;"))
			item.addChild(scItem)
		elif movie.currChannel == transitionChannel:
			item = QTreeWidgetItem(["Transition", ""])
			# from puppetTransition docs
			transTypes = {
				1:"wipe right",
				2:"wipe left",
				3:"wipe down",
				4:"wipe up",
				5:"center out, horizontal",
				6:"edges in, horizontal",
				7:"center out, vertical",
				8:"edges in, vertical",
				9:"center out, square",
				10:"edges in, square",
				11:"push left",
				12:"push right",
				13:"push down",
				14:"push up",
				15:"reveal up",
				16:"reveal up, right",
				17:"reveal right",
				18:"reveal down",
				19:"reveal down, right",
				20:"reveal down, left",
				21:"reveal left",
				22:"reveal up, left",
				23:"dissolve, pixels fast",
				24:"dissolve, boxy rects",
				25:"dissolve, boxy squares",
				26:"dissolve, patterns",
				27:"random rows",
				28:"random columns",
				29:"cover down",
				30:"cover down, left",
				31:"cover down, right",
				32:"cover left",
				33:"cover right",
				34:"cover up",
				35:"cover up, left",
				36:"cover up, right",
				37:"venetian blinds",
				38:"checkerboard",
				39:"strips on bottom, build left",
				40:"strips on bittom, build right",
				41:"strips on left, build down",
				42:"strips on left, build up",
				43:"strips on right, build down",
				44:"strips on right, build up",
				45:"strips on top, build left",
				46:"strips on top, build right",
				47:"zoom open",
				48:"zoom close",
				49:"vertical binds",
				50:"dissolve, bits fast",
				51:"dissolve, pixels",
				52:"dissolve, bits"
			}
			item.addChild(QTreeWidgetItem(["Type", transTypes[frame.transType]]))
			item.addChild(QTreeWidgetItem(["Duration", str(frame.transFlags & 0x7f)]))
			item.addChild(QTreeWidgetItem(["Chunk Size", str(frame.transChunkSize)]))
			if frame.transFlags & 0x80:
				item.addChild(QTreeWidgetItem(["Area", "Whole Stage"]))
			else:
				item.addChild(QTreeWidgetItem(["Area", "Changing Area"]))
		elif movie.currChannel == paletteChannel:
			item = QTreeWidgetItem(["Palette", ""])
			item.addChild(QTreeWidgetItem(["Palette ID", str(frame.palette)]))
			item.addChild(QTreeWidgetItem(["First Color", str((frame.paletteFirstColor - 0x80) % 256)]))
			item.addChild(QTreeWidgetItem(["Last Color", str((frame.paletteLastColor - 0x80) % 256)]))
			item.addChild(QTreeWidgetItem(["Speed", str(frame.paletteSpeed)]))
			item.addChild(QTreeWidgetItem(["# Frames", str(frame.paletteFrameCount)]))
			item.addChild(QTreeWidgetItem(["# Cycles", str(frame.paletteCycleCount)]))
			flags = []
			if frame.paletteFlags & 0x60 == 0x60:
				flags.append("fade->white")
			elif frame.paletteFlags & 0x60 == 0x40:
				flags.append("fade->black")
			if frame.paletteFlags & 0x4:
				flags.append("over time")
			if frame.paletteFlags & 0x80:
				flags.append("cycle")
			item.addChild(QTreeWidgetItem(["Flags", ", ".join(flags)]))
		if item:
			self.info.addTopLevelItem(item)
			self.info.expandItem(item)
		if movie.currChannel > 0:
			item = QTreeWidgetItem(["Sprite", ""])
			if info.height:
				item.addChild(QTreeWidgetItem(["Position", "%d, %d" % (info.x, info.y)]))
				item.addChild(QTreeWidgetItem(["Size", "%d, %d" % (info.width, info.height)]))
				inktypes = {0:"copy",1:"transparent",2:"reverse",3:"ghost",4:"not copy",5:"not trans",6:"not reverse",7:"not ghost",8:"matte",9:"mask",0x24:"backgnd trans",0x20:"blend",0x27:"dark",0x25:"light",0x22:"add",0x21:"add pin",0x26:"sub",0x23:"sub pin"}
				inktype = info.flags & 0x3f # TODO: correct?
				if inktype in inktypes.keys():
					ink = inktypes[inktype]
				else:
					ink = "<unknown (%02x)>" % inktype
				item.addChild(QTreeWidgetItem(["Ink", ink]))
				trails = "No"
				if info.flags & 0x40:
					trails = "Yes"
				item.addChild(QTreeWidgetItem(["Trails", trails]))
				antialias = "Off"
				if info.flags & 0x2000:
					antialias = "Low"
				elif info.flags & 0x4000:
					antialias = "Mid"
				if info.flags & 0x6000 == 0x6000:
					antialias = "High"
				item.addChild(QTreeWidgetItem(["Antialias", antialias]))
			self.info.addTopLevelItem(item)
			self.info.expandItem(item)

		self.info.resizeColumnToContents(0)

app = QApplication([])
movie = parser.parseFile(sys.argv[1])
win = MyMainWindow()
win.resize(1024, 768)
win.show()
app.exec_()
