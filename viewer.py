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
				item.addChild(QTreeWidgetItem(["Cast Name", str(movie.cast[myId].name)]))
			if info.height:
				item.addChild(QTreeWidgetItem(["Position", "%d, %d" % (info.x, info.y)]))
				item.addChild(QTreeWidgetItem(["Size", "%d, %d" % (info.width, info.height)]))
		self.info.addTopLevelItem(item)
		self.info.expandItem(item)

		self.info.resizeColumnToContents(0)

app = QApplication([])
movie = parser.parseFile(sys.argv[1])
win = MyMainWindow()
win.resize(1024, 768)
win.show()
app.exec_()
