import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

GRID_SIZE = 30

camState = 0
target = [0., 0., 0. ]
camAng = [0., 9.]
camDis = 10

upVector = [0, 1, 0]
prevPos = [0., 0.]
speedAng = [0.1, 0.1]
speedZoom = 0.5
speedPan = 0.001

count = 0

# draw a sphere of radius 1, centered at the origin. 
# numLats: number of latitude segments 
# numLongs: number of longitude segments
def drawSphere(numLats=12, numLongs=12):
	for i in range(0, numLats + 1):
		lat0 = np.pi * (-0.5 + float(float(i - 1) / float(numLats)))
		z0 = np.sin(lat0)
		zr0 = np.cos(lat0)
		
		lat1 = np.pi * (-0.5 + float(float(i) / float(numLats)))
		z1 = np.sin(lat1)
		zr1 = np.cos(lat1)
		# Use Quad strips to draw the sphere
		glBegin(GL_QUAD_STRIP)
	
		for j in range(0, numLongs + 1):
			lng = 2 * np.pi * float(float(j - 1) / float(numLongs))
			x = np.cos(lng)
			y = np.sin(lng)
			glVertex3f(x * zr0, y * zr0, z0)
			glVertex3f(x * zr1, y * zr1, z1)
		glEnd()

def drawGrid():
	glLineWidth(1)
	glColor3ub(255, 255, 255)
	for x in range(-GRID_SIZE, GRID_SIZE):
		glBegin(GL_LINE_LOOP)
		glVertex3f(-GRID_SIZE, 0., x)
		glVertex3f( GRID_SIZE, 0., x)
		glEnd()

	for z in range(-GRID_SIZE, GRID_SIZE):
		glBegin(GL_LINE_LOOP)
		glVertex3f(z, 0., -GRID_SIZE)
		glVertex3f(z, 0.,  GRID_SIZE)
		glEnd()

def calculateEye():
	global camAng, camDis, target
	tmpEye = [  target[0] + camDis * np.cos(np.radians(camAng[1])) * np.cos(np.radians(camAng[0])), 
				target[1] + camDis * np.sin(np.radians(camAng[1])), 
				target[2] + camDis * np.cos(np.radians(camAng[1])) * np.sin(np.radians(camAng[0]))   ]
	return tmpEye

def mouse_callback(window, button, action, mods):
	global camState    
	# orbit
	# Rotate the camera around the target point by changing azimuth / elevation angles.
	if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
		camState = 1
	if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.RELEASE:
		camState = 0
	
	# panning
	# Move both the target point and camera in left, right, up and down direction of the camera
	if button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.PRESS:
		camState = 2
	if button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.RELEASE:
		camState = 0

def scroll_callback(window, xoffset, yoffset):
	global camDis
	# zooming
	camDis = camDis - yoffset * speedZoom
	if camDis < 1: 
		camDis = 1

def cursor_callback(window, xpos, ypos):
	global prevPos, camAng, camState, upY, target, camDis, upVector
	# orbit
	xDistance = xpos - prevPos[0]
	yDistance = ypos - prevPos[1]

	if camState == 1: 
		camAng[1] += speedAng[0] * yDistance
		speed = speedAng[0]
		if camAng[1] < 0:
			camAng[1] += 360
		if camAng[1] >= 360:
			camAng[1] -= 360
		if camAng[1] >= 90 and camAng[1] < 270:
			upVector[1] = -1
		else:
			upVector[1] = 1

		camAng[0] += speed * xDistance
	
	# panning
	if camState == 2:
		tmpEye = calculateEye()
		eye = np.array(tmpEye)
		at = np.array(target)
		up = np.array(upVector)

		w = (eye - at) / np.sqrt(np.dot(eye - at, eye - at))
		u = np.cross(up, w) / np.sqrt(np.dot(np.cross(up, w), np.cross(up, w)))
		v = np.cross(w, u)

		target += xDistance * -u * speedPan * camDis
		target += yDistance *  v * speedPan * camDis

	prevPos[0] = xpos
	prevPos[1] = ypos

