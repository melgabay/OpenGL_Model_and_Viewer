from OpenGL.GL import *
from OpenGL.GLU import *

def draw_car(wireframe=False, show_lights=True):
    glPushMatrix()
    draw_chassis()
    draw_windows()
    draw_doors()

    # --- PNEU de référence : on le dessine une seule fois ---
    # Position de base (équivalent à +X, +Z dans ton ancien repère)
    glPushMatrix()
    draw_wheel(0.8, 0.6)
    glPopMatrix()

    # Miroir X -> (-X, +Z)  => 1 axe négatif => inverser winding
    glPushMatrix()
    glScalef(-1, 1, 1)
    glFrontFace(GL_CW)
    draw_wheel(0.8, 0.6)
    glFrontFace(GL_CCW)
    glPopMatrix()

    # Miroir Z -> (+X, -Z)  => 1 axe négatif => inverser winding
    glPushMatrix()
    glScalef(1, 1, -1)
    glFrontFace(GL_CW)
    draw_wheel(0.8, 0.6)
    glFrontFace(GL_CCW)
    glPopMatrix()

    # Miroir X et Z -> (-X, -Z)  => 2 axes négatifs (pair) => winding conservé
    glPushMatrix()
    glScalef(-1, 1, -1)
    # pas besoin de glFrontFace ici
    draw_wheel(0.8, 0.6)
    glPopMatrix()

    # --- PHARE de référence (droite, +X) ---
    draw_headlight(0.5)

    # Miroir X pour le phare gauche (-X) => 1 axe négatif => inverser winding
    glPushMatrix()
    glScalef(-1, 1, 1)
    glFrontFace(GL_CW)
    draw_headlight(0.5)
    glFrontFace(GL_CCW)
    glPopMatrix()

    # --- SPHÈRES de lumière (debug), même logique ---
    if show_lights:
        glPushAttrib(GL_LIGHTING_BIT)
        glMaterialfv(GL_FRONT, GL_EMISSION, [1, 1, 0, 1])
        # droite (+X)
        draw_light_sphere(0.5)
        # gauche (miroir X)
        glPushMatrix()
        glScalef(-1, 1, 1)
        glFrontFace(GL_CW)
        draw_light_sphere(0.5)
        glFrontFace(GL_CCW)
        glPopMatrix()
        glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])
        glPopAttrib()

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
