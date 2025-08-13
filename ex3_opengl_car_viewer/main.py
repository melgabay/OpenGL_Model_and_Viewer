# main.py – Low-poly car • Trackball (Euler) • HUD • Éclairage
# Python 3.x  +  PyOpenGL  +  FreeGLUT
from OpenGL.GL   import *
from OpenGL.GLU  import *
from OpenGL.GLUT import *
import sys, math
from trackball import Trackball

AXIS_LEN = 3.0  # longueur des axes XYZ

# --- proportions "blueprint" (repère: X=gauche/droite, Y=haut/bas, Z=avant/arrière) ---
HALF_LEN   = 2.25
HALF_W     = 1.30
BASE_Y0    = -0.52
BASE_Y1    =  0.32
ROOF_Y0    = 0.44
ROOF_Y1    = 1.02
ROOF_W     = 0.75
ROOF_L     = 1.10
ROOF_SHIFT = 0.10
WHEEL_R      = 0.45
WHEEL_HALF_W = 0.22
NOSE_LEN   = 1.35
TRUNK_LEN  = 1.00
HOOD_DROP  = 0.42
TRUNK_DROP = 0.30

app = None  # pour reshape / callbacks

# ───────────────────────────────────────────────
# 1)  STRUCTURES
# ───────────────────────────────────────────────
class Vertex:
    def __init__(self, x, y, z, u=0, v=0):
        self.x, self.y, self.z = x, y, z
        self.u, self.v = u, v

class Triangle:
    def __init__(self, vertices):
        self.vertices = vertices  # list[3] Vertex

