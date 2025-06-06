#!/usr/bin/python
import os
import sys
import time
import math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtOpenGL import *
from OpenGL.GL import *
from OpenGL.GLU import *

iioPath = "/sys/bus/iio/devices"
devices = []

def setup():
	for i in range(0, 6):
		device = os.popen(f'cat {iioPath}/iio:device{i}/name {iioPath}/iio:device{i}/label | tr "\\n" " "').read()
		devices.append(device [0:-1])

vertices = ( #cube definition
   	(1, -1, -1),
   	(1, 1, -1),
   	(-1, 1, -1),
   	(-1, -1, -1),
   	(1, -1, 1),
   	(1, 1, 1),
   	(-1, -1, 1),
   	(-1, 1, 1)
)
edges = (
   	(0,1),
   	(0,3),
   	(0,4),
   	(2,1),
   	(2,3),
   	(2,7),
   	(6,3),
   	(6,4),
   	(6,7),
   	(5,1),
   	(5,4),
   	(5,7)
) #/cube definition

def Cube(): # render cube
	glBegin(GL_LINES)
	for edge in edges:
		for vertex in edge:
			glVertex3fv(vertices[vertex])
	glEnd()

def Accel(): # render accelerometer reading
	glBegin(GL_LINES)

	glVertex3fv((0,0,0))
	glVertex3fv((0,-1,0))

	glEnd()


def readSensorValue(file):
	file.seek(0)
	return int(file.read())

def readGyro():
	global baseGyroXNow
	global baseGyroYNow
	global baseGyroZNow

	global Xrotation
	global Yrotation
	global Zrotation

	baseGyroXNow = readSensorValue(baseGyroX)/670 - baseGyroXCalib
	baseGyroYNow = readSensorValue(baseGyroY)/670 - baseGyroYCalib
	baseGyroZNow = readSensorValue(baseGyroZ)/670 - baseGyroZCalib

	Xtemp = Xrotation
	Ytemp = Yrotation
	Ztemp = Zrotation

	if abs(baseGyroZNow) >= 0.05:
		Zrotation += baseGyroZNow * math.cos(math.radians(Ytemp)) * math.cos(math.radians(Xtemp))
		Xrotation += baseGyroZNow * math.sin(math.radians(Ytemp))
		#X
	if abs(baseGyroXNow) >= 0.05:
		Xrotation += baseGyroXNow * math.cos(math.radians(Ztemp)) * math.cos(math.radians(Ytemp))
		Yrotation += baseGyroXNow * math.sin(math.radians(Ztemp))
		Zrotation += baseGyroXNow * math.sin(math.radians(Ytemp))
	if abs(baseGyroYNow) >= 0.05:
		Yrotation += baseGyroYNow * math.cos(math.radians(Ztemp)) * math.cos(math.radians(Xtemp))
		Xrotation -= baseGyroYNow * math.sin(math.radians(Ztemp))
		#X

	

def main():
	global cubeAngleX
	global cubeAngleY
	global cubeAngleZ
	readGyro()
	angleText.setText(str(-Xrotation))
	angleWidget.lidAngle = readSensorValue(angl)
	angleWidget.baseAngle = Xrotation
	angleWidget.update()
	glWidget.updateGL()
	
def calibrateBaseGyro():
	global baseGyroXCalib
	global Xrotation
	global baseGyroYCalib
	global Yrotation
	global baseGyroZCalib
	global Zrotation
	baseGyroXCalib = (readSensorValue(baseGyroX)/670)
	Xrotation = 0
	baseGyroYCalib = (readSensorValue(baseGyroY)/670)
	Yrotation = 0
	baseGyroZCalib = (readSensorValue(baseGyroZ)/670)
	Zrotation = 0

def log():
	print("Hello, World!")

