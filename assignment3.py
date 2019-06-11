import numpy as np
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import *
import ctypes
import math

GRID_SIZE = 30

camState = 0
target = [0., 0., 0.]
camAng = [0., 9.]
camDist = 10
camHeight = 3.

upVector = [0, 1, 0]
prevPos = [0., 0.]
speedAng = [0.1, 0.1]
speedZoom = 0.5
speedPan = 0.001

isObj = 0
flag = False
GRID_SIZE = 30

vertexArray, normalArray, faceArray = [], [], []
varr, narr, iarr, nnarr = None, None, None, None

skeleton = None
count = 0

class Joint:
	def __init__(self):
		self.name = None
		self.channels = []
		self.offset = []
		self.parent = None
		self.frames = []
		self.children = []
		self.idx = [0, 0]
		self.rot_mat = np.identity(4)
		self.trans_mat = np.identity(4)
		self.strans_mat = np.identity(4)
		self.localtoworld = np.identity(4)
		self.trtr = np.identity(4)
		self.worldpos = np.array([0, 0, 0, 0])

	def update_frame(self, frame):
		pos = [0., 0., 0.]
		rot = [0., 0., 0.]

		rot_mat = np.identity(4)
		trans_mat = np.identity(4)

		for idx, channel in enumerate(self.channels):
			if channel == 'Xposition':
				pos[0] = self.frames[frame][idx]
				trans_mat[0, 3] = pos[0]
			elif channel == 'Yposition':
				pos[1] = self.frames[frame][idx]
				trans_mat[1, 3] = pos[1]
			elif channel == 'Zposition':
				pos[2] = self.frames[frame][idx]
				trans_mat[2, 3] = pos[2]
			elif channel == 'Xrotation':
				rot[0] = self.frames[frame][idx]
				cos = np.cos(np.radians(rot[0]))
				sin = np.sin(np.radians(rot[0]))
				rot_mat2 = np.identity(4)
				rot_mat2[1, 1] = cos
				rot_mat2[1, 2] = -sin
				rot_mat2[2, 1] = sin
				rot_mat2[2, 2] = cos
				rot_mat = np.dot(rot_mat, rot_mat2)
			elif channel == 'Yrotation':
				rot[0] = self.frames[frame][idx]
				cos = np.cos(np.radians(rot[0]))
				sin = np.sin(np.radians(rot[0]))
				rot_mat2 = np.identity(4)
				rot_mat2[0, 0] = cos
				rot_mat2[0, 2] = sin
				rot_mat2[2, 0] = -sin
				rot_mat2[2, 2] = cos
				rot_mat = np.dot(rot_mat, rot_mat2)
			elif channel == 'Zrotation':
				rot[0] = self.frames[frame][idx]
				cos = np.cos(np.radians(rot[0]))
				sin = np.sin(np.radians(rot[0]))
				rot_mat2 = np.identity(4)
				rot_mat2[0, 0] = cos
				rot_mat2[0, 1] = -sin
				rot_mat2[1, 0] = sin
				rot_mat2[1, 1] = cos
				rot_mat = np.dot(rot_mat, rot_mat2)

		self.rot_mat = rot_mat
		self.trans_mat = trans_mat
		if self.parent:
			self.localtoworld = np.dot(self.parent.trtr, self.strans_mat)
		else:
			self.localtoworld = np.dot(self.strans_mat, self.trans_mat)

		self.trtr = np.dot(self.localtoworld, self.rot_mat)

		self.worldpos = np.array([self.localtoworld[0, 3],
								  self.localtoworld[1, 3],
								  self.localtoworld[2, 3],
								  self.localtoworld[3, 3]])
		for child in self.children:
			child.update_frame(frame)

