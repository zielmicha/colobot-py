from __future__ import division
# RULE: do not modify vector unless you know that no one else will use it
from euclid import Vector3, Vector2, Quaternion
import collections

from OpenGL import GL, GLU, GLUT
from OpenGL.GL import *

Triangle = collections.namedtuple('Triangle',
                                  'a b c na nb nc a_uv b_uv c_uv texture')

class options(object):
    enable_textures = True


class Object(object):
    def __init__(self):
        self.pos = Vector3()

    def _draw(self):
        glPushMatrix()
        glTranslate(self.pos.x, self.pos.y, self.pos.z)
        self._draw_content()
        glPopMatrix()

class TriangleObject(Object):
    def __init__(self, triangles=None):
        super(TriangleObject, self).__init__()
        self.triangles = triangles or []
    
    def _draw_content(self):
        for t in self.triangles:
            texture = t.texture
            if options.enable_textures and texture:
                glBindTexture(GL_TEXTURE_2D, texture.get_id())

            glBegin(GL_TRIANGLES)
                
            glNormal(t.na.x, t.na.y, t.na.z)
            if texture:
                glTexCoord(t.a_uv.x, t.a_uv.y)
            glVertex(t.a.x, t.a.y, t.a.z)

            glNormal(t.nb.x, t.nb.y, t.nb.z)
            if texture:
                glTexCoord(t.b_uv.x, t.b_uv.y)
            glVertex(t.b.x, t.b.y, t.b.z)

            glNormal(t.nc.x, t.nc.y, t.nc.z)
            if texture:
                glTexCoord(t.c_uv.x, t.c_uv.y)
            glVertex(t.c.x, t.c.y, t.c.z)

            glEnd()

class Container(Object):
    def __init__(self):
        super(Container, self).__init__()
        self.objects = []
    
    def _draw_content(self):
        for obj in self.objects:
            obj._draw()

    def add(self, obj):
        self.objects.append(obj)

    def remove(self, obj):
        self.objects.remove(obj)

def wrap(obj):
    ' Wraps object with a container, so its position can be changed without modifing it. '
    c = Container()
    c.add(obj)
    return c

def create_rgbx_texture(data, size):
    return TextureWrapper(data, size)

class TextureWrapper(object):
    def __init__(self, data, size):
        self.size = size
        self.data = data
        self._id = None

    def _load(self):
        w, h = self.size
        self._id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, w, h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, self.data)
        del self.size, self.data

    def get_id(self):
        if self._id == None:
            self._load()
        
        return self._id

class Camera:
    def __init__(self):
        self.center = Vector3(0, 0, 0)
        self.eye = Vector3(2, 2, 2)
        self.up = Vector3(0, 1, 0)

    def _setup(self):
        GLU.gluLookAt(self.eye.x, self.eye.y, self.eye.z,
                      self.center.x, self.center.y, self.center.z,
                      self.up.x, self.up.y, self.up.z)
        distance = abs(self.eye - self.center)
        scale = 1 / distance
        glScale(scale, scale, scale)
    
class Window:
    def __init__(self):
        self.root = Container()
        self.camera = Camera()
        self.event_handler = EventHandler()

    def loop(self):
        self._init()
        GLUT.glutMainLoop()

    def redraw(self):
        GLUT.glutPostRedisplay()
        
    def _init(self):
        GLUT.glutInit()
        GLUT.glutInitWindowSize(640, 480)
        GLUT.glutCreateWindow('3d')
        GLUT.glutInitDisplayMode(GLUT.GLUT_SINGLE | GLUT.GLUT_RGB)
        glClearColor(1, 1, 1, 1)
        GLUT.glutDisplayFunc(self._display)
        GLUT.glutMouseFunc(self._mouse)
        GLUT.glutPassiveMotionFunc(self._motion)
        GLUT.glutMotionFunc(self._motion)
        GLUT.glutMouseWheelFunc(self._mouse_wheel)

    def _mouse(self, button, state, x, y):
        if button == 3:
            self.event_handler.mouse_wheel(1)
        elif button == 4:
            self.event_handler.mouse_wheel(-1)
        else:
            pos = self._window_to_real(x, y)
            if state == GLUT.GLUT_UP:
                self.event_handler.mouse_up(button, pos)
            if state == GLUT.GLUT_DOWN:
                self.event_handler.mouse_down(button, pos)
        self.redraw()

    def _motion(self, x, y):
        self.event_handler.motion(self._window_to_real(x, y))
        self.redraw()

    def _window_to_real(self, x, y):
        return Vector2(x, y)

    def _mouse_wheel(self, button, dir, x, y):
        self.event_handler.mouse_wheel(dir)
        self.redraw()
    
    def _display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
                
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.2, 0.2, 0.2))

        glMatrixMode(GL_PROJECTION)
        #GLU.gluPerspective(90, 1, 0, 1000)
        glLoadIdentity()
        glOrtho(-2.0*64/48.0,2.0*64/48.0,-1.5, 1.5, 0.1, 100)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glClear(GL_COLOR_BUFFER_BIT)
        
        glColor3f(0.0,0.0,0.0)
        glPushMatrix()

        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1))
        glLightfv(GL_LIGHT0, GL_POSITION, (20, 20, 20, 1))
        
        glEnable(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

        self.camera._setup()
        self.root._draw()
        
        glPopMatrix()
        glFlush()

RIGHT_BUTTON = GLUT.GLUT_RIGHT_BUTTON
LEFT_BUTTON  = GLUT.GLUT_LEFT_BUTTON
        
class EventHandler:
    def motion(self, pos):
        pass

    def mouse_down(self, button, pos):
        pass

    def mouse_up(self, button, pos):
        pass

    def mouse_wheel(self, dir):
        pass