# ───────────────────────────────────────────────
# 2)  GEO UTILS
# ───────────────────────────────────────────────
class Sector:
    @staticmethod
    def _add_quad(tris, v0, v1, v2, v3):
        tris.append(Triangle([v0, v1, v2]))
        tris.append(Triangle([v0, v2, v3]))

    @staticmethod
    def _cuboid_half_open_x0(min_pt, max_pt):
        x0, y0, z0 = min_pt
        x1, y1, z1 = max_pt
        V = lambda x, y, z: Vertex(x, y, z)
        t = []
        # avant / arrière
        Sector._add_quad(t, V(x0, y0, z1), V(x1, y0, z1), V(x1, y1, z1), V(x0, y1, z1))
        Sector._add_quad(t, V(x1, y0, z0), V(x0, y0, z0), V(x0, y1, z0), V(x1, y1, z0))
        # dessus
        Sector._add_quad(t, V(x0, y1, z1), V(x1, y1, z1), V(x1, y1, z0), V(x0, y1, z0))
        # >>> DESSOUS (winding corrigé pour normal vers -Y) <<<
        Sector._add_quad(t, V(x0, y0, z1), V(x1, y0, z1), V(x1, y0, z0), V(x0, y0, z0))
        # côté x1 (seulement)
        Sector._add_quad(t, V(x1, y0, z1), V(x1, y0, z0), V(x1, y1, z0), V(x1, y1, z1))
        return t

    @staticmethod
    def _wedge_half_open_x0(tris, x0, x1, z0, z1, yb, yt0, yt1):
        V = lambda x, y, z: Vertex(x, y, z)
        # >>> DESSOUS (winding corrigé pour normal vers -Y) <<<
        Sector._add_quad(tris, V(x0, yb, z1), V(x1, yb, z1), V(x1, yb, z0), V(x0, yb, z0))
        # dessus incliné — winding inversé pour normale vers l'extérieur (+Y côté pente)
        Sector._add_quad(tris, V(x0, yt1, z1), V(x1, yt1, z1), V(x1, yt0, z0), V(x0, yt0, z0))
        # face z1
        Sector._add_quad(tris, V(x0, yb, z1), V(x1, yb, z1), V(x1, yt1, z1), V(x0, yt1, z1))
        # face z0
        Sector._add_quad(tris, V(x1, yb, z0), V(x0, yb, z0), V(x0, yt0, z0), V(x1, yt0, z0))
        # côté x1 uniquement
        Sector._add_quad(tris, V(x1, yb, z1), V(x1, yb, z0), V(x1, yt0, z0), V(x1, yt1, z1))

    @staticmethod
    def _cuboid(min_pt, max_pt):
        x1, y1, z1 = min_pt; x2, y2, z2 = max_pt
        V=lambda x,y,z: Vertex(x,y,z); t=[]
        Sector._add_quad(t, V(x1,y1,z2), V(x2,y1,z2), V(x2,y2,z2), V(x1,y2,z2))
        Sector._add_quad(t, V(x2,y1,z1), V(x1,y1,z1), V(x1,y2,z1), V(x2,y2,z1))
        Sector._add_quad(t, V(x1,y2,z2), V(x2,y2,z2), V(x2,y2,z1), V(x1,y2,z1))
        Sector._add_quad(t, V(x1,y1,z1), V(x2,y1,z1), V(x2,y1,z2), V(x1,y1,z2))
        Sector._add_quad(t, V(x1,y1,z1), V(x1,y1,z2), V(x1,y2,z2), V(x1,y2,z1))
        Sector._add_quad(t, V(x2,y1,z2), V(x2,y1,z1), V(x2,y2,z1), V(x2,y2,z2))
        return t

    @staticmethod
    def _cylinder(center, radius, half_w, segments=24):
        cx, cy, cz = center; tris=[]
        for i in range(segments):
            a1=2*math.pi*i/segments; a2=2*math.pi*(i+1)/segments
            x1=cx+radius*math.cos(a1); y1=cy+radius*math.sin(a1)
            x2=cx+radius*math.cos(a2); y2=cy+radius*math.sin(a2)
            zf,zb = cz-half_w, cz+half_w
            v0,v1=Vertex(x1,y1,zf),Vertex(x2,y2,zf); v2,v3=Vertex(x2,y2,zb),Vertex(x1,y1,zb)
            Sector._add_quad(tris, v0,v1,v2,v3)                      # manteau
            tris.append(Triangle([Vertex(cx,cy,zf), v1, v0]))        # face -z
            tris.append(Triangle([Vertex(cx,cy,zb), v3, v2]))        # face +z
        return tris

    @staticmethod
    def _mirror_tris_x(tris):
        # renvoie une copie mirroir en X, winding inversé pour rester CCW
        out = []
        for t in tris:
            m = [Vertex(-v.x, v.y, v.z) for v in t.vertices]
            out.append(Triangle([m[0], m[2], m[1]]))  # inversion de l'ordre
        return out

    def __init__(self):
        # 1/2 voiture (droite) + panneaux centraux + jupe sous phares
        half, win_side, glass_center, under_headlight = self._build_body_half()

        # miroir AU BUILD (pas au rendu)
        self.triangles_body = half + self._mirror_tris_x(half)
        self.triangles_windows = win_side + self._mirror_tris_x(win_side) + glass_center
        self.triangles_under_headlight = under_headlight + self._mirror_tris_x(under_headlight)

        # roues & phare
        self.triangles_wheel = self._cylinder((0, 0, 0), WHEEL_R, WHEEL_HALF_W)
        self.triangles_headlight = self._build_headlight()

    def _build_body_half(self):
        body_half = []
        windows_side = []
        glass_center = []  # pare-brise + lunette
        under_headlight = []  # jupe sous phares (séparée pour couleur)

        x0, x1 = 0.0, HALF_W
        z_mid_front = HALF_LEN - NOSE_LEN
        z_mid_back = -HALF_LEN + TRUNK_LEN

        V = lambda x, y, z: Vertex(x, y, z)
        EPS = 0.002

        # 1) Bas de caisse central (demi, ouvert sur x=0)
        body_half += self._cuboid_half_open_x0(
            (x0, BASE_Y0, z_mid_back),
            (x1, BASE_Y1, z_mid_front)
        )

        # 2) Cloison avant à z = z_mid_front (normale vers -Z)
        Sector._add_quad(
            body_half,
            V(x1, BASE_Y0, z_mid_front + EPS),
            V(x0, BASE_Y0, z_mid_front + EPS),
            V(x0, BASE_Y1, z_mid_front + EPS),
            V(x1, BASE_Y1, z_mid_front + EPS)
        )

        # 3) Plancher sous capot (horizontal) z_mid_front → HALF_LEN (normale -Y)
        floor_y = BASE_Y0 + 0.01
        Sector._add_quad(
            body_half,
            V(x0, floor_y, HALF_LEN - EPS),
            V(x1, floor_y, HALF_LEN - EPS),
            V(x1, floor_y, z_mid_front + EPS),
            V(x0, floor_y, z_mid_front + EPS)
        )

        # 4) Jupe sous phares (fermeture inférieure du nez) — stockée séparément
        BUMPER_LIP = 0.12
        BUMPER_TAPER = 0.18
        yb = BASE_Y0 + EPS
        yt0 = BASE_Y1 - BUMPER_LIP
        yt1 = BASE_Y1 - HOOD_DROP - BUMPER_TAPER
        tmp = []
        self._wedge_half_open_x0(tmp, x0, x1, z_mid_front, HALF_LEN, yb, yt0, yt1)
        # On ne l’ajoute qu’à under_headlight, pas au body_half
        under_headlight += tmp

        # 5) Capot avant (pente supérieure)
        self._wedge_half_open_x0(
            body_half, x0, x1, z_mid_front, HALF_LEN,
            BASE_Y0, BASE_Y1, BASE_Y1 - HOOD_DROP
        )

        # 6) Malle arrière
        self._wedge_half_open_x0(
            body_half, x0, x1, -HALF_LEN, z_mid_back,
            BASE_Y0, BASE_Y1 - TRUNK_DROP, BASE_Y1
        )

        # 7) Pavillon (moitié droite) — ALIGNE EN X AVEC LA CAISSE
        #    → x1 = HALF_W (au lieu de ROOF_W) + bas collé à BASE_Y1
        roof_z0 = -ROOF_L + ROOF_SHIFT - 0.25
        roof_z1 = ROOF_L + ROOF_SHIFT - 0.25
        body_half += self._cuboid_half_open_x0(
            (0.0, BASE_Y1, roof_z0),  # bas du pavillon collé à la caisse
            (HALF_W, ROOF_Y1, roof_z1)  # demi-largeur = même que la caisse
        )

        # 8) Vitres latérales (droite) — deux vitres séparées par un montant (B-pillar)
        inset = 0.05
        yb_w, yt_w = BASE_Y1 + 0.05, ROOF_Y1 - 0.06
        xg = HALF_W + inset

        # positions le long de Z
        pillar_w = 0.08                                    # largeur du montant central
        midZ = (roof_z0 + roof_z1) * 0.5
        zA = roof_z0 + 0.20                             # début vitre avant
        zB = midZ - pillar_w * 0.9                         # fin vitre avant
        zC = midZ + pillar_w * 0.9                         # début vitre arrière
        zD = roof_z1 - 0.20                              # fin vitre arrière

        # vitre avant (plan x = HALF_W + inset)
        windows_side += [
            Triangle([V(xg, yb_w, zA), V(xg, yb_w, zB), V(xg, yt_w, zB)]),
            Triangle([V(xg, yb_w, zA), V(xg, yt_w, zB), V(xg, yt_w, zA)]),
        ]
        # vitre arrière
        windows_side += [
            Triangle([V(xg, yb_w, zC), V(xg, yb_w, zD), V(xg, yt_w, zD)]),
            Triangle([V(xg, yb_w, zC), V(xg, yt_w, zD), V(xg, yt_w, zC)]),
        ]

        # 9) Pare-brise + lunette (panneaux centraux) — insets plus grands pour éviter le Z-fighting
        # 9) Pare-brise + lunette (panneaux centraux)
        #    Même technique que les vitres latérales : 2 triangles coplanaires
        #    sur un plan vertical à z constant (plus d'inclinaison → plus d'espace).
        inset_front = 0.001   # pousse très légèrement vers +Z (évite Z-fighting)
        inset_back  = -0.001  # pousse très légèrement vers −Z
        y_bottom_ws = BASE_Y1 + 0.02
        y_top_ws    = ROOF_Y1 - 0.02

        zf = z_mid_front + inset_front
        zb = z_mid_back  + inset_back
        pb_half_width = HALF_W * 0.7
        # Pare-brise avant (plan z = zf)
        glass_center += [
            Triangle([V(-pb_half_width, y_bottom_ws, zf+0.05),
                      V( pb_half_width, y_bottom_ws, zf+0.05),
                      V( pb_half_width, y_top_ws,    zf+0.05)]),
            Triangle([V(-pb_half_width, y_bottom_ws, zf+0.05),
                      V( pb_half_width, y_top_ws,    zf+0.05),
                      V(-pb_half_width, y_top_ws,    zf+0.05)])
        ]

        # Lunette arrière (plan z = zb)
        glass_center += [
            Triangle([V( pb_half_width, y_bottom_ws, zb),
                      V(-pb_half_width, y_bottom_ws, zb),
                      V(-pb_half_width, y_top_ws,    zb)]),
            Triangle([V( pb_half_width, y_bottom_ws, zb),
                      V(-pb_half_width, y_top_ws,    zb),
                      V( pb_half_width, y_top_ws,    zb)])
        ]

        return body_half, windows_side, glass_center, under_headlight



    def _build_headlight(self):
        r = 0.12; half_t = 0.03
        cx = HALF_W - 0.28
        cy = BASE_Y1 - 0.60
        cz = HALF_LEN + 0.02
        return self._cylinder((cx, cy, cz), r, half_t, segments=24)