class bvhreader:
	def __init__(self, filename):
		self.filename = filename
		self.__root = None
		self.__stack = []
		self.channel_num = 0
		self.frame_time = 0.3
		self.frames = 0
		self.motions = []
		self.loadbvh(self.filename)

	@property
	def root(self):
		return self.__root

	def loadbvh(self, filename):
		f = open(filename)
		lines = f.readlines()
		parent = None
		current = None
		motion = False

		jointName = []

		for line in lines[1:len(lines)]:
			tokens = line.split()
			if len(tokens) == 0:
				continue
			if tokens[0] in ["ROOT", "JOINT", "End"]:
				if current is not None:
					parent = current

				current = Joint()
				current.name = tokens[1]
				jointName.append(current.name)

				current.parent = parent
				if len(self.__stack) == 0:
					self.__root = current

				if current.parent is not None:
					current.parent.children.append(current)

				self.__stack.append(current)

			elif "{" in tokens[0]:
				...
			elif "OFFSET" in tokens[0]:
				offset = []
				for i in range(1, len(tokens)):
					offset.append(float(tokens[i]))
				current.offset = offset
				current.strans_mat[0, 3] = offset[0]
				current.strans_mat[1, 3] = offset[1]
				current.strans_mat[2, 3] = offset[2]
			elif "CHANNELS" in tokens[0]:
				current.channels = tokens[2:len(tokens)]
				current.idx = [self.channel_num,
							   self.channel_num + len(current.channels)]
				self.channel_num += len(current.channels)

			elif "}" in tokens[0]:
				current = current.parent
				if current:
					parent = current.parent

			elif "MOTION" in tokens[0]:
				motion = True
			elif "Frames:" in tokens[0]:
				self.frames = int(tokens[1])
				print("2. Number of Frames : " + str(self.frames))
			elif "Frame" in tokens[0]:
				self.frame_time = float(tokens[2])
				print("3. FPS : " + str(1/self.frame_time))
			elif motion:
				data = [float(token) for token in tokens]
				self.get_channel_data(self.__root, data)
				vals = []
				for token in tokens:
					vals.append(float(token))
				self.motions.append(vals)
		print("4: Number of joints : " + str(len(jointName)))
		print("5. Joint names : ")
		for i in jointName:
			print(i + " ")

	def get_channel_data(self, joint, data):
		channels = len(joint.channels)
		joint.frames.append(data[0:channels])
		data = data[channels:]

		for child in joint.children:
			data = self.get_channel_data(child, data)
		return data

	def update_frame(self, frame):
		self.root.update_frame(frame)

# draw grid in XZ plane
def drawGrid():
	glLineWidth(1)
	glColor3ub(255, 255, 255)
	
	for x in range(-GRID_SIZE, GRID_SIZE):
		glBegin(GL_LINE_LOOP)
		glVertex3f(-GRID_SIZE, 0., x)
		glVertex3f(GRID_SIZE, 0., x)
		glEnd()

	for z in range(-GRID_SIZE, GRID_SIZE):
		glBegin(GL_LINE_LOOP)
		glVertex3f(z, 0., -GRID_SIZE)
		glVertex3f(z, 0.,  GRID_SIZE)
		glEnd()

def drawCube(p1, p2, width):
	
	glColor3f(0.9, 0.9, 0.0)
	
	pt = [[[None]] * 4, [None] * 4]
	p1 = np.array(p1)
	p2 = np.array(p2)
	v1 = p1 - p2
	v1 = v1 / (np.sqrt(np.dot(v1, v1)))
	up = np.array([0.0, 1, 0.0])
	if 1.0 - v1[1] < 0.001:
		up[2] += 0.1

	v2 = np.cross(v1, up)
	v2 = v2 / (np.sqrt(np.dot(v2, v2)))
	
	v3 = np.cross(v1, v2)
	v3 = v3 / (np.sqrt(np.dot(v3, v3)))

	v2 *= width
	v3 *= width

	pt[0][0] = p1 + v2
	pt[0][2] = p1 - v2
	pt[0][1] = p1 + v3
	pt[0][3] = p1 - v3

	pt[1][0] = p2 + v2
	pt[1][2] = p2 - v2
	pt[1][1] = p2 + v3
	pt[1][3] = p2 - v3

	glBegin(GL_QUADS)
	for i in range(2):

		glNormal3f(v1[0], v1[0], v1[0])
		for p in pt[i]:
			glVertex3f(p[0], p[1], p[2])
	
	n1 = v2 + v3
	n1 = n1 / (np.sqrt(np.dot(n1, n1)))

	n2 = v2 - v3
	n2 = n2 / (np.sqrt(np.dot(n2, n2)))	

	glNormal3f(n1[0], n1[1], n1[2])
	glVertex3f(pt[0][0][0], pt[0][0][1], pt[0][0][2])
	glVertex3f(pt[1][0][0], pt[1][0][1], pt[1][0][2])
	glVertex3f(pt[1][1][0], pt[1][1][1], pt[1][1][2])
	glVertex3f(pt[0][1][0], pt[0][1][1], pt[0][1][2])

	glNormal3f(n2[0], n2[1], n2[2])
	glVertex3f(pt[0][1][0], pt[0][1][1], pt[0][1][2])
	glVertex3f(pt[1][1][0], pt[1][1][1], pt[1][1][2])
	glVertex3f(pt[1][2][0], pt[1][2][1], pt[1][2][2])
	glVertex3f(pt[0][2][0], pt[0][2][1], pt[0][2][2])

	glNormal3f(-n1[0], -n1[1], -n1[2])
	glVertex3f(pt[0][2][0], pt[0][2][1], pt[0][2][2])
	glVertex3f(pt[1][2][0], pt[1][2][1], pt[1][2][2])
	glVertex3f(pt[1][3][0], pt[1][3][1], pt[1][3][2])
	glVertex3f(pt[0][3][0], pt[0][3][1], pt[0][3][2])

	glNormal3f(-n2[0], -n2[1], -n2[2])
	glVertex3f(pt[0][3][0], pt[0][3][1], pt[0][3][2])
	glVertex3f(pt[1][3][0], pt[1][3][1], pt[1][3][2])
	glVertex3f(pt[1][0][0], pt[1][0][1], pt[1][0][2])
	glVertex3f(pt[0][0][0], pt[0][0][1], pt[0][0][2])

	glEnd()


