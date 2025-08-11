# main.py – Low-poly car • Trackball • HUD • Miroir • Éclairage
# Python 3.x  +  PyOpenGL  +  FreeGLUT
from OpenGL.GL   import *
from OpenGL.GLU  import *
from OpenGL.GLUT import *
import sys, math

AXIS_LEN = 3.0  # longueur des axes XYZ

# utilisé par reshape / callbacks
app = None

# ───────────────────────────────────────────────
# 1)  STRUCTURES DE DONNÉES
# ───────────────────────────────────────────────
class Vertex:
    def __init__(self, x, y, z, u=0, v=0):
        self.x, self.y, self.z = x, y, z
        self.u, self.v        = u, v

class Triangle:
    def __init__(self, vertices):
        self.vertices = vertices           # list[3] Vertex

# ───────────────────────────────────────────────
# 2)  LOW-POLY CAR (Sector) : on modèle UNE FOIS
# ───────────────────────────────────────────────
class Sector:
    # ---- helpers ----------------------------------------------------------------
    @staticmethod
    def _add_quad(tris, v0, v1, v2, v3):
        tris.append(Triangle([v0, v1, v2]))
        tris.append(Triangle([v0, v2, v3]))

    @staticmethod
    def _cuboid(min_pt, max_pt):
        x1, y1, z1 = min_pt
        x2, y2, z2 = max_pt
        uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
        V  = lambda x, y, z, i: Vertex(x, y, z, *uv[i])

        t = []
        Sector._add_quad(t, V(x1, y1, z2, 0), V(x2, y1, z2, 1), V(x2, y2, z2, 2), V(x1, y2, z2, 3))  # avant
        Sector._add_quad(t, V(x2, y1, z1, 0), V(x1, y1, z1, 1), V(x1, y2, z1, 2), V(x2, y2, z1, 3))  # arrière
        Sector._add_quad(t, V(x1, y2, z2, 0), V(x2, y2, z2, 1), V(x2, y2, z1, 2), V(x1, y2, z1, 3))  # dessus
        Sector._add_quad(t, V(x1, y1, z1, 0), V(x2, y1, z1, 1), V(x2, y1, z2, 2), V(x1, y1, z2, 3))  # dessous
        Sector._add_quad(t, V(x1, y1, z1, 0), V(x1, y1, z2, 1), V(x1, y2, z2, 2), V(x1, y2, z1, 3))  # gauche
        Sector._add_quad(t, V(x2, y1, z2, 0), V(x2, y1, z1, 1), V(x2, y2, z1, 2), V(x2, y2, z2, 3))  # droite
        return t

    @staticmethod
    def _cylinder(center, radius, half_w, segments=18):
        cx, cy, cz = center
        tris = []
        for i in range(segments):
            a1 = 2 * math.pi * i / segments
            a2 = 2 * math.pi * (i + 1) / segments
            x1, y1 = cx + radius * math.cos(a1), cy + radius * math.sin(a1)
            x2, y2 = cx + radius * math.cos(a2), cy + radius * math.sin(a2)
            zf, zb = cz - half_w, cz + half_w

            v0, v1 = Vertex(x1, y1, zf), Vertex(x2, y2, zf)
            v2, v3 = Vertex(x2, y2, zb), Vertex(x1, y1, zb)
            Sector._add_quad(tris, v0, v1, v2, v3)          # bande latérale
            tris.append(Triangle([Vertex(cx, cy, zf), v1, v0]))  # disque avant
            tris.append(Triangle([Vertex(cx, cy, zb), v3, v2]))  # disque arrière
        return tris
    # ------------------------------------------------------------------------------
    def __init__(self):
        self.triangles_body, self.triangles_windows = self._build_body()
        self.triangles_wheel = self._cylinder((0, 0, 0), 0.6, 0.2)  # une roue centrée
        self.triangles_headlight  = self._build_headlight()

    # --- un seul projecteur avant droit ---------------------------------
    def _build_headlight(self):
        return self._cuboid((0.6, -0.1, 1.05), (1.0, 0.1, 1.3))

    def _build_body(self):
        body, windows = [], []
        # châssis & toit — DEMI-CHÂSSIS (côté droit seulement)
        body += self._cuboid((0, -0.5, -1), (2, 0.5, 1))  # était (-2, -0.5, -1) → ( 2, 0.5, 1)
        body += self._cuboid((0, 0.5, -1), (1, 1.5, 1))  # était (-1,  0.5, -1) → ( 1, 1.5, 1)

        # vitres : (on garde le côté gauche tel quel, et on mirrora à droite dans render)
        y_bot, y_top, inset = 0.6, 1.4, 0.001
        V = lambda x, y, z: Vertex(x, y, z)
        self._add_quad(windows, V(-0.9, y_bot, 1.0 + inset), V(0.9, y_bot, 1.0 + inset),
                       V(0.9, y_top, 1.0 + inset), V(-0.9, y_top, 1.0 + inset))
        self._add_quad(windows, V(0.9, y_bot, -1.0 - inset), V(-0.9, y_bot, -1.0 - inset),
                       V(-0.9, y_top, -1.0 - inset), V(0.9, y_top, -1.0 - inset))
        self._add_quad(windows, V(-1.0 - inset, y_bot, -1.0), V(-1.0 - inset, y_bot, 0.0),
                       V(-1.0 - inset, y_top, 0.0), V(-1.0 - inset, y_top, -1.0))
        self._add_quad(windows, V(-1.0 - inset, y_bot, 0.0), V(-1.0 - inset, y_bot, 1.0),
                       V(-1.0 - inset, y_top, 1.0), V(-1.0 - inset, y_top, 0.0))
        return body, windows

