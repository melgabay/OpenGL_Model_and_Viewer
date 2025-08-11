from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import Image
import numpy as np
import sys

class Vertex:
    def __init__(self, x, y, z, u, v):
        self.x, self.y, self.z = x, y, z
        self.u, self.v = u, v

class Triangle:
    def __init__(self, vertices):
        self.vertices = vertices

class Sector:
    def __init__(self):
        self.triangles = self.create_cube()

    @staticmethod
    def create_cube():
        faces = []
        def add_face(vs):
            faces.append(Triangle([vs[0], vs[1], vs[2]]))
            faces.append(Triangle([vs[0], vs[2], vs[3]]))

        uv = [(0,0), (1,0), (1,1), (0,1)]
        def V(x, y, z, i): return Vertex(x, y, z, *uv[i])

        add_face([V(-1,-1, 1,0), V( 1,-1, 1,1), V( 1, 1, 1,2), V(-1, 1, 1,3)])  # front
        add_face([V( 1,-1,-1,0), V(-1,-1,-1,1), V(-1, 1,-1,2), V( 1, 1,-1,3)])  # back
        add_face([V(-1, 1, 1,0), V( 1, 1, 1,1), V( 1, 1,-1,2), V(-1, 1,-1,3)])  # top
        add_face([V(-1,-1,-1,0), V( 1,-1,-1,1), V( 1,-1, 1,2), V(-1,-1, 1,3)])  # bottom
        add_face([V(-1,-1,-1,0), V(-1,-1, 1,1), V(-1, 1, 1,2), V(-1, 1,-1,3)])  # left
        add_face([V( 1,-1, 1,0), V( 1,-1,-1,1), V( 1, 1,-1,2), V( 1, 1, 1,3)])  # right

        return faces

class Renderer:
    def __init__(self):
        self.sector = Sector()
        self.texture_ids = glGenTextures(3)
        self.filter_mode = 0
        self.angle_x = 20.0
        self.angle_y = 30.0
        self.mouse_dragging = False
        self.last_mouse = (0, 0)

    def load_texture(self, image_path):
        try:
            image = Image.open(image_path)
        except FileNotFoundError:
            print(f"Error: texture file '{image_path}' not found.")
            sys.exit(1)

        image = image.resize((256, 256)).transpose(Image.FLIP_TOP_BOTTOM)
        img_data = np.array(image.convert("RGB"), dtype=np.uint8)
        w, h = image.size

        glBindTexture(GL_TEXTURE_2D, self.texture_ids[0])
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)

    def init_gl(self):
        glEnable(GL_TEXTURE_2D)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        self.load_texture("mud.bmp")

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, 0, -6)
        glRotatef(self.angle_x, 1, 0, 0)
        glRotatef(self.angle_y, 0, 1, 0)

        glBindTexture(GL_TEXTURE_2D, self.texture_ids[self.filter_mode])
        for tri in self.sector.triangles:
            glBegin(GL_TRIANGLES)
            for v in tri.vertices:
                glTexCoord2f(v.u, v.v)
                glVertex3f(v.x, v.y, v.z)
            glEnd()

        glutSwapBuffers()

    def on_mouse_motion(self, x, y):
        if self.mouse_dragging:
            dx = x - self.last_mouse[0]
            dy = y - self.last_mouse[1]
            self.angle_y += dx * 0.5
            self.angle_x += dy * 0.5
            self.last_mouse = (x, y)

    def on_mouse_click(self, button, state, x, y):
        if button == GLUT_LEFT_BUTTON:
            self.mouse_dragging = (state == GLUT_DOWN)
            self.last_mouse = (x, y)

def reshape(w, h):
    h = max(h, 1)
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(80.0, w / h, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def main():
    global app
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Textured Cube - Mouse Controlled")

    app = Renderer()
    app.init_gl()

    glutDisplayFunc(app.render)
    glutReshapeFunc(reshape)
    glutMouseFunc(app.on_mouse_click)
    glutMotionFunc(app.on_mouse_motion)
    glutIdleFunc(app.render)

    glutMainLoop()

if __name__ == "__main__":
    main()
