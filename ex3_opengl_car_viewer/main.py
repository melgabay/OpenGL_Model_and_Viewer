import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from car_model import draw_car
from trackball import Trackball

zoom = -6
trackball = Trackball()
show_axes = True
show_lights = True
wireframe = False

def init():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glEnable(GL_NORMALIZE)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glClearColor(0.1, 0.1, 0.1, 1.0)
    setup_lights()

def setup_lights():
    glLightfv(GL_LIGHT0, GL_POSITION, [3, 3, 3, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])
    glLightfv(GL_LIGHT1, GL_POSITION, [-3, 3, 3, 1])
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
    glLightfv(GL_LIGHT1, GL_SPECULAR, [0.8, 0.8, 0.8, 1])

def draw_axes():
    glDisable(GL_LIGHTING)
    glBegin(GL_LINES)
    glColor3f(1,0,0); glVertex3f(0,0,0); glVertex3f(1,0,0)
    glColor3f(0,1,0); glVertex3f(0,0,0); glVertex3f(0,1,0)
    glColor3f(0,0,1); glVertex3f(0,0,0); glVertex3f(0,0,1)
    glEnd()
    glEnable(GL_LIGHTING)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0, 0, zoom)
    trackball.apply()

    if show_axes:
        draw_axes()

    draw_car(wireframe, show_lights)

def reshape(window, w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, w/h if h > 0 else 1, 0.1, 100)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def key_callback(win, key, scancode, action, mods):
    global show_axes, show_lights, wireframe
    if action == glfw.PRESS:
        if key == glfw.KEY_A:
            show_axes = not show_axes
        elif key == glfw.KEY_L:
            show_lights = not show_lights
        elif key == glfw.KEY_P:
            wireframe = not wireframe
            mode = GL_LINE if wireframe else GL_FILL
            glPolygonMode(GL_FRONT_AND_BACK, mode)

def scroll_callback(win, xoff, yoff):
    global zoom
    zoom += yoff * 0.5

def cursor_callback(win, xpos, ypos):
    if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
        trackball.drag(xpos, ypos)

def main():
    if not glfw.init(): return
    win = glfw.create_window(800, 600, "OpenGL Car Viewer", None, None)
    if not win: glfw.terminate(); return
    glfw.make_context_current(win)

    glfw.set_key_callback(win, key_callback)
    glfw.set_scroll_callback(win, scroll_callback)
    glfw.set_cursor_pos_callback(win, cursor_callback)
    glfw.set_window_size_callback(win, reshape)

    init()
    while not glfw.window_should_close(win):
        display()
        glfw.swap_buffers(win)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()
