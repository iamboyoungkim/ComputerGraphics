import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

gComposedM = np.array([[1.,0.,0.],
                        [0.,1.,0.],
                        [0.,0.,1.]])

def drawFrame():
    glBegin(GL_LINES)
    glColor3ub(255, 0, 0)
    glVertex2fv(np.array([0., 0.]))
    glVertex2fv(np.array([1., 0.]))
    glColor3ub(0, 255, 0)
    glVertex2fv(np.array([0., 0.]))
    glVertex2fv(np.array([0., 1.]))
    glEnd()

def drawTriangle():
    glBegin(GL_TRIANGLES)
    glVertex2fv(np.array([0., .5]))
    glVertex2fv(np.array([0., 0.]))
    glVertex2fv(np.array([.5, 0.]))
    glEnd()

    
def main():
    global gComposedM
    if not glfw.init():
        return
    window = glfw.create_window(480,480,"2015004402-5-2", None,None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        # white
        drawFrame()
        glColor3ub(255,255,255)
        drawTriangle()

        # blue
        glBegin(GL_TRIANGLES)
        glColor3ub(0,0,255)
        th = np.radians(30)
        R = np.array([[np.cos(th), -np.sin(th)],
                      [np.sin(th), np.cos(th)]])
        T = np.array([0.6, 0.])
        glVertex2fv(R @ np.array([0., .5]) + T)
        glVertex2fv(R @ np.array([0., 0.]) + T)
        glVertex2fv(R @ np.array([.5, 0.]) + T)
        glEnd()

        glBegin(GL_LINES)
        glColor3ub(255, 0, 0)
        glVertex2fv(R @ np.array([0., 0.]) + T)
        glVertex2fv(R @ np.array([1., 0.]) + T)
        glColor3ub(0, 255, 0)
        glVertex2fv(R @ np.array([0., 0.]) + T)
        glVertex2fv(R @ np.array([0., 1.]) + T)
        glEnd()

        
        glfw.swap_buffers(window)
    glfw.terminate()

if __name__ == "__main__":
    main()
