' Camera drivers for interactive model viewing. '
import g3d
import math

from g3d import Vector2, Vector3

class CameraDriver(g3d.EventHandler):
    def __init__(self):
        self.camera = g3d.Camera()
    
    def install(self, window):
        window.camera = self.camera
        window.event_handler = self

class LookAtCameraDriver(CameraDriver):
    ''' Camera is on sphere with object in its center, always pointed on it. '''
    def __init__(self, radius=5, look_at=Vector3(0, 0, 0)):
        CameraDriver.__init__(self)
        self.radius = radius
        self.last_pos = None

        assert look_at == Vector3(0, 0, 0), 'look_at != (0, 0, 0) not yet supported'
        
        self.camera.center = look_at
        self.camera.eye = Vector2()
        self.spherical = Vector2(0, 0)

        self._update()
    
    def motion(self, pos):
        if self.last_pos is not None:
            delta = pos - self.last_pos
            delta /= 30.
            self.spherical += delta
            self._update()

            self.last_pos = pos

    def _update(self):
        # TODO: handle cases when look_at != (0, 0)
        self.camera.eye = Vector3(
            self.radius * math.sin(self.spherical.x) * math.cos(self.spherical.y),
            self.radius * math.sin(self.spherical.x) * math.sin(self.spherical.y),
            self.radius * math.cos(self.spherical.x),
        )
            
    def mouse_down(self, button, pos):
        self.last_pos = pos

    def mouse_up(self, button, pos):
        self.last_pos = None