def drawJoint(joint, skeleton, count, d_flag):
	global flag
	offset = joint.offset
	pos = [0, 0, 0]
	rot_mat = np.array([[1., 0., 0., 0.],
						[0., 1., 0., 0.],
						[0., 0., 1., 0.],
						[0., 0., 0., 1.]])
	offset = np.array([float(offset[0]), float(offset[1]), float(offset[2])])

	if flag == True:
		for j in range(len(joint.channels)):

			i = joint.idx[0] + j
			channel = joint.channels[j]

			if channel.lower() == "xposition":
				pos[0] = skeleton.motions[count][i]
			elif channel.lower() == "yposition":
				pos[1] = skeleton.motions[count][i]
			elif channel.lower() == "zposition":
				pos[2] = skeleton.motions[count][i]
			if channel.lower() == "xrotation":
				rot = skeleton.motions[count][i]
				x = math.radians(rot)
				cos = math.cos(x)
				sin = math.sin(x)
				rot_mat2 = np.array([[1., 0., 0., 0.],
									 [0., cos, -sin, 0.],
									 [0., sin, cos, 0.],
									 [0., 0., 0., 1.]])
				rot_mat = np.dot(rot_mat, rot_mat2)
			elif channel.lower() == "yrotation":
				rot = skeleton.motions[count][i]
				x = math.radians(rot)
				cos = math.cos(x)
				sin = math.sin(x)
				rot_mat2 = np.array([[cos, 0., sin, 0.],
									 [0., 1., 0, 0.],
									 [-sin, 0, cos, 0.],
									 [0., 0., 0., 1.]])
				rot_mat = np.dot(rot_mat, rot_mat2)
			elif channel.lower() == "zrotation":
				rot = skeleton.motions[count][i]
				x = math.radians(rot)
				cos = math.cos(x)
				sin = math.sin(x)
				rot_mat2 = np.array([[cos, -sin, 0., 0.],
									 [sin, cos, 0., 0.],
									 [0., 0., 1., 0.],
									 [0., 0., 0., 1.]])
				rot_mat = np.dot(rot_mat, rot_mat2)

	glPushMatrix()
	glTranslatef(pos[0], pos[1], pos[2])

	if d_flag is True:
		drawCube([0, 0, 0], offset, 0.05)
		# glBegin(GL_LINES)
		# glColor3ub(255, 255, 0)
		# glVertex3f(0, 0, 0)
		# glVertex3f(offset[0], offset[1], offset[2])
		# glEnd()


	glTranslatef(offset[0], offset[1], offset[2])
	glMultMatrixf(rot_mat.T)

	for child in joint.children:
		drawJoint(child, skeleton, count, True)
	glPopMatrix()

