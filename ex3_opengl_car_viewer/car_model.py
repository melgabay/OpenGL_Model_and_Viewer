from OpenGL.GL import *
from OpenGL.GLU import *

def draw_car(wireframe=False, show_lights=True):
    glPushMatrix()
    draw_chassis()
    draw_windows()
    draw_doors()
    for x in [-0.8, 0.8]:
        for z in [-0.6, 0.6]:
            draw_wheel(x, z)
    draw_headlight(0.5)
    draw_headlight(-0.5)
    if show_lights:
        draw_light_sphere(0.5)
        draw_light_sphere(-0.5)
    glPopMatrix()

def draw_chassis():
    glColor3f(0.6, 0.1, 0.1)
    glBegin(GL_QUADS)
    # Front, Back, Top, Bottom, Left, Right
    for x in [-1, 1]:
        for y in [-0.3, 0.3]:
            for z in [-0.5, 0.5]:
                glVertex3f(x, y, z)
    glEnd()

def draw_windows():
    glColor3f(0.2, 0.5, 0.8)
    glBegin(GL_QUADS)
    glVertex3f(-0.3, 0.3, 0.51)
    glVertex3f(0.3, 0.3, 0.51)
    glVertex3f(0.3, 0.0, 0.51)
    glVertex3f(-0.3, 0.0, 0.51)
    glEnd()

def draw_doors():
    glDisable(GL_LIGHTING)
    glColor3f(1,1,1)
    glBegin(GL_LINES)
    glVertex3f(0, -0.3, 0.51)
    glVertex3f(0, 0.3, 0.51)
    glEnd()
    glEnable(GL_LIGHTING)

def draw_wheel(x, z):
    glPushMatrix()
    glTranslatef(x, -0.35, z)
    glRotatef(90, 0, 1, 0)
    quad = gluNewQuadric()
    gluCylinder(quad, 0.1, 0.1, 0.05, 20, 1)
    glTranslatef(0, 0, 0.05)
    gluDisk(quad, 0, 0.1, 20, 1)
    glPopMatrix()

def draw_headlight(x):
    glPushMatrix()
    glTranslatef(x, 0.0, 0.55)
    glColor3f(1, 1, 0.8)
    quad = gluNewQuadric()
    gluCylinder(quad, 0.05, 0.05, 0.1, 20, 1)
    glTranslatef(0, 0, 0.1)
    gluDisk(quad, 0, 0.05, 20, 1)
    glPopMatrix()

def draw_light_sphere(x):
    glPushMatrix()
    glTranslatef(x, 1.5, 1.5)
    glMaterialfv(GL_FRONT, GL_EMISSION, [1, 1, 0, 1])
    glut = gluNewQuadric()
    gluSphere(glut, 0.05, 10, 10)
    glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])
    glPopMatrix()
