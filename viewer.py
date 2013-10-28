import sys
from PySide.QtCore import *
from PySide.QtGui import *
import timeline
import preview
import parser

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

	def updateTable(self):
		while self.info.takeTopLevelItem(0):
			pass
		if movie.currFrame == -1:
			return
		item = QTreeWidgetItem(["Selection", ""])
		item.addChild(QTreeWidgetItem(["Frame", str(movie.currFrame)]))
		if movie.currChannel != -1:
			info = movie.frames[movie.currFrame].cast[movie.currChannel]
			item.addChild(QTreeWidgetItem(["Channel", str(movie.currChannel)]))
		self.info.addTopLevelItem(item)
		self.info.expandItem(item)
		if movie.currChannel != -1:
			item = QTreeWidgetItem(["Cast Member", ""])
			item.addChild(QTreeWidgetItem(["Cast ID", str(info.castId)]))
			myId = info.castId + 1024
			if myId in movie.cast:
				item.addChild(QTreeWidgetItem(["Name", movie.cast[myId].name]))
				scItem = QTreeWidgetItem(["Script", movie.cast[myId].script])
				scItem.setToolTip(1, movie.cast[myId].script.replace("\r", "<br>").replace(" ", "&nbsp;"))
				item.addChild(scItem)
				item.addChild(QTreeWidgetItem(["Filename", movie.cast[myId].extFilename]))
				item.addChild(QTreeWidgetItem(["Directory", movie.cast[myId].extDirectory]))
				item.addChild(QTreeWidgetItem(["Resource Type", movie.cast[myId].extType]))
		self.info.addTopLevelItem(item)
		self.info.expandItem(item)
		if movie.currChannel != -1:
			item = QTreeWidgetItem(["Sprite", ""])
			if info.height:
				item.addChild(QTreeWidgetItem(["Position", "%d, %d" % (info.x, info.y)]))
				item.addChild(QTreeWidgetItem(["Size", "%d, %d" % (info.width, info.height)]))
				pentypes = {0:"copy",1:"transparent",2:"reverse",3:"ghost",4:"not copy",5:"not trans",6:"not reverse",7:"not ghost",8:"matte",9:"mask",0x24:"backgnd trans",0x20:"blend",0x27:"dark",0x25:"light",0x22:"add",0x21:"add pin",0x26:"sub",0x23:"sub pin"}
				pentype = info.flags & 0x3f # TODO: correct?
				if pentype in pentypes.keys():
					pen = pentypes[pentype]
				else:
					pen = "<unknown (%02x)>" % pentype
				item.addChild(QTreeWidgetItem(["Pen", pen]))
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
