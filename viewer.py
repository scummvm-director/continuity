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
			item.addChild(QTreeWidgetItem(["Tempo", str(frame.tempo)]))
		elif movie.currChannel == scriptChannel:
			item = QTreeWidgetItem(["Frame Action", ""])
			text = movie.actions[frame.actionId].script
			scItem = QTreeWidgetItem(["Script", text])
			scItem.setToolTip(1, "<p>"+text.replace("\r", "<br>").replace(" ", "&nbsp;"))
			item.addChild(scItem)
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