# ───────────────────────────────────────────────
# 2b)  LAMPADAIRE
# ───────────────────────────────────────────────
class ExtraModels:
    def __init__(self):
        self.tris = []
        self.tris += self._build_lamp_post()

    def _build_lamp_post(self):
        t = []
        t += Sector._cylinder((5, 0, 0), 0.1, 2.0)
        t += Sector._cuboid((4.8, 2.0, -0.2), (5.2, 2.2, 0.2))
        self.lamp_sphere_pos = (5.0, 2.1, 0.0)
        return t

    def draw_emissive_sphere(self):
        # Affichage "balise" indépendante des lumières de la scène
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_LIGHTING_BIT)
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 1.0, 0.2)
        glPushMatrix()
        glTranslatef(*self.lamp_sphere_pos)
        glutSolidSphere(0.15, 12, 12)
        glPopMatrix()
        glPopAttrib()

# ───────────────────────────────────────────────
# 3)  RENDERER
# ───────────────────────────────────────────────
class Renderer:
    LIGHT0_POS = [ 3.0, 3.0,  4.0, 1.0]
    LIGHT1_POS = [-4.0, 5.0, -2.0, 1.0]


    def __init__(self):
        self.sector = Sector()
        self.zoom = 10.0
        self.angle_x, self.angle_y = 20.0, 30.0
        self.mouse_drag = False
        self.mouse_drag_zoom = False
        self.last_mouse = (0, 0)
        self.win_w, self.win_h = 800, 600
        self.car_pos     = [0.0, 0.0, 0.0]
        self.axis_origin = [0.0, 0.0, 0.0]
        self.show_lights = True
        self.extras = ExtraModels()

        # AJOUTS
        self.show_axes = True
        self.wireframe = False
        self.use_trackball = True
        self.trackball = Trackball()


    # init OpenGL
    def init_gl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_LIGHT1)
        glEnable(GL_NORMALIZE)
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_FALSE)
        glEnable(GL_CULL_FACE); glCullFace(GL_BACK); glFrontFace(GL_CCW)
        glShadeModel(GL_SMOOTH)
        glClearColor(0, 0, 0, 1)
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1,1,1,1]); glLightfv(GL_LIGHT0, GL_SPECULAR, [1,1,1,1])
        glLightfv(GL_LIGHT1, GL_DIFFUSE,  [0.8,0.8,1,1]); glLightfv(GL_LIGHT1, GL_SPECULAR,[0.8,0.8,1,1])

    # petits helpers
    def _draw_axes(self):
        glDisable(GL_LIGHTING)  # couleur non affectée par la lumière
        glLineWidth(2.0)
        glBegin(GL_LINES)

        ox, oy, oz = self.axis_origin

        # X rouge
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(ox, oy, oz)
        glVertex3f(ox + AXIS_LEN, oy, oz)

        # Y vert
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(ox, oy, oz)
        glVertex3f(ox, oy + AXIS_LEN, oz)

        # Z bleu
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(ox, oy, oz)
        glVertex3f(ox, oy, oz + AXIS_LEN)

        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

    def _draw_text(self, txt, x, y, color=(1,1,1)):
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, 800, 0, 600)
        glMatrixMode(GL_MODELVIEW);  glPushMatrix(); glLoadIdentity()
        glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST); glColor3f(*color)
        glRasterPos2f(x, y)
        for ch in txt: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
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

    # rendu
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, 0, -self.zoom)
        glRotatef(self.angle_x, 1, 0, 0)
        glRotatef(self.angle_y, 0, 1, 0)

        glLightfv(GL_LIGHT0, GL_POSITION, Renderer.LIGHT0_POS)
        glLightfv(GL_LIGHT1, GL_POSITION, Renderer.LIGHT1_POS)

        self._draw_axes()

        # ===== voiture =====
        glPushMatrix(); glTranslatef(*self.car_pos)

        glDisable(GL_CULL_FACE)

        # carrosserie
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0.22, 0.45, 0.80, 1])  # bleu carrosserie
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.35, 0.45, 0.55, 1])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 48)
        self._draw_mesh(self.sector.triangles_body)


        # vitres
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0.95, 0.95, 0.85, 1])  # beige clair
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1])  # reflet blanc
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 64)
        self._draw_mesh(self.sector.triangles_windows)

        # phares (un modèle + miroir simple)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0.95,0.85,0.30,1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0,1.0,0.8,1])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 40)
        self._draw_mesh(self.sector.triangles_headlight)
        glPushMatrix(); glScalef(-1,1,1); glFrontFace(GL_CW)
        self._draw_mesh(self.sector.triangles_headlight)
        glFrontFace(GL_CCW); glPopMatrix()

        # ---- couleur spécifique pour la pièce sous phares ----
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0.22, 0.45, 0.80, 1])  # bleu carrosserie
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.35, 0.45, 0.55, 1])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 48)
        self._draw_mesh(self.sector.triangles_under_headlight)

        # roues (1 mesh × 4)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0.95, 0.95, 0.85, 1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 16)

        wheel_x = HALF_W - 0.12
        wheel_z_front = HALF_LEN - 0.55
        wheel_z_back  = HALF_LEN - 1.55
        wheel_y = BASE_Y0

        def place_wheel(x, y, z):
            glPushMatrix(); glTranslatef(x,y,z); glRotatef(90,0,1,0)
            self._draw_mesh(self.sector.triangles_wheel); glPopMatrix()

        place_wheel(+wheel_x, wheel_y, +wheel_z_front)
        place_wheel(-wheel_x, wheel_y, +wheel_z_front)
        place_wheel(+wheel_x, wheel_y, -wheel_z_back)
        place_wheel(-wheel_x, wheel_y, -wheel_z_back)

        glPopMatrix()  # ===== fin voiture =====

        # sphères repères des lumières
        if self.show_lights:
            glPushAttrib(GL_LIGHTING_BIT)
            glMaterialfv(GL_FRONT, GL_EMISSION, [1,1,0,1])
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1,1,0,1])
            for px, py, pz, _ in (Renderer.LIGHT0_POS, Renderer.LIGHT1_POS):
                glPushMatrix(); glTranslatef(px,py,pz); glutSolidSphere(0.25,16,16); glPopMatrix()
            glMaterialfv(GL_FRONT, GL_EMISSION, [0,0,0,1]); glPopAttrib()

        # bonus lampadaire
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0.3,0.3,0.3,1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.5,0.5,0.5,1])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 16)
        self._draw_mesh(self.extras.tris)
        self.extras.draw_emissive_sphere()

        # HUD
        self._draw_text(f"Car Pos:   {self.car_pos}", 10, 580)
        self._draw_text(f"Axis Orig: {self.axis_origin}", 10, 555)
        self._draw_text(f"'l' : toggle light spheres", 10, 530)

        glutSwapBuffers()

    # entrées
    def on_keys(self, key, *_):
        if   key == b'w': self.car_pos[1] += 0.1
        elif key == b's': self.car_pos[1] -= 0.1
        elif key == b'a': self.car_pos[0] -= 0.1
        elif key == b'd': self.car_pos[0] += 0.1
        elif key == b'z': self.car_pos[2] += 0.1
        elif key == b'x': self.car_pos[2] -= 0.1
        elif key == b'i': self.axis_origin[1] += 0.1
        elif key == b'k': self.axis_origin[1] -= 0.1
        elif key == b'j': self.axis_origin[0] -= 0.1
        elif key == b'L': self.axis_origin[0] += 0.1
        elif key == b'u': self.axis_origin[2] += 0.1
        elif key == b'o': self.axis_origin[2] -= 0.1
        elif key == b'+': self.zoom = max(2.0, self.zoom - 0.5)
        elif key == b'-': self.zoom += 0.5
        elif key == b'l': self.show_lights = not self.show_lights

        # AJOUTS: toggles demandés par l'énoncé
        elif key == b'p':
            self.wireframe = not self.wireframe
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if self.wireframe else GL_FILL)
        elif key == b'a':
            self.show_axes = not self.show_axes

        glutPostRedisplay()

    def _draw_wheel_glu(self, radius=WHEEL_R, half_w=WHEEL_HALF_W, slices=24):
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)

        # Cylindre le long de +Z (hauteur = 2*half_w)
        gluCylinder(quad, radius, radius, 2.0 * half_w, slices, 1)

        # Disque arrière (z=0)
        gluDisk(quad, 0.0, radius, slices, 1)

        # Disque avant (z=2*half_w)
        glPushMatrix()
        glTranslatef(0.0, 0.0, 2.0 * half_w)
        gluDisk(quad, 0.0, radius, slices, 1)
        glPopMatrix()

        gluDeleteQuadric(quad)

    def _draw_headlight_glu(self, radius=0.12, half_t=0.03, slices=24):
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)

        # On dessine un cylindre centré en z dans [0, 2*half_t]
        gluCylinder(quad, radius, radius, 2.0 * half_t, slices, 1)

        # Disque arrière (z=0)
        gluDisk(quad, 0.0, radius, slices, 1)

        # Disque avant (z=2*half_t)
        glPushMatrix()
        glTranslatef(0.0, 0.0, 2.0 * half_t)
        gluDisk(quad, 0.0, radius, slices, 1)
        glPopMatrix()

        gluDeleteQuadric(quad)

    def on_mouse_click(self, button, state, x, y):
        if button == 3 and state == GLUT_DOWN:
            self.zoom = max(2.0, self.zoom - 0.5); glutPostRedisplay(); return
        if button == 4 and state == GLUT_DOWN:
            self.zoom += 0.5; glutPostRedisplay(); return
        if button == GLUT_RIGHT_BUTTON:
            self.mouse_drag_zoom = (state == GLUT_DOWN); self.last_mouse = (x, y)
        if button == GLUT_LEFT_BUTTON:
            self.mouse_drag = (state == GLUT_DOWN); self.last_mouse = (x, y)
            if self.use_trackball:
                # réinitialise la séquence de drag du trackball
                self.trackball.prev = None

    def on_mouse_motion(self, x, y):
        if self.mouse_drag_zoom:
            dy = y - self.last_mouse[1]
            self.zoom = max(2.0, self.zoom + dy * 0.05)
        elif self.mouse_drag:
            dx = x - self.last_mouse[0]; dy = y - self.last_mouse[1]
            self.angle_y += dx * 0.5; self.angle_x += dy * 0.5
        self.last_mouse = (x, y); glutPostRedisplay()

# ───────────────────────────────────────────────
# 4)  RESHAPE
# ───────────────────────────────────────────────
def reshape(w, h):
    global app
    h = max(h, 1)
    app.win_w, app.win_h = w, h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(80.0, w / float(h), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    # MAJ trackball pour une projection correcte de la souris
    if hasattr(app, "trackball") and app.trackball:
        app.trackball.win_w, app.trackball.win_h = w, h

# ───────────────────────────────────────────────
# 5)  MAIN
# ───────────────────────────────────────────────
def main():
    global app
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Low-poly Car  Trackball Lights")

    app = Renderer(); app.init_gl()
    glutDisplayFunc(app.render)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(app.on_keys)
    glutMouseFunc(app.on_mouse_click)
    glutMotionFunc(app.on_mouse_motion)
    glutIdleFunc(app.render)
    glutMainLoop()

if __name__ == "__main__":
    main()