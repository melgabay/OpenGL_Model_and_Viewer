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
    def __init__(self, filename):
        self.triangles = self.load_world_file(filename)

    @staticmethod
    def load_world_file(filename):
        triangles = []
        try:
            with open(filename, "r") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith("/")]
                num = int(lines[0].split()[1])
                for i in range(num):
                    v0 = Vertex(*map(float, lines[i * 3 + 1].split()))
                    v1 = Vertex(*map(float, lines[i * 3 + 2].split()))
                    v2 = Vertex(*map(float, lines[i * 3 + 3].split()))
                    triangles.append(Triangle([v0, v1, v2]))
        except FileNotFoundError:
            print(f"Error: {filename} not found.")
            sys.exit(1)
        return triangles

class Renderer:
    def __init__(self):
        self.sector = Sector("world.txt")
        self.texture_ids = glGenTextures(3)
        self.filter_mode = 0
        self.angle = 0.0

    def load_texture(self, image_path):
        try:
            image = Image.open(image_path)
        except FileNotFoundError:
            print(f"Error: texture file '{image_path}' not found.")
            sys.exit(1)

        # Force resize to 256x256 if needed (safe for legacy OpenGL)
        image = image.resize((256, 256))
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        img_data = np.array(image.convert("RGB"), dtype=np.uint8)
        w, h = image.size

        # NEAREST
        glBindTexture(GL_TEXTURE_2D, self.texture_ids[0])
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)

        # LINEAR
        glBindTexture(GL_TEXTURE_2D, self.texture_ids[1])
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)

        # MIPMAP
        glBindTexture(GL_TEXTURE_2D, self.texture_ids[2])
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGB, w, h, GL_RGB, GL_UNSIGNED_BYTE, img_data)

    def init_gl(self):
        glEnable(GL_TEXTURE_2D)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.0, 0.0, 0.0, 0.5)
        glClearDepth(1.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        self.load_texture("mud.bmp")

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -5.0)
        glRotatef(self.angle, 0.0, 1.0, 0.0)
        glBindTexture(GL_TEXTURE_2D, self.texture_ids[self.filter_mode])

        for tri in self.sector.triangles:
            glBegin(GL_TRIANGLES)
            for v in tri.vertices:
                glTexCoord2f(v.u, v.v)
                glVertex3f(v.x, v.y, v.z)
            glEnd()

        glutSwapBuffers()
        self.angle += 0.5

def reshape(w, h):
    h = max(h, 1)
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(80.0, w / h, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def timer(value):
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)

def main():
    global app
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Lesson10 - Safe Version")

    app = Renderer()
    app.init_gl()

    glutDisplayFunc(app.render)
    glutReshapeFunc(reshape)
    glutTimerFunc(0, timer, 0)
    glutMainLoop()

if __name__ == "__main__":
    main()