def calculateEye():
	global camAng, camDist, target
	tmpEye = [target[0] + camDist * np.cos(np.radians(camAng[1])) * np.cos(np.radians(camAng[0])),
			  target[1] + camDist * np.sin(np.radians(camAng[1])),
			  target[2] + camDist * np.cos(np.radians(camAng[1])) * np.sin(np.radians(camAng[0]))]
	return tmpEye

def drop_callback(window, paths):
	global vertexArray, normalArray, faceArray, isObj, skeleton, flag, count
	isObj = 1
	flag = False
	count = 0
	print("1. File name: " + paths[0])
	skeleton = bvhreader(paths[0])


def key_callback(window, key, scancode, action, mods):
	global camAng, camHeight, camDist, flag, count
	if action == glfw.PRESS or action == glfw.REPEAT:
		if key == glfw.KEY_1:
			camAng += np.radians(-10)
		elif key == glfw.KEY_3:
			camAng += np.radians(10)
		elif key == glfw.KEY_2:
			camHeight += .1
		elif key == glfw.KEY_W:
			camHeight += -.1
		elif key == glfw.KEY_A:
			camDist -= .1
		elif key == glfw.KEY_SPACE:
			if flag:
				count = 0
			flag = not flag

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
	global camDist
	# zooming
	camDist = camDist - yoffset * speedZoom
	if camDist < 1:
		camDist = 1

def cursor_callback(window, xpos, ypos):
	global prevPos, camAng, camState, target, camDist, upVector
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

		target += xDistance * -u * speedPan * camDist
		target += yDistance * v * speedPan * camDist

	prevPos[0] = xpos
	prevPos[1] = ypos

def render(count):
	global camAng, camHeight, camDist, tmpEye, target, upVector, isObj, skeleton, flag

	# glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	glEnable(GL_DEPTH_TEST)

	drawGrid()

	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	gluPerspective(45, 1, 1, 1000)

	# lighting
	glShadeModel(GL_SMOOTH)
	glEnable(GL_LIGHTING)
	glEnable(GL_LIGHT0)
	
	# light 0
	glPushMatrix()
	
	lightPos = (100.,50.,100.,1.)
	specularObjectColor = (1.,1.,1.,1.)
	ambientLightColor1 = (0.25, 0.25, 0.25, 1.)
	diffuseLightColor1 = (0.90, 0.90, 0.90, 1.)
	
	glLightfv(GL_LIGHT0, GL_POSITION, lightPos)
	glLightfv(GL_LIGHT0, GL_AMBIENT, ambientLightColor1)
	glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuseLightColor1)
	glLightfv(GL_LIGHT0, GL_SPECULAR, specularObjectColor)
	
	glEnable(GL_COLOR_MATERIAL)
	glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
	glMaterialfv(GL_FRONT, GL_SPECULAR, specularObjectColor)
	glMateriali(GL_FRONT, GL_SHININESS, 10)

	glPopMatrix()

	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()
	tmpEye = calculateEye()
	gluLookAt(tmpEye[0], tmpEye[1], tmpEye[2],
			  target[0], target[1], target[2],
			  upVector[0], upVector[1], upVector[2])


	if skeleton is not None:
		glPushMatrix()
		if count == skeleton.frames:
			count = 0
		drawJoint(skeleton.root, skeleton, int(count / 2) % skeleton.frames, False)
		glPopMatrix()

	glDisable(GL_LIGHTING)

def main():
	global isObj, flag, count, skeleton
	if not glfw.init():
		return
	window = glfw.create_window(640, 640, 'assignment3-2015004402', None, None)
	if not window:
		glfw.terminate()
		return
	glfw.make_context_current(window)
	glfw.set_mouse_button_callback(window, mouse_callback)
	glfw.set_cursor_pos_callback(window, cursor_callback)
	glfw.set_scroll_callback(window, scroll_callback)
	glfw.set_key_callback(window, key_callback)
	glfw.set_drop_callback(window, drop_callback)
	glfw.make_context_current(window)
	# Loop until the user closes the window
	glfw.swap_interval(1)
	count = 0
	while not glfw.window_should_close(window):
		glfw.poll_events()
		render(count)
		glfw.swap_buffers(window)
		if flag == True:
			count += 1
	glfw.terminate()

if __name__ == "__main__":
	main()