class ExtraModels:
    def __init__(self):
        self.tris = []
        self.tris += self._build_lamp_post()

    def _build_lamp_post(self):
        t = []
        # Tige verticale
        t += Sector._cylinder((5, 0, 0), 0.1, 2.0)
        # Tête du lampadaire
        t += Sector._cuboid((4.8, 2.0, -0.2), (5.2, 2.2, 0.2))
        # Sphère émissive (optionnel, visible uniquement)
        self.lamp_sphere_pos = (5.0, 2.1, 0.0)
        return t

    def draw_emissive_sphere(self):
        # Sphère lumineuse jaune non affectée par l’éclairage
        glPushAttrib(GL_LIGHTING_BIT)
        glMaterialfv(GL_FRONT, GL_EMISSION, [1, 1, 0.2, 1])  # jaune doux
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1, 1, 0.2, 1])
        glPushMatrix()
        glTranslatef(*self.lamp_sphere_pos)
        glutSolidSphere(0.15, 12, 12)
        glPopMatrix()
        glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])  # reset
        glPopAttrib()

# ───────────────────────────────────────────────
# 3)  RENDERER
# ───────────────────────────────────────────────
class Renderer:
    # --- positions WORLD des lumières ----
    LIGHT0_POS = [ 3.0, 3.0,  4.0, 1.0]
    LIGHT1_POS = [-4.0, 5.0, -2.0, 1.0]

    def __init__(self):
        self.sector = Sector()

        # caméra / trackball
        self.zoom            = 10.0
        self.angle_x, self.angle_y = 20.0, 30.0
        self.mouse_drag = False
        self.mouse_drag_zoom = False
        self.last_mouse = (0, 0)

        # translation de la voiture / origine axes
        self.car_pos     = [0.0, 0.0, 0.0]
        self.axis_origin = [0.0, 0.0, 0.0]

        # toggle sphères lumières
        self.show_lights = True

        self.rot_q = [1.0, 0.0, 0.0, 0.0]  # quaternion (w,x,y,z)
        self.last_vec = (0.0, 0.0, 1.0)
        self.win_w, self.win_h = 800, 600
        self.extras = ExtraModels()
    # ------------------------------------------------------------------
    # 1)  INITIALISATION OPENGL
    # ------------------------------------------------------------------
    def init_gl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_NORMALIZE)

        # --- modèle d’éclairage : one-sided (définitif) ---------------
        #      ↳ passe à GL_TRUE seulement pour déboguer les normales
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_FALSE)

        # --- back-face culling (exigence finale) -----------------------
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)  # CCW = face avant

        glShadeModel(GL_SMOOTH)
        glClearColor(1.0, 1.0, 1.0, 1.0)

        # couleurs des deux lampes
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.8, 0.8, 1, 1])
        glLightfv(GL_LIGHT1, GL_SPECULAR, [0.8, 0.8, 1, 1])


    # ---------- utilitaires ------------------------------------------------------
    def _draw_axes(self):
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(*self.axis_origin); glVertex3f(self.axis_origin[0]+AXIS_LEN, self.axis_origin[1], self.axis_origin[2])
        glColor3f(0, 1, 0); glVertex3f(*self.axis_origin); glVertex3f(self.axis_origin[0], self.axis_origin[1]+AXIS_LEN, self.axis_origin[2])
        glColor3f(0, 0, 1); glVertex3f(*self.axis_origin); glVertex3f(self.axis_origin[0], self.axis_origin[1], self.axis_origin[2]+AXIS_LEN)
        glEnd()
        glColor3f(1, 1, 1)

    def _draw_text(self, txt, x, y, color=(0, 0, 0)):
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        gluOrtho2D(0, 800, 0, 600)
        glMatrixMode(GL_MODELVIEW);  glPushMatrix(); glLoadIdentity()
        glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)
        glColor3f(*color)
        glRasterPos2f(x, y)
        for ch in txt:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        glEnable(GL_DEPTH_TEST); glEnable(GL_LIGHTING)
        glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

    @staticmethod
    def _face_normal(p0, p1, p2):
        ux, uy, uz = p1.x-p0.x, p1.y-p0.y, p1.z-p0.z
        vx, vy, vz = p2.x-p0.x, p2.y-p0.y, p2.z-p0.z
        nx, ny, nz = uy*vz - uz*vy, uz*vx - ux*vz, ux*vy - uy*vx
        inv_len = 1.0 / math.sqrt(nx*nx + ny*ny + nz*nz)
        return nx*inv_len, ny*inv_len, nz*inv_len

    def _draw_mesh(self, tris):
        glBegin(GL_TRIANGLES)
        for tri in tris:
            n = self._face_normal(*tri.vertices)
            glNormal3f(*n)
            for v in tri.vertices:
                glVertex3f(v.x, v.y, v.z)
        glEnd()

    # ---------- dessin principal --------------------------------------------------
    # ------------------------------------------------------------------
    # 3)  RENDER
    # ------------------------------------------------------------------
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # ---------- CAMÉRA ----------
        # 1) rotation (trackball)  2) zoom (recul sur Z)
        # ancien comportement souris (Euler)
        glTranslatef(0, 0, -self.zoom)
        glRotatef(self.angle_x, 1, 0, 0)
        glRotatef(self.angle_y, 0, 1, 0)

        # positions des lampes dans le repère courant
        glLightfv(GL_LIGHT0, GL_POSITION, Renderer.LIGHT0_POS)
        glLightfv(GL_LIGHT1, GL_POSITION, Renderer.LIGHT1_POS)

        self._draw_axes()

        # ------------------ voiture -----------------------------------
        glPushMatrix()
        glTranslatef(*self.car_pos)

        # carrosserie (demi-châssis modélisé une seule fois → miroir X pour l’autre côté)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0.9, 0.1, 0.1, 1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1, 1, 1, 1])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 64)

        # côté droit (modélisé)
        self._draw_mesh(self.sector.triangles_body)

        # miroir X → côté gauche (1 axe négatif → winding inversé)
        glPushMatrix()
        glScalef(-1, 1, 1)
        glFrontFace(GL_CW)
        self._draw_mesh(self.sector.triangles_body)
        glFrontFace(GL_CCW)
        glPopMatrix()

        # vitres (gauche + miroir droite)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0.1, 0.1, 0.1, 1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.5, 0.5, 0.5, 1])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 16)
        self._draw_mesh(self.sector.triangles_windows)
        glPushMatrix()
        glScalef(-1, 1, 1);
        glFrontFace(GL_CW)
        self._draw_mesh(self.sector.triangles_windows)
        glFrontFace(GL_CCW);
        glPopMatrix()

        # ----- phares (un modèle, miroir à gauche) --------------------------
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [1.0, 0.9, 0.3, 1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 0.8, 1])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32)

        # projecteur droit (celui qu’on a réellement modélisé)
        self._draw_mesh(self.sector.triangles_headlight)

        # miroir : projecteur gauche
        glPushMatrix()
        glScalef(-1, 1, 1)
        glFrontFace(GL_CW)
        self._draw_mesh(self.sector.triangles_headlight)
        glFrontFace(GL_CCW)
        glPopMatrix()

        # roues (4 × même mesh)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0.05, 0.05, 0.05, 1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.3, 0.3, 0.3, 1])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 8)
        for x, y, z in [(1.1, -0.5, -1.5), (-1.1, -0.5, -1.5),
                        (1.1, -0.5, 1.5), (-1.1, -0.5, 1.5)]:
            glPushMatrix();
            glTranslatef(x, y, z)
            if x < 0:
                glScalef(-1, 1, 1);
                glFrontFace(GL_CW)
            self._draw_mesh(self.sector.triangles_wheel)
            if x < 0: glFrontFace(GL_CCW)
            glPopMatrix()

        glPopMatrix()  # voiture

        # ------------------ sphères-repères des lampes -----------------
        if self.show_lights:
            glPushAttrib(GL_LIGHTING_BIT)
            glMaterialfv(GL_FRONT, GL_EMISSION, [1, 1, 0, 1])  # jaune émissif
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1, 1, 0, 1])
            for px, py, pz, _ in (Renderer.LIGHT0_POS, Renderer.LIGHT1_POS):
                glPushMatrix();
                glTranslatef(px, py, pz)
                glutSolidSphere(0.25, 16, 16)
                glPopMatrix()
            glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])  # reset
            glPopAttrib()

        # ------------------ modèle bonus : lampadaire ---------------------
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0.3, 0.3, 0.3, 1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.5, 0.5, 0.5, 1])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 16)
        self._draw_mesh(self.extras.tris)
        self.extras.draw_emissive_sphere()

        # ------------------ HUD ----------------------------------------
        self._draw_text(f"Car Pos:   {self.car_pos}", 10, 580)
        self._draw_text(f"Axis Orig: {self.axis_origin}", 10, 555)
        self._draw_text(f"'l' : toggle light spheres", 10, 530)

        glutSwapBuffers()

    # -------- quaternions utilitaires -----------------------------------
    def _project_on_sphere(self, x, y):
        # convertit coordonnées pixels → [-1,1] puis projette sur sphère de rayon 1
        nx = (2.0 * x - self.win_w) / self.win_w
        ny = -(2.0 * y - self.win_h) / self.win_h
        nz2 = 1.0 - nx * nx - ny * ny
        nz = math.sqrt(max(0.0, nz2))
        l = math.sqrt(nx * nx + ny * ny + nz * nz)
        return (nx / l, ny / l, nz / l)

    @staticmethod
    def _quat_mult(q1, q2):
        w1, x1, y1, z1 = q1;
        w2, x2, y2, z2 = q2
        return (
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
        )

    @staticmethod
    def _quat_normalize(q):
        w, x, y, z = q
        n = math.sqrt(w * w + x * x + y * y + z * z)
        if n == 0.0:
            return (1.0, 0.0, 0.0, 0.0)
        return (w / n, x / n, y / n, z / n)

    @staticmethod
    def _quat_to_matrix(q):
        # retourne une matrice 4×4 en colonne-majeur (OpenGL)
        w, x, y, z = q
        xx, xy, xz = 1 - 2*(y*y + z*z), 2*(x*y - w*z),     2*(x*z + w*y)
        yx, yy, yz = 2*(x*y + w*z),     1 - 2*(x*x + z*z), 2*(y*z - w*x)
        zx, zy, zz = 2*(x*z - w*y),     2*(y*z + w*x),     1 - 2*(x*x + y*y)
        return [
            xx, yx, zx, 0,
            xy, yy, zy, 0,
            xz, yz, zz, 0,
             0,  0,  0, 1
        ]

    # ---------- entrées clavier/souris -------------------------------------------
    # ------------------------------------------------------------------
    # 2)  CLAVIER
    # ------------------------------------------------------------------
    def on_keys(self, key, *_):
        if key == b'w':
            self.car_pos[1] += 0.1
        elif key == b's':
            self.car_pos[1] -= 0.1
        elif key == b'a':
            self.car_pos[0] -= 0.1
        elif key == b'd':
            self.car_pos[0] += 0.1
        elif key == b'z':
            self.car_pos[2] += 0.1
        elif key == b'x':
            self.car_pos[2] -= 0.1

        elif key == b'i':
            self.axis_origin[1] += 0.1
        elif key == b'k':
            self.axis_origin[1] -= 0.1
        elif key == b'j':
            self.axis_origin[0] -= 0.1
        elif key == b'L':
            self.axis_origin[0] += 0.1  # (majuscule)

        elif key == b'u':
            self.axis_origin[2] += 0.1
        elif key == b'o':
            self.axis_origin[2] -= 0.1

        elif key == b'+':
            self.zoom = max(2.0, self.zoom - 0.5)
        elif key == b'-':
            self.zoom += 0.5

        elif key == b'l':
            self.show_lights = not self.show_lights  # toggle sphères

        glutPostRedisplay()



    def on_mouse_click(self, button, state, x, y):
        if button == 3 and state == GLUT_DOWN:  # molette +
            self.zoom = max(2.0, self.zoom - 0.5); glutPostRedisplay(); return
        if button == 4 and state == GLUT_DOWN:  # molette -
            self.zoom += 0.5; glutPostRedisplay(); return
        if button == GLUT_RIGHT_BUTTON:
            self.mouse_drag_zoom = (state == GLUT_DOWN); self.last_mouse = (x, y)
        if button == GLUT_LEFT_BUTTON:
            self.mouse_drag = (state == GLUT_DOWN); self.last_mouse = (x, y)

    def on_mouse_motion(self, x, y):
        if self.mouse_drag_zoom:
            dy = y - self.last_mouse[1]
            self.zoom = max(2.0, self.zoom + dy * 0.05)

        elif self.mouse_drag:
            dx = x - self.last_mouse[0]
            dy = y - self.last_mouse[1]
            self.angle_y += dx * 0.5  # horizontal → yaw
            self.angle_x += dy * 0.5  # vertical   → pitch
            # (optionnel) clamp pour éviter les flips :
            # self.angle_x = max(-89.0, min(89.0, self.angle_x))

        self.last_mouse = (x, y)
        glutPostRedisplay()


# ───────────────────────────────────────────────
# 4)  RESHAPE
# ───────────────────────────────────────────────
def reshape(w, h):
    global app                         # ← accès à l'instance Renderer
    h = max(h, 1)
    app.win_w, app.win_h = w, h        # mets à jour pour le trackball
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(80.0, w / float(h), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
# ───────────────────────────────────────────────
# 5)  MAIN
# ───────────────────────────────────────────────
def main():
    global app                         # ← variable globale partagée
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Low-poly Car  Trackball Lights")

    app = Renderer()
    app.init_gl()

    glutDisplayFunc(app.render)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(app.on_keys)
    glutMouseFunc(app.on_mouse_click)
    glutMotionFunc(app.on_mouse_motion)
    glutIdleFunc(app.render)

    glutMainLoop()


if __name__ == "__main__":
    main()