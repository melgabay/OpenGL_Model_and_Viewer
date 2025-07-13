from OpenGL.GL import *
import numpy as np

class Trackball:
    def __init__(self):
        self.prev = None
        self.rot = np.identity(4)

    def _project(self, x, y):
        x = 2.0 * x / 800 - 1
        y = 1 - 2.0 * y / 600
        z2 = 1.0 - x*x - y*y
        z = np.sqrt(z2) if z2 > 0 else 0.0
        return np.array([x, y, z])

    def drag(self, x, y):
        curr = self._project(x, y)
        if self.prev is None:
            self.prev = curr
            return
        axis = np.cross(self.prev, curr)
        angle = np.arccos(np.clip(np.dot(self.prev, curr), -1, 1))
        self.prev = curr
        self.rot = np.dot(self.rotation_matrix(axis, np.degrees(angle)), self.rot)

    def apply(self):
        glMultMatrixf(self.rot.T)

    def rotation_matrix(self, axis, angle):
        axis = axis / np.linalg.norm(axis)
        a = np.radians(angle)
        c = np.cos(a)
        s = np.sin(a)
        x, y, z = axis
        R = np.array([
            [c + x*x*(1-c), x*y*(1-c) - z*s, x*z*(1-c) + y*s, 0],
            [y*x*(1-c) + z*s, c + y*y*(1-c), y*z*(1-c) - x*s, 0],
            [z*x*(1-c) - y*s, z*y*(1-c) + x*s, c + z*z*(1-c), 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        return R