def render():
	global camAng, camDis, tmpEye, target, upVector

	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	glEnable(GL_DEPTH_TEST)
	glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()

	# projection transformation
	gluPerspective(60, 1, 1, 1000)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()
	
	# viewing transformation
	tmpEye = calculateEye()
	gluLookAt(  tmpEye[0], tmpEye[1], tmpEye[2],
				target[0], target[1], target[2],
				upVector[0], upVector[1], upVector[2])

	drawGrid()
	drawHands()

def makeHands(idx):
	# 각 손가락들의 위치 나타냄
	if idx == 1:
		xCur = -0.5
		yCur = -0.13
	elif idx == 2:
		xCur = -0.22
		yCur = 0
	elif idx == 3:
		xCur = 0.05
		yCur = 0
	elif idx == 4:
		xCur = 0.34
		yCur = -0.05

	glPushMatrix()
	glTranslatef(xCur, yCur, 0)
	glPushMatrix()
	glRotatef((np.sin(np.radians(count)) + 1) * 45, 1, 0, 0)
	glTranslatef(.08, 0, 0)

	# 관절 표현
	glPushMatrix()
	glScalef(.06, .06, .06)
	glColor3ub(255, 0, 255)
	drawSphere()
	glPopMatrix()

	glPushMatrix()
	glTranslatef(0, .3, 0)
	glScalef(.05, .15, .1)
	drawSphere()
	glPopMatrix()

	glPushMatrix()
	glTranslatef(0, .55, 0)
	glScalef(.06, .06, .06)
	drawSphere()
	glPopMatrix()

	glPushMatrix()
	glTranslatef(0, .5, 0)
	glRotatef((np.sin(np.radians(count + 10)) + 1) * 45, 1, 0, 0)

	glPushMatrix()
	glTranslatef(0, .2, 0)
	glScalef(.05, .15, .1)
	drawSphere()
	glPopMatrix()

	glPushMatrix()
	glTranslatef(0, .6, 0)
	glScalef(.05, .15, .1)
	drawSphere()
	glPopMatrix()

	glPushMatrix()
	glTranslatef(0, .45, 0)
	glRotatef((np.sin(np.radians(count + 20)) + 1) * 45, 1, 0, 0)
	glPushMatrix()
	glScalef(.06, .06, .06)
	drawSphere()
	glPopMatrix()
	glPopMatrix()

	glPopMatrix()
	glPopMatrix()
	glPopMatrix()

def drawHands():
	global count
	glPushMatrix()

	glTranslatef(0, -.5, 0)
	glScalef(.5, .5, .2)
	glColor3ub(255, 0, 255)
	drawSphere()
	glPopMatrix()

	# 손가락
	glPushMatrix()

	glPushMatrix()
	glTranslatef(-.45, -.45, 0.3)
	glScalef(.06, .06, .06)
	drawSphere()
	glPopMatrix()

	glPushMatrix()
	glTranslatef(-.5, -.5, 0.1)
	glRotatef((np.sin(np.radians(count)) + 1) * 45, 0, 1, 0)

	glPushMatrix()

	glPushMatrix()
	glTranslatef(-.2, 0, 0)
	glScalef(.2, .10, .1)
	drawSphere()
	glPopMatrix()

	glPushMatrix()
	glTranslatef(-.5, 0, 0)
	glScalef(.06, .06, .06)
	drawSphere()
	glPopMatrix()

	glPushMatrix()
	glTranslatef(-.6, 0, 0)
	glRotatef((np.sin(np.radians(count + 20)) + 1) * 45, 0, 1, 0)
	glPushMatrix()
	glTranslatef(-.2, 0, 0)
	glScalef(.2, .12, .1)
	drawSphere()
	glPopMatrix()
	glPopMatrix()

	glPopMatrix()
	glPopMatrix()
	glPopMatrix()

	for i in range(4):
		makeHands(i + 1)

def main():
	global count
	if not glfw.init():
		return
	window = glfw.create_window(640,640,"assignment1-2015004402", None,None)
	if not window:
		glfw.terminate()
		return
	glfw.make_context_current(window)
	glfw.set_mouse_button_callback(window, mouse_callback)
	glfw.set_cursor_pos_callback(window, cursor_callback)
	glfw.set_scroll_callback(window, scroll_callback)
	glfw.swap_interval(1)
	
	while not glfw.window_should_close(window):
		count += 2
		glfw.poll_events()
		render()
		glfw.swap_buffers(window)

	glfw.terminate()

if __name__ == "__main__":
	main()