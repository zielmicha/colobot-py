from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import Image

def axis(length):
    """ Draws an axis (basicly a line with a cone on top) """
    glPushMatrix()
    glBegin(GL_LINES)
    glVertex3d(0,0,0)
    glVertex3d(0,0,length)
    glEnd()
    glTranslated(0,0,length)
    glutWireCone(0.04,0.2, 12, 9)
    glPopMatrix()
    
def threeAxis(length):
    """ Draws an X, Y and Z-axis """ 
    
    glPushMatrix()
    # Z-axis
    glColor3f(1.0,0.0,0.0)
    axis(length)
    # X-axis
    glRotated(90,0,1.0,0)
    glColor3f(0.0,1.0,0.0)
    axis(length)
    # Y-axis
    glRotated(-90,1.0,0,0)
    glColor3f(0.0,0.0,1.0)
    axis(length)
    glPopMatrix()
    
def displayFun():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    light = True
    if light:
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)
    #glEnable(GL_COLOR_MATERIAL)
    #glShadeModel(GL_SMOOTH)

    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.2, 0.2, 0.2))
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-2.0*64/48.0,2.0*64/48.0,-1.5, 1.5, 0.1, 100)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(2.0, 2.0, 2.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    #glRotate(*rotate)

    
    glClear(GL_COLOR_BUFFER_BIT)
    threeAxis(0.5)
    
    glColor3f(0.0,0.0,0.0)
    glPushMatrix()
    glTranslated(0.5,0.5,0.5);

    if light:
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1))
        glLightfv(GL_LIGHT0, GL_POSITION, (20, 20, 20, 1))
    

    s = 0.05
    glScale(s, s, s)

    tex = True
    
    if tex:
        glEnable(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

    if tex_cache == None:
        initTexCache()
        
    for t in triangles:
        if tex: glBindTexture(GL_TEXTURE_2D, tex_cache[t.tex_name])

        glBegin(GL_TRIANGLES)
        
        glNormal(*t.na)
        if tex: glTexCoord(*t.a_uv)
        glVertex(*t.a)
        
        glNormal(*t.nb)
        if tex: glTexCoord(*t.b_uv)
        glVertex(*t.b)
        
        glNormal(*t.nc)
        if tex: glTexCoord(*t.c_uv)
        glVertex(*t.c)
    
        glEnd()

    
    #glPolygonMode( GL_FRONT_AND_BACK, GL_LINE );

    #glBegin(GL_TRIANGLES)

    #for t in triangles:
    #    glVertex(*t.a)
    #    glVertex(*t.b)
    #    glVertex(*t.c)
        
    #glEnd()
    
    #glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
    
    glPopMatrix()
    glFlush()

start_pos = None
rotate = [0,0,0]

def mouseFun(button,state,x,y):
    global start_pos
    if state == GLUT_DOWN:
        start_pos = x,y
    elif state == GLUT_UP:
        start_pos = None
    glutPostRedisplay()

def motionFun(x, y):
    if start_pos:
        sx, sy = start_pos

def initTexCache():
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_TEXTURE_2D)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

    global tex_cache
    tex_cache = {}
    
    id = 1
    for t in triangles:
        if t.tex_name not in tex_cache:
            print t.a_uv, t.b_uv
            im = Image.open(tex_files.open(t.tex_name))
            iw, ih = im.size
            image = im.tostring('raw', 'RGBX', 0, -1)
            id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, id)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexImage2D(GL_TEXTURE_2D, 0, 3, iw, ih, 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, image)
            tex_cache[t.tex_name] = id

    print tex_cache
        
if __name__ == '__main__':
    import OpenGL
    OpenGL.FULL_LOGGING = True
    
    import sys, metafile, modfile
    f = metafile.MetaFile(metafile.cipher_keys['full'], open('colobot.data/colobot2.dat'))

    tex_files = metafile.MetaFile(metafile.cipher_keys['full'], open('colobot.data/colobot1.dat'))
    
    inp = f.open(sys.argv[1] if sys.argv[1:] else 'keyb.mod')
    triangles = list(modfile.load_modfile(inp))

    tex_cache = None
    
    glutInit()

            
    glutInitWindowSize(640,480)
    glutCreateWindow("3D")
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glClearColor(1.0,1.0,1.0,0.0)
    glutDisplayFunc(displayFun)
    glutMouseFunc(mouseFun)
    glutMotionFunc(motionFun)
    glutMainLoop()