class GLWidget(QGLWidget):
	def __init__(self, parent=None):
		self.parent = parent
		super().__init__(self.parent)
		QGLWidget.__init__(self, parent)
		self.setMinimumSize(200, 200)

	def initializeGL(self):
		self.qglClearColor(QColor(0, 0, 0, 0))			# blank the screen
		glEnable(GL_DEPTH_TEST)							# enable depth testing

	def resizeGL(self, width, height):
		glViewport(0, 0, width, height)
		glMatrixMode(GL_PROJECTION)
		self.aspect = width / float(height)

	def paintGL(self):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluPerspective(45 * (self.aspect > 1) + (self.aspect <= 1) * (360 * math.atan(1/(2.5*self.aspect))/math.pi), self.aspect, 0.1, 50.0)
		# arguments to above function are as follows: 
		# - trigonometry to determine FOV to keep scene visible in aspect ratios which are taller than they are wide
		# - aspect ratio to render at to avoid the scene being warped
		# - minimum view distance
		# - maximum view distance
		glTranslatef(0.0,0.0, -5)
		glRotatef(-Xrotation, -1, 0, 0)
		glRotatef(-Yrotation, 0, 0, 1)
		glRotatef(-Zrotation, 0, -1, 0)
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
		Cube()
		glRotatef(Zrotation, 0, -1, 0)
		glRotatef(Yrotation, 0, 0, 1)
		glRotatef(Xrotation, -1, 0, 0)
		
		
		Accel()


class angleDisplay(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.lidAngle = 0
		self.baseAngle = 0
		self.setMinimumSize(200, 200)
		self.line_length = 0
	
	def paintEvent(self, event):
		self.line_length = min(self.height(), self.width())/3

		painter = QPainter(self)
		
		pen = QPen(Qt.black, 2, Qt.SolidLine)
		painter.setPen(pen)

		lidAngle_display = math.radians(self.lidAngle - self.baseAngle)
		baseAngle_display = math.radians(-self.baseAngle)
		center_point = QPointF(self.width() / 2, self.height() / 2)
		lid_endpoint = QPointF(
			center_point.x() + self.line_length * -math.cos(lidAngle_display),
			center_point.y() - self.line_length * math.sin(lidAngle_display),
		)
		base_endpoint = QPointF(
			center_point.x() + self.line_length * -math.cos(baseAngle_display),
			center_point.y() - self.line_length * math.sin(baseAngle_display),
		)
		if self.lidAngle <= 360:
			painter.drawLine(center_point, lid_endpoint)
		painter.drawLine(center_point, base_endpoint)



setup()
anglID = devices.index("cros-ec-lid-angle")
angl = open(f'{iioPath}/iio:device{anglID}/in_angl_raw', 'r')
baseGyroID = devices.index("cros-ec-gyro accel-base")
baseGyroX = open(f'{iioPath}/iio:device{baseGyroID}/in_anglvel_x_raw', 'r')
baseGyroY = open(f'{iioPath}/iio:device{baseGyroID}/in_anglvel_y_raw', 'r')
baseGyroZ = open(f'{iioPath}/iio:device{baseGyroID}/in_anglvel_z_raw', 'r')
Xrotation = 0
Yrotation = 0
Zrotation = 0
calibrateBaseGyro()
app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout()
angleDisp = QVBoxLayout()
angleDisp2 = QHBoxLayout()
angleText = QLabel("")
angleText.setMaximumHeight(20)
angleWidget = angleDisplay()
calibButton = QPushButton('Calibrate')
angleDisp.addWidget(angleText)
angleDisp2.addWidget(angleWidget)
glWidget = GLWidget()
angleDisp2.addWidget(glWidget)
angleDisp.addLayout(angleDisp2)
angleDisp.addWidget(calibButton)
layout.addLayout(angleDisp)
button = QPushButton('Test Button')
layout.addWidget(button)
updateTimer = QTimer()
updateTimer.setInterval(50)
updateTimer.setSingleShot(False)
updateTimer.timeout.connect(main)
updateTimer.start()
button.clicked.connect(log)
calibButton.clicked.connect(calibrateBaseGyro)
window.setLayout(layout)
window.setWindowTitle("Sensor GUI")
window.show()
app.exec()

