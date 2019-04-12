#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Impressive, a fancy presentation tool
# Copyright (C) 2005-2014 Martin J. Fiedler <martin.fiedler@gmx.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

__title__   = "Impressive"
__version__ = "0.11.1"
__rev__     = 186
__author__  = "Martin J. Fiedler"
__email__   = "martin.fiedler@gmx.net"
__website__ = "http://impressive.sourceforge.net/"

import sys
if __rev__ and (("WIP" in __version__) or ("rc" in __version__) or ("alpha" in __version__) or ("beta" in __version__)):
    __version__ += " (SVN r%s)" % __rev__
def greet():
    print >>sys.stderr, "Welcome to", __title__, "version", __version__
if __name__ == "__main__":
    greet()


TopLeft, BottomLeft, TopRight, BottomRight, TopCenter, BottomCenter = range(6)
NoCache, MemCache, CompressedCache, FileCache, PersistentCache = range(5)  # for CacheMode
Off, First, Last = range(3)  # for AutoOverview

# You may change the following lines to modify the default settings
Verbose = False
Fullscreen = True
FakeFullscreen = False
Scaling = False
Supersample = None
BackgroundRendering = True
PDFRendererPath = None
UseAutoScreenSize = True
ScreenWidth = 1024
ScreenHeight = 768
WindowPos = None
TransitionDuration = 1000
MouseHideDelay = 3000
BoxFadeDuration = 100
ZoomDuration = 250
BlankFadeDuration = 250
BoxFadeBlur = 1.5
BoxFadeDarkness = 0.25
BoxFadeDarknessStep = 0.05
MarkColor = (1.0, 0.0, 0.0, 0.1)
BoxEdgeSize = 4
SpotRadius = 64
MinSpotDetail = 13
SpotDetail = 12
CacheMode = FileCache
HighQualityOverview = True
OverviewBorder = 3
OverviewLogoBorder = 24
AutoOverview = Off
InitialPage = None
Wrap = False
AutoAdvance = None
AutoAutoAdvance = False
RenderToDirectory = None
Rotation = 0
DAR = None
PAR = 1.0
Overscan = 3
PollInterval = 0
PageRangeStart = 0
PageRangeEnd = 999999
FontSize = 14
FontTextureWidth = 512
FontTextureHeight = 256
Gamma = 1.0
BlackLevel = 0
GammaStep = 1.1
BlackLevelStep = 8
EstimatedDuration = None
PageProgress = False
AutoAdvanceProgress = False
ProgressBarSizeFactor = 0.02
ProgressBarAlpha = 0.5
ProgressBarColorNormal = (0.0, 1.0, 0.0)
ProgressBarColorWarning = (1.0, 1.0, 0.0)
ProgressBarColorCritical = (1.0, 0.0, 0.0)
ProgressBarColorPage = (0.0, 0.5, 1.0)
ProgressBarWarningFactor = 1.25
ProgressBarCriticalFactor = 1.5
CursorImage = None
CursorHotspot = (0, 0)
MinutesOnly = False
OSDMargin = 16
OSDAlpha = 1.0
OSDTimePos = TopRight
OSDTitlePos = BottomLeft
OSDPagePos = BottomRight
OSDStatusPos = TopLeft
ZoomFactor = 2
FadeInOut = False
ShowLogo = True
Shuffle = False
QuitAtEnd = False
ShowClock = False
HalfScreen = False
InvertPages = False
MinBoxSize = 20
UseBlurShader = True
TimeTracking = False
EventTestMode = False


# import basic modules
import random, getopt, os, types, re, codecs, tempfile, glob, cStringIO, re
import traceback, subprocess, time, itertools, ctypes.util, zlib, urllib
from math import *
from ctypes import *

# import hashlib for MD5 generation, but fall back to old md5 lib if unavailable
# (this is the case for Python versions older than 2.5)
try:
    import hashlib
    md5obj = hashlib.md5
except ImportError:
    import md5
    md5obj = md5.new

# initialize some platform-specific settings
if os.name == "nt":
    root = os.path.split(sys.argv[0])[0] or "."
    _find_paths = [root, os.path.join(root, "win32"), os.path.join(root, "gs")] + filter(None, os.getenv("PATH").split(';'))
    def FindBinary(binary):
        if not binary.lower().endswith(".exe"):
            binary += ".exe"
        for p in _find_paths:
            path = os.path.join(p, binary)
            if os.path.isfile(path):
                return path
        return binary  # fall-back if not found
    pdftkPath = FindBinary("pdftk.exe")
    GhostScriptPlatformOptions = ["-I" + os.path.join(root, "gs")]
    try:
        import win32api
        HaveWin32API = True
        MPlayerPath = FindBinary("mplayer.exe")
        def RunURL(url):
            win32api.ShellExecute(0, "open", url, "", "", 0)
    except ImportError:
        HaveWin32API = False
        MPlayerPath = ""
        def RunURL(url): print "Error: cannot run URL `%s'" % url
    MPlayerPlatformOptions = [ "-colorkey", "0x000000" ]
    MPlayerColorKey = True
    if getattr(sys, "frozen", False):
        sys.path.append(root)
    FontPath = []
    FontList = ["Verdana.ttf", "Arial.ttf"]
    Nice = []
else:
    def FindBinary(x): return x
    GhostScriptPlatformOptions = []
    MPlayerPath = "mplayer"
    MPlayerPlatformOptions = [ "-vo", "gl" ]
    MPlayerColorKey = False
    pdftkPath = "pdftk"
    FontPath = ["/usr/share/fonts", "/usr/local/share/fonts", "/usr/X11R6/lib/X11/fonts/TTF"]
    FontList = ["DejaVuSans.ttf", "Vera.ttf", "Verdana.ttf"]
    Nice = ["nice", "-n", "7"]
    def RunURL(url):
        try:
            subprocess.Popen(["xdg-open", url])
        except OSError:
            print >>sys.stderr, "Error: cannot open URL `%s'" % url

# import special modules
try:
    import pygame
    from pygame.locals import *
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps
    from PIL import TiffImagePlugin, BmpImagePlugin, JpegImagePlugin, PngImagePlugin, PpmImagePlugin
except (ValueError, ImportError), err:
    print >>sys.stderr, "Oops! Cannot load necessary modules:", err
    print >>sys.stderr, """To use Impressive, you need to install the following Python modules:
 - PyGame   [python-pygame]   http://www.pygame.org/
 - PIL      [python-imaging]  http://www.pythonware.com/products/pil/
   or Pillow                  http://pypi.python.org/pypi/Pillow/
 - PyWin32  (OPTIONAL, Win32) http://sourceforge.net/projects/pywin32/
Additionally, please be sure to have pdftoppm or GhostScript installed if you
intend to use PDF input."""
    sys.exit(1)

try:
    import thread
    HaveThreads = True
    def create_lock(): return thread.allocate_lock()
    def get_thread_id(): return thread.get_ident()
except ImportError:
    HaveThreads = False
    class pseudolock:
        def __init__(self): self.state = False
        def acquire(self, dummy=0): self.state = True
        def release(self): self.state = False
        def locked(self): return self.state
    def create_lock(): return pseudolock()
    def get_thread_id(): return 0xDEADC0DE

CleanExit = False


##### GLOBAL VARIABLES #########################################################

# initialize private variables
DocumentTitle = None
FileName = ""
FileList = []
InfoScriptPath = None
AvailableRenderers = []
PDFRenderer = None
BaseWorkingDir = '.'
Marking = False
Tracing = False
Panning = False
FileProps = {}
PageProps = {}
PageCache = {}
CacheFile = None
CacheFileName = None
CacheFilePos = 0
CacheMagic = ""
MPlayerProcess = None
VideoPlaying = False
MarkValid, MarkBaseX, MarkBaseY = False, 0, 0
PanValid, PanBaseX, PanBaseY = False, 0, 0
MarkUL = (0, 0)
MarkLR = (0, 0)
ZoomX0 = 0.0
ZoomY0 = 0.0
ZoomArea = 1.0
ZoomMode = False
IsZoomed = False
HighResZoomFailed = False
TransitionRunning = False
TransitionPhase = 0.0
CurrentCaption = 0
OverviewNeedUpdate = False
FileStats = None
OSDFont = None
CurrentOSDCaption = ""
CurrentOSDPage = ""
CurrentOSDStatus = ""
CurrentOSDComment = ""
Lrender = create_lock()
Lcache = create_lock()
Loverview = create_lock()
RTrunning = False
RTrestart = False
StartTime = 0
CurrentTime = 0
PageEnterTime = 0
PageLeaveTime = 0
PageTimeout = 0
TimeDisplay = False
FirstPage = True
ProgressBarPos = 0
CursorVisible = True
OverviewMode = False
LastPage = 0
WantStatus = False
GLVendor = ""
GLRenderer = ""
GLVersion = ""
RequiredShaders = []
DefaultScreenTransform = (-1.0, 1.0, 2.0, -2.0)
ScreenTransform = DefaultScreenTransform
SpotVertices = None
SpotIndices = None
CallQueue = []

# tool constants (used in info scripts)
FirstTimeOnly = 2


##### PLATFORM-SPECIFIC PYGAME INTERFACE CODE ##################################

class Platform_PyGame(object):
    name = 'pygame'
    allow_custom_fullscreen_res = True
    has_hardware_cursor = True

    _buttons = { 1: "lmb", 2: "mmb", 3: "rmb", 4: "wheelup", 5: "wheeldown" }
    _keys = dict((getattr(pygame.locals, k), k[2:].lower()) for k in [k for k in dir(pygame.locals) if k.startswith('K_')])

    def __init__(self):
        self.next_event = None
        self.schedule_map_ev2flag = {}
        self.schedule_map_ev2name = {}
        self.schedule_map_name2ev = {}
        self.schedule_max = USEREVENT

    def Init(self):
        pygame.display.init()

    def GetTicks(self):
        return pygame.time.get_ticks()

    def GetScreenSize(self):
        return pygame.display.list_modes()[0]

    def StartDisplay(self):
        global ScreenWidth, ScreenHeight, Fullscreen, FakeFullscreen, WindowPos
        pygame.display.set_caption(__title__)
        flags = OPENGL | DOUBLEBUF
        if Fullscreen:
            if FakeFullscreen:
                print >>sys.stderr, "Using \"fake-fullscreen\" mode."
                flags |= NOFRAME
                if not WindowPos:
                    WindowPos = (0,0)
            else:
                flags |= FULLSCREEN
        if WindowPos:
            os.environ["SDL_VIDEO_WINDOW_POS"] = ','.join(map(str, WindowPos))
        pygame.display.set_mode((ScreenWidth, ScreenHeight), flags)
        pygame.key.set_repeat(500, 30)

    def LoadOpenGL(self):
        try:
            sdl = CDLL(ctypes.util.find_library("SDL") or ctypes.util.find_library("SDL-1.2") or "SDL", RTLD_GLOBAL)
            get_proc_address = CFUNCTYPE(c_void_p, c_char_p)(('SDL_GL_GetProcAddress', sdl))
        except OSError:
            raise ImportError("failed to load the SDL library")
        except AttributeError:
            raise ImportError("failed to load SDL_GL_GetProcAddress from the SDL library")
        def loadsym(name, prototype):
            try:
                addr = get_proc_address(name)
            except EnvironmentError:
                return None
            if not addr:
                return None
            return prototype(addr)
        return OpenGL(loadsym, desktop=True)

    def SwapBuffers(self):
        pygame.display.flip()

    def Done(self):
        pygame.display.quit()
    def Quit(self):
        pygame.quit()

    def SetWindowTitle(self, text):
        pygame.display.set_caption(text, __title__)
    def GetWindowID(self):
        return pygame.display.get_wm_info()['window']

    def GetMousePos(self):
        return pygame.mouse.get_pos()
    def SetMousePos(self, coords):
        pygame.mouse.set_pos(coords)
    def SetMouseVisible(self, visible):
        pygame.mouse.set_visible(visible)

    def _translate_mods(self, key, mods):
        if mods & KMOD_SHIFT:
            key = "shift+" + key
        if mods & KMOD_ALT:
            key = "alt+" + key
        if mods & KMOD_CTRL:
            key = "ctrl+" + key
        return key
    def _translate_button(self, ev):
        try:
            return self._translate_mods(self._buttons[ev.button], pygame.key.get_mods())
        except KeyError:
            return 'unknown-button-' + str(ev.button)
    def _translate_key(self, ev):
        try:
            return self._translate_mods(self._keys[ev.key], ev.mod)
        except KeyError:
            return 'unknown-key-' + str(ev.key)

    def GetEvent(self, poll=False):
        if self.next_event:
            ev = self.next_event
            self.next_event = None
            return ev
        if poll:
            ev = pygame.event.poll()
        else:
            ev = pygame.event.wait()
        if ev.type == NOEVENT:
            return None
        elif ev.type == QUIT:
            return "$quit"
        elif ev.type == VIDEOEXPOSE:
            return "$expose"
        elif ev.type == MOUSEBUTTONDOWN:
            return '+' + self._translate_button(ev)
        elif ev.type == MOUSEBUTTONUP:
            ev = self._translate_button(ev)
            self.next_event = '-' + ev
            return '*' + ev
        elif ev.type == MOUSEMOTION:
            pygame.event.clear(MOUSEMOTION)
            return "$move"
        elif ev.type == KEYDOWN:
            if ev.mod & KMOD_ALT:
                if ev.key == K_F4:
                    return self.PostQuitEvent()
                elif ev.key == K_TAB:
                    return "$alt-tab"
            ev = self._translate_key(ev)
            self.next_event = '*' + ev
            return '+' + ev
        elif ev.type == KEYUP:
            return '-' + self._translate_key(ev)
        elif (ev.type >= USEREVENT) and (ev.type < self.schedule_max):
            if not(self.schedule_map_ev2flag.get(ev.type)):
                pygame.time.set_timer(ev.type, 0)
            return self.schedule_map_ev2name.get(ev.type)
        else:
            return "$?"

    def CheckAnimationCancelEvent(self):
        return bool(pygame.event.get([KEYDOWN, MOUSEBUTTONUP]))

    def ScheduleEvent(self, name, msec=0, periodic=False):
        try:
            ev_code = self.schedule_map_name2ev[name]
        except KeyError:
            ev_code = self.schedule_max
            self.schedule_map_name2ev[name] = ev_code
            self.schedule_map_ev2name[ev_code] = name
            self.schedule_max += 1
        self.schedule_map_ev2flag[ev_code] = periodic
        pygame.time.set_timer(ev_code, msec)

    def PostQuitEvent(self):
        pygame.event.post(pygame.event.Event(QUIT))

    def ToggleFullscreen(self):
        return pygame.display.toggle_fullscreen()

    def Minimize(self):
        pygame.display.iconify()

    def SetGammaRamp(self, gamma, black_level):
        scale = 1.0 / (255 - black_level)
        power = 1.0 / gamma
        ramp = [int(65535.0 * ((max(0, x - black_level) * scale) ** power)) for x in range(256)]
        return pygame.display.set_gamma_ramp(ramp, ramp, ramp)


class Platform_Win32(Platform_PyGame):
    name = 'pygame-win32'

    def GetScreenSize(self):
        if HaveWin32API:
            dm = win32api.EnumDisplaySettings(None, -1) #ENUM_CURRENT_SETTINGS
            return (int(dm.PelsWidth), int(dm.PelsHeight))
        return Platform_PyGame.GetScreenSize(self)

    def LoadOpenGL(self):
        try:
            opengl32 = WinDLL("opengl32")
            get_proc_address = WINFUNCTYPE(c_void_p, c_char_p)(('wglGetProcAddress', opengl32))
        except OSError:
            raise ImportError("failed to load the OpenGL library")
        except AttributeError:
            raise ImportError("failed to load wglGetProcAddress from the OpenGL library")
        def loadsym(name, prototype):
            # try to load OpenGL 1.1 function from opengl32.dll first
            try:
                return prototype((name, opengl32))
            except AttributeError:
                pass
            # if that fails, load the extension function via wglGetProcAddress
            try:
                addr = get_proc_address(name)
            except EnvironmentError:
                addr = None
            if not addr:
                return None
            return prototype(addr)
        return OpenGL(loadsym, desktop=True)


class Platform_Unix(Platform_PyGame):
    name = 'pygame-unix'

    def GetScreenSize(self):
        re_res = re.compile(r'\s*(\d+)x(\d+)\s+\d+\.\d+\*')
        res = None
        try:
            xrandr = subprocess.Popen(["xrandr"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in xrandr.stdout:
                m = re_res.match(line)
                if m:
                    res = tuple(map(int, m.groups()))
            xrandr.wait()
        except OSError:
            pass
        if res:
            return res
        return Platform_PyGame.GetScreenSize(self)


class Platform_EGL(Platform_Unix):
    name = 'egl'

    def StartDisplay(self, display=None, window=None, width=None, height=None):
        global ScreenWidth, ScreenHeight
        width  = width  or ScreenWidth
        height = height or ScreenHeight

        # load the GLESv2 library before the EGL library (required on the BCM2835)
        try:
            self.gles = ctypes.CDLL(ctypes.util.find_library("GLESv2"))
        except OSError:
            raise ImportError("failed to load the OpenGL ES 2.0 library")

        # import all functions first
        try:
            egl = CDLL(ctypes.util.find_library("EGL"))
            def loadfunc(func, ret, *args):
                return CFUNCTYPE(ret, *args)((func, egl))
            eglGetDisplay = loadfunc("eglGetDisplay", c_void_p, c_void_p)
            eglInitialize = loadfunc("eglInitialize", c_uint, c_void_p, POINTER(c_int), POINTER(c_int))
            eglChooseConfig = loadfunc("eglChooseConfig", c_uint, c_void_p, c_void_p, POINTER(c_void_p), c_int, POINTER(c_int))
            eglCreateWindowSurface = loadfunc("eglCreateWindowSurface", c_void_p, c_void_p, c_void_p, c_void_p, c_void_p)
            eglCreateContext = loadfunc("eglCreateContext", c_void_p, c_void_p, c_void_p, c_void_p, c_void_p)
            eglMakeCurrent = loadfunc("eglMakeCurrent", c_uint, c_void_p, c_void_p, c_void_p, c_void_p)
            self.eglSwapBuffers = loadfunc("eglSwapBuffers", c_int, c_void_p, c_void_p)
        except OSError:
            raise ImportError("failed to load the EGL library")
        except AttributeError:
            raise ImportError("failed to load required symbols from the EGL library")

        # prepare parameters
        config_attribs = [
            0x3024, 8,      # EGL_RED_SIZE >= 8
            0x3023, 8,      # EGL_GREEN_SIZE >= 8
            0x3022, 8,      # EGL_BLUE_SIZE >= 8
            0x3021, 0,      # EGL_ALPHA_SIZE >= 0
            0x3025, 0,      # EGL_DEPTH_SIZE >= 0
            0x3040, 0x0004, # EGL_RENDERABLE_TYPE = EGL_OPENGL_ES2_BIT
            0x3033, 0x0004, # EGL_SURFACE_TYPE = EGL_WINDOW_BIT
            0x3038          # EGL_NONE
        ]
        context_attribs = [
            0x3098, 2,      # EGL_CONTEXT_CLIENT_VERSION = 2
            0x3038          # EGL_NONE
        ]
        config_attribs = (c_int * len(config_attribs))(*config_attribs)
        context_attribs = (c_int * len(context_attribs))(*context_attribs)

        # perform actual initialization
        eglMakeCurrent(None, None, None, None)
        self.egl_display = eglGetDisplay(display)
        if not self.egl_display:
            raise RuntimeError("could not get EGL display")
        if not eglInitialize(self.egl_display, None, None):
            raise RuntimeError("could not initialize EGL")
        config = c_void_p()
        num_configs = c_int(0)
        if not eglChooseConfig(self.egl_display, config_attribs, byref(config), 1, byref(num_configs)):
            raise RuntimeError("failed to get a framebuffer configuration")
        if not num_configs.value:
            raise RuntimeError("no suitable framebuffer configuration found")
        self.egl_surface = eglCreateWindowSurface(self.egl_display, config, window, None)
        if not self.egl_surface:
            raise RuntimeError("could not create EGL surface")
        context = eglCreateContext(self.egl_display, config, None, context_attribs)
        if not context:
            raise RuntimeError("could not create OpenGL ES rendering context")
        if not eglMakeCurrent(self.egl_display, self.egl_surface, self.egl_surface, context):
            raise RuntimeError("could not activate OpenGL ES rendering context")

    def LoadOpenGL(self):
        def loadsym(name, prototype):
            return prototype((name, self.gles))
        return OpenGL(loadsym, desktop=False)

    def SwapBuffers(self):
        self.eglSwapBuffers(self.egl_display, self.egl_surface)


class Platform_BCM2835(Platform_EGL):
    name = 'bcm2835'
    allow_custom_fullscreen_res = False
    has_hardware_cursor = False
    DISPLAY_ID = 0

    def __init__(self, libbcm_host):
        Platform_EGL.__init__(self)
        self.libbcm_host_path = libbcm_host

    def Init(self):
        try:
            self.bcm_host = CDLL(self.libbcm_host_path)
            def loadfunc(func, ret, *args):
                return CFUNCTYPE(ret, *args)((func, self.bcm_host))
            bcm_host_init = loadfunc("bcm_host_init", None)
            graphics_get_display_size = loadfunc("graphics_get_display_size", c_int32, c_uint16, POINTER(c_uint32), POINTER(c_uint32))
        except OSError:
            raise ImportError("failed to load the bcm_host library")
        except AttributeError:
            raise ImportError("failed to load required symbols from the bcm_host library")
        bcm_host_init()
        x, y = c_uint32(0), c_uint32(0)
        if graphics_get_display_size(self.DISPLAY_ID, byref(x), byref(y)) < 0:
            raise RuntimeError("could not determine display size")
        self.screen_size = (int(x.value), int(y.value))

    def GetScreenSize(self):
        return self.screen_size

    def StartDisplay(self):
        global ScreenWidth, ScreenHeight, Fullscreen, FakeFullscreen, WindowPos
        class VC_DISPMANX_ALPHA_T(Structure):
            _fields_ = [("flags", c_int), ("opacity", c_uint32), ("mask", c_void_p)]
        class EGL_DISPMANX_WINDOW_T(Structure):
            _fields_ = [("element", c_uint32), ("width", c_int), ("height", c_int)]

        # first, import everything
        try:
            def loadfunc(func, ret, *args):
                return CFUNCTYPE(ret, *args)((func, self.bcm_host))
            vc_dispmanx_display_open = loadfunc("vc_dispmanx_display_open", c_uint32, c_uint32)
            vc_dispmanx_update_start = loadfunc("vc_dispmanx_update_start", c_uint32, c_int32)
            vc_dispmanx_element_add = loadfunc("vc_dispmanx_element_add", c_int32,
                c_uint32, c_uint32, c_int32,  # update, display, layer
                c_void_p, c_uint32, c_void_p, c_uint32,  # dest_rect, src, drc_rect, protection
                POINTER(VC_DISPMANX_ALPHA_T),  # alpha
                c_void_p, c_uint32)  # clamp, transform
            vc_dispmanx_update_submit_sync = loadfunc("vc_dispmanx_update_submit_sync", c_int, c_uint32)
        except AttributeError:
            raise ImportError("failed to load required symbols from the bcm_host library")

        # sanitize arguments
        width  = min(ScreenWidth,  self.screen_size[0])
        height = min(ScreenHeight, self.screen_size[1])
        if WindowPos:
            x0, y0 = WindowPos
        else:
            x0 = (self.screen_size[0] - width)  / 2
            y0 = (self.screen_size[1] - height) / 2
        x0 = max(min(x0, self.screen_size[0] - width),  0)
        y0 = max(min(y0, self.screen_size[1] - height), 0)

        # prepare arguments
        dst_rect = (c_int32 * 4)(x0, y0, width, height)
        src_rect = (c_int32 * 4)(0, 0, width << 16, height << 16)
        alpha = VC_DISPMANX_ALPHA_T(1, 255, None)  # DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS

        # perform initialization
        display = vc_dispmanx_display_open(self.DISPLAY_ID)
        update = vc_dispmanx_update_start(0)
        layer = vc_dispmanx_element_add(update, display, 0, byref(dst_rect), 0, byref(src_rect), 0, byref(alpha), None, 0)
        vc_dispmanx_update_submit_sync(update)
        self.window = EGL_DISPMANX_WINDOW_T(layer, width, height)
        Platform_EGL.StartDisplay(self, None, byref(self.window), width, height)

        # finally, tell PyGame what just happened
        pygame.display.set_mode((width, height), 0)
        pygame.mouse.set_pos((width / 2, height / 2))


libbcm_host = ctypes.util.find_library("bcm_host")
if libbcm_host:
    Platform = Platform_BCM2835(libbcm_host)
elif os.name == "nt":
    Platform = Platform_Win32()
else:
    Platform = Platform_Unix()


##### TOOL CODE ################################################################

# read and write the PageProps and FileProps meta-dictionaries
def GetProp(prop_dict, key, prop, default=None):
    if not key in prop_dict: return default
    if type(prop) == types.StringType:
        return prop_dict[key].get(prop, default)
    for subprop in prop:
        try:
            return prop_dict[key][subprop]
        except KeyError:
            pass
    return default
def SetProp(prop_dict, key, prop, value):
    if not key in prop_dict:
        prop_dict[key] = {prop: value}
    else:
        prop_dict[key][prop] = value
def DelProp(prop_dict, key, prop):
    try:
        del prop_dict[key][prop]
    except KeyError:
        pass

def GetPageProp(page, prop, default=None):
    global PageProps
    return GetProp(PageProps, page, prop, default)
def SetPageProp(page, prop, value):
    global PageProps
    SetProp(PageProps, page, prop, value)
def DelPageProp(page, prop):
    global PageProps
    DelProp(PageProps, page, prop)
def GetTristatePageProp(page, prop, default=0):
    res = GetPageProp(page, prop, default)
    if res != FirstTimeOnly: return res
    return (GetPageProp(page, '_shown', 0) == 1)

def GetFileProp(page, prop, default=None):
    global FileProps
    return GetProp(FileProps, page, prop, default)
def SetFileProp(page, prop, value):
    global FileProps
    SetProp(FileProps, page, prop, value)

# the Impressive logo (256x64 pixels grayscale PNG)
LOGO = """iVBORw0KGgoAAAANSUhEUgAAAQAAAABACAAAAADQNvZiAAAL8ElEQVR4Xu2Ze1hVVfrHv+cc7siAEiF4AW1QEkmD8pJUWlkaaSWWk9pk5ZT5szKvPydvoVhqKuWY9jhkmjZpmZmO9wwzLwhiCImAeEFEkJtyk/se17tZ66yz9zlp+IcPD3z++Z79ujxrne963/XupWjytNCCy5QtuXm/vueAxmBAk8dnWyhpWkhFszTA7VR7qMy
ajz+PEUS/RXO7omnyDP/9eBKNNuCdg1Pn/PYUmiQR4HRutAEeiwyA0yo0RVwGg1PYaAO6OQKAfys0Qbq6gHO60QacVQCgoAxNkPa4PQPsmOQumQIoU9BI5gYCyHy/CRuAqb8Pq4jZi0byakcA36MpG4Avv0SjcaQ1ZNxxA5S0xnWB26YTfccZ3Bl8wMmquEMG/BV3MgPcwTmJZmnAX8D55U4ZcA+T8hwArd3xJ3H0gnU8nGENVzfbGRCLW8Xe2
2BpQN/+NwgE0ZV9DgMRPGHp11Gj3SGwD5+8KubtMKM+AwrHLNmdU3S1Mml2F+0K+zPaAHAY/fH6mY+D4/X2ocLKK3nb5z4CS3quPphXXJaxZf6TkPH75KeLpSUXdix+wWQtA0pOMAljk3WChAvN30GMf3Xflarcor0LnobAWKncYAmIbexzOgDD6CMKkTOczzX1okLs84FEhmJB3edekImgaAjw6Dn24Te+rsU1CifaHmY8V9YpnKNmC5znVoh
w2kixBSYR/C8Yx9nDRkjMoEXdC8JuernC+aYVz4AOjtIxHsAkDfDf91UfED7fqg4MOL2oPYjHk7pBYOevKao3knvoj4h0dP1BHtgneYodOO8eaA+O76lxRnB67z74CAjnuDnO4HTZkCw2RVMBR+ivwYzbFCbfpKrpHf+RCzgj4oPIAFqiMMDUSTXgheTHIFh5N2CKlPbdaykEHe2gwTu2j9aAnDLP7R4wE7a3MyT6Jt4NFcOX9EkQ9imIRcGQ6
bbexhFwmIrFG4J3WfHVRarG/dwTEoFxQXoDOjowOT2W8iN71yUw7hoL47pZRqA2eUcOGE8NEhs+h+RE9Ai/Li8uOAWGxxZvjQFp9puZcvrupPSr3LXwn5tyyNF5UHlnIIjCUsgMmgCipNhWEyhNFBkgp4D7JCZfp9ELy37awrr90dO+OktH6lIQi1lFVJvAGKgwNrPIpgcNMMyl51h8dkOuR3sDppUUWcsL4GuF8Afh+HE9Pe6BgM6NlTEsys8
Ad4opv3alHN3CwrXBIBJp0L86whQ6cXO5ODPUWTYGwhD05vqCG+FKqDysNLADKrksEAXOHPpyMt8ujgam9KJGoP4M9SSkFaSDGM8XWt3geTw9LGMjAsBwukKLh8oqhagSdftYJQXC+bMTOXLhRihz6aB2Izf8BGAtDdlpBGHYw572qn5Wyuvv+D034HfaEai0/qxOGBDODZgGFbJzn+imV9njGu4FM5T319XsKZXqN1lycJmicomX8VQ+w0FPq
KxngVwQwxWV0xBEKbJBCOKOnhTlOoAC59uIA5Ge6VztTh99wRl8hgxwqmXhx8B54Bg3YCQ3gGf9NBa4xvcjkj3V0HnThbrO1XvA3a2iFDACBoqdkc9sFA08yjMYKhufKIRKFhNvmqLDauzN0NwEFmQz6ecHiy/ExcHX0MBkkneK+PPRFCbUqLzB6ATOzu6LmXiaLMMJfd7SdIGy41A5QtFAEG3eZbL2LM1Hmz07U1wd9tCsRsDXWdsFURF+Cg1
Ug9g9qopHFCbl9QDwgcf+59ppDCifR9LN0oDiQZfQQAAVXuZ2CGhRXcxGTjKAU7mBSQ7dcyY4glO/RtMFfq3l3tRIjXAy86dmPg18hQ7RNdpZjXyJmVIXrIng+8/35PSIOnDoFxeRW3//ZYiHi8YAxFszYKRwFC8bmCyvh+A89WjaFuoJw7a1hgXKMSY9D/nbvAoc4IHrSWYDPN9msoa+PoL6zhel2lntrHXB2bsgaEsy4hoE5BEt9M2T4RUPQ
GtAhhUDtkjfOIAkOhoS3ABlRRST8OPDEyGzvD+T0MTRO2xcBWLBOcJW1AeMqW4AqqPUdgHGxInaWXkG1J+TKiBOe9W5nqy9/WVQAT1XJtnHKcvRGVA1GQLnXrBKa5JVF1WTD42FzNZ4dcz2eUarGVCeAMiHQHcXAF7UyGKyJAP0s3IDsqjWNT9HRDIVCFx9xZAxWQ121J6HxCXpxHLoyOTzcxD0cIBVikmKnikldVq9xhlm6oZmkRpm7vaylgG
Hai0NMLE0mObKvF8Ahsc9NmalEtCcgZXZ+v0mtB7lg9tXC+2IYvmfixJgxoskpxQakkGcfGGzK8jdkOHStLnhe3zAeOLEiEP6DIiVSvsyG9j7F3iPp3afLc2aXwQNmdyATMmAs4qUIp62DSCEfYJ2lMy5mtECT5LXd8EGu3tvoVXgvoRRUqdICf22n/r1sRNXQOCuMwBHhqltYLoLgMoP5Vlnr4IWI9q2kl8D9BWgNSCAR2wZEEySK48+o6v1P
Njk9we3gfjLt31h5vKAFSDslr8EQcS9xDEQ8oWw7TgqvpybzGqnvwvq91sfKea55O2mM6A7yTFpdEk+zBSQFME21579YCa1Sqetvc9BUDPh+CpqUoY1WaIK+J9rDWjvO90ZwPWPbjarUdsFb54BmgrQGTCYZLetBEnnLxO2UWa/WA6G1yLIrOmfS+q40sBDvkNeDjLBguM1TIa9QRf5XM2stgxQztpIWIqU52gjGbYNiHiMSfYpqwYIMwPxh3z
X7zzpsC4gRI9PIA1+GoT/vks/rku5OBQylSeYLHQCULFQZFU+zWrTgMsVGgNslrirjz4D6s9C4LqMJAaEnZ/OgKKiWzAASQ/G0fKGwoJLD28mfR6MvsmPM/HZGqWvARcAWHFF8t2mAdozsDrrFrugeMyugmBmB6r6aBD+drzFaGpgoBFWcIOgYA5JoCZcOUURYee1raAy4xGtAUT5Ys2sYa42DZDS+1w9BO5eVpuA7S7YbxLJp1d1dglSmPQcC
ws69GDyQ6QDOPuoUdCKl8S4g3P+kAi/FsCDhiirBizP18zq8z4s8HwIxrvcb7UL6iN6A8L3OlAn+xC2DVhNsqANzDjNOn0X09BZieJFuc4o/runx2unhkAgwr0gCDWBQzcqovRjmFlfzWRyAMyYxqcHwWjRBTvfvAuS69cKuIUesgGey39wppkjKmQDKnIgc+wQjd0fBM7zqZEuaQD83BF0eLEziOGUfL8BMHaH748bPEGE9OZh3AuBsx8kDoP
4tBBm8jYxcdgTBs6jiSvapMMoX4b97G+jCzo8uTxzApV83atpljcJWPJeLW1rwiRvAE4PTYr93h9l2SwEwDQl+7txAfB4j27utYlsEhcAIy/smNzD4DpqO60xTvO91dn6GihZApmZJUz8DyzoAMA+9P9+jL0PSIedyADbV6HSPE1Ea8D86Wjl5cmz8PpLW/WjZeIjIynvlyzJO+nR097cp+8Do01EBMpagYjKE2HXwYNR7gpiI+1x/N/ASarWG
/BJMWQuTFjHxDhjRnGSXaiaZmWXGwzIL/mj14AMXRcUkQBx9xcUDaHViTdLvQGI8nsdhPdAHtrPZFMvXuqtQCTMZ3IwZowJhCuInPEkX0wSLzaRkEmsdgCuLYUlX/k3jGrdn4diAaOuC9Ze+LNdUKZ2VdBhCDo4WDWgfuxCBTJH+k+lNBjaPwESZ0ZTseSN7bkTEvmjikivjq2Fyr+3Q6YqEcCyq9Awb1w1ZFKHDwWMurvg+VoI3Lxv3gVlitY
FvZWrsysTOv6/z1EIkoc+dAAqB3qNPCfqen5wGu9hTz9xgoeVmMBYqOzqlUQl+uY/9NeB4mjo+DxoGwTnxwRvVgCDowFArWqlgxFAvWyTE5OaOghM9mQx38ACT/ZUCVQVFOSn7oyrgwVGBz5aT/CQMF/vwtTU06lJ9ZAwdA65PyQoJzllRzpk2oWEhPQoSkn5OR5mTPf39oiPuwYNfV/Bgf/AGp2eHdCubUXqDU7UqNPhdvAoZjIzCk0XIxqLn
OLN3IAzzduAFgMKrzZXA8R7cTPOgGZugNvdzdoA0QWbtQEtGdBiQEl+MzagqSdAiwEttPA/JcotzChXXBQAAAAASUVORK5CYII="""
# the default cursor (19x23 pixel RGBA PNG)
DEFAULT_CURSOR = """iVBORw0KGgoAAAANSUhEUgAAABMAAAAXCAYAAADpwXTaAAADCklEQVR42qWUXWwMURTH787MznbWbm1VtdWP0KBN+pFWlQRVQlJBQkR4lGqioY0IibSprAchHgQhoh76hAQPJB4IRdBobdFstbZ4oJLup9au3c5Md3fmjnPHdE2qZVsn+c3snDv3v/9zzt2lEcRbx90rnAk/d7x2xdF/BAWwFmv6jm1bal4db95Xp
uVmLcbEJfQ9Y0Fu8YZ1yzsvnTu6G3LG2YopPM+HbfMWohTObC0pWXLjWrv9DOS52YjJAi8EKJpBqbZMxNAMlZeXdeTOzdP36/duzYF1w4yciSI/gmUJxLIQw7CIomiUZrOu37m9puukvW51sn0kL2FBEN0Yy2qClGswUIiijYjjUvJXrijuaLt4uCGZPv7qmTAWIGIKMMeajliTGQQNqkOGYbiCxTmXr7e3XC0tXmT5mxhNLtVrq3KWLS3YQxw
RjCyHBD6IFPUVclUMHGeqWFVVWJuXm/Gku2cwNK0zr9fvJc5UdwqGqVoRZ56rOjMAFMWon1NTLZU11WXdZ0/Vb56qj2ri0eOXwzAAnBDEGKWl56oCk2FZNqOoMP9e24XG5sl9VMv0+0eM9XW7mhijkSXPpF+M0YRkOY7iMVFfbsKE1cJtrN1UXmrmUjr6XUMi0lmVYKKj5Hjo3dnSshENU9WXS75IxgoOhfmxWEwurSwvaIX96mCYCbFoNBrEW
MqnMK0JSurx6HcNhxwOR8TnHx33eALjXt+o4A8EBUVReNjnBgaALGBoQkwWRRGOB1ZFDJhSBV90OoIHmuxOWZZ98E4Q4HVEgDDgAUiZyoQYjsbiI2SSMpRKynrv+jR2sKmlF4TewLpD20RExrXNMY24dpcTYvBj94F1RHC7vdH9Dcf6eF5wwtpDwKk5wZMnoY/fzqIxH3EWiQhS46ETAz7/t3eQfwqQe2g6gT/OGYkfobBHisfkVvv5vg8fP/d
D6hnQq/Xqn0KJc0aiorxofq9zkL11+8FXeOwCOgGfVlpSof+vygTWAGagB/iiNTfp0IsRkWxA0hxFZyI0lbBRX/pM4ycZx2V6yAv08AAAAABJRU5ErkJggg=="""

# get the contents of a PIL image as a string
def img2str(img):
    if hasattr(img, "tobytes"):
        return img.tobytes()
    else:
        return img.tostring()

# create a PIL image from a string
def str2img(mode, size, data):
    if hasattr(Image, "frombytes"):
        return Image.frombytes(mode, size, data)
    else:
        return Image.fromstring(mode, size, data)

# determine the next power of two
def npot(x):
    res = 1
    while res < x: res <<= 1
    return res

# convert boolean value to string
def b2s(b):
    if b: return "Y"
    return "N"

# extract a number at the beginning of a string
def num(s):
    s = s.strip()
    r = ""
    while s[0] in "0123456789":
        r += s[0]
        s = s[1:]
    try:
        return int(r)
    except ValueError:
        return -1

# linearly interpolate between two floating-point RGB colors represented as tuples
def lerpColor(a, b, t):
    return tuple([min(1.0, max(0.0, x + t * (y - x))) for x, y in zip(a, b)])

# get a representative subset of file statistics
def my_stat(filename):
    try:
        s = os.stat(filename)
    except OSError:
        return None
    return (s.st_size, s.st_mtime, s.st_ctime, s.st_mode)

# determine (pagecount,width,height) of a PDF file
def analyze_pdf(filename):
    f = file(filename,"rb")
    pdf = f.read()
    f.close()
    box = map(float, pdf.split("/MediaBox",1)[1].split("]",1)[0].split("[",1)[1].strip().split())
    return (max(map(num, pdf.split("/Count")[1:])), box[2]-box[0], box[3]-box[1])

# unescape &#123; literals in PDF files
re_unescape = re.compile(r'&#[0-9]+;')
def decode_literal(m):
    try:
        code = int(m.group(0)[2:-1])
        if code:
            return chr(code)
        else:
            return ""
    except ValueError:
        return '?'
def unescape_pdf(s):
    return re_unescape.sub(decode_literal, s)

# parse pdftk output
def pdftkParse(filename, page_offset=0):
    f = file(filename, "r")
    InfoKey = None
    BookmarkTitle = None
    Title = None
    Pages = 0
    for line in f.xreadlines():
        try:
            key, value = [item.strip() for item in line.split(':', 1)]
        except ValueError:
            continue
        key = key.lower()
        if key == "numberofpages":
            Pages = int(value)
        elif key == "infokey":
            InfoKey = value.lower()
        elif (key == "infovalue") and (InfoKey == "title"):
            Title = unescape_pdf(value)
            InfoKey = None
        elif key == "bookmarktitle":
            BookmarkTitle = unescape_pdf(value)
        elif key == "bookmarkpagenumber" and BookmarkTitle:
            try:
                page = int(value)
                if not GetPageProp(page + page_offset, '_title'):
                    SetPageProp(page + page_offset, '_title', BookmarkTitle)
            except ValueError:
                pass
            BookmarkTitle = None
    f.close()
    if AutoOverview:
        SetPageProp(page_offset + 1, '_overview', True)
        for page in xrange(page_offset + 2, page_offset + Pages):
            SetPageProp(page, '_overview', \
                        not(not(GetPageProp(page + AutoOverview - 1, '_title'))))
        SetPageProp(page_offset + Pages, '_overview', True)
    return (Title, Pages)

# translate pixel coordinates to normalized screen coordinates
def MouseToScreen(mousepos):
    return (ZoomX0 + mousepos[0] * ZoomArea / ScreenWidth,
            ZoomY0 + mousepos[1] * ZoomArea / ScreenHeight)

# normalize rectangle coordinates so that the upper-left point comes first
def NormalizeRect(X0, Y0, X1, Y1):
    return (min(X0, X1), min(Y0, Y1), max(X0, X1), max(Y0, Y1))

# check if a point is inside a box (or a list of boxes)
def InsideBox(x, y, box):
    return (x >= box[0]) and (y >= box[1]) and (x < box[2]) and (y < box[3])
def FindBox(x, y, boxes):
    for i in xrange(len(boxes)):
        if InsideBox(x, y, boxes[i]):
            return i
    raise ValueError

# zoom an image size to a destination size, preserving the aspect ratio
def ZoomToFit(size, dest=None):
    if not dest:
        dest = (ScreenWidth + Overscan, ScreenHeight + Overscan)
    newx = dest[0]
    newy = size[1] * newx / size[0]
    if newy > dest[1]:
        newy = dest[1]
        newx = size[0] * newy / size[1]
    return (newx, newy)

# get the overlay grid screen coordinates for a specific page
def OverviewPos(page):
    return ( \
        int(page % OverviewGridSize) * OverviewCellX + OverviewOfsX, \
        int(page / OverviewGridSize) * OverviewCellY + OverviewOfsY  \
    )

def StopMPlayer():
    global MPlayerProcess, VideoPlaying
    if not MPlayerProcess: return

    # first, ask politely
    try:
        MPlayerProcess.stdin.write('quit\n')
        for i in xrange(10):
            if not(MPlayerProcess.poll() is None):
                MPlayerProcess = None
                VideoPlaying = False
                return
            time.sleep(0.1)
    except:
        pass

    # if that didn't work, be rude
    print >>sys.stderr, "MPlayer didn't exit properly, killing PID", MPlayerProcess.pid
    try:
        if os.name == 'nt':
            win32api.TerminateProcess(win32api.OpenProcess(1, False, MPlayerProcess.pid), 0)
        else:
            os.kill(MPlayerProcess.pid, 2)
        MPlayerProcess = None
    except:
        pass
    VideoPlaying = False

def ClockTime(minutes):
    if minutes:
        return time.strftime("%H:%M")
    else:
        return time.strftime("%H:%M:%S")

def FormatTime(t, minutes=False):
    if minutes and (t < 3600):
        return "%d min" % (t / 60)
    elif minutes:
        return "%d:%02d" % (t / 3600, (t / 60) % 60)
    elif t < 3600:
        return "%d:%02d" % (t / 60, t % 60)
    else:
        ms = t % 3600
        return "%d:%02d:%02d" % (t / 3600, ms / 60, ms % 60)

def SafeCall(func, args=[], kwargs={}):
    if not func: return None
    try:
        return func(*args, **kwargs)
    except:
        print >>sys.stderr, "----- Unhandled Exception ----"
        traceback.print_exc(file=sys.stderr)
        print >>sys.stderr, "----- End of traceback -----"

def Quit(code=0):
    global CleanExit
    if not code:
        CleanExit = True
    StopMPlayer()
    Platform.Done()
    print >>sys.stderr, "Total presentation time: %s." % \
                        FormatTime((Platform.GetTicks() - StartTime) / 1000)
    sys.exit(code)


##### OPENGL (ES) 2.0 LOADER AND TOOLKIT #######################################

if os.name == 'nt':
    GLFUNCTYPE = WINFUNCTYPE
else:
    GLFUNCTYPE = CFUNCTYPE

class GLFunction(object):
    def __init__(self, required, name, ret, *args):
        self.name = name
        self.required = required
        self.prototype = GLFUNCTYPE(ret, *args)

class OpenGL(object):
    FALSE = 0
    TRUE = 1
    NO_ERROR = 0
    INVALID_ENUM = 0x0500
    INVALID_VALUE = 0x0501
    INVALID_OPERATION = 0x0502
    OUT_OF_MEMORY = 0x0505
    INVALID_FRAMEBUFFER_OPERATION = 0x0506
    VENDOR = 0x1F00
    RENDERER = 0x1F01
    VERSION = 0x1F02
    EXTENSIONS = 0x1F03
    POINTS = 0x0000
    LINES = 0x0001
    LINE_LOOP = 0x0002
    LINE_STRIP = 0x0003
    TRIANGLES = 0x0004
    TRIANGLE_STRIP = 0x0005
    TRIANGLE_FAN = 0x0006
    BYTE = 0x1400
    UNSIGNED_BYTE = 0x1401
    SHORT = 0x1402
    UNSIGNED_SHORT = 0x1403
    INT = 0x1404
    UNSIGNED_INT = 0x1405
    FLOAT = 0x1406
    DEPTH_TEST = 0x0B71
    BLEND = 0x0BE2
    ZERO = 0
    ONE = 1
    SRC_COLOR = 0x0300
    ONE_MINUS_SRC_COLOR = 0x0301
    SRC_ALPHA = 0x0302
    ONE_MINUS_SRC_ALPHA = 0x0303
    DST_ALPHA = 0x0304
    ONE_MINUS_DST_ALPHA = 0x0305
    DST_COLOR = 0x0306
    ONE_MINUS_DST_COLOR = 0x0307
    DEPTH_BUFFER_BIT = 0x00000100
    COLOR_BUFFER_BIT = 0x00004000
    TEXTURE0 = 0x84C0
    TEXTURE_2D = 0x0DE1
    TEXTURE_RECTANGLE = 0x84F5
    TEXTURE_MAG_FILTER = 0x2800
    TEXTURE_MIN_FILTER = 0x2801
    TEXTURE_WRAP_S = 0x2802
    TEXTURE_WRAP_T = 0x2803
    NEAREST = 0x2600
    LINEAR = 0x2601
    NEAREST_MIPMAP_NEAREST = 0x2700
    LINEAR_MIPMAP_NEAREST = 0x2701
    NEAREST_MIPMAP_LINEAR = 0x2702
    LINEAR_MIPMAP_LINEAR = 0x2703
    CLAMP_TO_EDGE = 0x812F
    REPEAT = 0x2901
    ALPHA = 0x1906
    RGB = 0x1907
    RGBA = 0x1908
    LUMINANCE = 0x1909
    LUMINANCE_ALPHA = 0x190A
    ARRAY_BUFFER = 0x8892
    ELEMENT_ARRAY_BUFFER = 0x8893
    STREAM_DRAW = 0x88E0
    STATIC_DRAW = 0x88E4
    DYNAMIC_DRAW = 0x88E8
    FRAGMENT_SHADER = 0x8B30
    VERTEX_SHADER = 0x8B31
    COMPILE_STATUS = 0x8B81
    LINK_STATUS = 0x8B82
    INFO_LOG_LENGTH = 0x8B84
    _funcs = [
        GLFunction(True,  "GetString",                c_char_p, c_uint),
        GLFunction(True,  "Enable",                   None, c_uint),
        GLFunction(True,  "Disable",                  None, c_uint),
        GLFunction(True,  "GetError",                 c_uint),
        GLFunction(True,  "Viewport",                 None, c_int, c_int, c_int, c_int),
        GLFunction(True,  "Clear",                    None, c_uint),
        GLFunction(True,  "ClearColor",               None, c_float, c_float, c_float, c_float),
        GLFunction(True,  "BlendFunc",                None, c_uint, c_uint),
        GLFunction(True,  "GenTextures",              None, c_uint, POINTER(c_int)),
        GLFunction(True,  "BindTexture",              None, c_uint, c_int),
        GLFunction(True,  "ActiveTexture",            None, c_uint),
        GLFunction(True,  "TexParameteri",            None, c_uint, c_uint, c_int),
        GLFunction(True,  "TexImage2D",               None, c_uint, c_uint, c_uint, c_uint, c_uint, c_uint, c_uint, c_uint, c_void_p),
        GLFunction(True,  "GenerateMipmap",           None, c_uint),
        GLFunction(True,  "GenBuffers",               None, c_uint, POINTER(c_int)),
        GLFunction(True,  "BindBuffer",               None, c_uint, c_int),
        GLFunction(True,  "BufferData",               None, c_uint, c_void_p, c_void_p, c_uint),
        GLFunction(True,  "CreateProgram",            c_uint),
        GLFunction(True,  "CreateShader",             c_uint, c_uint),
        GLFunction(True,  "ShaderSource",             None, c_uint, c_uint, c_void_p, c_void_p),
        GLFunction(True,  "CompileShader",            None, c_uint),
        GLFunction(True,  "GetShaderiv",              None, c_uint, c_uint, POINTER(c_uint)),
        GLFunction(True,  "GetShaderInfoLog",         None, c_uint, c_uint, c_void_p, c_void_p),
        GLFunction(True,  "AttachShader",             None, c_uint, c_uint),
        GLFunction(True,  "LinkProgram",              None, c_uint),
        GLFunction(True,  "GetProgramiv",             None, c_uint, c_uint, POINTER(c_uint)),
        GLFunction(True,  "GetProgramInfoLog",        None, c_uint, c_uint, c_void_p, c_void_p),
        GLFunction(True,  "UseProgram",               None, c_uint),
        GLFunction(True,  "BindAttribLocation",       None, c_uint, c_uint, c_char_p),
        GLFunction(True,  "GetAttribLocation",        c_int, c_uint, c_char_p),
        GLFunction(True,  "GetUniformLocation",       c_int, c_uint, c_char_p),
        GLFunction(True,  "Uniform1f",                None, c_uint, c_float),
        GLFunction(True,  "Uniform2f",                None, c_uint, c_float, c_float),
        GLFunction(True,  "Uniform3f",                None, c_uint, c_float, c_float, c_float),
        GLFunction(True,  "Uniform4f",                None, c_uint, c_float, c_float, c_float, c_float),
        GLFunction(True,  "Uniform1i",                None, c_uint, c_int),
        GLFunction(True,  "Uniform2i",                None, c_uint, c_int, c_int),
        GLFunction(True,  "Uniform3i",                None, c_uint, c_int, c_int, c_int),
        GLFunction(True,  "Uniform4i",                None, c_uint, c_int, c_int, c_int, c_int),
        GLFunction(True,  "EnableVertexAttribArray",  None, c_uint),
        GLFunction(True,  "DisableVertexAttribArray", None, c_uint),
        GLFunction(True,  "VertexAttribPointer",      None, c_uint, c_uint, c_uint, c_uint, c_uint, c_void_p),
        GLFunction(True,  "DrawArrays",               None, c_uint, c_uint, c_uint),
        GLFunction(True,  "DrawElements",             None, c_uint, c_uint, c_uint, c_void_p),
    ]
    _typemap = {
                  BYTE:  c_int8,
         UNSIGNED_BYTE: c_uint8,
                 SHORT:  c_int16,
        UNSIGNED_SHORT: c_uint16,
                   INT:  c_int32,
          UNSIGNED_INT: c_uint32,
                 FLOAT:  c_float
    }

    def __init__(self, loader, desktop=False):
        global GLVendor, GLRenderer, GLVersion
        self._is_desktop_gl = desktop
        for func in self._funcs:
            funcptr = None
            for suffix in ("", "ARB", "ObjectARB", "EXT", "OES"):
                funcptr = loader("gl" + func.name + suffix, func.prototype)
                if funcptr:
                    break
            if not funcptr:
                if func.required:
                    raise ImportError("failed to import required OpenGL function 'gl%s'" % func.name)
                else:
                    def errfunc(*args):
                        raise ImportError("call to unimplemented OpenGL function 'gl%s'" % func.name)
                    funcptr = errfunc
            if hasattr(self, func.name):
                setattr(self, '_' + func.name, funcptr)
            else:
                setattr(self, func.name, funcptr)
            if func.name == "GetString":
                GLVendor = self.GetString(self.VENDOR) or ""
                GLRenderer = self.GetString(self.RENDERER) or ""
                GLVersion = self.GetString(self.VERSION) or ""
        self._init()

    def GenTextures(self, n=1):
        bufs = (c_int * n)()
        self._GenTextures(n, bufs)
        if n == 1: return bufs[0]
        return list(bufs)

    def ActiveTexture(self, tmu):
        if tmu < self.TEXTURE0:
            tmu += self.TEXTURE0
        self._ActiveTexture(tmu)

    def GenBuffers(self, n=1):
        bufs = (c_int * n)()
        self._GenBuffers(n, bufs)
        if n == 1: return bufs[0]
        return list(bufs)

    def BufferData(self, target, size=0, data=None, usage=STATIC_DRAW, type=None):
        if isinstance(data, list):
            if type:
                type = self._typemap[type]
            elif isinstance(data[0], int):
                type = c_int32
            elif isinstance(data[0], float):
                type = c_float
            else:
                raise TypeError("cannot infer buffer data type")
            size = len(data) * sizeof(type)
            data = (type * len(data))(*data)
        self._BufferData(target, cast(size, c_void_p), cast(data, c_void_p), usage)

    def ShaderSource(self, shader, source):
        source = c_char_p(source)
        self._ShaderSource(shader, 1, pointer(source), None)

    def GetShaderi(self, shader, pname):
        res = (c_uint * 1)()
        self.GetShaderiv(shader, pname, res)
        return res[0]

    def GetShaderInfoLog(self, shader):
        length = self.GetShaderi(shader, self.INFO_LOG_LENGTH)
        if not length: return None
        buf = create_string_buffer(length + 1)
        self._GetShaderInfoLog(shader, length + 1, None, buf)
        return buf.raw.split('\0', 1)[0]

    def GetProgrami(self, program, pname):
        res = (c_uint * 1)()
        self.GetProgramiv(program, pname, res)
        return res[0]

    def GetProgramInfoLog(self, program):
        length = self.GetProgrami(program, self.INFO_LOG_LENGTH)
        if not length: return None
        buf = create_string_buffer(length + 1)
        self._GetProgramInfoLog(program, length + 1, None, buf)
        return buf.raw.split('\0', 1)[0]

    def Uniform(self, location, *values):
        if not values:
            raise TypeError("no values for glUniform")
        if (len(values) == 1) and (isinstance(values[0], list) or isinstance(values[0], tuple)):
            values = values[0]
        l = len(values)
        if l > 4:
            raise TypeError("uniform vector has too-high order(%d)" % len(values))
        if any(isinstance(v, float) for v in values):
            if   l == 1: self.Uniform1f(location, values[0])
            elif l == 2: self.Uniform2f(location, values[0], values[1])
            elif l == 3: self.Uniform3f(location, values[0], values[1], values[2])
            else:        self.Uniform4f(location, values[0], values[1], values[2], values[3])
        else:
            if   l == 1: self.Uniform1i(location, values[0])
            elif l == 2: self.Uniform2i(location, values[0], values[1])
            elif l == 3: self.Uniform3i(location, values[0], values[1], values[2])
            else:        self.Uniform4i(location, values[0], values[1], values[2], values[3])

    ##### Convenience Functions #####

    def _init(self):
        self.enabled_attribs = set()

    def set_enabled_attribs(self, *attrs):
        want = set(attrs)
        for a in (want - self.enabled_attribs):
            self.EnableVertexAttribArray(a)
        for a in (self.enabled_attribs - want):
            self.DisableVertexAttribArray(a)
        self.enabled_attribs = want

    def set_texture(self, target=TEXTURE_2D, tex=0, tmu=0):
        self.ActiveTexture(self.TEXTURE0 + tmu)
        self.BindTexture(target, tex)

    def make_texture(self, target=TEXTURE_2D, wrap=CLAMP_TO_EDGE, filter=LINEAR_MIPMAP_NEAREST, img=None):
        tex = self.GenTextures()
        min_filter = filter
        if min_filter < self.NEAREST_MIPMAP_NEAREST:
            mag_filter = min_filter
        else:
            mag_filter = self.NEAREST + (min_filter & 1)
        self.BindTexture(target, tex)
        self.TexParameteri(target, self.TEXTURE_WRAP_S, wrap)
        self.TexParameteri(target, self.TEXTURE_WRAP_T, wrap)
        self.TexParameteri(target, self.TEXTURE_MIN_FILTER, min_filter)
        self.TexParameteri(target, self.TEXTURE_MAG_FILTER, mag_filter)
        if img:
            self.load_texture(target, img)
        return tex

    def load_texture(self, target, tex_or_img, img=None):
        if img:
            gl.BindTexture(target, tex_or_img)
        else:
            img = tex_or_img
        if   img.mode == 'RGBA': format = self.RGBA
        elif img.mode == 'RGB':  format = self.RGB
        elif img.mode == 'LA':   format = self.LUMINANCE_ALPHA
        elif img.mode == 'L':    format = self.LUMINANCE
        else: raise TypeError("image has unsupported color format '%s'" % img.mode)
        gl.TexImage2D(target, 0, format, img.size[0], img.size[1], 0, format, self.UNSIGNED_BYTE, img2str(img))

class GLShaderCompileError(SyntaxError):
    pass
class GLInvalidShaderError(GLShaderCompileError):
    pass

class GLShader(object):
    LOG_NEVER = 0
    LOG_ON_ERROR = 1
    LOG_IF_NOT_EMPTY = 2
    LOG_ALWAYS = 3
    LOG_DEFAULT = LOG_ON_ERROR

    def __init__(self, vs=None, fs=None, attributes=[], uniforms=[], loglevel=None):
        if not(vs): vs = self.vs
        if not(fs): fs = self.fs
        if not(attributes) and hasattr(self, 'attributes'):
            attributes = self.attributes
        if isinstance(attributes, dict):
            attributes = attributes.items()
        if not(uniforms) and hasattr(self, 'uniforms'):
            uniforms = self.uniforms
        if isinstance(uniforms, dict):
            uniforms = uniforms.items()
        uniforms = [((u, None) if isinstance(u, basestring) else u) for u in uniforms]
        if (loglevel is None) and hasattr(self, 'loglevel'):
            loglevel = self.loglevel
        if loglevel is None:
            loglevel = self.LOG_DEFAULT

        self.program = gl.CreateProgram()
        def handle_shader_log(status, log_getter, action):
            force_log = (loglevel >= self.LOG_ALWAYS) or ((loglevel >= self.LOG_ON_ERROR) and not(status))
            if force_log or (loglevel >= self.LOG_IF_NOT_EMPTY):
                log = log_getter().rstrip()
            else:
                log = "" 
            if force_log or ((loglevel >= self.LOG_IF_NOT_EMPTY) and log):
                if status:
                    print >>sys.stderr, "Info: log for %s %s:" % (self.__class__.__name__, action)
                else:
                    print >>sys.stderr, "Error: %s %s failed - log information follows:" % (self.__class__.__name__, action)
                for line in log.split('\n'):
                    print >>sys.stderr, '>', line.rstrip()
            if not status:
                raise GLShaderCompileError("failure during %s %s" % (self.__class__.__name__, action))
        def handle_shader(type_enum, type_name, src):
            if gl._is_desktop_gl:
                src = src.replace("highp ", "")
                src = src.replace("mediump ", "")
                src = src.replace("lowp ", "")
            shader = gl.CreateShader(type_enum)
            gl.ShaderSource(shader, src)
            gl.CompileShader(shader)
            handle_shader_log(gl.GetShaderi(shader, gl.COMPILE_STATUS),
                              lambda: gl.GetShaderInfoLog(shader),
                              type_name + " shader compilation")
            gl.AttachShader(self.program, shader)
        handle_shader(gl.VERTEX_SHADER, "vertex", vs)
        handle_shader(gl.FRAGMENT_SHADER, "fragment", fs)
        for attr in attributes:
            if not isinstance(attr, basestring):
                loc, name = attr
                if isinstance(loc, basestring):
                    loc, name = name, loc
                setattr(self, name, loc)
            elif hasattr(self, attr):
                name = attr
                loc = getattr(self, name)
            gl.BindAttribLocation(self.program, loc, name)
        gl.LinkProgram(self.program)
        handle_shader_log(gl.GetProgrami(self.program, gl.LINK_STATUS),
                          lambda: gl.GetProgramInfoLog(self.program),
                          "linking")
        gl.UseProgram(self.program)
        for name in attributes:
            if isinstance(name, basestring) and not(hasattr(self, attr)):
                setattr(self, name, int(gl.GetAttribLocation(self.program, name)))
        for u in uniforms:
            loc = int(gl.GetUniformLocation(self.program, u[0]))
            setattr(self, u[0], loc)
            if u[1] is not None:
                gl.Uniform(loc, *u[1:])

    def use(self):
        gl.UseProgram(self.program)
        return self

    @classmethod
    def get_instance(self):
        try:
            instance = self._instance
            if instance:
                return instance
            else:
                raise GLInvalidShaderError("shader failed to compile in the past")
        except AttributeError:
            try:
                self._instance = self()
            except GLShaderCompileError, e:
                self._instance = None
                raise
            return self._instance

# NOTE: OpenGL drawing code in Impressive uses the following conventions:
# - program binding is undefined
# - vertex attribute layout is undefined
# - vertex attribute enable/disable is managed by gl.set_enabled_attribs()
# - texture bindings are undefined
# - ActiveTexure is TEXTURE0
# - array and element array buffer bindings are undefined
# - BLEND is disabled, BlendFunc is (SRC_ALPHA, ONE_MINUS_SRC_ALPHA)


##### STOCK SHADERS ############################################################

class SimpleQuad(object):
    "vertex buffer singleton for a simple quad (used by various shaders)"
    vbuf = None
    @classmethod
    def draw(self):
        gl.set_enabled_attribs(0)
        if not self.vbuf:
            self.vbuf = gl.GenBuffers()
            gl.BindBuffer(gl.ARRAY_BUFFER, self.vbuf)
            gl.BufferData(gl.ARRAY_BUFFER, data=[0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0])
        else:
            gl.BindBuffer(gl.ARRAY_BUFFER, self.vbuf)
        gl.VertexAttribPointer(0, 2, gl.FLOAT, False, 0, 0)
        gl.DrawArrays(gl.TRIANGLE_STRIP, 0, 4)


class TexturedRectShader(GLShader):
    vs = """
        attribute highp vec2 aPos;
        uniform highp vec4 uPosTransform;
        uniform highp vec4 uScreenTransform;
        uniform highp vec4 uTexTransform;
        varying mediump vec2 vTexCoord;
        void main() {
            highp vec2 pos = uPosTransform.xy + aPos * uPosTransform.zw;
            gl_Position = vec4(uScreenTransform.xy + pos * uScreenTransform.zw, 0.0, 1.0);
            vTexCoord = uTexTransform.xy + aPos * uTexTransform.zw;
        }
    """
    fs = """
        uniform lowp vec4 uColor;
        uniform lowp sampler2D uTex;
        varying mediump vec2 vTexCoord;
        void main() {
            gl_FragColor = uColor * texture2D(uTex, vTexCoord);
        }
    """
    attributes = { 0: 'aPos' }
    uniforms = ['uPosTransform', 'uScreenTransform', 'uTexTransform', 'uColor']

    def draw(self, x0, y0, x1, y1, s0=0.0, t0=0.0, s1=1.0, t1=1.0, tex=None, color=1.0):
        self.use()
        if tex:
            gl.BindTexture(gl.TEXTURE_2D, tex)
        if isinstance(color, float):
            gl.Uniform4f(self.uColor, color, color, color, 1.0)
        else:
            gl.Uniform(self.uColor, color)
        gl.Uniform(self.uPosTransform, x0, y0, x1 - x0, y1 - y0)
        gl.Uniform(self.uScreenTransform, ScreenTransform)
        gl.Uniform(self.uTexTransform, s0, t0, s1 - s0, t1 - t0)
        SimpleQuad.draw()
RequiredShaders.append(TexturedRectShader)


class TexturedMeshShader(GLShader):
    vs = """
        attribute highp vec3 aPosAndAlpha;
        uniform highp vec4 uPosTransform;
        uniform highp vec4 uScreenTransform;
        uniform highp vec4 uTexTransform;
        varying mediump vec2 vTexCoord;
        varying lowp float vAlpha;
        void main() {
            highp vec2 pos = uPosTransform.xy + aPosAndAlpha.xy * uPosTransform.zw;
            gl_Position = vec4(uScreenTransform.xy + pos * uScreenTransform.zw, 0.0, 1.0);
            vTexCoord = uTexTransform.xy + aPosAndAlpha.xy * uTexTransform.zw;
            vAlpha = aPosAndAlpha.z;
        }
    """
    fs = """
        uniform lowp sampler2D uTex;
        varying mediump vec2 vTexCoord;
        varying lowp float vAlpha;
        void main() {
            gl_FragColor = vec4(1.0, 1.0, 1.0, vAlpha) * texture2D(uTex, vTexCoord);
        }
    """
    attributes = { 0: 'aPosAndAlpha' }
    uniforms = ['uPosTransform', 'uScreenTransform', 'uTexTransform']

    def setup(self, x0, y0, x1, y1, s0=0.0, t0=0.0, s1=1.0, t1=1.0, tex=None):
        self.use()
        if tex:
            gl.BindTexture(gl.TEXTURE_2D, tex)
        gl.Uniform(self.uPosTransform, x0, y0, x1 - x0, y1 - y0)
        gl.Uniform(self.uScreenTransform, ScreenTransform)
        gl.Uniform(self.uTexTransform, s0, t0, s1 - s0, t1 - t0)
RequiredShaders.append(TexturedMeshShader)


class BlurShader(GLShader):
    vs = """
        attribute highp vec2 aPos;
        uniform highp vec4 uScreenTransform;
        varying mediump vec2 vTexCoord;
        void main() {
            gl_Position = vec4(uScreenTransform.xy + aPos * uScreenTransform.zw, 0.0, 1.0);
            vTexCoord = aPos;
        }
    """
    fs = """
        uniform lowp float uIntensity;
        uniform mediump sampler2D uTex;
        uniform mediump vec2 uDeltaTexCoord;
        varying mediump vec2 vTexCoord;
        void main() {
            lowp vec3 color = (uIntensity * 0.125) * (
                texture2D(uTex, vTexCoord).rgb * 3.0
              + texture2D(uTex, vTexCoord + uDeltaTexCoord * vec2(+0.89, +0.45)).rgb
              + texture2D(uTex, vTexCoord + uDeltaTexCoord * vec2(+0.71, -0.71)).rgb
              + texture2D(uTex, vTexCoord + uDeltaTexCoord * vec2(-0.45, -0.89)).rgb
              + texture2D(uTex, vTexCoord + uDeltaTexCoord * vec2(-0.99, +0.16)).rgb
              + texture2D(uTex, vTexCoord + uDeltaTexCoord * vec2(-0.16, +0.99)).rgb
            );
            lowp float gray = dot(vec3(0.299, 0.587, 0.114), color);
            gl_FragColor = vec4(mix(color, vec3(gray, gray, gray), uIntensity), 1.0);
        }
    """
    attributes = { 0: 'aPos' }
    uniforms = ['uScreenTransform', 'uDeltaTexCoord', 'uIntensity']

    def draw(self, dtx, dty, intensity=1.0, tex=None):
        self.use()
        if tex:
            gl.BindTexture(gl.TEXTURE_2D, tex)
        gl.Uniform(self.uScreenTransform, ScreenTransform)
        gl.Uniform2f(self.uDeltaTexCoord, dtx, dty)
        gl.Uniform1f(self.uIntensity, intensity)
        SimpleQuad.draw()
# (not added to RequiredShaders because this shader is allowed to fail)


class ProgressBarShader(GLShader):
    vs = """
        attribute highp vec2 aPos;
        uniform highp vec4 uPosTransform;
        uniform lowp vec4 uColor0;
        uniform lowp vec4 uColor1;
        varying lowp vec4 vColor;
        void main() {
            gl_Position = vec4(uPosTransform.xy + aPos * uPosTransform.zw, 0.0, 1.0);
            vColor = mix(uColor0, uColor1, aPos.y);
        }
    """
    fs = """
        varying lowp vec4 vColor;
        void main() {
            gl_FragColor = vColor;
        }
    """
    attributes = { 0: 'aPos' }
    uniforms = ['uPosTransform', 'uColor0', 'uColor1']

    def draw(self, x0, y0, x1, y1, color0, color1):
        self.use()
        tx0 = ScreenTransform[0] + ScreenTransform[2] * x0
        ty0 = ScreenTransform[1] + ScreenTransform[3] * y0
        tx1 = ScreenTransform[0] + ScreenTransform[2] * x1
        ty1 = ScreenTransform[1] + ScreenTransform[3] * y1
        gl.Uniform4f(self.uPosTransform, tx0, ty0, tx1 - tx0, ty1 - ty0)
        gl.Uniform(self.uColor0, color0)
        gl.Uniform(self.uColor1, color1)
        SimpleQuad.draw()
RequiredShaders.append(ProgressBarShader)


##### RENDERING TOOL CODE ######################################################

# meshes for highlight boxes and the spotlight are laid out in the same manner:
# - vertex 0 is the center vertex
# - for each slice, there are two further vertices:
#   - vertex 2*i+1 is the "inner" vertex with full alpha
#   - vertex 2*i+2 is the "outer" vertex with zero alpha

class HighlightIndexBuffer(object):
    def __init__(self, npoints, reuse_buf=None, dynamic=False):
        if not reuse_buf:
            self.buf = gl.GenBuffers()
        elif isinstance(reuse_buf, HighlightIndexBuffer):
            self.buf = reuse_buf.buf
        else:
            self.buf = reuse_buf
        data = []
        for i in xrange(npoints):
            if i:
                b0 = 2 * i - 1
            else:
                b0 = 2 * npoints - 1
            b1 = 2 * i + 1
            data.extend([
                0, b1, b0,
                b1, b1+1, b0,
                b1+1, b0+1, b0
            ])
        self.vertices = 9 * npoints
        if dynamic:
            usage = gl.DYNAMIC_DRAW
        else:
            usage = gl.STATIC_DRAW
        gl.BindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.buf)
        gl.BufferData(gl.ELEMENT_ARRAY_BUFFER, data=data, type=gl.UNSIGNED_SHORT, usage=usage)

    def draw(self):
        gl.BindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.buf)
        gl.DrawElements(gl.TRIANGLES, self.vertices, gl.UNSIGNED_SHORT, 0)


def GenerateSpotMesh():
    global SpotVertices, SpotIndices
    rx0 = SpotRadius * PixelX
    ry0 = SpotRadius * PixelY
    rx1 = (SpotRadius + BoxEdgeSize) * PixelX
    ry1 = (SpotRadius + BoxEdgeSize) * PixelY
    slices = max(MinSpotDetail, int(2.0 * pi * SpotRadius / SpotDetail / ZoomArea))
    SpotIndices = HighlightIndexBuffer(slices, reuse_buf=SpotIndices, dynamic=True)

    vertices = [0.0, 0.0, 1.0]
    for i in xrange(slices):
        a = i * 2.0 * pi / slices
        vertices.extend([
            rx0 * sin(a), ry0 * cos(a), 1.0,
            rx1 * sin(a), ry1 * cos(a), 0.0
        ])
    if not SpotVertices:
        SpotVertices = gl.GenBuffers()
    gl.BindBuffer(gl.ARRAY_BUFFER, SpotVertices)
    gl.BufferData(gl.ARRAY_BUFFER, data=vertices, usage=gl.DYNAMIC_DRAW)


##### TRANSITIONS ##############################################################

# base class for all transitions
class Transition(object):

    # constructor: must instantiate (i.e. compile) all required shaders
    # and (optionally) perform some additional initialization
    def __init__(self):
        pass

    # called once at the start of each transition
    def start(self):
        pass

    # render a frame of the transition, using the relative time 't' and the
    # global texture identifiers Tcurrent and Tnext
    def render(self, t):
        pass

# smoothstep() makes most transitions better :)
def smoothstep(t):
    return t * t * (3.0 - 2.0 * t)

# an array containing all possible transition classes
AllTransitions = []


class Crossfade(Transition):
    """simple crossfade"""
    class CrossfadeShader(GLShader):
        vs = """
            attribute highp vec2 aPos;
            uniform highp vec4 uTexTransform;
            varying mediump vec2 vTexCoord;
            void main() {
                gl_Position = vec4(vec2(-1.0, 1.0) + aPos * vec2(2.0, -2.0), 0.0, 1.0);
                vTexCoord = uTexTransform.xy + aPos * uTexTransform.zw;
            }
        """
        fs = """
            uniform lowp sampler2D uTcurrent;
            uniform lowp sampler2D uTnext;
            uniform lowp float uTime;
            varying mediump vec2 vTexCoord;
            void main() {
                gl_FragColor = mix(texture2D(uTcurrent, vTexCoord), texture2D(uTnext, vTexCoord), uTime);
            }
        """
        attributes = { 0: 'aPos' }
        uniforms = [('uTnext', 1), 'uTexTransform', 'uTime']
    def __init__(self):
        shader = self.CrossfadeShader.get_instance().use()
        gl.Uniform4f(shader.uTexTransform, 0.0, 0.0, TexMaxS, TexMaxT)
    def render(self, t):
        shader = self.CrossfadeShader.get_instance().use()
        gl.set_texture(gl.TEXTURE_2D, Tnext, 1)
        gl.set_texture(gl.TEXTURE_2D, Tcurrent, 0)
        gl.Uniform1f(shader.uTime, t)
        SimpleQuad.draw()
AllTransitions.append(Crossfade)


class FadeOutFadeIn(Transition):
    "fade out to black and fade in again"
    def render(self, t):
        if t < 0.5:
            tex = Tcurrent
            t = 1.0 - 2.0 * t
        else:
            tex = Tnext
            t = 2.0 * t - 1.0
        TexturedRectShader.get_instance().draw(
            0.0, 0.0, 1.0, 1.0,
            s1=TexMaxS, t1=TexMaxT,
            tex=tex,
            color=(t, t, t, 1.0)
        )
AllTransitions.append(FadeOutFadeIn)


class Slide(Transition):
    def render(self, t):
        t = smoothstep(t)
        x = self.dx * t
        y = self.dy * t
        TexturedRectShader.get_instance().draw(
            x, y, x + 1.0, y + 1.0,
            s1=TexMaxS, t1=TexMaxT,
            tex=Tcurrent
        )
        TexturedRectShader.get_instance().draw(
            x - self.dx,       y - self.dy,
            x - self.dx + 1.0, y - self.dy + 1.0,
            s1=TexMaxS, t1=TexMaxT,
            tex=Tnext
        )
class SlideUp(Slide):
    "slide upwards"
    dx, dy = 0.0, -1.0
class SlideDown(Slide):
    "slide downwards"
    dx, dy = 0.0, 1.0
class SlideLeft(Slide):
    "slide to the left"
    dx, dy = -1.0, 0.0
class SlideRight(Slide):
    "slide to the right"
    dx, dy = 1.0, 0.0
AllTransitions.extend([SlideUp, SlideDown, SlideLeft, SlideRight])


class Squeeze(Transition):
    def render(self, t):
        for tex, x0, y0, x1, y1 in self.getparams(smoothstep(t)):
            TexturedRectShader.get_instance().draw(
                x0, y0, x1, y1,
                s1=TexMaxS, t1=TexMaxT,
                tex=tex
            )
class SqueezeUp(Squeeze):
    "squeeze upwards"
    def getparams(self, t):
        return ((Tcurrent, 0.0, 0.0, 1.0, 1.0 - t),
                (Tnext,    0.0, 1.0 - t, 1.0, 1.0))
class SqueezeDown(Squeeze):
    "squeeze downwards"
    def getparams(self, t):
        return ((Tcurrent, 0.0, t, 1.0, 1.0),
                (Tnext,    0.0, 0.0, 1.0, t))
class SqueezeLeft(Squeeze):
    "squeeze to the left"
    def getparams(self, t):
        return ((Tcurrent, 0.0, 0.0, 1.0 - t, 1.0),
                (Tnext,    1.0 - t, 0.0, 1.0, 1.0))
class SqueezeRight(Squeeze):
    "squeeze to the right"
    def getparams(self, t):
        return ((Tcurrent, t, 0.0, 1.0, 1.0),
                (Tnext,    0.0, 0.0, t, 1.0))
AllTransitions.extend([SqueezeUp, SqueezeDown, SqueezeLeft, SqueezeRight])


class Wipe(Transition):
    band_size = 0.5    # relative size of the wiping band
    rx, ry = 16, 16    # mask texture resolution
    class_mask = True  # True if the mask shall be shared between all instances of this subclass
    class WipeShader(GLShader):
        vs = """
            attribute highp vec2 aPos;
            uniform highp vec4 uTexTransform;
            uniform highp vec4 uMaskTransform;
            varying mediump vec2 vTexCoord;
            varying mediump vec2 vMaskCoord;
            void main() {
                gl_Position = vec4(vec2(-1.0, 1.0) + aPos * vec2(2.0, -2.0), 0.0, 1.0);
                vTexCoord = uTexTransform.xy + aPos * uTexTransform.zw;
                vMaskCoord = uMaskTransform.xy + aPos * uMaskTransform.zw;
            }
        """
        fs = """
            uniform lowp sampler2D uTcurrent;
            uniform lowp sampler2D uTnext;
            uniform mediump sampler2D uMaskTex;
            uniform mediump vec2 uAlphaTransform;
            varying mediump vec2 vTexCoord;
            varying mediump vec2 vMaskCoord;
            void main() {
                mediump float mask = texture2D(uMaskTex, vMaskCoord).r;
                mask = (mask + uAlphaTransform.x) * uAlphaTransform.y;
                mask = smoothstep(0.0, 1.0, mask);
                gl_FragColor = mix(texture2D(uTnext, vTexCoord), texture2D(uTcurrent, vTexCoord), mask);
                // gl_FragColor = texture2D(uMaskTex, vMaskCoord);  // uncomment for mask debugging
            }
        """
        attributes = { 0: 'aPos' }
        uniforms = [('uTnext', 1), ('uMaskTex', 2), 'uTexTransform', 'uMaskTransform', 'uAlphaTransform']
        def __init__(self):
            GLShader.__init__(self)
            self.mask_tex = gl.make_texture(gl.TEXTURE_2D, gl.CLAMP_TO_EDGE, gl.LINEAR)
    mask = None
    def __init__(self):
        shader = self.WipeShader.get_instance().use()
        gl.Uniform4f(shader.uTexTransform, 0.0, 0.0, TexMaxS, TexMaxT)
        if not self.class_mask:
            self.mask = self.prepare_mask()
        elif not self.mask:
            self.__class__.mask = self.prepare_mask()
    def start(self):
        shader = self.WipeShader.get_instance().use()
        gl.Uniform4f(shader.uMaskTransform,
            0.5 / self.rx, 0.5 / self.ry,
            1.0 - 1.0 / self.rx,
            1.0 - 1.0 / self.ry)
        gl.BindTexture(gl.TEXTURE_2D, shader.mask_tex)
        gl.TexImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, self.rx, self.ry, 0, gl.LUMINANCE, gl.UNSIGNED_BYTE, self.mask)
    def bind_mask_tex(self, shader):
        gl.set_texture(gl.TEXTURE_2D, shader.mask_tex, 2)
    def render(self, t):
        shader = self.WipeShader.get_instance().use()
        self.bind_mask_tex(shader)  # own method b/c WipeBrightness overrides it
        gl.set_texture(gl.TEXTURE_2D, Tnext, 1)
        gl.set_texture(gl.TEXTURE_2D, Tcurrent, 0)
        gl.Uniform2f(shader.uAlphaTransform,
            self.band_size - t * (1.0 + self.band_size),
            1.0 / self.band_size)
        SimpleQuad.draw()
    def prepare_mask(self):
        scale = 1.0 / (self.rx - 1)
        xx = [i * scale for i in xrange((self.rx + 3) & (~3))]
        scale = 1.0 / (self.ry - 1)
        yy = [i * scale for i in xrange(self.ry)]
        def iter2d():
            for y in yy:
                for x in xx:
                    yield (x, y)
        return ''.join(chr(max(0, min(255, int(self.f(x, y) * 255.0 + 0.5)))) for x, y in iter2d())
    def f(self, x, y):
        return 0.5
class WipeLeft(Wipe):
    "wipe from right to left"
    def f(self, x, y):
        return 1.0 - x
class WipeRight(Wipe):
    "wipe from left to right"
    def f(self, x, y):
        return x
class WipeUp(Wipe):
    "wipe upwards"
    def f(self, x, y):
        return 1.0 - y
class WipeDown(Wipe):
    "wipe downwards"
    def f(self, x, y):
        return y
class WipeUpLeft(Wipe):
    "wipe from the lower-right to the upper-left corner"
    def f(self, x, y):
        return 1.0 - 0.5 * (x + y)
class WipeUpRight(Wipe):
    "wipe from the lower-left to the upper-right corner"
    def f(self, x, y):
        return 0.5 * (1.0 - y + x)
class WipeDownLeft(Wipe):
    "wipe from the upper-right to the lower-left corner"
    def f(self, x, y):
        return 0.5 * (1.0 - x + y)
class WipeDownRight(Wipe):
    "wipe from the upper-left to the lower-right corner"
    def f(self, x, y):
        return 0.5 * (x + y)
class WipeCenterOut(Wipe):
    "wipe from the center outwards"
    rx, ry = 64, 32
    def __init__(self):
        self.scale = 1.0
        self.scale = 1.0 / self.f(0.0, 0.0)
        Wipe.__init__(self)
    def f(self, x, y):
        return hypot((x - 0.5) * DAR, y - 0.5) * self.scale
class WipeCenterIn(Wipe):
    "wipe from the corners inwards"
    rx, ry = 64, 32
    def __init__(self):
        self.scale = 1.0
        self.scale = 1.0 / (1.0 - self.f(0.0, 0.0))
        Wipe.__init__(self)
    def f(self, x, y):
        return 1.0 - hypot((x - 0.5) * DAR, y - 0.5) * self.scale
class WipeBlobs(Wipe):
    """wipe using nice "blob"-like patterns"""
    rx, ry = 64, 32
    class_mask = False
    def __init__(self):
        self.x0 = random.random() * 6.2
        self.y0 = random.random() * 6.2
        self.sx = (random.random() * 15.0 + 5.0) * DAR
        self.sy =  random.random() * 15.0 + 5.0
        Wipe.__init__(self)
    def f(self, x, y):
        return 0.5 + 0.25 * (cos(self.x0 + self.sx * x) + cos(self.y0 + self.sy * y))
class WipeClouds(Wipe):
    """wipe using cloud-like patterns"""
    rx, ry = 128, 128
    class_mask = False
    decay = 0.25
    blur = 5
    def prepare_mask(self):
        assert self.rx == self.ry
        noise = str2img('L', (self.rx * 4, self.ry * 2), ''.join(map(chr, (random.randrange(256) for i in xrange(self.rx * self.ry * 8)))))
        img = Image.new('L', (1, 1), random.randrange(256))
        alpha = 1.0
        npos = 0
        border = 0
        while img.size[0] <= self.rx:
            border += 2
            next = img.size[0] * 2
            alpha *= self.decay
            img = Image.blend(
                img.resize((next, next), Image.BILINEAR),
                noise.crop((npos, 0, npos + next, next)),
                alpha)
            npos += next
        img = ImageOps.equalize(ImageOps.autocontrast(img))
        for i in xrange(self.blur):
            img = img.filter(ImageFilter.BLUR)
        img = img.crop((border, border, img.size[0] - 2 * border, img.size[1] - 2 * border)).resize((self.rx, self.ry), Image.ANTIALIAS)
        return img2str(img)
class WipeBrightness1(Wipe):
    """wipe based on the current slide's brightness"""
    band_size = 1.0
    def prepare_mask(self):
        return True  # dummy
    def start(self):
        shader = self.WipeShader.get_instance().use()
        gl.Uniform4f(shader.uMaskTransform, 0.0, 0.0, TexMaxS, TexMaxT)
    def bind_mask_tex(self, dummy):
        gl.set_texture(gl.TEXTURE_2D, Tcurrent, 2)
class WipeBrightness2(WipeBrightness1):
    """wipe based on the next slide's brightness"""
    def bind_mask_tex(self, dummy):
        gl.set_texture(gl.TEXTURE_2D, Tnext, 2)
AllTransitions.extend([WipeLeft, WipeRight, WipeUp, WipeDown, WipeUpLeft, WipeUpRight, WipeDownLeft, WipeDownRight, WipeCenterOut, WipeCenterIn, WipeBlobs, WipeClouds, WipeBrightness1, WipeBrightness2])


class PagePeel(Transition):
    "an unrealistic, but nice page peel effect"
    class PagePeel_PeeledPageShader(GLShader):
        vs = """
            attribute highp vec2 aPos;
            uniform highp vec4 uPosTransform;
            varying mediump vec2 vTexCoord;
            void main() {
                highp vec2 pos = uPosTransform.xy + aPos * uPosTransform.zw;
                gl_Position = vec4(vec2(-1.0, 1.0) + pos * vec2(2.0, -2.0), 0.0, 1.0);
                vTexCoord = aPos + vec2(0.0, -0.5);
            }
        """
        fs = """
            uniform lowp sampler2D uTex;
            uniform highp vec4 uTexTransform;
            uniform highp float uHeight;
            uniform mediump float uShadowStrength;
            varying mediump vec2 vTexCoord;
            void main() {
                mediump vec2 tc = vTexCoord;
                tc.y *= 1.0 - tc.x * uHeight;
                tc.x = mix(tc.x, tc.x * tc.x, uHeight);
                tc = uTexTransform.xy + (tc + vec2(0.0, 0.5)) * uTexTransform.zw;
                mediump float shadow_pos = 1.0 - vTexCoord.x;
                mediump float light = 1.0 - (shadow_pos * shadow_pos) * uShadowStrength;
                gl_FragColor = vec4(light, light, light, 1.0) * texture2D(uTex, tc);
            }
        """
        attributes = { 0: 'aPos' }
        uniforms = ['uPosTransform', 'uTexTransform', 'uHeight', 'uShadowStrength']
    class PagePeel_RevealedPageShader(GLShader):
        vs = """
            attribute highp vec2 aPos;
            uniform highp vec4 uPosTransform;
            uniform highp vec4 uTexTransform;
            varying mediump vec2 vTexCoord;
            varying mediump float vShadowPos;
            void main() {
                highp vec2 pos = uPosTransform.xy + aPos * uPosTransform.zw;
                gl_Position = vec4(vec2(-1.0, 1.0) + pos * vec2(2.0, -2.0), 0.0, 1.0);
                vShadowPos = 1.0 - aPos.x;
                vTexCoord = uTexTransform.xy + aPos * uTexTransform.zw;
            }
        """
        fs = """
            uniform lowp sampler2D uTex;
            uniform mediump float uShadowStrength;
            varying mediump vec2 vTexCoord;
            varying mediump float vShadowPos;
            void main() {
                mediump float light = 1.0 - (vShadowPos * vShadowPos) * uShadowStrength;
                gl_FragColor = vec4(light, light, light, 1.0) * texture2D(uTex, vTexCoord);
            }
        """
        attributes = { 0: 'aPos' }
        uniforms = ['uPosTransform', 'uTexTransform', 'uShadowStrength']
    def __init__(self):
        shader = self.PagePeel_PeeledPageShader.get_instance().use()
        gl.Uniform4f(shader.uTexTransform, 0.0, 0.0, TexMaxS, TexMaxT)
        self.PagePeel_RevealedPageShader.get_instance()
    def render(self, t):
        angle = t * 0.5 * pi
        split = cos(angle)
        height = sin(angle)
        # draw the old page that is peeled away
        gl.BindTexture(gl.TEXTURE_2D, Tcurrent)
        shader = self.PagePeel_PeeledPageShader.get_instance().use()
        gl.Uniform4f(shader.uPosTransform, 0.0, 0.0, split, 1.0)
        gl.Uniform1f(shader.uHeight, height * 0.25)
        gl.Uniform1f(shader.uShadowStrength, 0.2 * (1.0 - split));
        SimpleQuad.draw()
        # draw the new page that is revealed
        gl.BindTexture(gl.TEXTURE_2D, Tnext)
        shader = self.PagePeel_RevealedPageShader.get_instance().use()
        gl.Uniform4f(shader.uPosTransform, split, 0.0, 1.0 - split, 1.0)
        gl.Uniform4f(shader.uTexTransform, split * TexMaxS, 0.0, (1.0 - split) * TexMaxS, TexMaxT)
        gl.Uniform1f(shader.uShadowStrength, split);
        SimpleQuad.draw()
AllTransitions.append(PagePeel)


# the AvailableTransitions array contains a list of all transition classes that
# can be randomly assigned to pages;
# this selection normally only includes "unintrusive" transtitions, i.e. mostly
# crossfade/wipe variations
AvailableTransitions = [ # from coolest to lamest
    WipeBlobs,
    WipeCenterOut,
    WipeDownRight, WipeRight, WipeDown
]


##### OSD FONT RENDERER ########################################################

# force a string or sequence of ordinals into a unicode string
def ForceUnicode(s, charset='iso8859-15'):
    if type(s) == types.UnicodeType:
        return s
    if type(s) == types.StringType:
        return unicode(s, charset, 'ignore')
    if type(s) in (types.TupleType, types.ListType):
        return u''.join(map(unichr, s))
    raise TypeError, "string argument not convertible to Unicode"

# search a system font path for a font file
def SearchFont(root, name):
    if not os.path.isdir(root):
        return None
    infix = ""
    fontfile = []
    while (len(infix) < 10) and not(fontfile):
        fontfile = filter(os.path.isfile, glob.glob(root + infix + name))
        infix += "*/"
    if not fontfile:
        return None
    else:
        return fontfile[0]

# load a system font
def LoadFont(dirs, name, size):
    # first try to load the font directly
    try:
        return ImageFont.truetype(name, size, encoding='unic')
    except:
        pass
    # no need to search further on Windows
    if os.name == 'nt':
        return None
    # start search for the font
    for dir in dirs:
        fontfile = SearchFont(dir + "/", name)
        if fontfile:
            try:
                return ImageFont.truetype(fontfile, size, encoding='unic')
            except:
                pass
    return None

# alignment constants
Left = 0
Right = 1
Center = 2
Down = 0
Up = 1
Auto = -1

# font renderer class
class GLFont:
    def __init__(self, width, height, name, size, search_path=[], default_charset='iso8859-15', extend=1, blur=1):
        self.width = width
        self.height = height
        self._i_extend = range(extend)
        self._i_blur = range(blur)
        self.feather = extend + blur + 1
        self.current_x = 0
        self.current_y = 0
        self.max_height = 0
        self.boxes = {}
        self.widths = {}
        self.line_height = 0
        self.default_charset = default_charset
        if isinstance(name, basestring):
            self.font = LoadFont(search_path, name, size)
        else:
            for check_name in name:
                self.font = LoadFont(search_path, check_name, size)
                if self.font: break
        if not self.font:
            raise IOError, "font file not found"
        self.img = Image.new('LA', (width, height))
        self.alpha = Image.new('L', (width, height))
        self.extend = ImageFilter.MaxFilter()
        self.blur = ImageFilter.Kernel((3, 3), [1,2,1,2,4,2,1,2,1])
        self.tex = gl.make_texture(gl.TEXTURE_2D, filter=gl.NEAREST)
        self.AddString(range(32, 128))
        self.vertices = None
        self.index_buffer = None
        self.index_buffer_capacity = 0

    def AddCharacter(self, c):
        w, h = self.font.getsize(c)
        try:
            ox, oy = self.font.getoffset(c)
            w += ox
            h += oy
        except AttributeError:
            pass
        self.line_height = max(self.line_height, h)
        size = (w + 2 * self.feather, h + 2 * self.feather)
        glyph = Image.new('L', size)
        draw = ImageDraw.Draw(glyph)
        draw.text((self.feather, self.feather), c, font=self.font, fill=255)
        del draw

        box = self.AllocateGlyphBox(*size)
        self.img.paste(glyph, (box.orig_x, box.orig_y))

        for i in self._i_extend: glyph = glyph.filter(self.extend)
        for i in self._i_blur:   glyph = glyph.filter(self.blur)
        self.alpha.paste(glyph, (box.orig_x, box.orig_y))

        self.boxes[c] = box
        self.widths[c] = w
        del glyph

    def AddString(self, s, charset=None, fail_silently=False):
        update_count = 0
        try:
            for c in ForceUnicode(s, self.GetCharset(charset)):
                if c in self.widths:
                    continue
                self.AddCharacter(c)
                update_count += 1
        except ValueError:
            if fail_silently:
                pass
            else:
                raise
        if not update_count: return
        self.img.putalpha(self.alpha)
        gl.load_texture(gl.TEXTURE_2D, self.tex, self.img)

    def AllocateGlyphBox(self, w, h):
        if self.current_x + w > self.width:
            self.current_x = 0
            self.current_y += self.max_height
            self.max_height = 0
        if self.current_y + h > self.height:
            raise ValueError, "bitmap too small for all the glyphs"
        box = self.GlyphBox()
        box.orig_x = self.current_x
        box.orig_y = self.current_y
        box.size_x = w
        box.size_y = h
        box.x0 =  self.current_x      / float(self.width)
        box.y0 =  self.current_y      / float(self.height)
        box.x1 = (self.current_x + w) / float(self.width)
        box.y1 = (self.current_y + h) / float(self.height)
        box.dsx = w * PixelX
        box.dsy = h * PixelY
        self.current_x += w
        self.max_height = max(self.max_height, h)
        return box

    def GetCharset(self, charset=None):
        if charset: return charset
        return self.default_charset

    def SplitText(self, s, charset=None):
        return ForceUnicode(s, self.GetCharset(charset)).split(u'\n')

    def GetLineHeight(self):
        return self.line_height

    def GetTextWidth(self, s, charset=None):
        return max([self.GetTextWidthEx(line) for line in self.SplitText(s, charset)])

    def GetTextHeight(self, s, charset=None):
        return len(self.SplitText(s, charset)) * self.line_height

    def GetTextSize(self, s, charset=None):
        lines = self.SplitText(s, charset)
        return (max([self.GetTextWidthEx(line) for line in lines]), len(lines) * self.line_height)

    def GetTextWidthEx(self, u):
        if u: return sum([self.widths.get(c, 0) for c in u])
        else: return 0

    def GetTextHeightEx(self, u=[]):
        return self.line_height

    def AlignTextEx(self, x, u, align=Left):
        if not align: return x
        return x - (self.GetTextWidthEx(u) / align)

    class FontShader(GLShader):
        vs = """
            attribute highp vec4 aPosAndTexCoord;
            varying mediump vec2 vTexCoord;
            void main() {
                gl_Position = vec4(vec2(-1.0, 1.0) + aPosAndTexCoord.xy * vec2(2.0, -2.0), 0.0, 1.0);
                vTexCoord = aPosAndTexCoord.zw;
            }
        """
        fs = """
            uniform lowp sampler2D uTex;
            uniform lowp vec4 uColor;
            varying mediump vec2 vTexCoord;
            void main() {
                gl_FragColor = uColor * texture2D(uTex, vTexCoord);
            }
        """
        attributes = { 0: 'aPosAndTexCoord' }
        uniforms = ['uColor']

    def BeginDraw(self):
        self.vertices = []

    def EndDraw(self, color=(1.0, 1.0, 1.0), alpha=1.0, beveled=True):
        if not self.vertices:
            self.vertices = None
            return
        char_count = len(self.vertices) / 16
        if char_count > 16383:
            print >>sys.stderr, "Internal Error: too many characters (%d) to display in one go, truncating." % char_count
            char_count = 16383

        # create an index buffer large enough for the text
        if not(self.index_buffer) or (self.index_buffer_capacity < char_count):
            self.index_buffer_capacity = (char_count + 63) & (~63)
            data = []
            for b in xrange(0, self.index_buffer_capacity * 4, 4):
                data.extend([b+0, b+2, b+1, b+1, b+2, b+3])
            if not self.index_buffer:
                self.index_buffer = gl.GenBuffers()
            gl.BindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.index_buffer)
            gl.BufferData(gl.ELEMENT_ARRAY_BUFFER, data=data, type=gl.UNSIGNED_SHORT, usage=gl.DYNAMIC_DRAW)
        else:
            gl.BindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.index_buffer)

        # set the vertex buffer
        vbuf = (c_float * len(self.vertices))(*self.vertices)
        gl.BindBuffer(gl.ARRAY_BUFFER, 0)
        gl.set_enabled_attribs(0)
        gl.VertexAttribPointer(0, 4, gl.FLOAT, False, 0, vbuf)

        # draw it
        shader = self.FontShader.get_instance().use()
        gl.BindTexture(gl.TEXTURE_2D, self.tex)
        if beveled:
            gl.BlendFunc(gl.ZERO, gl.ONE_MINUS_SRC_ALPHA)
            gl.Uniform4f(shader.uColor, 0.0, 0.0, 0.0, alpha)
            gl.DrawElements(gl.TRIANGLES, char_count * 6, gl.UNSIGNED_SHORT, 0)
        gl.BlendFunc(gl.ONE, gl.ONE)
        gl.Uniform4f(shader.uColor, color[0] * alpha, color[1] * alpha, color[2] * alpha, 1.0)
        gl.DrawElements(gl.TRIANGLES, char_count * 6, gl.UNSIGNED_SHORT, 0)
        gl.BlendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)
        self.vertices = None

    def Draw(self, origin, text, charset=None, align=Left, color=(1.0, 1.0, 1.0), alpha=1.0, beveled=True, bold=False):
        own_draw = (self.vertices is None)
        if own_draw:
            self.BeginDraw()
        lines = self.SplitText(text, charset)
        x0, y = origin
        x0 -= self.feather
        y -= self.feather
        for line in lines:
            sy = y * PixelY
            x = self.AlignTextEx(x0, line, align)
            for c in line:
                if not c in self.widths: continue
                self.boxes[c].add_vertices(self.vertices, x * PixelX, sy)
                x += self.widths[c]
            y += self.line_height
        if bold and not(beveled):
            self.Draw((origin[0] + 1, origin[1]), text, charset=charset, align=align, color=color, alpha=alpha, beveled=False, bold=False)
        if own_draw:
            self.EndDraw(color, alpha, beveled)

    class GlyphBox:
        def add_vertices(self, vertex_list, sx=0.0, sy=0.0):
            vertex_list.extend([
                sx,            sy,            self.x0, self.y0,
                sx + self.dsx, sy,            self.x1, self.y0,
                sx,            sy + self.dsy, self.x0, self.y1,
                sx + self.dsx, sy + self.dsy, self.x1, self.y1,
            ])

# high-level draw function
def DrawOSD(x, y, text, halign=Auto, valign=Auto, alpha=1.0):
    if not(OSDFont) or not(text) or (alpha <= 0.004): return
    if alpha > 1.0: alpha = 1.0
    if halign == Auto:
        if x < 0:
            x += ScreenWidth
            halign = Right
        else:
            halign = Left
    if HalfScreen and (halign == Left):
        x += ScreenWidth / 2
    if valign == Auto:
        if y < 0:
            y += ScreenHeight
            valign = Up
        else:
            valign = Down
        if valign != Down:
            y -= OSDFont.GetLineHeight() / valign
    OSDFont.Draw((x, y), text, align=halign, alpha=alpha)

# very high-level draw function
def DrawOSDEx(position, text, alpha_factor=1.0):
    xpos = position >> 1
    y = (1 - 2 * (position & 1)) * OSDMargin
    if xpos < 2:
        x = (1 - 2 * xpos) * OSDMargin
        halign = Auto
    else:
        x = ScreenWidth / 2
        halign = Center
    DrawOSD(x, y, text, halign, alpha = OSDAlpha * alpha_factor)

RequiredShaders.append(GLFont.FontShader)


##### PDF PARSER ###############################################################

class PDFError(Exception):
    pass

class PDFref:
    def __init__(self, ref):
        self.ref = ref
    def __repr__(self):
        return "PDFref(%d)" % self.ref

re_pdfstring = re.compile(r'\(\)|\(.*?[^\\]\)')
pdfstringrepl = [("\\"+x[0], x[1:]) for x in "(( )) n\n r\r t\t".split(" ")]
def pdf_maskstring(s):
    s = s[1:-1]
    for a, b in pdfstringrepl:
        s = s.replace(a, b)
    return " <" + "".join(["%02X"%ord(c) for c in s]) + "> "
def pdf_mask_all_strings(s):
    return re_pdfstring.sub(lambda x: pdf_maskstring(x.group(0)), s)
def pdf_unmaskstring(s):
    return "".join([chr(int(s[i:i+2], 16)) for i in xrange(1, len(s)-1, 2)])

class PDFParser:
    def __init__(self, filename):
        self.f = file(filename, "rb")
        self.errors = 0

        # find the first cross-reference table
        self.f.seek(0, 2)
        filesize = self.f.tell()
        self.f.seek(filesize - 128)
        trailer = self.f.read()
        i = trailer.rfind("startxref")
        if i < 0:
            raise PDFError, "cross-reference table offset missing"
        try:
            offset = int(trailer[i:].split("\n")[1].strip())
        except (IndexError, ValueError):
            raise PDFError, "malformed cross-reference table offset"

        # follow the trailer chain
        self.xref = {}
        while offset:
            newxref = self.xref
            self.xref, rootref, offset = self.parse_trailer(offset)
            self.xref.update(newxref)

        # scan the page and names tree
        self.obj2page = {}
        self.page2obj = {}
        self.annots = {}
        self.page_count = 0
        self.box = {}
        self.names = {}
        self.rotate = {}
        root = self.getobj(rootref, 'Catalog')
        try:
            self.scan_page_tree(root['Pages'].ref)
        except KeyError:
            raise PDFError, "root page tree node missing"
        try:
            self.scan_names_tree(root['Names'].ref)
        except KeyError:
            pass

    def getline(self):
        while True:
            line = self.f.readline().strip()
            if line: return line

    def find_length(self, tokens, begin, end):
        level = 1
        for i in xrange(1, len(tokens)):
            if tokens[i] == begin:  level += 1
            if tokens[i] == end:    level -= 1
            if not level: break
        return i + 1

    def parse_tokens(self, tokens, want_list=False):
        res = []
        while tokens:
            t = tokens[0]
            v = t
            tlen = 1
            if (len(tokens) >= 3) and (tokens[2] == 'R'):
                v = PDFref(int(t))
                tlen = 3
            elif t == "<<":
                tlen = self.find_length(tokens, "<<", ">>")
                v = self.parse_tokens(tokens[1 : tlen - 1], True)
                v = dict(zip(v[::2], v[1::2]))
            elif t == "[":
                tlen = self.find_length(tokens, "[", "]")
                v = self.parse_tokens(tokens[1 : tlen - 1], True)
            elif not(t) or (t[0] == "null"):
                v = None
            elif (t[0] == '<') and (t[-1] == '>'):
                v = pdf_unmaskstring(t)
            elif t[0] == '/':
                v = t[1:]
            elif t == 'null':
                v = None
            else:
                try:
                    v = float(t)
                    v = int(t)
                except ValueError:
                    pass
            res.append(v)
            del tokens[:tlen]
        if want_list:
            return res
        if not res:
            return None
        if len(res) == 1:
            return res[0]
        return res

    def parse(self, data):
        data = pdf_mask_all_strings(data)
        data = data.replace("<<", " << ").replace("[", " [ ").replace("(", " (")
        data = data.replace(">>", " >> ").replace("]", " ] ").replace(")", ") ")
        data = data.replace("/", " /").replace("><", "> <")
        return self.parse_tokens(filter(None, data.split()))

    def getobj(self, obj, force_type=None):
        if isinstance(obj, PDFref):
            obj = obj.ref
        if type(obj) != types.IntType:
            raise PDFError, "object is not a valid reference"
        offset = self.xref.get(obj, 0)
        if not offset:
            raise PDFError, "referenced non-existing PDF object"
        self.f.seek(offset)
        header = self.getline().split(None, 3)
        if (len(header) < 3) or (header[2] != "obj") or (header[0] != str(obj)):
            raise PDFError, "object does not start where it's supposed to"
        if len(header) == 4:
            data = [header[3]]
        else:
            data = []
        while True:
            line = self.getline()
            if line in ("endobj", "stream"): break
            data.append(line)
        data = self.parse(" ".join(data))
        if force_type:
            try:
                t = data['Type']
            except (KeyError, IndexError, ValueError):
                t = None
            if t != force_type:
                raise PDFError, "object does not match the intended type"
        return data

    def parse_xref_section(self, start, count):
        xref = {}
        for obj in xrange(start, start + count):
            line = self.getline()
            if line[-1] == 'f':
                xref[obj] = 0
            else:
                xref[obj] = int(line[:10], 10)
        return xref

    def parse_trailer(self, offset):
        self.f.seek(offset)
        xref = {}
        rootref = 0
        offset = 0
        if self.getline() != "xref":
            raise PDFError, "cross-reference table does not start where it's supposed to"
            return (xref, rootref, offset)   # no xref table found, abort
        # parse xref sections
        while True:
            line = self.getline()
            if line == "trailer": break
            start, count = map(int, line.split())
            xref.update(self.parse_xref_section(start, count))
        # parse trailer
        trailer = ""
        while True:
            line = self.getline()
            if line in ("startxref", "%%EOF"): break
            trailer += line
        trailer = self.parse(trailer)
        try:
            rootref = trailer['Root'].ref
        except KeyError:
            raise PDFError, "root catalog entry missing"
        except AttributeError:
            raise PDFError, "root catalog entry is not a reference"
        return (xref, rootref, trailer.get('Prev', 0))

    def scan_page_tree(self, obj, mbox=None, cbox=None, rotate=0):
        try:
            node = self.getobj(obj)
            if node['Type'] == 'Pages':
                for kid in node['Kids']:
                    self.scan_page_tree(kid.ref, \
                                        node.get('MediaBox', mbox), \
                                        node.get('CropBox', cbox), \
                                        node.get('Rotate', 0))
            else:
                page = self.page_count + 1
                anode = node.get('Annots', [])
                if anode.__class__ == PDFref:
                    anode = self.getobj(anode.ref)
                self.page_count = page
                self.obj2page[obj] = page
                self.page2obj[page] = obj
                self.box[page] = node.get('CropBox', cbox) or node.get('MediaBox', mbox)
                self.rotate[page] = node.get('Rotate', rotate)
                self.annots[page] = [a.ref for a in anode]
        except (KeyError, TypeError, ValueError):
            self.errors += 1

    def scan_names_tree(self, obj, come_from=None, name=None):
        try:
            node = self.getobj(obj)
            # if we came from the root node, proceed to Dests
            if not come_from:
                for entry in ('Dests', ):
                    if entry in node:
                        self.scan_names_tree(node[entry], entry)
            elif come_from == 'Dests':
                if 'Kids' in node:
                    for kid in node['Kids']:
                        self.scan_names_tree(kid, come_from)
                elif 'Names' in node:
                    nlist = node['Names']
                    while (len(nlist) >= 2) \
                    and (type(nlist[0]) == types.StringType) \
                    and (nlist[1].__class__ == PDFref):
                        self.scan_names_tree(nlist[1], come_from, nlist[0])
                        del nlist[:2]
                elif name and ('D' in node):
                    page = self.dest2page(node['D'])
                    if page:
                        self.names[name] = page
            # else: unsupported node, don't care
        except PDFError:
            self.errors += 1

    def dest2page(self, dest):
        if type(dest) in (types.StringType, types.UnicodeType):
            return self.names.get(dest, None)
        if type(dest) != types.ListType:
            return dest
        elif dest[0].__class__ == PDFref:
            return self.obj2page.get(dest[0].ref, None)
        else:
            return dest[0]

    def get_href(self, obj):
        try:
            node = self.getobj(obj, 'Annot')
            if node['Subtype'] != 'Link': return None
            dest = None
            if 'Dest' in node:
                dest = self.dest2page(node['Dest'])
            elif 'A' in node:
                a = node['A']
                if isinstance(a, PDFref):
                    a = self.getobj(a)
                action = a['S']
                if action == 'URI':
                    dest = a.get('URI', None)
                    for prefix in ("file://", "file:", "run://", "run:"):
                        if dest.startswith(prefix):
                            dest = urllib.unquote(dest[len(prefix):])
                            break
                elif action == 'Launch':
                    dest = a.get('F', None)
                elif action == 'GoTo':
                    dest = self.dest2page(a.get('D', None))
            if dest:
                return tuple(node['Rect'] + [dest])
        except PDFError:
            self.errors += 1

    def GetHyperlinks(self):
        res = {}
        for page in self.annots:
            try:
                a = filter(None, map(self.get_href, self.annots[page]))
            except (PDFError, TypeError, ValueError):
                self.errors += 1
                a = None
            if a: res[page] = a
        return res


def rotate_coord(x, y, rot):
    if   rot == 1: x, y = 1.0 - y,       x
    elif rot == 2: x, y = 1.0 - x, 1.0 - y
    elif rot == 3: x, y =       y, 1.0 - x
    return (x, y)


def AddHyperlink(page_offset, page, target, linkbox, pagebox, rotate):
    page += page_offset
    if type(target) == types.IntType:
        target += page_offset

    # compute relative position of the link on the page
    w = 1.0 / (pagebox[2] - pagebox[0])
    h = 1.0 / (pagebox[3] - pagebox[1])
    x0 = (linkbox[0] - pagebox[0]) * w
    y0 = (pagebox[3] - linkbox[3]) * h
    x1 = (linkbox[2] - pagebox[0]) * w
    y1 = (pagebox[3] - linkbox[1]) * h

    # get effective rotation
    rotate /= 90
    page_rot = GetPageProp(page, 'rotate')
    if page_rot is None:
        page_rot = Rotation
    if page_rot:
        rotate += page_rot
    while rotate < 0:
        rotate += 1000000
    rotate &= 3

    # rotate the rectangle
    x0, y0 = rotate_coord(x0, y0, rotate)
    x1, y1 = rotate_coord(x1, y1, rotate)
    if x0 > x1: x0, x1 = x1, x0
    if y0 > y1: y0, y1 = y1, y0

    # save the hyperlink
    href = (0, target, x0, y0, x1, y1)
    if GetPageProp(page, '_href'):
        PageProps[page]['_href'].append(href)
    else:
        SetPageProp(page, '_href', [href])


def FixHyperlinks(page):
    if not(GetPageProp(page, '_box')) or not(GetPageProp(page, '_href')):
        return  # no hyperlinks or unknown page size
    bx0, by0, bx1, by1 = GetPageProp(page, '_box')
    bdx = bx1 - bx0
    bdy = by1 - by0
    href = []
    for fixed, target, x0, y0, x1, y1 in GetPageProp(page, '_href'):
        if fixed:
            href.append((1, target, x0, y0, x1, y1))
        else:
            href.append((1, target, \
                int(bx0 + bdx * x0), int(by0 + bdy * y0), \
                int(bx0 + bdx * x1), int(by0 + bdy * y1)))
    SetPageProp(page, '_href', href)


def ParsePDF(filename):
    try:
        assert 0 == subprocess.Popen([pdftkPath, filename, "output", TempFileName + ".pdf", "uncompress"]).wait()
    except OSError:
        print >>sys.stderr, "Note: pdftk not found, hyperlinks disabled."
        return
    except AssertionError:
        print >>sys.stderr, "Note: pdftk failed, hyperlinks disabled."
        return

    count = 0
    try:
        try:
            pdf = PDFParser(TempFileName + ".pdf")
            for page, annots in pdf.GetHyperlinks().iteritems():
                for page_offset in FileProps[filename]['offsets']:
                    for a in annots:
                        AddHyperlink(page_offset, page, a[4], a[:4], pdf.box[page], pdf.rotate[page])
                count += len(annots)
                FixHyperlinks(page)
            if pdf.errors:
                print >>sys.stderr, "Note: there are errors in the PDF file, hyperlinks might not work properly"
            del pdf
            return count
        except IOError:
            print >>sys.stderr, "Note: file produced by pdftk not readable, hyperlinks disabled."
        except PDFError, e:
            print >>sys.stderr, "Note: error in PDF file, hyperlinks disabled."
            print >>sys.stderr, "      PDF parser error message:", e
    finally:
        try:
            os.remove(TempFileName + ".pdf")
        except OSError:
            pass


##### PAGE CACHE MANAGEMENT ####################################################

# helper class that allows PIL to write and read image files with an offset
class IOWrapper:
    def __init__(self, f, offset=0):
        self.f = f
        self.offset = offset
        self.f.seek(offset)
    def read(self, count=None):
        if count is None:
            return self.f.read()
        else:
            return self.f.read(count)
    def write(self, data):
        self.f.write(data)
    def seek(self, pos, whence=0):
        assert(whence in (0, 1))
        if whence:
            self.f.seek(pos, 1)
        else:
            self.f.seek(pos + self.offset)
    def tell(self):
        return self.f.tell() - self.offset

# generate a "magic number" that is used to identify persistent cache files
def UpdateCacheMagic():
    global CacheMagic
    pool = [PageCount, ScreenWidth, ScreenHeight, b2s(Scaling), b2s(Supersample), b2s(Rotation)]
    flist = list(FileProps.keys())
    flist.sort(lambda a,b: cmp(a.lower(), b.lower()))
    for f in flist:
        pool.append(f)
        pool.extend(list(GetFileProp(f, 'stat', [])))
    CacheMagic = md5obj("\0".join(map(str, pool))).hexdigest()

# set the persistent cache file position to the current end of the file
def UpdatePCachePos():
    global CacheFilePos
    CacheFile.seek(0, 2)
    CacheFilePos = CacheFile.tell()

# rewrite the header of the persistent cache
def WritePCacheHeader(reset=False):
    pages = ["%08x" % PageCache.get(page, 0) for page in range(1, PageCount+1)]
    CacheFile.seek(0)
    CacheFile.write(CacheMagic + "".join(pages))
    if reset:
        CacheFile.truncate()
    UpdatePCachePos()

# return an image from the persistent cache or None if none is available
def GetPCacheImage(page):
    if CacheMode != PersistentCache:
        return  # not applicable if persistent cache isn't used
    Lcache.acquire()
    try:
        if page in PageCache:
            img = Image.open(IOWrapper(CacheFile, PageCache[page]))
            img.load()
            return img
    finally:
        Lcache.release()

# returns an image from the non-persistent cache or None if none is available
def GetCacheImage(page):
    if CacheMode in (NoCache, PersistentCache):
        return  # not applicable in uncached or persistent-cache mode
    Lcache.acquire()
    try:
        if page in PageCache:
            if CacheMode == FileCache:
                CacheFile.seek(PageCache[page])
                return CacheFile.read(TexSize)
            elif CacheMode == CompressedCache:
                return zlib.decompress(PageCache[page])
            else:
                return PageCache[page]
    finally:
        Lcache.release()

# adds an image to the persistent cache
def AddToPCache(page, img):
    if CacheMode != PersistentCache:
        return  # not applicable if persistent cache isn't used
    Lcache.acquire()
    try:
        if page in PageCache:
            return  # page is already cached and we can't update it safely
                    # -> stop here (the new image will be identical to the old
                    #    one anyway)
        img.save(IOWrapper(CacheFile, CacheFilePos), "ppm")
        PageCache[page] = CacheFilePos
        WritePCacheHeader()
    finally:
        Lcache.release()

# adds an image to the non-persistent cache
def AddToCache(page, data):
    global CacheFilePos
    if CacheMode in (NoCache, PersistentCache):
        return  # not applicable in uncached or persistent-cache mode
    Lcache.acquire()
    try:
        if CacheMode == FileCache:
            if not(page in PageCache):
                PageCache[page] = CacheFilePos
                CacheFilePos += len(data)
            CacheFile.seek(PageCache[page])
            CacheFile.write(data)
        elif CacheMode == CompressedCache:
            PageCache[page] = zlib.compress(data, 1)
        else:
            PageCache[page] = data
    finally:
        Lcache.release()

# invalidates the whole cache
def InvalidateCache():
    global PageCache, CacheFilePos
    Lcache.acquire()
    try:
        PageCache = {}
        if CacheMode == PersistentCache:
            UpdateCacheMagic()
            WritePCacheHeader(True)
        else:
            CacheFilePos = 0
    finally:
        Lcache.release()

# initialize the persistent cache
def InitPCache():
    global CacheFile, CacheMode

    # try to open the pre-existing cache file
    try:
        CacheFile = file(CacheFileName, "rb+")
    except IOError:
        CacheFile = None

    # check the cache magic
    UpdateCacheMagic()
    if CacheFile and (CacheFile.read(32) != CacheMagic):
        print >>sys.stderr, "Cache file mismatch, recreating cache."
        CacheFile.close()
        CacheFile = None

    if CacheFile:
        # if the magic was valid, import cache data
        print >>sys.stderr, "Using already existing persistent cache file."
        for page in range(1, PageCount+1):
            offset = int(CacheFile.read(8), 16)
            if offset:
                PageCache[page] = offset
        UpdatePCachePos()
    else:
        # if the magic was invalid or the file didn't exist, (re-)create it
        try:
            CacheFile = file(CacheFileName, "wb+")
        except IOError:
            print >>sys.stderr, "Error: cannot write the persistent cache file (`%s')" % CacheFileName
            print >>sys.stderr, "Falling back to temporary file cache."
            CacheMode = FileCache
        WritePCacheHeader()


##### PAGE RENDERING ###########################################################

class RenderError(RuntimeError):
    pass
class RendererUnavailable(RenderError):
    pass

class PDFRendererBase(object):
    name = None
    binaries = []
    test_run_args = []
    supports_anamorphic = False
    required_options = []

    @classmethod
    def supports(self, binary):
        if not binary:
            return True
        binary = os.path.basename(binary).lower()
        if binary.endswith(".exe"):
            binary = binary[:-4]
        return (binary in self.binaries)

    def __init__(self, binary=None):
        # search for a working binary and run it to get a list of its options
        self.binary = None
        for test_binary in ([binary] if binary else self.binaries):
            test_binary = FindBinary(test_binary)
            try:
                p = subprocess.Popen([test_binary] + self.test_run_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                data = p.stdout.read()
                p.wait()
            except OSError:
                continue
            self.binary = test_binary
            break
        if not self.binary:
            raise RendererUnavailable("program not found")

        # parse the output into an option list
        data = [line.strip().replace('\t', ' ') for line in data.split('\n')]
        self.options = set([line.split(' ', 1)[0].split('=', 1)[0].strip('-,') for line in data if line.startswith('-')])
        if not(set(self.required_options) <= self.options):
            raise RendererUnavailable("%s does not support all required options" % os.path.basename(self.binary))

    def render(self, filename, page, res, antialias=True):
        raise RenderError()

    def execute(self, args, wait=True):
        args = [self.binary] + args
        if get_thread_id() == RTrunning:
            args = Nice + args
        try:
            process = subprocess.Popen(args)
            if not wait:
                return process
            if process.wait() != 0:
                raise RenderError("rendering failed")
        except OSError, e:
            raise RenderError("could not start renderer - %s" % e)

    def load(self, imgfile, autoremove=False):
        try:
            img = Image.open(imgfile)
            img.load()
        except (KeyboardInterrupt, SystemExit):
            raise
        except IOError, e:
            raise RenderError("could not read image file - %s" % e)
        if autoremove:
            self.remove(imgfile)
        return img

    def remove(self, tmpfile):
        try:
            os.unlink(tmpfile)
        except OSError:
            pass

class MuPDFRenderer(PDFRendererBase):
    name = "MuPDF"
    binaries = ["mudraw", "pdfdraw"]
    test_run_args = []
    required_options = ["o", "r", "b"]

    # helper object for communication with the reader thread
    class ThreadComm(object):
        def __init__(self, imgfile):
            self.imgfile = imgfile
            self.buffer = None
            self.error = None
            self.cancel = False

        def getbuffer(self):
            if self.buffer:
                return self.buffer
            # the reader thread might still be busy reading the last
            # chunks of the data and converting them into a StringIO;
            # let's give it some time
            maxwait = time.time() + (0.1 if self.error else 0.5)
            while not(self.buffer) and (time.time() < maxwait):
                time.sleep(0.01)
            return self.buffer

    @staticmethod
    def ReaderThread(comm):
        try:
            f = open(comm.imgfile, 'rb')
            comm.buffer = cStringIO.StringIO(f.read())
            f.close()
        except IOError, e:
            comm.error = "could not open FIFO for reading - %s" % e

    def render(self, filename, page, res, antialias=True):
        imgfile = TempFileName + ".ppm"
        fifo = False
        if HaveThreads:
            self.remove(imgfile)
            try:
                os.mkfifo(imgfile)
                fifo = True
                comm = self.ThreadComm(imgfile)
                thread.start_new_thread(self.ReaderThread, (comm, ))
            except (OSError, IOError, AttributeError):
                pass
        if not antialias:
            aa_opts = ["-b", "0"]
        else:
            aa_opts = []
        try:
            self.execute([
                "-o", imgfile,
                "-r", str(res[0]),
                ] + aa_opts + [
                filename,
                str(page)
            ])
            if fifo:
                if comm.error:
                    raise RenderError(comm.error)
                if not comm.getbuffer():
                    raise RenderError("could not read from FIFO")
                return self.load(comm.buffer, autoremove=False)
            else:
                return self.load(imgfile)
        finally:
            if fifo:
                comm.error = True
                if not comm.getbuffer():
                    # if rendering failed and the client process didn't write
                    # to the FIFO at all, the reader thread would block in
                    # read() forever; so let's open+close the FIFO to
                    # generate an EOF and thus wake the thead up
                    try:
                        f = open(imgfile, "w")
                        f.close()
                    except IOError:
                        pass
            self.remove(imgfile)
AvailableRenderers.append(MuPDFRenderer)

class XpdfRenderer(PDFRendererBase):
    name = "Xpdf/Poppler"
    binaries = ["pdftoppm"]
    test_run_args = ["-h"]
    required_options = ["q", "f", "l", "r"]

    def __init__(self, binary=None):
        PDFRendererBase.__init__(self, binary)
        self.supports_anamorphic = ('rx' in self.options) and ('ry' in self.options)

    def render(self, filename, page, res, antialias=True):
        if self.supports_anamorphic:
            args = ["-rx", str(res[0]), "-ry", str(res[1])]
        else:
            args = ["-r", str(res[0])]
        if not antialias:
            for arg in ("aa", "aaVector"):
                if arg in self.options:
                    args += ['-'+arg, 'no']
        self.execute([
            "-q",
            "-f", str(page),
            "-l", str(page)
            ] + args + [
            filename,
            TempFileName
        ])
        digits = GetFileProp(filename, 'digits', 6)
        try_digits = range(6, 0, -1)
        try_digits.sort(key=lambda n: abs(n - digits))
        try_digits = [(n, TempFileName + ("-%%0%dd.ppm" % n) % page) for n in try_digits]
        for digits, imgfile in try_digits:
            if not os.path.exists(imgfile):
                continue
            SetFileProp(filename, 'digits', digits)
            return self.load(imgfile, autoremove=True)
        raise RenderError("could not find generated image file")
AvailableRenderers.append(XpdfRenderer)

class GhostScriptRenderer(PDFRendererBase):
    name = "GhostScript"
    binaries = ["gs", "gswin32c"]
    test_run_args = ["--version"]
    supports_anamorphic = True

    def render(self, filename, page, res, antialias=True):
        imgfile = TempFileName + ".tif"
        aa_bits = (4 if antialias else 1)
        try:
            self.execute(["-q"] + GhostScriptPlatformOptions + [
                "-dBATCH", "-dNOPAUSE",
                "-sDEVICE=tiff24nc",
                "-dUseCropBox",
                "-sOutputFile=" + imgfile,
                "-dFirstPage=%d" % page,
                "-dLastPage=%d" % page,
                "-r%dx%d" % res,
                "-dTextAlphaBits=%d" % aa_bits,
                "-dGraphicsAlphaBits=%s" % aa_bits,
                filename
            ])
            return self.load(imgfile)
        finally:
            self.remove(imgfile)
AvailableRenderers.append(GhostScriptRenderer)

def InitPDFRenderer():
    global PDFRenderer
    if PDFRenderer:
        return PDFRenderer
    fail_reasons = []
    for r_class in AvailableRenderers:
        if not r_class.supports(PDFRendererPath):
            continue
        try:
            PDFRenderer = r_class(PDFRendererPath)
            print >>sys.stderr, "PDF renderer:", PDFRenderer.name
            return PDFRenderer
        except RendererUnavailable, e:
            if Verbose:
                print >>sys.stderr, "Not using %s for PDF rendering:" % r_class.name, e
            else:
                fail_reasons.append((r_class.name, str(e)))
    print >>sys.stderr, "ERROR: PDF renderer initialization failed."
    for item in fail_reasons:
        print >>sys.stderr, "       - %s: %s" % item
    print >>sys.stderr, "       Display of PDF files will not be supported."


# generate a dummy image
def DummyPage():
    img = Image.new('RGB', (ScreenWidth, ScreenHeight))
    img.paste(LogoImage, ((ScreenWidth  - LogoImage.size[0]) / 2,
                          (ScreenHeight - LogoImage.size[1]) / 2))
    return img

# load a page from a PDF file
def RenderPDF(page, MayAdjustResolution, ZoomMode):
    if not PDFRenderer:
        return DummyPage()

    # load props
    SourceFile = GetPageProp(page, '_file')
    RealPage = GetPageProp(page, '_page')
    OutputSizes = GetPageProp(page, '_out')
    if not OutputSizes:
        OutputSizes = GetFileProp(SourceFile, 'out', [(ScreenWidth + Overscan, ScreenHeight + Overscan), (ScreenWidth + Overscan, ScreenHeight + Overscan)])
        SetPageProp(page, '_out', OutputSizes)
    Resolutions = GetPageProp(page, '_res')
    if not Resolutions:
        Resolutions = GetFileProp(SourceFile, 'res', [(72.0, 72.0), (72.0, 72.0)])
        SetPageProp(page, '_res', Resolutions)
    rot = GetPageProp(page, 'rotate', Rotation)
    out = OutputSizes[rot & 1]
    res = Resolutions[rot & 1]
    zscale = 1

    # handle supersample and zoom mode
    use_aa = True
    if ZoomMode:
        res = (ZoomFactor * res[0], ZoomFactor * res[1])
        out = (ZoomFactor * out[0], ZoomFactor * out[1])
        zscale = ZoomFactor
    elif Supersample:
        res = (Supersample * res[0], Supersample * res[1])
        out = (Supersample * out[0], Supersample * out[1])
        use_aa = False

    # prepare the renderer options
    if PDFRenderer.supports_anamorphic:
        parscale = False
        useres = (int(res[0] + 0.5), int(res[1] + 0.5))
    else:
        parscale = (abs(1.0 - PAR) > 0.01)
        useres = max(res[0], res[1])
        res = (useres, useres)
        useres = int(useres + 0.5)
        useres = (useres, useres)

    # call the renderer
    try:
        img = PDFRenderer.render(SourceFile, RealPage, useres, use_aa)
    except RenderError, e:
        print >>sys.stderr, "ERROR: failed to render page %d:" % page, e
        return DummyPage()

    # apply rotation
    if rot: img = img.rotate(90 * (4 - rot))

    # compute final output image size based on PAR
    if not parscale:
        got = img.size
    elif PAR > 1.0:
        got = (int(img.size[0] / PAR + 0.5), img.size[1])
    else:
        got = (img.size[0], int(img.size[1] * PAR + 0.5))

    # if the image size is strange, re-adjust the rendering resolution
    tolerance = max(4, (ScreenWidth + ScreenHeight) / 400)
    if MayAdjustResolution and (max(abs(got[0] - out[0]), abs(got[1] - out[1])) >= tolerance):
        newout = ZoomToFit((img.size[0], img.size[1] * PAR))
        rscale = (float(newout[0]) / img.size[0], float(newout[1]) / img.size[1])
        if rot & 1:
            newres = (res[0] * rscale[1], res[1] * rscale[0])
        else:
            newres = (res[0] * rscale[0], res[1] * rscale[1])
        # only modify anything if the resolution deviation is large enough
        if max(abs(1.0 - newres[0] / res[0]), abs(1.0 - newres[1] / res[1])) > 0.05:
            # create a copy of the old values: they are lists and thus stored
            # in the PageProps as references; we don't want to influence other
            # pages though
            OutputSizes = OutputSizes[:]
            Resolutions = Resolutions[:]
            # modify the appropriate rotation slot
            OutputSizes[rot & 1] = newout
            Resolutions[rot & 1] = newres
            # store the new values for this page ...
            SetPageProp(page, '_out', OutputSizes)
            SetPageProp(page, '_res', Resolutions)
            # ... and as a default for the file as well (future pages are likely
            # to have the same resolution)
            SetFileProp(SourceFile, 'out', OutputSizes)
            SetFileProp(SourceFile, 'res', Resolutions)
            return RenderPDF(page, False, ZoomMode)

    # downsample a supersampled image
    if Supersample and not(ZoomMode):
        img = img.resize((int(float(out[0]) / Supersample + 0.5),
                          int(float(out[1]) / Supersample + 0.5)), Image.ANTIALIAS)
        parscale = False  # don't scale again

    # perform PAR scaling (required for pdftoppm which doesn't support different
    # dpi for horizontal and vertical)
    if parscale:
        if PAR > 1.0:
            img = img.resize((int(img.size[0] / PAR + 0.5), img.size[1]), Image.ANTIALIAS)
        else:
            img = img.resize((img.size[0], int(img.size[1] * PAR + 0.5)), Image.ANTIALIAS)

    # crop the overscan (if present)
    if Overscan:
        target = (ScreenWidth * zscale, ScreenHeight * zscale)
        scale = None
        if (img.size[1] > target[1]) and (img.size[0] < target[0]):
            scale = float(target[1]) / img.size[1]
        elif (img.size[0] > target[0]) and (img.size[1] < target[1]):
            scale = float(target[0]) / img.size[0]
        if scale:
            w = int(img.size[0] * scale + 0.5)
            h = int(img.size[1] * scale + 0.5)
            if (w <= img.size[0]) and (h <= img.size[1]):
                x0 = (img.size[0] - w) / 2
                y0 = (img.size[1] - h) / 2
                img = img.crop((x0, y0, x0 + w, y0 + h))

    return img


# load a page from an image file
def LoadImage(page, ZoomMode):
    # open the image file with PIL
    try:
        img = Image.open(GetPageProp(page, '_file'))
        img.load()
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        print >>sys.stderr, "Image file `%s' is broken." % GetPageProp(page, '_file')
        return DummyPage()

    # apply rotation
    rot = GetPageProp(page, 'rotate')
    if rot is None:
        rot = Rotation
    if rot:
        img = img.rotate(90 * (4 - rot))

    # determine destination size
    newsize = ZoomToFit((img.size[0], int(img.size[1] * PAR + 0.5)),
                        (ScreenWidth, ScreenHeight))
    # don't scale if the source size is too close to the destination size
    if abs(newsize[0] - img.size[0]) < 2: newsize = img.size
    # don't scale if the source is smaller than the destination
    if not(Scaling) and (newsize > img.size): newsize = img.size
    # zoom up (if wanted)
    if ZoomMode: newsize = (2 * newsize[0], 2 * newsize[1])
    # skip processing if there was no change
    if newsize == img.size: return img

    # select a nice filter and resize the image
    if newsize > img.size:
        filter = Image.BICUBIC
    else:
        filter = Image.ANTIALIAS
    return img.resize(newsize, filter)


# render a page to an OpenGL texture
def PageImage(page, ZoomMode=False, RenderMode=False):
    global OverviewNeedUpdate, HighQualityOverview
    EnableCacheRead = not(ZoomMode or RenderMode)
    EnableCacheWrite = EnableCacheRead and \
                       (page >= PageRangeStart) and (page <= PageRangeEnd)

    # check for the image in the cache
    if EnableCacheRead:
        data = GetCacheImage(page)
        if data: return data

    # if it's not in the temporary cache, render it
    Lrender.acquire()
    try:
        # retrieve the image from the persistent cache or fully re-render it
        if EnableCacheRead:
            img = GetPCacheImage(page)
        else:
            img = None
        if not img:
            if GetPageProp(page, '_page'):
                img = RenderPDF(page, not(ZoomMode), ZoomMode)
            else:
                img = LoadImage(page, ZoomMode)
            if GetPageProp(page, 'invert', InvertPages):
                img = ImageChops.invert(img)
            if EnableCacheWrite:
                AddToPCache(page, img)

        # create black background image to paste real image onto
        if ZoomMode:
            TextureImage = Image.new('RGB', (ZoomFactor * TexWidth, ZoomFactor * TexHeight))
            TextureImage.paste(img, ((ZoomFactor * ScreenWidth  - img.size[0]) / 2, \
                                     (ZoomFactor * ScreenHeight - img.size[1]) / 2))
        else:
            TextureImage = Image.new('RGB', (TexWidth, TexHeight))
            x0 = (ScreenWidth  - img.size[0]) / 2
            y0 = (ScreenHeight - img.size[1]) / 2
            TextureImage.paste(img, (x0, y0))
            SetPageProp(page, '_box', (x0, y0, x0 + img.size[0], y0 + img.size[1]))
            FixHyperlinks(page)

        # paste thumbnail into overview image
        if GetPageProp(page, ('overview', '_overview'), True) \
        and (page >= PageRangeStart) and (page <= PageRangeEnd) \
        and not(GetPageProp(page, '_overview_rendered')) \
        and not(RenderMode):
            pos = OverviewPos(OverviewPageMapInv[page])
            Loverview.acquire()
            try:
                # first, fill the underlying area with black (i.e. remove the dummy logo)
                blackness = Image.new('RGB', (OverviewCellX - OverviewBorder, \
                                              OverviewCellY - OverviewBorder))
                OverviewImage.paste(blackness, (pos[0] + OverviewBorder / 2, \
                                                pos[1] + OverviewBorder))
                del blackness
                # then, scale down the original image and paste it
                if HalfScreen:
                    img = img.crop((0, 0, img.size[0] / 2, img.size[1]))
                sx = OverviewCellX - 2 * OverviewBorder
                sy = OverviewCellY - 2 * OverviewBorder
                if HighQualityOverview:
                    t0 = time.time()
                    img.thumbnail((sx, sy), Image.ANTIALIAS)
                    if (time.time() - t0) > 0.5:
                        print >>sys.stderr, "Note: Your system seems to be quite slow; falling back to a faster,"
                        print >>sys.stderr, "      but slightly lower-quality overview page rendering mode"
                        HighQualityOverview = False
                else:
                    img.thumbnail((sx * 2, sy * 2), Image.NEAREST)
                    img.thumbnail((sx, sy), Image.BILINEAR)
                OverviewImage.paste(img, \
                   (pos[0] + (OverviewCellX - img.size[0]) / 2, \
                    pos[1] + (OverviewCellY - img.size[1]) / 2))
            finally:
                Loverview.release()
            SetPageProp(page, '_overview_rendered', True)
            OverviewNeedUpdate = True
        del img

        # return texture data
        if RenderMode:
            return TextureImage
        data = img2str(TextureImage)
        del TextureImage
    finally:
      Lrender.release()

    # finally add it back into the cache and return it
    if EnableCacheWrite:
        AddToCache(page, data)
    return data

# render a page to an OpenGL texture
def RenderPage(page, target):
    gl.BindTexture(gl.TEXTURE_2D, target)
    while gl.GetError():
        pass  # clear all OpenGL errors
    gl.TexImage2D(gl.TEXTURE_2D, 0, gl.RGB, TexWidth, TexHeight, 0, gl.RGB, gl.UNSIGNED_BYTE, PageImage(page))
    if gl.GetError():
        print >>sys.stderr, "I'm sorry, but your graphics card is not capable of rendering presentations"
        print >>sys.stderr, "in this resolution. Either the texture memory is exhausted, or there is no"
        print >>sys.stderr, "support for large textures (%dx%d). Please try to run Impressive in a" % (TexWidth, TexHeight)
        print >>sys.stderr, "smaller resolution using the -g command-line option."
        sys.exit(1)

# background rendering thread
def RenderThread(p1, p2):
    global RTrunning, RTrestart
    RTrunning = get_thread_id() or True
    RTrestart = True
    while RTrestart:
        RTrestart = False
        for pdf in FileProps:
            if not pdf.lower().endswith(".pdf"): continue
            if RTrestart: break
            SafeCall(ParsePDF, [pdf])
        if RTrestart: continue
        for page in xrange(1, PageCount + 1):
            if RTrestart: break
            if (page != p1) and (page != p2) \
            and (page >= PageRangeStart) and (page <= PageRangeEnd):
                SafeCall(PageImage, [page])
    RTrunning = False
    if CacheMode >= FileCache:
        print >>sys.stderr, "Background rendering finished, used %.1f MiB of disk space." %\
              (CacheFilePos / 1048576.0)
    elif CacheMode >= MemCache:
        print >>sys.stderr, "Background rendering finished, using %.1f MiB of memory." %\
              (sum(map(len, PageCache.itervalues())) / 1048576.0)


##### RENDER MODE ##############################################################

def DoRender():
    global TexWidth, TexHeight
    TexWidth = ScreenWidth
    TexHeight = ScreenHeight
    if os.path.exists(RenderToDirectory):
        print >>sys.stderr, "Destination directory `%s' already exists," % RenderToDirectory
        print >>sys.stderr, "refusing to overwrite anything."
        return 1
    try:
        os.mkdir(RenderToDirectory)
    except OSError, e:
        print >>sys.stderr, "Cannot create destination directory `%s':" % RenderToDirectory
        print >>sys.stderr, e.strerror
        return 1
    print >>sys.stderr, "Rendering presentation into `%s'" % RenderToDirectory
    for page in xrange(1, PageCount + 1):
        PageImage(page, RenderMode=True).save("%s/page%04d.png" % (RenderToDirectory, page))
        sys.stdout.write("[%d] " % page)
        sys.stdout.flush()
    print >>sys.stderr
    print >>sys.stderr, "Done."
    return 0


##### INFO SCRIPT I/O ##########################################################

# info script reader
def LoadInfoScript():
    global PageProps
    try:
        os.chdir(os.path.dirname(InfoScriptPath) or BaseWorkingDir)
    except OSError:
        pass
    OldPageProps = PageProps
    try:
        execfile(InfoScriptPath, globals())
    except IOError:
        pass
    except:
        print >>sys.stderr, "----- Exception in info script ----"
        traceback.print_exc(file=sys.stderr)
        print >>sys.stderr, "----- End of traceback -----"
    NewPageProps = PageProps
    PageProps = OldPageProps
    del OldPageProps
    for page in NewPageProps:
        for prop in NewPageProps[page]:
            SetPageProp(page, prop, NewPageProps[page][prop])
    del NewPageProps

# we can't save lambda expressions, so we need to warn the user
# in every possible way
ScriptTainted = False
LambdaWarning = False
def here_was_a_lambda_expression_that_could_not_be_saved():
    global LambdaWarning
    if not LambdaWarning:
        print >>sys.stderr, "WARNING: The info script for the current file contained lambda expressions that"
        print >>sys.stderr, "         were removed during the a save operation."
        LambdaWarning = True

# "clean" a PageProps entry so that only 'public' properties are left
def GetPublicProps(props):
    props = props.copy()
    # delete private (underscore) props
    for prop in list(props.keys()):
        if str(prop)[0] == '_':
            del props[prop]
    # clean props to default values
    if props.get('overview', False):
        del props['overview']
    if not props.get('skip', True):
        del props['skip']
    if ('boxes' in props) and not(props['boxes']):
        del props['boxes']
    return props

# Generate a string representation of a property value. Mainly this converts
# classes or instances to the name of the class.
def PropValueRepr(value):
    global ScriptTainted
    if type(value) == types.FunctionType:
        if value.__name__ != "<lambda>":
            return value.__name__
        if not ScriptTainted:
            print >>sys.stderr, "WARNING: The info script contains lambda expressions, which cannot be saved"
            print >>sys.stderr, "         back. The modifed script will be written into a separate file to"
            print >>sys.stderr, "         minimize data loss."
            ScriptTainted = True
        return "here_was_a_lambda_expression_that_could_not_be_saved"
    elif type(value) == types.ClassType:
        return value.__name__
    elif type(value) == types.InstanceType:
        return value.__class__.__name__
    elif type(value) == types.DictType:
        return "{ " + ", ".join([PropValueRepr(k) + ": " + PropValueRepr(value[k]) for k in value]) + " }"
    else:
        return repr(value)

# generate a nicely formatted string representation of a page's properties
def SinglePagePropRepr(page):
    props = GetPublicProps(PageProps[page])
    if not props: return None
    return "\n%3d: {%s\n     }" % (page, \
        ",".join(["\n       " + repr(prop) + ": " + PropValueRepr(props[prop]) for prop in props]))

# generate a nicely formatted string representation of all page properties
def PagePropRepr():
    pages = PageProps.keys()
    pages.sort()
    return "PageProps = {%s\n}" % (",".join(filter(None, map(SinglePagePropRepr, pages))))

# count the characters of a python dictionary source code, correctly handling
# embedded strings and comments, and nested dictionaries
def CountDictChars(s, start=0):
    context = None
    level = 0
    for i in xrange(start, len(s)):
        c = s[i]
        if context is None:
            if c == '{': level += 1
            if c == '}': level -= 1
            if c == '#': context = '#'
            if c == '"': context = '"'
            if c == "'": context = "'"
        elif context[0] == "\\":
            context=context[1]
        elif context == '#':
            if c in "\r\n": context = None
        elif context == '"':
            if c == "\\": context = "\\\""
            if c == '"': context = None
        elif context == "'":
            if c == "\\": context = "\\'"
            if c == "'": context = None
        if level < 0: return i
    raise ValueError, "the dictionary never ends"

# modify and save a file's info script
def SaveInfoScript(filename):
    # read the old info script
    try:
        f = file(filename, "r")
        script = f.read()
        f.close()
    except IOError:
        script = ""
    if not script:
        script = "# -*- coding: iso-8859-1 -*-\n"

    # replace the PageProps of the old info script with the current ones
    try:
        m = re.search("^.*(PageProps)\s*=\s*(\{).*$", script,re.MULTILINE)
        if m:
            script = script[:m.start(1)] + PagePropRepr() + \
                     script[CountDictChars(script, m.end(2)) + 1 :]
        else:
            script += "\n" + PagePropRepr() + "\n"
    except (AttributeError, ValueError):
        pass

    if ScriptTainted:
        filename += ".modified"

    # write the script back
    try:
        f = file(filename, "w")
        f.write(script)
        f.close()
    except:
        print >>sys.stderr, "Oops! Could not write info script!"


##### OPENGL RENDERING #########################################################

# draw OSD overlays
def DrawOverlays(trans_time=0.0):
    reltime = Platform.GetTicks() - StartTime
    gl.Enable(gl.BLEND)

    if (EstimatedDuration or PageProgress or (PageTimeout and AutoAdvanceProgress)) \
    and (OverviewMode or GetPageProp(Pcurrent, 'progress', True)):
        r, g, b = ProgressBarColorPage
        a = ProgressBarAlpha
        if PageTimeout and AutoAdvanceProgress:
            rel = (reltime - PageEnterTime) / float(PageTimeout)
            if TransitionRunning:
                a = int(a * (1.0 - TransitionPhase))
            elif PageLeaveTime > PageEnterTime:
                # we'll be called one frame after the transition finished, but
                # before the new page has been fully activated => don't flash
                a = 0
        elif EstimatedDuration:
            rel = (0.001 * reltime) / EstimatedDuration
            if rel < 1.0:
                r, g, b = ProgressBarColorNormal
            elif rel < ProgressBarWarningFactor:
                r, g, b = lerpColor(ProgressBarColorNormal, ProgressBarColorWarning,
                          (rel - 1.0) / (ProgressBarWarningFactor - 1.0))
            elif rel < ProgressBarCriticalFactor:
                r, g, b = lerpColor(ProgressBarColorWarning, ProgressBarColorCritical,
                          (rel - ProgressBarWarningFactor) / (ProgressBarCriticalFactor - ProgressBarWarningFactor))
            else:
                r, g, b = ProgressBarColorCritical
        else:  # must be PageProgress
            rel = (Pcurrent + trans_time * (Pnext - Pcurrent)) / PageCount
        if HalfScreen:
            zero = 0.5
            rel = 0.5 + 0.5 * rel
        else:
            zero = 0.0
        ProgressBarShader.get_instance().draw(
            zero, 1.0 - ProgressBarSizeFactor,
            rel,  1.0,
            color0=(r, g, b, 0.0),
            color1=(r, g, b, a)
        )

    if OSDFont:
        OSDFont.BeginDraw()
        if WantStatus:
            DrawOSDEx(OSDStatusPos, CurrentOSDStatus)
        if TimeDisplay:
            if ShowClock:
                DrawOSDEx(OSDTimePos, ClockTime(MinutesOnly))
            else:
                t = reltime / 1000
                DrawOSDEx(OSDTimePos, FormatTime(t, MinutesOnly))
        if CurrentOSDComment and (OverviewMode or not(TransitionRunning)):
            DrawOSD(ScreenWidth/2, \
                    ScreenHeight - 3*OSDMargin - FontSize, \
                    CurrentOSDComment, Center, Up)
        OSDFont.EndDraw()

    if CursorImage and CursorVisible:
        x, y = Platform.GetMousePos()
        x -= CursorHotspot[0]
        y -= CursorHotspot[1]
        X0 = x * PixelX
        Y0 = y * PixelY
        X1 = X0 + CursorSX
        Y1 = Y0 + CursorSY
        TexturedRectShader.get_instance().draw(
            X0, Y0, X1, Y1,
            s1=CursorTX, t1=CursorTY,
            tex=CursorTexture
        )

    gl.Disable(gl.BLEND)


# draw the complete image of the current page
def DrawCurrentPage(dark=1.0, do_flip=True):
    global ScreenTransform
    if VideoPlaying: return
    boxes = GetPageProp(Pcurrent, 'boxes')
    gl.Clear(gl.COLOR_BUFFER_BIT)

    # pre-transform for zoom
    if ZoomArea != 1.0:
        ScreenTransform = (
            -2.0 * ZoomX0 / ZoomArea - 1.0,
            +2.0 * ZoomY0 / ZoomArea + 1.0,
            +2.0 / ZoomArea,
            -2.0 / ZoomArea
        )

    # background layer -- the page's image, darkened if it has boxes
    is_dark = (boxes or Tracing) and (dark > 0.001)
    if not is_dark:
        # standard mode
        TexturedRectShader.get_instance().draw(
            0.0, 0.0, 1.0, 1.0,
            s1=TexMaxS, t1=TexMaxT,
            tex=Tcurrent
        )
    elif UseBlurShader:
        # blurred background (using shader)
        blur_scale = BoxFadeBlur * ZoomArea * dark
        BlurShader.get_instance().draw(
            PixelX * blur_scale,
            PixelY * blur_scale,
            1.0 - BoxFadeDarkness * dark,
            tex=Tcurrent
        )
        gl.Enable(gl.BLEND)
        # note: BLEND stays enabled during the rest of this function;
        # it will be disabled at the end of DrawOverlays()
    else:
        # blurred background (using oldschool multi-pass blend fallback)
        intensity = 1.0 - BoxFadeDarkness * dark
        for dx, dy, alpha in (
            (0.0,  0.0, 1.0),
            (-ZoomArea, 0.0, dark / 2),
            (+ZoomArea, 0.0, dark / 3),
            (0.0, -ZoomArea, dark / 4),
            (0.0, +ZoomArea, dark / 5),
        ):
            TexturedRectShader.get_instance().draw(
                0.0, 0.0, 1.0, 1.0,
                TexMaxS *  PixelX * dx,
                TexMaxT *  PixelY * dy,
                TexMaxS * (PixelX * dx + 1.0),
                TexMaxT * (PixelY * dy + 1.0),
                tex=Tcurrent,
                color=(intensity, intensity, intensity, alpha)
            )
            gl.Enable(gl.BLEND)
        

    if boxes and is_dark:
        TexturedMeshShader.get_instance().setup(
            0.0, 0.0, 1.0, 1.0,
            s1=TexMaxS, t1=TexMaxT
            # tex is already set
        )
        for X0, Y0, X1, Y1 in boxes:
            vertices = (c_float * 27)(
                X0, Y0, 1.0,  # note: this produces two degenerate triangles
                X0,         Y0,         1.0,
                X0 - EdgeX, Y0 - EdgeY, 0.0,
                X1,         Y0,         1.0,
                X1 + EdgeX, Y0 - EdgeY, 0.0,
                X1,         Y1,         1.0,
                X1 + EdgeX, Y1 + EdgeY, 0.0,
                X0,         Y1,         1.0,
                X0 - EdgeX, Y1 + EdgeY, 0.0,
            )
            gl.BindBuffer(gl.ARRAY_BUFFER, 0)
            gl.VertexAttribPointer(0, 3, gl.FLOAT, False, 0, vertices)
            BoxIndexBuffer.draw()

    if Tracing and is_dark:
        x, y = MouseToScreen(Platform.GetMousePos())
        TexturedMeshShader.get_instance().setup(
            x, y, x + 1.0, y + 1.0,
            x * TexMaxS, y * TexMaxT,
            (x + 1.0) * TexMaxS, (y + 1.0) * TexMaxT
            # tex is already set
        )
        gl.BindBuffer(gl.ARRAY_BUFFER, SpotVertices)
        gl.VertexAttribPointer(0, 3, gl.FLOAT, False, 0, 0)
        SpotIndices.draw()

    if Marking:
        x0 = min(MarkUL[0], MarkLR[0])
        y0 = min(MarkUL[1], MarkLR[1])
        x1 = max(MarkUL[0], MarkLR[0])
        y1 = max(MarkUL[1], MarkLR[1])
        # red frame (misusing the progress bar shader as a single-color shader)
        color = (MarkColor[0], MarkColor[1], MarkColor[2], 1.0)
        ProgressBarShader.get_instance().draw(
            x0 - PixelX * ZoomArea, y0 - PixelY * ZoomArea,
            x1 + PixelX * ZoomArea, y1 + PixelY * ZoomArea,
            color0=color, color1=color
        )
        # semi-transparent inner area
        gl.Enable(gl.BLEND)
        TexturedRectShader.get_instance().draw(
            x0, y0, x1, y1,
            x0 * TexMaxS, y0 * TexMaxT,
            x1 * TexMaxS, y1 * TexMaxT,
            tex=Tcurrent, color=(1.0, 1.0, 1.0, 1.0 - MarkColor[3])
        )

    # unapply the zoom transform
    ScreenTransform = DefaultScreenTransform

    # Done.
    DrawOverlays()
    if do_flip:
        Platform.SwapBuffers()

# draw a black screen with the Impressive logo at the center
def DrawLogo():
    gl.Clear(gl.COLOR_BUFFER_BIT)
    if not ShowLogo:
        return
    if HalfScreen:
        x0 = 0.25
    else:
        x0 = 0.5
    TexturedRectShader.get_instance().draw(
        x0 - 128.0 / ScreenWidth,  0.5 - 32.0 / ScreenHeight,
        x0 + 128.0 / ScreenWidth,  0.5 + 32.0 / ScreenHeight,
        tex=LogoTexture
    )
    if OSDFont:
        gl.Enable(gl.BLEND)
        OSDFont.Draw((int(ScreenWidth * x0), ScreenHeight / 2 + 48), \
                     __version__.split()[0], align=Center, alpha=0.25, beveled=False)
        gl.Disable(gl.BLEND)

# draw the prerender progress bar
def DrawProgress(position):
    x0 = 0.1
    x2 = 1.0 - x0
    x1 = position * x2 + (1.0 - position) * x0
    y1 = 0.9
    y0 = y1 - 16.0 / ScreenHeight
    if HalfScreen:
        x0 *= 0.5
        x1 *= 0.5
        x2 *= 0.5
    ProgressBarShader.get_instance().draw(
        x0, y0, x2, y1,
        color0=(0.25, 0.25, 0.25, 1.0),
        color1=(0.50, 0.50, 0.50, 1.0)
    )
    ProgressBarShader.get_instance().draw(
        x0, y0, x1, y1,
        color0=(0.25, 0.50, 1.00, 1.0),
        color1=(0.03, 0.12, 0.50, 1.0)
    )

# fade mode
def DrawFadeMode(intensity, alpha):
    if VideoPlaying: return
    DrawCurrentPage(do_flip=False)
    gl.Enable(gl.BLEND)
    color = (intensity, intensity, intensity, alpha)
    ProgressBarShader.get_instance().draw(
        0.0, 0.0, 1.0, 1.0,
        color0=color, color1=color
    )
    gl.Disable(gl.BLEND)
    Platform.SwapBuffers()

def EnterFadeMode(intensity=0.0):
    t0 = Platform.GetTicks()
    while True:
        if Platform.CheckAnimationCancelEvent(): break
        t = (Platform.GetTicks() - t0) * 1.0 / BlankFadeDuration
        if t >= 1.0: break
        DrawFadeMode(intensity, t)
    DrawFadeMode(intensity, 1.0)

def LeaveFadeMode(intensity=0.0):
    t0 = Platform.GetTicks()
    while True:
        if Platform.CheckAnimationCancelEvent(): break
        t = (Platform.GetTicks() - t0) * 1.0 / BlankFadeDuration
        if t >= 1.0: break
        DrawFadeMode(intensity, 1.0 - t)
    DrawCurrentPage()

def FadeMode(intensity):
    EnterFadeMode(intensity)
    def fade_action_handler(action):
        if action == "$quit":
            PageLeft()
            Quit()
        elif action == "$expose":
            DrawFadeMode(intensity, 1.0)
        elif action == "*quit":
            Platform.PostQuitEvent()
        else:
            return False
        return True
    while True:
        ev = Platform.GetEvent()
        if ev and not(ProcessEvent(ev, fade_action_handler)) and ev.startswith('*'):
            break
    LeaveFadeMode(intensity)

# gamma control
def SetGamma(new_gamma=None, new_black=None, force=False):
    global Gamma, BlackLevel
    if new_gamma is None: new_gamma = Gamma
    if new_gamma <  0.1:  new_gamma = 0.1
    if new_gamma > 10.0:  new_gamma = 10.0
    if new_black is None: new_black = BlackLevel
    if new_black <   0:   new_black = 0
    if new_black > 254:   new_black = 254
    if not(force) and (abs(Gamma - new_gamma) < 0.01) and (new_black == BlackLevel):
        return
    Gamma = new_gamma
    BlackLevel = new_black
    return Platform.SetGammaRamp(new_gamma, new_black)

# cursor image
def PrepareCustomCursor(cimg):
    global CursorTexture, CursorHotspot, CursorSX, CursorSY, CursorTX, CursorTY
    if not cimg:
        CursorHotspot = (1,0)
        cimg = Image.open(cStringIO.StringIO(DEFAULT_CURSOR.decode('base64')))
    w, h = cimg.size
    tw, th = map(npot, cimg.size)
    if (tw > 256) or (th > 256):
        print >>sys.stderr, "Custom cursor is ridiculously large, reverting to normal one."
        return False
    img = Image.new('RGBA', (tw, th))
    img.paste(cimg, (0, 0))
    CursorTexture = gl.make_texture(gl.TEXTURE_2D, gl.CLAMP_TO_EDGE, gl.NEAREST)
    gl.load_texture(gl.TEXTURE_2D, img)
    CursorSX = w * PixelX
    CursorSY = h * PixelY
    CursorTX = w / float(tw)
    CursorTY = h / float(th)
    return True


##### CONTROL AND NAVIGATION ###################################################

# update the applications' title bar
def UpdateCaption(page=0, force=False):
    global CurrentCaption, CurrentOSDCaption, CurrentOSDPage, CurrentOSDStatus
    global CurrentOSDComment
    if (page == CurrentCaption) and not(force):
        return
    CurrentCaption = page
    caption = __title__
    if DocumentTitle:
        caption += " - " + DocumentTitle
    if page < 1:
        CurrentOSDCaption = ""
        CurrentOSDPage = ""
        CurrentOSDStatus = ""
        CurrentOSDComment = ""
        Platform.SetWindowTitle(caption)
        return
    CurrentOSDPage = "%d/%d" % (page, PageCount)
    caption = "%s (%s)" % (caption, CurrentOSDPage)
    title = GetPageProp(page, 'title') or GetPageProp(page, '_title')
    if title:
        caption += ": %s" % title
        CurrentOSDCaption = title
    else:
        CurrentOSDCaption = ""
    status = []
    if GetPageProp(page, 'skip', False):
        status.append("skipped: yes")
    if not GetPageProp(page, ('overview', '_overview'), True):
        status.append("on overview page: no")
    CurrentOSDStatus = ", ".join(status)
    CurrentOSDComment = GetPageProp(page, 'comment')
    Platform.SetWindowTitle(caption)

# get next/previous page
def GetNextPage(page, direction):
    try_page = page
    while True:
        try_page += direction
        if try_page == page:
            return 0  # tried all pages, but none found
        if Wrap:
            if try_page < 1: try_page = PageCount
            if try_page > PageCount: try_page = 1
        else:
            if try_page < 1 or try_page > PageCount:
                return 0  # start or end of presentation
        if not GetPageProp(try_page, 'skip', False):
            return try_page

# pre-load the following page into Pnext/Tnext
def PreloadNextPage(page):
    global Pnext, Tnext
    if (page < 1) or (page > PageCount):
        Pnext = 0
        return 0
    if page == Pnext:
        return 1
    RenderPage(page, Tnext)
    Pnext = page
    return 1

# perform box fading; the fade animation time is mapped through func()
def BoxFade(func):
    t0 = Platform.GetTicks()
    while BoxFadeDuration > 0:
        if Platform.CheckAnimationCancelEvent(): break
        t = (Platform.GetTicks() - t0) * 1.0 / BoxFadeDuration
        if t >= 1.0: break
        DrawCurrentPage(func(t))
    DrawCurrentPage(func(1.0))
    return 0

# reset the timer
def ResetTimer():
    global StartTime, PageEnterTime
    if TimeTracking and not(FirstPage):
        print "--- timer was reset here ---"
    StartTime = Platform.GetTicks()
    PageEnterTime = 0

# start video playback
def PlayVideo(video):
    global MPlayerProcess, VideoPlaying
    if not video: return
    StopMPlayer()
    opts = ["-quiet", "-slave", \
            "-monitorpixelaspect", "1:1", \
            "-autosync", "100"] + \
            MPlayerPlatformOptions
    if Fullscreen:
        opts += ["-fs"]
    else:
        try:
            opts += ["-wid", str(Platform.GetWindowID())]
        except KeyError:
            print >>sys.stderr, "Sorry, but Impressive only supports video on your operating system if fullscreen"
            print >>sys.stderr, "mode is used."
            VideoPlaying = False
            MPlayerProcess = None
            return
    if not isinstance(video, list):
        video = [video]
    try:
        MPlayerProcess = subprocess.Popen([MPlayerPath] + opts + video, stdin=subprocess.PIPE)
        if MPlayerColorKey:
            gl.Clear(gl.COLOR_BUFFER_BIT)
            Platform.SwapBuffers()
        VideoPlaying = True
    except OSError:
        MPlayerProcess = None

# called each time a page is entered, AFTER the transition, BEFORE entering box-fade mode
def PreparePage():
    global SpotRadius, SpotRadiusBase
    global BoxFadeDarkness, BoxFadeDarknessBase
    override = GetPageProp(Pcurrent, 'radius')
    if override:
        SpotRadius = override
        SpotRadiusBase = override
        GenerateSpotMesh()
    override = GetPageProp(Pcurrent, 'darkness')
    if override is not None:
        BoxFadeDarkness = override * 0.01
        BoxFadeDarknessBase = override * 0.01

# called each time a page is entered, AFTER the transition, AFTER entering box-fade mode
def PageEntered(update_time=True):
    global PageEnterTime, PageTimeout, MPlayerProcess, IsZoomed, WantStatus
    if update_time:
        PageEnterTime = Platform.GetTicks() - StartTime
    IsZoomed = False  # no, we don't have a pre-zoomed image right now
    WantStatus = False  # don't show status unless it's changed interactively
    PageTimeout = AutoAdvance
    shown = GetPageProp(Pcurrent, '_shown', 0)
    try:
        os.chdir(os.path.dirname(GetPageProp(Pcurrent, '_file')))
    except OSError:
        pass
    if not(shown) or Wrap:
        PageTimeout = GetPageProp(Pcurrent, 'timeout', PageTimeout)
    if not(shown) or GetPageProp(Pcurrent, 'always', False):
        video = GetPageProp(Pcurrent, 'video')
        sound = GetPageProp(Pcurrent, 'sound')
        PlayVideo(video)
        if sound and not(video):
            StopMPlayer()
            try:
                MPlayerProcess = subprocess.Popen( \
                    [MPlayerPath, "-quiet", "-really-quiet", "-novideo", sound], \
                    stdin=subprocess.PIPE)
            except OSError:
                MPlayerProcess = None
        SafeCall(GetPageProp(Pcurrent, 'OnEnterOnce'))
    SafeCall(GetPageProp(Pcurrent, 'OnEnter'))
    if PageTimeout:
        Platform.ScheduleEvent("$page-timeout", PageTimeout)
    SetPageProp(Pcurrent, '_shown', shown + 1)

# called each time a page is left
def PageLeft(overview=False):
    global FirstPage, LastPage, WantStatus, PageLeaveTime
    PageLeaveTime = Platform.GetTicks() - StartTime
    WantStatus = False
    if not overview:
        if GetTristatePageProp(Pcurrent, 'reset'):
            ResetTimer()
        FirstPage = False
        LastPage = Pcurrent
        if GetPageProp(Pcurrent, '_shown', 0) == 1:
            SafeCall(GetPageProp(Pcurrent, 'OnLeaveOnce'))
        SafeCall(GetPageProp(Pcurrent, 'OnLeave'))
    if TimeTracking:
        t1 = Platform.GetTicks() - StartTime
        dt = (t1 - PageEnterTime + 500) / 1000
        if overview:
            p = "over"
        else:
            p = "%4d" % Pcurrent
        print "%s%9s%9s%9s" % (p, FormatTime(dt), \
                                  FormatTime(PageEnterTime / 1000), \
                                  FormatTime(t1 / 1000))

# create an instance of a transition class
def InstantiateTransition(trans_class):
    try:
        return trans_class()
    except GLInvalidShaderError:
        return None
    except GLShaderCompileError:
        print >>sys.stderr, "Note: all %s transitions will be disabled" % trans_class.__name__
        return None

# perform a transition to a specified page
def TransitionTo(page, allow_transition=True):
    global Pcurrent, Pnext, Tcurrent, Tnext
    global PageCount, Marking, Tracing, Panning
    global TransitionRunning, TransitionPhase

    # first, stop video and kill the auto-timer
    if VideoPlaying:
        StopMPlayer()
    Platform.ScheduleEvent("$page-timeout", 0)

    # invalid page? go away
    if not PreloadNextPage(page):
        if QuitAtEnd:
            LeaveZoomMode(allow_transition)
            if FadeInOut:
                EnterFadeMode()
            PageLeft()
            Quit()
        return 0

    # leave zoom mode now, if enabled
    LeaveZoomMode(allow_transition)

    # notify that the page has been left
    PageLeft()

    # box fade-out
    if GetPageProp(Pcurrent, 'boxes') or Tracing:
        skip = BoxFade(lambda t: 1.0 - t)
    else:
        skip = 0

    # some housekeeping
    Marking = False
    Tracing = False
    UpdateCaption(page)

    # check if the transition is valid
    tpage = max(Pcurrent, Pnext)
    trans = None
    if allow_transition:
        trans = GetPageProp(tpage, 'transition', GetPageProp(tpage, '_transition'))
    else:
        trans = None
    if trans is not None:
        transtime = GetPageProp(tpage, 'transtime', TransitionDuration)
        try:
            dummy = trans.__class__
        except AttributeError:
            # ah, gotcha! the transition is not yet instantiated!
            trans = InstantiateTransition(trans)
            PageProps[tpage][tkey] = trans
    if trans is None:
        transtime = 0

    # backward motion? then swap page buffers now
    backward = (Pnext < Pcurrent)
    if Wrap and (min(Pcurrent, Pnext) == 1) and (max(Pcurrent, Pnext) == PageCount):
        backward = not(backward)  # special case: last<->first in wrap mode
    if backward:
        Pcurrent, Pnext = (Pnext, Pcurrent)
        Tcurrent, Tnext = (Tnext, Tcurrent)

    # transition animation
    if not(skip) and transtime:
        transtime = 1.0 / transtime
        TransitionRunning = True
        trans.start()
        t0 = Platform.GetTicks()
        while not(VideoPlaying):
            if Platform.CheckAnimationCancelEvent():
                skip = 1
                break
            t = (Platform.GetTicks() - t0) * transtime
            if t >= 1.0: break
            TransitionPhase = t
            if backward: t = 1.0 - t
            gl.Clear(gl.COLOR_BUFFER_BIT)
            trans.render(t)
            DrawOverlays(t)
            Platform.SwapBuffers()
        TransitionRunning = False

    # forward motion => swap page buffers now
    if not backward:
        Pcurrent, Pnext = (Pnext, Pcurrent)
        Tcurrent, Tnext = (Tnext, Tcurrent)

    # prepare the page's changeable metadata
    PreparePage()

    # box fade-in
    if not(skip) and GetPageProp(Pcurrent, 'boxes'): BoxFade(lambda t: t)

    # finally update the screen and preload the next page
    DrawCurrentPage()
    PageEntered()
    if not PreloadNextPage(GetNextPage(Pcurrent, 1)):
        PreloadNextPage(GetNextPage(Pcurrent, -1))
    return 1

# zoom mode animation
def ZoomAnimation(targetx, targety, func, duration_override=None):
    global ZoomX0, ZoomY0, ZoomArea
    t0 = Platform.GetTicks()
    if duration_override is None:
        duration = ZoomDuration
    else:
        duration = duration_override
    while duration > 0:
        if Platform.CheckAnimationCancelEvent(): break
        t = (Platform.GetTicks() - t0) * 1.0 / duration
        if t >= 1.0: break
        t = func(t)
        t = (2.0 - t) * t
        ZoomX0 = targetx * t
        ZoomY0 = targety * t
        ZoomArea = 1.0 - (1.0 - 1.0 / ZoomFactor) * t
        DrawCurrentPage()
    t = func(1.0)
    ZoomX0 = targetx * t
    ZoomY0 = targety * t
    ZoomArea = 1.0 - (1.0 - 1.0 / ZoomFactor) * t
    GenerateSpotMesh()
    DrawCurrentPage()

# enter zoom mode
def EnterZoomMode(targetx, targety):
    global ZoomMode, IsZoomed, HighResZoomFailed
    ZoomAnimation(targetx, targety, lambda t: t)
    ZoomMode = True
    if IsZoomed or HighResZoomFailed:
        return
    gl.BindTexture(gl.TEXTURE_2D, Tcurrent)
    while gl.GetError():
        pass  # clear all OpenGL errors
    gl.TexImage2D(gl.TEXTURE_2D, 0, gl.RGB, ZoomFactor * TexWidth, ZoomFactor * TexHeight, 0, gl.RGB, gl.UNSIGNED_BYTE, PageImage(Pcurrent, True))
    if gl.GetError():
        print >>sys.stderr, "I'm sorry, but your graphics card is not capable of rendering presentations"
        print >>sys.stderr, "in this resolution. Either the texture memory is exhausted, or there is no"
        print >>sys.stderr, "support for large textures (%dx%d). Please try to run Impressive in a" % (TexWidth, TexHeight)
        print >>sys.stderr, "smaller resolution using the -g command-line option."
        HighResZoomFailed = True
        return
    DrawCurrentPage()
    IsZoomed = True

# leave zoom mode (if enabled)
def LeaveZoomMode(allow_transition=True):
    global ZoomMode
    if not ZoomMode: return
    ZoomAnimation(ZoomX0, ZoomY0, lambda t: 1.0 - t, (None if allow_transition else 0))
    ZoomMode = False
    Panning = False

# increment/decrement spot radius
def IncrementSpotSize(delta):
    global SpotRadius
    if not Tracing:
        return
    SpotRadius = max(SpotRadius + delta, 8)
    GenerateSpotMesh()
    DrawCurrentPage()

# post-initialize the page transitions
def PrepareTransitions():
    Unspecified = 0xAFFED00F
    # STEP 1: randomly assign transitions where the user didn't specify them
    cnt = sum([1 for page in xrange(1, PageCount + 1) \
               if GetPageProp(page, 'transition', Unspecified) == Unspecified])
    newtrans = ((cnt / len(AvailableTransitions) + 1) * AvailableTransitions)[:cnt]
    random.shuffle(newtrans)
    for page in xrange(1, PageCount + 1):
        if GetPageProp(page, 'transition', Unspecified) == Unspecified:
            SetPageProp(page, '_transition', newtrans.pop())
    # STEP 2: instantiate transitions
    for page in PageProps:
        for key in ('transition', '_transition'):
            if not key in PageProps[page]:
                continue
            trans = PageProps[page][key]
            if trans is not None:
                PageProps[page][key] = InstantiateTransition(trans)

# update timer values and screen timer
def TimerTick():
    global CurrentTime, ProgressBarPos
    redraw = False
    newtime = (Platform.GetTicks() - StartTime) * 0.001
    if EstimatedDuration:
        newpos = int(ScreenWidth * newtime / EstimatedDuration)
        if newpos != ProgressBarPos:
            redraw = True
        ProgressBarPos = newpos
    newtime = int(newtime)
    if TimeDisplay and (CurrentTime != newtime):
        redraw = True
    if PageTimeout and AutoAdvanceProgress:
        redraw = True
    CurrentTime = newtime
    return redraw

# enables time tracking mode (if not already done so)
def EnableTimeTracking(force=False):
    global TimeTracking
    if force or (TimeDisplay and not(TimeTracking) and not(ShowClock) and FirstPage):
        print >>sys.stderr, "Time tracking mode enabled."
        TimeTracking = True
        print "page duration    enter    leave"
        print "---- -------- -------- --------"

# set cursor visibility
def SetCursor(visible):
    global CursorVisible
    CursorVisible = visible
    if not(CursorImage) and (MouseHideDelay != 1):
        Platform.SetMouseVisible(visible)

# handle a shortcut key event: store it (if shifted) or return the
# page number to navigate to (if not)
def HandleShortcutKey(key, current=0):
    if not(key) or (key[0] != '*'):
        return None
    shift = key.startswith('*shift+')
    if shift:
        key = key[7:]
    else:
        key = key[1:]
    if (len(key) == 1) or ((key >= "f1") and (key <= "f9")):
        # Note: F10..F12 are implicitly included due to lexicographic sorting
        page = None
        for check_page, props in PageProps.iteritems():
            if props.get('shortcut') == key:
                page = check_page
                break
        if shift:
            if page:
                DelPageProp(page, 'shortcut')
            SetPageProp(current, 'shortcut', key)
        elif page and (page != current):
            return page
    return None


##### EVENT-TO-ACTION BINDING CODE #############################################

SpecialKeyNames = set(filter(None, """
ampersand asterisk at backquote backslash backspace break capslock caret clear
comma down escape euro end exclaim greater hash help home insert kp_divide
kp_enter kp_equals kp_minus kp_multiply kp_plus lalt last lctrl left leftbracket
leftparen less lmeta lshift lsuper menu minus mode numlock pagedown pageup pause
period plus power print question quote quotedbl ralt rctrl return right
rightbracket rightparen rmeta rshift rsuper scrollock semicolon slash space
sysreq tab underscore up
""".split()))
KnownEvents = set(list(SpecialKeyNames) + filter(None, """
a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9
kp0 kp1 kp2 kp3 kp4 kp5 kp6 kp7 kp8 kp9 f1 f2 f3 f4 f5 f6 f7 f8 f9 f10 f11 f12
lmb mmb rmb wheeldown wheelup
""".split()))

# event handling model:
# - Platform.GetEvent() generates platform-neutral event (= string) that
#   identifies a key or mouse button, with prefix:
#   - '+' = key pressed, '-' = key released, '*' = main event ('*' is generated
#      directly before '-' for keys and directly after '+' for mouse buttons)
#   - "ctrl+", "alt+", "shift+" modifiers, in that order
# - event gets translated into a list of actions via the EventMap dictionary
# - actions are processed in order of that list, like priorities:
#   - list processing terminates at the first action that is successfully handled
#   - exception: "forced actions" will always be executed, even if a higher-prio
#     action of that list has already been executed; also, they will not stop
#     action list execution, even if they have been handled

KnownActions = {}
EventMap = {}
ForcedActions = set()
ActivateReleaseActions = set()

class ActionNotHandled(Exception):
    pass

def ActionValidIf(cond):
    if not cond:
        raise ActionNotHandled()

class ActionRelayBase(object):
    def __init__(self):
        global KnownActions, ActivateReleaseActions
        for item in dir(self):
            if (item[0] == '_') and (item[1] != '_') and (item[1] != 'X') and (item[-1] != '_'):
                doc = getattr(self, item).__doc__
                if item.endswith("_ACTIVATE"):
                    item = item[:-9]
                    ActivateReleaseActions.add(item)
                elif item.endswith("_RELEASE"):
                    item = item[:-8]
                    ActivateReleaseActions.add(item)
                item = item[1:].replace('_', '-')
                olddoc = KnownActions.get(item)
                if not olddoc:
                    KnownActions[item] = doc

    def __call__(self, ev):
        evname = ev[1:].replace('-', '_')
        if ev[0] == '$':
            meth = getattr(self, '_X_' + evname, None)
        elif ev[0] == '*':
            meth = getattr(self, '_' + evname, None)
        elif ev[0] == '+':
            meth = getattr(self, '_' + evname + '_ACTIVATE', None)
        elif ev[0] == '-':
            meth = getattr(self, '_' + evname + '_RELEASE', None)
        if not meth:
            return False
        try:
            meth()
            return True
        except ActionNotHandled:
            return False

def ProcessEvent(ev, handler_func):
    """
    calls the appropriate action handlers for an event
    as returned by Platform.GetEvent()
    """
    if not ev:
        return False
    if ev[0] == '$':
        handler_func(ev)
    try:
        events = EventMap[ev[1:]]
    except KeyError:
        return False
    prefix = ev[0]
    handled = False
    no_forced = not(any(((prefix + ev) in ForcedActions) for ev in events))
    if no_forced and (prefix in "+-"):
        if not(any((ev in ActivateReleaseActions) for ev in events)):
            return False
    for ev in events:
        ev = prefix + ev
        if ev in ForcedActions:
            handler_func(ev)
        elif not handled:
            handled = handler_func(ev)
        if handled and no_forced:
            break
    return handled

def ValidateEvent(ev, error_prefix=None):
    for prefix in ("ctrl+", "alt+", "shift+"):
        if ev.startswith(prefix):
            ev = ev[len(prefix):]
    if (ev in KnownEvents) or ev.startswith('unknown-'):
        return True
    if error_prefix:
        error_prefix += ": "
    else:
        error_prefix = ""
    print >>sys.stderr, "ERROR: %signoring unknown event '%s'" % (error_prefix, ev)
    return False

def ValidateAction(ev, error_prefix=None):
    if not(KnownActions) or (ev in KnownActions):
        return True
    if error_prefix:
        error_prefix += ": "
    else:
        error_prefix = ""
    print >>sys.stderr, "ERROR: %signoring unknown action '%s'" % (error_prefix, ev)
    return False

def BindEvent(events, actions=None, clear=False, remove=False, error_prefix=None):
    """
    bind one or more events to one or more actions
    - events and actions can be lists or single comma-separated strings
    - if clear is False, actions will be *added* to the raw events,
      if clear is True, the specified actions will *replace* the current set,
      if remove is True, the specified actions will be *removed* from the set
    - actions can be omitted; instead, events can be a string consisting
      of raw event and internal event names, separated by one of:
        '=' -> add or replace, based on the clear flag
        '+=' -> always add
        ':=' -> always clear
        '-=' -> always remove
    - some special events are recognized:
        'clearall' clears *all* actions of *all* raw events;
        'defaults' loads all defaults
        'include', followed by whitespace and a filename, will include a file
        (that's what the basedirs option is for)
    """
    global EventMap
    if isinstance(events, basestring):
        if not actions:
            if (';' in events) or ('\n' in events):
                for cmd in events.replace('\n', ';').split(';'):
                    BindEvent(cmd, clear=clear, remove=remove, error_prefix=error_prefix)
                return
            if '=' in events:
                events, actions = events.split('=', 1)
                events = events.rstrip()
                if events.endswith('+'):
                    clear = False
                    events = events[:-1]
                elif events.endswith(':'):
                    clear = True
                    events = events[:-1]
                elif events.endswith('-'):
                    remove = True
                    events = events[:-1]
        events = events.split(',')
    if actions is None:
        actions = []
    elif isinstance(actions, basestring):
        actions = actions.split(',')
    actions = [b.replace('_', '-').strip(' \t$+-').lower() for b in actions]
    actions = [a for a in actions if ValidateAction(a, error_prefix)]
    for event in events:
        event_orig = event.replace('\t', ' ').strip(' \r\n+-$')
        if not event_orig:
            continue
        event = event_orig.replace('-', '_').lower()
        if event.startswith('include '):
            filename = event_orig[8:].strip()
            if (filename.startswith('"') and filename.endswith('"')) \
            or (filename.startswith("'") and filename.endswith("'")):
                filename = filename[1:-1]
            ParseInputBindingFile(filename)
            continue
        elif event == 'clearall':
            EventMap = {}
            continue
        elif event == 'defaults':
            LoadDefaultBindings()
            continue
        event = event.replace(' ', '')
        if not ValidateEvent(event, error_prefix):
            continue
        if remove:
            if event in EventMap:
                for a in actions:
                    try:
                        EventMap[event].remove(a)
                    except ValueError:
                        pass
        elif clear or not(event in EventMap):
            EventMap[event] = actions[:]
        else:
            EventMap[event].extend(actions)

def ParseInputBindingFile(filename):
    """
    parse an input configuration file;
    basically calls BindEvent() for each line;
    '#' is the comment character
    """
    try:
        f = open(filename, "r")
        n = 0
        for line in f:
            n += 1
            line = line.split('#', 1)[0].strip()
            if line:
                BindEvent(line, error_prefix="%s:%d" % (filename, n))
        f.close()
    except IOError, e:
        print >>sys.stderr, "ERROR: failed to read the input configuration file '%s' -" % filename, e

def EventHelp():
    evlist = ["a-z", "0-9", "kp0-kp9", "f1-f12"] + sorted(list(SpecialKeyNames))
    print "Event-to-action binding syntax:"
    print "  <event> [,<event2...>] = <action> [,<action2...>]"
    print "  By default, this will *add* actions to an event."
    print "  To *overwrite* the current binding for an event, use ':=' instead of '='."
    print "  To remove actions from an event, use '-=' instead of '='."
    print "  Join multiple bindings with a semi-colon (';')."
    print "Special commands:"
    print "  clearall       = clear all bindings"
    print "  defaults       = load default bindings"
    print "  include <file> = load bindings from a file"
    print "Binding files use the same syntax with one binding per line;"
    print "comments start with a '#' symbol."
    print
    print "Recognized keyboard event names:"
    while evlist:
        line = "  "
        while evlist and ((len(line) + len(evlist[0])) < 78):
            line += evlist.pop(0) + ", "
        line = line.rstrip()
        if not evlist:
            line = line.rstrip(',')
        print line
    print "Recognized mouse event names:"
    print "  lmb, mmb, rmb (= left, middle and right mouse buttons),"
    print "  wheelup, wheeldown"
    print
    print "Recognized actions:"
    maxalen = max(map(len, KnownActions))
    for action in sorted(KnownActions):
        doc = KnownActions[action]
        if doc:
            print "  %s - %s" % (action.ljust(maxalen), doc)
        else:
            print "  %s" % action
    print
    if not EventMap: return
    print "Current bindings:"
    maxelen = max(map(len, EventMap))
    for event in sorted(EventMap):
        if EventMap[event]:
            print "  %s = %s" % (event.ljust(maxelen), ", ".join(EventMap[event]))

def LoadDefaultBindings():
    BindEvent("""clearall
    escape, return, kp_enter, lmb, rmb = video-stop
    space = video-pause
    period = video-step
    down = video-seek-backward-10
    left = video-seek-forward-10
    right = video-seek-forward-1
    up = video-seek-forward-10

    escape = overview-exit, zoom-exit, spotlight-exit, box-clear, quit
    q = quit
    f = fullscreen
    tab = overview-enter, overview-exit
    s = save
    t = time-toggle
    r = time-reset
    c = box-clear
    y, z = zoom-enter, zoom-exit
    o = toggle-overview
    i = toggle-skip
    b, period = fade-to-black
    w, comma = fade-to-white
    return, kp_enter = overview-confirm, spotlight-enter, spotlight-exit
    plus, kp_plus, 0, wheelup = spotlight-grow
    minus, kp_minus, 9, wheeldown = spotlight-shrink
    ctrl+9, ctrl+0 = spotlight-reset
    7 = fade-less
    8 = fade-more
    ctrl+7, ctrl+8 = fade-reset
    leftbracket = gamma-decrease
    rightbracket = gamma-increase
    shift+leftbracket = gamma-bl-decrease
    shift+rightbracket = gamma-bl-increase
    backslash = gamma-reset
    lmb = box-add, hyperlink, overview-confirm
    ctrl+lmb = hyperlink-notrans
    rmb = zoom-pan, box-remove, overview-exit
    mmb = zoom-exit, overview-enter, overview-exit
    left, wheelup = overview-prev
    right, wheeldown = overview-next
    up = overview-up
    down = overview-down

    lmb, wheeldown, pagedown, down, right, space = goto-next
    ctrl+lmb, ctrl+wheeldown, ctrl+pagedown, ctrl+down, ctrl+right, ctrl+space = goto-next-notrans
    rmb, wheelup, pageup, up, left, backspace = goto-prev
    ctrl+rmb, ctrl+wheelup, ctrl+pageup, ctrl+up, ctrl+left, ctrl+backspace = goto-prev-notrans
    home = goto-start
    ctrl+home = goto-start-notrans
    end = goto-end
    ctrl+end = goto-end-notrans
    l = goto-last
    ctrl+l = goto-last-notrans
    lmb = spotlight-enter, spotlight-exit
    """, error_prefix="LoadDefaultBindings")

# basic action implementations (i.e. stuff that is required to work in all modes)
class BaseActions(ActionRelayBase):
    def _X_quit(self):
        Quit()

    def _X_alt_tab(self):
        ActionValidIf(Fullscreen)
        SetFullscreen(False)
        Platform.Minimize()

    def _quit(self):
        "quit Impressive immediately"
        Platform.PostQuitEvent()

    def _X_move(self):
        # mouse move in fullscreen mode -> show mouse cursor and reset mouse timer
        if Fullscreen:
            Platform.ScheduleEvent("$hide-mouse", MouseHideDelay)
            SetCursor(True)

    def _X_call(self):
        while CallQueue:
            func, args, kwargs = CallQueue.pop(0)
            func(*args, **kwargs)


##### OVERVIEW MODE ############################################################

def UpdateOverviewTexture():
    global OverviewNeedUpdate
    Loverview.acquire()
    try:
        gl.load_texture(gl.TEXTURE_2D, Tnext, OverviewImage)
    finally:
        Loverview.release()
    OverviewNeedUpdate = False

# draw the overview page
def DrawOverview():
    if VideoPlaying: return
    gl.Clear(gl.COLOR_BUFFER_BIT)
    TexturedRectShader.get_instance().draw(
        0.0, 0.0, 1.0, 1.0,
        s1=TexMaxS, t1=TexMaxT,
        tex=Tnext, color=0.75
    )

    pos = OverviewPos(OverviewSelection)
    X0 = PixelX *  pos[0]
    Y0 = PixelY *  pos[1]
    X1 = PixelX * (pos[0] + OverviewCellX)
    Y1 = PixelY * (pos[1] + OverviewCellY)
    TexturedRectShader.get_instance().draw(
        X0, Y0, X1, Y1,
        X0 * TexMaxS, Y0 * TexMaxT,
        X1 * TexMaxS, Y1 * TexMaxT,
        color=1.0
    )

    gl.Enable(gl.BLEND)
    if OSDFont:
        OSDFont.BeginDraw()
        DrawOSDEx(OSDTitlePos,  CurrentOSDCaption)
        DrawOSDEx(OSDPagePos,   CurrentOSDPage)
        DrawOSDEx(OSDStatusPos, CurrentOSDStatus)
        OSDFont.EndDraw()
        DrawOverlays()
    Platform.SwapBuffers()

# overview zoom effect, time mapped through func
def OverviewZoom(func):
    global TransitionRunning
    if ZoomDuration <= 0:
        return
    pos = OverviewPos(OverviewSelection)
    X0 = PixelX * (pos[0] + OverviewBorder)
    Y0 = PixelY * (pos[1] + OverviewBorder)
    X1 = PixelX * (pos[0] - OverviewBorder + OverviewCellX)
    Y1 = PixelY * (pos[1] - OverviewBorder + OverviewCellY)

    shader = TexturedRectShader.get_instance()
    TransitionRunning = True
    t0 = Platform.GetTicks()
    while not(VideoPlaying):
        t = (Platform.GetTicks() - t0) * 1.0 / ZoomDuration
        if t >= 1.0: break
        t = func(t)
        t1 = t*t
        t = 1.0 - t1

        zoom = (t * (X1 - X0) + t1) / (X1 - X0)
        OX = zoom * (t * X0 - X0) - (zoom - 1.0) * t * X0
        OY = zoom * (t * Y0 - Y0) - (zoom - 1.0) * t * Y0
        OX = t * X0 - zoom * X0
        OY = t * Y0 - zoom * Y0

        gl.Clear(gl.COLOR_BUFFER_BIT)
        shader.draw(  # base overview page
            OX, OY, OX + zoom, OY + zoom,
            s1=TexMaxS, t1=TexMaxT,
            tex=Tnext, color=0.75
        )
        shader.draw(  # highlighted part
            OX + X0 * zoom, OY + Y0 * zoom,
            OX + X1 * zoom, OY + Y1 * zoom,
            X0 * TexMaxS, Y0 * TexMaxT,
            X1 * TexMaxS, Y1 * TexMaxT,
            color=1.0
        )
        gl.Enable(gl.BLEND)
        shader.draw(  # overlay of the original high-res page
            t * X0,      t * Y0,
            t * X1 + t1, t * Y1 + t1,
            s1=TexMaxS, t1=TexMaxT,
            tex=Tcurrent, color=(1.0, 1.0, 1.0, 1.0 - t * t * t)
        )

        if OSDFont:
            OSDFont.BeginDraw()
            DrawOSDEx(OSDTitlePos,  CurrentOSDCaption, alpha_factor=t)
            DrawOSDEx(OSDPagePos,   CurrentOSDPage,    alpha_factor=t)
            DrawOSDEx(OSDStatusPos, CurrentOSDStatus,  alpha_factor=t)
            OSDFont.EndDraw()
            DrawOverlays()
        Platform.SwapBuffers()
    TransitionRunning = False

# overview keyboard navigation
def OverviewKeyboardNav(delta):
    global OverviewSelection
    dest = OverviewSelection + delta
    if (dest >= OverviewPageCount) or (dest < 0):
        return
    OverviewSelection = dest
    x, y = OverviewPos(OverviewSelection)
    Platform.SetMousePos((x + (OverviewCellX / 2), y + (OverviewCellY / 2)))

# overview mode PageProp toggle
def OverviewTogglePageProp(prop, default):
    if (OverviewSelection < 0) or (OverviewSelection >= len(OverviewPageMap)):
        return
    page = OverviewPageMap[OverviewSelection]
    SetPageProp(page, prop, not(GetPageProp(page, prop, default)))
    UpdateCaption(page, force=True)
    DrawOverview()

class ExitOverview(Exception):
    pass

# action implementation for overview mode
class OverviewActions(BaseActions):
    def _X_move(self):
        global OverviewSelection
        BaseActions._X_move(self)
        # determine highlighted page
        x, y = Platform.GetMousePos()
        OverviewSelection = \
             int((x - OverviewOfsX) / OverviewCellX) + \
             int((y - OverviewOfsY) / OverviewCellY) * OverviewGridSize
        if (OverviewSelection < 0) or (OverviewSelection >= len(OverviewPageMap)):
            UpdateCaption(0)
        else:
            UpdateCaption(OverviewPageMap[OverviewSelection])
        DrawOverview()

    def _X_quit(self):
        PageLeft(overview=True)
        Quit()

    def _X_expose(self):
        DrawOverview()

    def _X_hide_mouse(self):
        # mouse timer event -> hide fullscreen cursor
        SetCursor(False)
        DrawOverview()

    def _X_timer_update(self):
        force_update = OverviewNeedUpdate
        if OverviewNeedUpdate:
            UpdateOverviewTexture()
        if TimerTick() or force_update:
            DrawOverview()

    def _overview_exit(self):
        "exit overview mode and return to the last page"
        global OverviewSelection
        OverviewSelection = -1
        raise ExitOverview
    def _overview_confirm(self):
        "exit overview mode and go to the selected page"
        raise ExitOverview

    def _fullscreen(self):
        SetFullscreen(not(Fullscreen))

    def _save(self):
        SaveInfoScript(InfoScriptPath)

    def _fade_to_black(self):
        FadeMode(0.0)
    def _fade_to_white(self):
        FadeMode(1.0)

    def _time_toggle(self):
        global TimeDisplay
        TimeDisplay = not(TimeDisplay)
        DrawOverview()
    def _time_reset(self):
        ResetTimer()
        if TimeDisplay:
            DrawOverview()

    def _toggle_skip(self):
        TogglePageProp('skip', False)
    def _toggle_overview(self):
        TogglePageProp('overview', GetPageProp(Pcurrent, '_overview', True))

    def _overview_up(self):
        "move the overview selection upwards"
        OverviewKeyboardNav(-OverviewGridSize)
    def _overview_prev(self):
        "select the previous page in overview mode"
        OverviewKeyboardNav(-1)
    def _overview_next(self):
        "select the next page in overview mode"
        OverviewKeyboardNav(+1)
    def _overview_down(self):
        "move the overview selection downwards"
        OverviewKeyboardNav(+OverviewGridSize)
OverviewActions = OverviewActions()

# overview mode entry/loop/exit function
def DoOverview():
    global Pcurrent, Pnext, Tcurrent, Tnext, Tracing, OverviewSelection
    global PageEnterTime, OverviewMode

    Platform.ScheduleEvent("$page-timeout", 0)
    PageLeft()
    UpdateOverviewTexture()

    if GetPageProp(Pcurrent, 'boxes') or Tracing:
        BoxFade(lambda t: 1.0 - t)
    Tracing = False
    OverviewSelection = OverviewPageMapInv[Pcurrent]

    OverviewMode = True
    OverviewZoom(lambda t: 1.0 - t)
    DrawOverview()
    PageEnterTime = Platform.GetTicks() - StartTime

    try:
        while True:
            ev = Platform.GetEvent()
            if not ev:
                continue
            if not ProcessEvent(ev, OverviewActions):
                try:
                    page = OverviewPageMap[OverviewSelection]
                except IndexError:
                    page = 0
                page = HandleShortcutKey(ev, page)
                if page:
                    OverviewSelection = OverviewPageMapInv[page]
                    x, y = OverviewPos(OverviewSelection)
                    Platform.SetMousePos((x + (OverviewCellX / 2), \
                                          y + (OverviewCellY / 2)))
                    DrawOverview()
    except ExitOverview:
        PageLeft(overview=True)

    if (OverviewSelection < 0) or (OverviewSelection >= OverviewPageCount):
        OverviewSelection = OverviewPageMapInv[Pcurrent]
        Pnext = Pcurrent
    else:
        Pnext = OverviewPageMap[OverviewSelection]
    if Pnext != Pcurrent:
        Pcurrent = Pnext
        RenderPage(Pcurrent, Tcurrent)
    UpdateCaption(Pcurrent)
    OverviewZoom(lambda t: t)
    OverviewMode = False
    DrawCurrentPage()

    if GetPageProp(Pcurrent, 'boxes'):
        BoxFade(lambda t: t)
    PageEntered()
    if not PreloadNextPage(GetNextPage(Pcurrent, 1)):
        PreloadNextPage(GetNextPage(Pcurrent, -1))


##### EVENT HANDLING ###########################################################

# set fullscreen mode
def SetFullscreen(fs, do_init=True):
    global Fullscreen
    if FakeFullscreen:
        return  # this doesn't work in fake-fullscreen mode
    if do_init:
        if fs == Fullscreen: return
        if not Platform.ToggleFullscreen(): return
    Fullscreen = fs
    DrawCurrentPage()
    if fs:
        Platform.ScheduleEvent("$hide-mouse", MouseHideDelay)
    else:
        Platform.ScheduleEvent("$hide-mouse", 0)
        SetCursor(True)

# PageProp toggle
def TogglePageProp(prop, default):
    global WantStatus
    SetPageProp(Pcurrent, prop, not(GetPageProp(Pcurrent, prop, default)))
    UpdateCaption(Pcurrent, force=True)
    WantStatus = True
    DrawCurrentPage()

# basic action implementations (i.e. stuff that is required to work, except in overview mode)
class BaseDisplayActions(BaseActions):
    def _X_quit(self):
        if FadeInOut:
            EnterFadeMode()
        PageLeft()
        Quit()

    def _X_expose(self):
        DrawCurrentPage()

    def _X_hide_mouse(self):
        # mouse timer event -> hide fullscreen cursor
        SetCursor(False)
        DrawCurrentPage()

    def _X_page_timeout(self):
        TransitionTo(GetNextPage(Pcurrent, 1))

    def _X_poll_file(self):
        global RTrunning, RTrestart, Pnext
        dirty = False
        for f in FileProps:
            s = my_stat(f)
            if s != GetFileProp(f, 'stat'):
                dirty = True
                SetFileProp(f, 'stat', s)
        if dirty:
            # first, check if the new file is valid
            if not os.path.isfile(GetPageProp(Pcurrent, '_file')):
                return
            # invalidate everything we used to know about the input files
            InvalidateCache()
            for props in PageProps.itervalues():
                for prop in ('_overview_rendered', '_box', '_href'):
                    if prop in props: del props[prop]
            LoadInfoScript()
            # force a transition to the current page, reloading it
            Pnext = -1
            TransitionTo(Pcurrent)
            # restart the background renderer thread. this is not completely safe,
            # i.e. there's a small chance that we fail to restart the thread, but
            # this isn't critical
            if CacheMode and BackgroundRendering:
                if RTrunning:
                    RTrestart = True
                else:
                    RTrunning = True
                    thread.start_new_thread(RenderThread, (Pcurrent, Pnext))

    def _X_timer_update(self):
        if VideoPlaying and MPlayerProcess:
            if MPlayerProcess.poll() is not None:
                StopMPlayer()
                DrawCurrentPage()
        elif TimerTick():
            DrawCurrentPage()

# action implementations for video playback
class VideoActions(BaseDisplayActions):
    def _video_stop(self):
        "stop video playback"
        StopMPlayer()
        DrawCurrentPage()

    def mplayer_command(self, cmd):
        "helper for the various video-* actions"
        try:
            MPlayerProcess.stdin.write(cmd + "\n")
        except:
            StopMPlayer()
            DrawCurrentPage()
    def _video_pause(self):
        "pause video playback"
        self.mplayer_command("pause")
    def _video_step(self):
        "advance to the next frame in paused video"
        self.mplayer_command("framestep")
    def _video_seek_backward_10(self):
        "seek 10 seconds backward in video"
        self.mplayer_command("seek -10 pausing_keep")
    def _video_seek_backward_1(self):
        "seek 1 second backward in video"
        self.mplayer_command("seek -1 pausing_keep")
    def _video_seek_forward_1(self):
        "seek 1 second forward in video"
        self.mplayer_command("seek 1 pausing_keep")
    def _video_seek_forward_10(self):
        "seek 10 seconds forward in video"
        self.mplayer_command("seek 10 pausing_keep")
VideoActions = VideoActions()

# action implementation for normal page display (i.e. everything except overview mode)
class PageDisplayActions(BaseDisplayActions):
    def _X_move(self):
        global Marking, MarkLR, Panning, ZoomX0, ZoomY0
        BaseActions._X_move(self)
        x, y = Platform.GetMousePos()
        # activate marking if mouse is moved away far enough
        if MarkValid and not(Marking):
            if (abs(x - MarkBaseX) > 4) and (abs(y - MarkBaseY) > 4):
                Marking = True
        # mouse move while marking -> update marking box
        if Marking:
            MarkLR = MouseToScreen((x, y))
        # mouse move while RMB is pressed -> panning
        if PanValid and ZoomMode:
            if not(Panning) and (abs(x - PanBaseX) > 1) and (abs(y - PanBaseY) > 1):
                Panning = True
            ZoomX0 = PanAnchorX + (PanBaseX - x) * ZoomArea / ScreenWidth
            ZoomY0 = PanAnchorY + (PanBaseY - y) * ZoomArea / ScreenHeight
            ZoomX0 = min(max(ZoomX0, 0.0), 1.0 - ZoomArea)
            ZoomY0 = min(max(ZoomY0, 0.0), 1.0 - ZoomArea)
        # if anything changed, redraw the page
        if Marking or Tracing or Panning or (CursorImage and CursorVisible):
            DrawCurrentPage()

    def _zoom_pan_ACTIVATE(self):
        "pan visible region in zoom mode"
        global PanValid, Panning, PanBaseX, PanBaseY, PanAnchorX, PanAnchorY
        ActionValidIf(ZoomMode)
        PanValid = True
        Panning = False
        PanBaseX, PanBaseY = Platform.GetMousePos()
        PanAnchorX = ZoomX0
        PanAnchorY = ZoomY0
    def _zoom_pan(self):
        ActionValidIf(ZoomMode and Panning)
    def _zoom_pan_RELEASE(self):
        global PanValid, Panning
        PanValid = False
        Panning = False

    def _zoom_enter(self):
        "enter zoom mode"
        ActionValidIf(not(ZoomMode))
        tx, ty = MouseToScreen(Platform.GetMousePos())
        EnterZoomMode((1.0 - 1.0 / ZoomFactor) * tx, \
                      (1.0 - 1.0 / ZoomFactor) * ty)
    def _zoom_exit(self):
        "leave zoom mode"
        ActionValidIf(ZoomMode)
        LeaveZoomMode()

    def _box_add_ACTIVATE(self):
        "draw a new highlight box [mouse-only]"
        global MarkValid, Marking, MarkBaseX, MarkBaseY, MarkUL, MarkLR
        MarkValid = True
        Marking = False
        MarkBaseX, MarkBaseY = Platform.GetMousePos()
        MarkUL = MarkLR = MouseToScreen((MarkBaseX, MarkBaseY))
    def _box_add(self):
        global Marking
        ActionValidIf(Marking)
        Marking = False
        # reject too small boxes
        if  ((abs(MarkUL[0] - MarkLR[0]) * ScreenWidth)  >= MinBoxSize) \
        and ((abs(MarkUL[1] - MarkLR[1]) * ScreenHeight) >= MinBoxSize):
            boxes = GetPageProp(Pcurrent, 'boxes', [])
            oldboxcount = len(boxes)
            boxes.append(NormalizeRect(MarkUL[0], MarkUL[1], MarkLR[0], MarkLR[1]))
            SetPageProp(Pcurrent, 'boxes', boxes)
            if not(oldboxcount) and not(Tracing):
                BoxFade(lambda t: t)
        else:
            raise ActionNotHandled()
        DrawCurrentPage()
    def _box_add_RELEASE(self):
        global MarkValid
        MarkValid = False

    def _box_remove(self):
        "remove the highlight box under the mouse cursor"
        ActionValidIf(not(Panning) and not(Marking))
        boxes = GetPageProp(Pcurrent, 'boxes', [])
        x, y = MouseToScreen(Platform.GetMousePos())
        try:
            # if a box is already present around the clicked position, kill it
            idx = FindBox(x, y, boxes)
            if (len(boxes) == 1) and not(Tracing):
                BoxFade(lambda t: 1.0 - t)
            del boxes[idx]
            SetPageProp(Pcurrent, 'boxes', boxes)
            DrawCurrentPage()
        except ValueError:
            # no box present
            raise ActionNotHandled()

    def _box_clear(self):
        "remove all highlight boxes on the current page"
        ActionValidIf(GetPageProp(Pcurrent, 'boxes'))
        if not Tracing:
            BoxFade(lambda t: 1.0 - t)
        DelPageProp(Pcurrent, 'boxes')
        DrawCurrentPage()

    def _hyperlink(self, allow_transition=True):
        "navigate to the hyperlink under the mouse cursor"
        x, y = Platform.GetMousePos()
        for valid, target, x0, y0, x1, y1 in GetPageProp(Pcurrent, '_href', []):
            if valid and (x >= x0) and (x < x1) and (y >= y0) and (y < y1):
                if type(target) == types.IntType:
                    TransitionTo(target, allow_transition=allow_transition)
                elif target:
                    RunURL(target)
                return
        raise ActionNotHandled()
    def _hyperlink_notrans(self):
        "like 'hyperlink', but no transition on page change"
        return self._hyperlink(allow_transition=False)

    def _goto_prev(self):
        "go to the previous page (with transition)"
        TransitionTo(GetNextPage(Pcurrent, -1), allow_transition=True)
    def _goto_prev_notrans(self):
        "go to the previous page (without transition)"
        TransitionTo(GetNextPage(Pcurrent, -1), allow_transition=False)
    def _goto_next(self):
        "go to the next page (with transition)"
        TransitionTo(GetNextPage(Pcurrent, +1), allow_transition=True)
    def _goto_next_notrans(self):
        "go to the next page (without transition)"
        TransitionTo(GetNextPage(Pcurrent, +1), allow_transition=False)
    def _goto_last(self):
        "go to the last visited page (with transition)"
        TransitionTo(LastPage, allow_transition=True)
    def _goto_last_notrans(self):
        "go to the last visited page (without transition)"
        TransitionTo(LastPage, allow_transition=False)
    def _goto_start(self):
        "go to the first page (with transition)"
        ActionValidIf(Pcurrent != 1)
        TransitionTo(1, allow_transition=True)
    def _goto_start_notrans(self):
        "go to the first page (without transition)"
        ActionValidIf(Pcurrent != 1)
        TransitionTo(1, allow_transition=False)
    def _goto_end(self):
        "go to the final page (with transition)"
        ActionValidIf(Pcurrent != PageCount)
        TransitionTo(PageCount, allow_transition=True)
    def _goto_end_notrans(self):
        "go to the final page (without transition)"
        ActionValidIf(Pcurrent != PageCount)
        TransitionTo(PageCount, allow_transition=False)

    def _overview_enter(self):
        "zoom out to the overview page"
        LeaveZoomMode()
        DoOverview()

    def _spotlight_enter(self):
        "enter spotlight mode"
        global Tracing
        ActionValidIf(not(Tracing))
        Tracing = True
        if GetPageProp(Pcurrent, 'boxes'):
            DrawCurrentPage()
        else:
            BoxFade(lambda t: t)
    def _spotlight_exit(self):
        "exit spotlight mode"
        global Tracing
        ActionValidIf(Tracing)
        if not GetPageProp(Pcurrent, 'boxes'):
            BoxFade(lambda t: 1.0 - t)
        Tracing = False
        DrawCurrentPage()

    def _spotlight_shrink(self):
        "decrease the spotlight radius"
        ActionValidIf(Tracing)
        IncrementSpotSize(-8)
    def _spotlight_grow(self):
        "increase the spotlight radius"
        ActionValidIf(Tracing)
        IncrementSpotSize(+8)
    def _spotlight_reset(self):
        "reset the spotlight radius to its default value"
        global SpotRadius
        ActionValidIf(Tracing)
        SpotRadius = SpotRadiusBase
        GenerateSpotMesh()
        DrawCurrentPage()

    def _fullscreen(self):
        "toggle fullscreen mode"
        SetFullscreen(not(Fullscreen))

    def _save(self):
        "save the info script"
        SaveInfoScript(InfoScriptPath)

    def _fade_to_black(self):
        "fade to a black screen"
        FadeMode(0.0)
    def _fade_to_white(self):
        "fade to a white screen"
        FadeMode(1.0)

    def _time_toggle(self):
        "toggle time display and/or time tracking mode"
        global TimeDisplay
        TimeDisplay = not(TimeDisplay)
        DrawCurrentPage()
        EnableTimeTracking()
    def _time_reset(self):
        "reset the on-screen timer"
        ResetTimer()
        if TimeDisplay:
            DrawCurrentPage()

    def _toggle_skip(self):
        "toggle 'skip' flag of current page"
        TogglePageProp('skip', False)
    def _toggle_overview(self):
        "toggle 'visible on overview' flag of current page"
        TogglePageProp('overview', GetPageProp(Pcurrent, '_overview', True))

    def _fade_less(self):
        "decrease the spotlight/box background darkness"
        global BoxFadeDarkness
        BoxFadeDarkness = max(0.0, BoxFadeDarkness - BoxFadeDarknessStep)
        DrawCurrentPage()
    def _fade_more(self):
        "increase the spotlight/box background darkness"
        global BoxFadeDarkness
        BoxFadeDarkness = min(1.0, BoxFadeDarkness + BoxFadeDarknessStep)
        DrawCurrentPage()
    def _fade_reset(self):
        "reset spotlight/box background darkness to default"
        global BoxFadeDarkness
        BoxFadeDarkness = BoxFadeDarknessBase
        DrawCurrentPage()

    def _gamma_decrease(self):
        "decrease gamma"
        SetGamma(new_gamma=Gamma / GammaStep)
    def _gamma_increase(self):
        "increase gamma"
        SetGamma(new_gamma=Gamma * GammaStep)
    def _gamma_bl_decrease(self):
        "decrease black level"
        SetGamma(new_black=BlackLevel - BlackLevelStep)
    def _gamma_bl_increase(self):
        "increase black level"
        SetGamma(new_black=BlackLevel + BlackLevelStep)
    def _gamma_reset(self):
        "reset gamma and black level to the defaults"
        SetGamma(1.0, 0)

PageDisplayActions = PageDisplayActions()
ForcedActions.update(("-zoom-pan", "+zoom-pan", "-box-add", "+box-add"))

# main event handling function
def EventHandlerLoop():
    while True:
        ev = Platform.GetEvent()
        if VideoPlaying:
            # video mode -> ignore all non-video actions
            ProcessEvent(ev, VideoActions)
        elif ProcessEvent(ev, PageDisplayActions):
            # normal action has been handled -> done
            continue
        elif ev and (ev[0] == '*'):
            # handle a shortcut key
            ctrl = ev.startswith('*ctrl+')
            if ctrl:
                ev = '*' + ev[6:]
            page = HandleShortcutKey(ev, Pcurrent)
            if page:
                TransitionTo(page, allow_transition=not(ctrl))


##### FILE LIST GENERATION #####################################################

def IsImageFileName(name):
    return os.path.splitext(name)[1].lower() in \
           (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".ppm", ".pgm")
def IsPlayable(name):
    return IsImageFileName(name) or name.lower().endswith(".pdf") or os.path.isdir(name)

def AddFile(name, title=None, implicit=False):
    global FileList, FileName

    # handle list files
    if name.startswith('@') and os.path.isfile(name[1:]):
        name = name[1:]
        dirname = os.path.dirname(name)
        try:
            f = file(name, "r")
            next_title = None
            for line in f:
                line = [part.strip() for part in line.split('#', 1)]
                if len(line) == 1:
                    subfile = line[0]
                    title = None
                else:
                    subfile, title = line
                if subfile:
                    AddFile(os.path.normpath(os.path.join(dirname, subfile)), title, implicit=True)
            f.close()
        except IOError:
            print >>sys.stderr, "Error: cannot read list file `%s'" % name
        return

    # generate absolute path
    path_sep_at_end = name.endswith(os.path.sep)
    name = os.path.normpath(os.path.abspath(name)).rstrip(os.path.sep)
    if path_sep_at_end:
        name += os.path.sep

    # set FileName to first (explicitly specified) input file
    if not implicit:
        if not FileList:
            FileName = name
        else:
            FileName = ""

    if os.path.isfile(name):
        FileList.append(name)
        if title: SetFileProp(name, 'title', title)

    elif os.path.isdir(name):
        images = [os.path.join(name, f) for f in os.listdir(name) if IsImageFileName(f)]
        images.sort(lambda a, b: cmp(a.lower(), b.lower()))
        if not images:
            print >>sys.stderr, "Warning: no image files in directory `%s'" % name
        for img in images:
            AddFile(img, implicit=True)

    else:
        files = list(filter(IsPlayable, glob.glob(name)))
        if files:
            for f in files: AddFile(f, implicit=True)
        else:
            print >>sys.stderr, "Error: input file `%s' not found" % name


##### INITIALIZATION ###########################################################

LoadDefaultBindings()

def main():
    global gl, ScreenWidth, ScreenHeight, TexWidth, TexHeight, TexSize
    global TexMaxS, TexMaxT, EdgeX, EdgeY, PixelX, PixelY, LogoImage
    global OverviewGridSize, OverviewCellX, OverviewCellY
    global OverviewOfsX, OverviewOfsY, OverviewBorder, OverviewImage, OverviewPageCount
    global OverviewPageMap, OverviewPageMapInv, FileName, FileList, PageCount
    global DocumentTitle, PageProps, LogoTexture, OSDFont
    global Pcurrent, Pnext, Tcurrent, Tnext, InitialPage
    global CacheFile, CacheFileName, BaseWorkingDir, RenderToDirectory
    global PAR, DAR, TempFileName
    global BackgroundRendering, FileStats, RTrunning, RTrestart, StartTime
    global CursorImage, CursorVisible, InfoScriptPath
    global HalfScreen, AutoAdvance, WindowPos
    global BoxFadeDarknessBase, SpotRadiusBase
    global BoxIndexBuffer, UseBlurShader

    # allocate temporary file
    TempFileName = tempfile.mktemp(prefix="impressive-", suffix="_tmp")

    # some input guesswork
    BaseWorkingDir = os.getcwd()
    if not(FileName) and (len(FileList) == 1):
        FileName = FileList[0]
    if FileName and not(FileList):
        AddFile(FileName)
    if FileName:
        DocumentTitle = os.path.splitext(os.path.split(FileName)[1])[0]

    # early graphics initialization
    Platform.Init()

    # detect screen size and compute aspect ratio
    if Fullscreen and (UseAutoScreenSize or not(Platform.allow_custom_fullscreen_res)):
        size = Platform.GetScreenSize()
        if size:
            ScreenWidth, ScreenHeight = size
            print >>sys.stderr, "Detected screen size: %dx%d pixels" % (ScreenWidth, ScreenHeight)
    if DAR is None:
        PAR = 1.0
        DAR = float(ScreenWidth) / float(ScreenHeight)
    else:
        PAR = DAR / float(ScreenWidth) * float(ScreenHeight)

    # override some irrelevant settings in event test mode
    if EventTestMode:
        FileList = ["XXX.EventTestDummy.XXX"]
        InfoScriptPath = None
        RenderToDirectory = False
        InitialPage = None
        HalfScreen = False

    # fill the page list
    if Shuffle:
        random.shuffle(FileList)
    PageCount = 0
    for name in FileList:
        ispdf = name.lower().endswith(".pdf")
        if ispdf:
            # PDF input -> initialize renderers and if none available, reject
            if not InitPDFRenderer():
                print >>sys.stderr, "Ignoring unrenderable input file '%s'." % name
                continue

            # try to pre-parse the PDF file
            pages = 0
            out = [(ScreenWidth + Overscan, ScreenHeight + Overscan),
                   (ScreenWidth + Overscan, ScreenHeight + Overscan)]
            res = [(72.0, 72.0), (72.0, 72.0)]

            # phase 1: internal PDF parser
            try:
                pages, pdf_width, pdf_height = analyze_pdf(name)
                out = [ZoomToFit((pdf_width, pdf_height * PAR)),
                       ZoomToFit((pdf_height, pdf_width * PAR))]
                res = [(out[0][0] * 72.0 / pdf_width, out[0][1] * 72.0 / pdf_height),
                       (out[1][1] * 72.0 / pdf_width, out[1][0] * 72.0 / pdf_height)]
            except KeyboardInterrupt:
                raise
            except:
                pass

            # phase 2: use pdftk
            try:
                assert 0 == subprocess.Popen([pdftkPath, name, "dump_data", "output", TempFileName + ".txt"]).wait()
                title, pages = pdftkParse(TempFileName + ".txt", PageCount)
                if title and (len(FileList) == 1):
                    DocumentTitle = title
            except KeyboardInterrupt:
                raise
            except:
                pass
        else:
            # Image File
            pages = 1
            SetPageProp(PageCount + 1, '_title', os.path.split(name)[-1])

        # validity check
        if not pages:
            print >>sys.stderr, "WARNING: The input file `%s' could not be analyzed." % name
            continue

        # add pages and files into PageProps and FileProps
        pagerange = list(range(PageCount + 1, PageCount + pages + 1))
        for page in pagerange:
            SetPageProp(page, '_file', name)
            if ispdf: SetPageProp(page, '_page', page - PageCount)
            title = GetFileProp(name, 'title')
            if title: SetPageProp(page, '_title', title)
        SetFileProp(name, 'pages', GetFileProp(name, 'pages', []) + pagerange)
        SetFileProp(name, 'offsets', GetFileProp(name, 'offsets', []) + [PageCount])
        if not GetFileProp(name, 'stat'): SetFileProp(name, 'stat', my_stat(name))
        if ispdf:
            SetFileProp(name, 'out', out)
            SetFileProp(name, 'res', res)
        PageCount += pages

    # no pages? strange ...
    if not PageCount:
        print >>sys.stderr, "The presentation doesn't have any pages, quitting."
        sys.exit(1)

    # if rendering is wanted, do it NOW
    if RenderToDirectory:
        sys.exit(DoRender())

    # load and execute info script
    if not InfoScriptPath:
        InfoScriptPath = FileName + ".info"
    LoadInfoScript()

    # initialize some derived variables
    BoxFadeDarknessBase = BoxFadeDarkness
    SpotRadiusBase = SpotRadius

    # get the initial page number
    if not InitialPage:
        InitialPage = GetNextPage(0, 1)
    Pcurrent = InitialPage
    if (Pcurrent <= 0) or (Pcurrent > PageCount):
        print >>sys.stderr, "Attempt to start the presentation at an invalid page (%d of %d), quitting." % (InitialPage, PageCount)
        sys.exit(1)

    # initialize graphics
    try:
        Platform.StartDisplay()
    except:
        print >>sys.stderr, "FATAL: failed to create rendering surface in the desired resolution (%dx%d)" % (ScreenWidth, ScreenHeight)
        sys.exit(1)
    if Fullscreen:
        Platform.SetMouseVisible(False)
        CursorVisible = False
    if (Gamma <> 1.0) or (BlackLevel <> 0):
        SetGamma(force=True)

    # initialize OpenGL
    try:
        gl = Platform.LoadOpenGL()
        print >>sys.stderr, "OpenGL renderer:", GLRenderer

        # check if graphics are unaccelerated
        renderer = GLRenderer.lower().replace(' ', '').replace('(r)', '')
        if not(renderer) \
        or (renderer in ("mesaglxindirect", "gdigeneric")) \
        or renderer.startswith("software") \
        or ("llvmpipe" in renderer):
            print >>sys.stderr, "WARNING: Using an OpenGL software renderer. Impressive will work, but it will"
            print >>sys.stderr, "         very likely be too slow to be usable."

        # check for old hardware that can't deal with the blur shader
        for substr in ("i915", "intel915", "intel945", "intelq3", "intelg3", "inteligd", "gma900", "gma950", "gma3000", "gma3100", "gma3150"):
            if substr in renderer:
                UseBlurShader = False

        # check the OpenGL version (2.0 needed to ensure NPOT texture support)
        extensions = set((gl.GetString(gl.EXTENSIONS) or "").split())
        if (GLVersion < "2") and (not("GL_ARB_shader_objects" in extensions) or not("GL_ARB_texture_non_power_of_two" in extensions)):
            raise ImportError("OpenGL version %r is below 2.0 and the necessary extensions are unavailable" % GLVersion)
    except ImportError, e:
        if GLVendor: print >>sys.stderr, "OpenGL vendor:", GLVendor
        if GLRenderer: print >>sys.stderr, "OpenGL renderer:", GLRenderer
        if GLVersion: print >>sys.stderr, "OpenGL version:", GLVersion
        print >>sys.stderr, "FATAL:", e
        print >>sys.stderr, "This likely means that your graphics driver or hardware is too old."
        sys.exit(1)

    # some further OpenGL configuration
    if Verbose:
        GLShader.LOG_DEFAULT = GLShader.LOG_IF_NOT_EMPTY
    for shader in RequiredShaders:
        shader.get_instance()
    if UseBlurShader:
        try:
            BlurShader.get_instance()
        except GLShaderCompileError:
            UseBlurShader = False
    if Verbose:
        if UseBlurShader:
            print >>sys.stderr, "Using blur-and-desaturate shader for highlight box and spotlight mode."
        else:
            print >>sys.stderr, "Using legacy multi-pass blur for highlight box and spotlight mode."
    gl.BlendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)
    BoxIndexBuffer = HighlightIndexBuffer(4)

    # setup the OpenGL texture size
    TexWidth  = (ScreenWidth + 3) & (-4)
    TexHeight = (ScreenHeight + 3) & (-4)
    TexMaxS = float(ScreenWidth) / TexWidth
    TexMaxT = float(ScreenHeight) / TexHeight
    TexSize = TexWidth * TexHeight * 3

    # set up some variables
    PixelX = 1.0 / ScreenWidth
    PixelY = 1.0 / ScreenHeight
    ScreenAspect = float(ScreenWidth) / float(ScreenHeight)
    EdgeX = BoxEdgeSize * PixelX
    EdgeY = BoxEdgeSize * PixelY

    # prepare logo image
    LogoImage = Image.open(cStringIO.StringIO(LOGO.decode('base64')))
    LogoTexture = gl.make_texture(gl.TEXTURE_2D, filter=gl.NEAREST, img=LogoImage)
    DrawLogo()
    Platform.SwapBuffers()

    # initialize OSD font
    try:
        OSDFont = GLFont(FontTextureWidth, FontTextureHeight, FontList, FontSize, search_path=FontPath)
        DrawLogo()
        titles = []
        for key in ('title', '_title'):
            titles.extend([p[key] for p in PageProps.itervalues() if key in p])
        if titles:
            OSDFont.AddString("".join(titles))
    except ValueError:
        print >>sys.stderr, "The OSD font size is too large, the OSD will be rendered incompletely."
    except IOError:
        print >>sys.stderr, "Could not open OSD font file, disabling OSD."
    except (NameError, AttributeError, TypeError):
        print >>sys.stderr, "Your version of PIL is too old or incomplete, disabling OSD."

    # handle event test mode
    if EventTestMode:
        DoEventTestMode()

    # initialize mouse cursor
    if CursorImage or not(Platform.has_hardware_cursor):
        img = None
        if CursorImage and not(CursorImage.lower() in ("-", "default")):
            try:
                img = Image.open(CursorImage).convert('RGBA')
                img.load()
            except:
                print >>sys.stderr, "Could not open the mouse cursor image, using standard cursor."
                img = None
        CursorImage = PrepareCustomCursor(img)

    # set up page cache
    if CacheMode == PersistentCache:
        if not CacheFileName:
            CacheFileName = FileName + ".cache"
        InitPCache()
    if CacheMode == FileCache:
        CacheFile = tempfile.TemporaryFile(prefix="impressive-", suffix=".cache")

    # initialize overview metadata
    OverviewPageMap=[i for i in xrange(1, PageCount + 1) \
        if GetPageProp(i, ('overview', '_overview'), True) \
        and (i >= PageRangeStart) and (i <= PageRangeEnd)]
    OverviewPageCount = max(len(OverviewPageMap), 1)
    OverviewPageMapInv = {}
    for page in xrange(1, PageCount + 1):
        OverviewPageMapInv[page] = len(OverviewPageMap) - 1
        for i in xrange(len(OverviewPageMap)):
            if OverviewPageMap[i] >= page:
                OverviewPageMapInv[page] = i
                break

    # initialize overview page geometry
    OverviewGridSize = 1
    while OverviewPageCount > OverviewGridSize * OverviewGridSize:
        OverviewGridSize += 1
    if HalfScreen:
        # in half-screen mode, temporarily override ScreenWidth
        saved_screen_width = ScreenWidth
        ScreenWidth /= 2
    OverviewCellX = int(ScreenWidth  / OverviewGridSize)
    OverviewCellY = int(ScreenHeight / OverviewGridSize)
    OverviewOfsX = int((ScreenWidth  - OverviewCellX * OverviewGridSize)/2)
    OverviewOfsY = int((ScreenHeight - OverviewCellY * \
                   int((OverviewPageCount + OverviewGridSize - 1) / OverviewGridSize)) / 2)
    while OverviewBorder and (min(OverviewCellX - 2 * OverviewBorder, OverviewCellY - 2 * OverviewBorder) < 16):
        OverviewBorder -= 1
    OverviewImage = Image.new('RGB', (TexWidth, TexHeight))
    if HalfScreen:
        OverviewOfsX += ScreenWidth
        ScreenWidth = saved_screen_width

    # fill overlay "dummy" images
    dummy = LogoImage.copy()
    border = max(OverviewLogoBorder, 2 * OverviewBorder)
    maxsize = (OverviewCellX - border, OverviewCellY - border)
    if (dummy.size[0] > maxsize[0]) or (dummy.size[1] > maxsize[1]):
        dummy.thumbnail(ZoomToFit(dummy.size, maxsize), Image.ANTIALIAS)
    margX = int((OverviewCellX - dummy.size[0]) / 2)
    margY = int((OverviewCellY - dummy.size[1]) / 2)
    dummy = dummy.convert(mode='RGB')
    for page in range(OverviewPageCount):
        pos = OverviewPos(page)
        OverviewImage.paste(dummy, (pos[0] + margX, pos[1] + margY))
    del dummy

    # compute auto-advance timeout, if applicable
    if EstimatedDuration and AutoAutoAdvance:
        time_left = EstimatedDuration * 1000
        pages = 0
        p = InitialPage
        while p:
            override = GetPageProp(p, 'timeout')
            if override:
                time_left -= override
            else:
                pages += 1
            pnext = GetNextPage(p, 1)
            if pnext:
                time_left -= GetPageProp(p, 'transtime', TransitionDuration)
            p = pnext
        if pages and (time_left >= pages):
            AutoAdvance = time_left / pages
            print >>sys.stderr, "Setting auto-advance timeout to %.1f seconds." % (0.001 * AutoAdvance)
        else:
            print >>sys.stderr, "Warning: Could not determine auto-advance timeout automatically."

    # set up background rendering
    if not HaveThreads:
        print >>sys.stderr, "Note: Background rendering isn't available on this platform."
        BackgroundRendering = False

    # if caching is enabled, pre-render all pages
    if CacheMode and not(BackgroundRendering):
        DrawLogo()
        DrawProgress(0.0)
        Platform.SwapBuffers()
        for pdf in FileProps:
            if pdf.lower().endswith(".pdf"):
                ParsePDF(pdf)
        stop = False
        progress = 0.0
        def prerender_action_handler(action):
            if action in ("$quit", "*quit"):
                Quit()
        for page in range(InitialPage, PageCount + 1) + range(1, InitialPage):
            while True:
                ev = Platform.GetEvent(poll=True)
                if not ev: break
                ProcessEvent(ev, prerender_action_handler)
                if ev.startswith('*'):
                    stop = True
            if stop: break
            if (page >= PageRangeStart) and (page <= PageRangeEnd):
                PageImage(page)
            DrawLogo()
            progress += 1.0 / PageCount
            DrawProgress(progress)
            Platform.SwapBuffers()

    # create buffer textures
    DrawLogo()
    Platform.SwapBuffers()
    Tcurrent, Tnext = [gl.make_texture(gl.TEXTURE_2D, gl.CLAMP_TO_EDGE, gl.LINEAR) for dummy in (1,2)]

    # prebuffer current and next page
    Pnext = 0
    RenderPage(Pcurrent, Tcurrent)
    PageEntered(update_time=False)
    PreloadNextPage(GetNextPage(Pcurrent, 1))

    # some other preparations
    PrepareTransitions()
    GenerateSpotMesh()
    if PollInterval:
        Platform.ScheduleEvent("$poll-file", PollInterval * 1000, periodic=True)

    # start the background rendering thread
    if CacheMode and BackgroundRendering:
        RTrunning = True
        thread.start_new_thread(RenderThread, (Pcurrent, Pnext))

    # parse PDF file if caching is disabled
    if not CacheMode:
        for pdf in FileProps:
            if pdf.lower().endswith(".pdf"):
                SafeCall(ParsePDF, [pdf])

    # start output and enter main loop
    StartTime = Platform.GetTicks()
    if TimeTracking:
        EnableTimeTracking(True)
    Platform.ScheduleEvent("$timer-update", 100, periodic=True)
    if not(Fullscreen) and CursorImage:
        Platform.SetMouseVisible(False)
    if FadeInOut:
        LeaveFadeMode()
    else:
        DrawCurrentPage()
    UpdateCaption(Pcurrent)
    EventHandlerLoop()  # never returns


# event test mode implementation
def DoEventTestMode():
    last_event = "(None)"
    need_redraw = True
    cx = ScreenWidth / 2
    y1 = ScreenHeight / 5
    y2 = (ScreenHeight * 4) / 5
    if OSDFont:
        dy = OSDFont.GetLineHeight()
    Platform.ScheduleEvent('$dummy', 1000)  # required to ensure that time measurement works :(
    print >>sys.stderr, "Entering Event Test Mode."
    print " timestamp | delta-time | event"
    t0 = Platform.GetTicks()
    while True:
        if need_redraw:
            DrawLogo()
            if OSDFont:
                gl.Enable(gl.BLEND)
                OSDFont.BeginDraw()
                OSDFont.Draw((cx, y1 - dy), "Event Test Mode", align=Center, beveled=False, bold=True)
                OSDFont.Draw((cx, y1), "press Alt+F4 to quit", align=Center, beveled=False)
                OSDFont.Draw((cx, y2 - dy), "Last Event:", align=Center, beveled=False, bold=True)
                OSDFont.Draw((cx, y2), last_event, align=Center, beveled=False)
                OSDFont.EndDraw()
                gl.Disable(gl.BLEND)
            Platform.SwapBuffers()
            need_redraw = False
        ev = Platform.GetEvent()
        if ev == '$expose':
            need_redraw = True
        elif ev == '$quit':
            Quit()
        elif ev and ev.startswith('*'):
            now = Platform.GetTicks()
            print "%7d ms | %7d ms | %s" % (int(now), int(now - t0), ev[1:])
            t0 = now
            last_event = ev[1:]
            need_redraw = True


# wrapper around main() that ensures proper uninitialization
def run_main():
    global CacheFile
    try:
        try:
            main()
        except SystemExit:
            raise
        except KeyboardInterrupt:
            pass
        except:
            print >>sys.stderr
            print >>sys.stderr, 79 * "="
            print >>sys.stderr, "OOPS! Impressive crashed!"
            print >>sys.stderr, "This shouldn't happen. Please report this incident to the author, including the"
            print >>sys.stderr, "full output of the program, particularly the following lines. If possible,"
            print >>sys.stderr, "please also send the input files you used."
            print >>sys.stderr
            print >>sys.stderr, "Impressive version:", __version__
            print >>sys.stderr, "Python version:", sys.version
            print >>sys.stderr, "PyGame version:", pygame.__version__
            print >>sys.stderr, "PIL version:", Image.VERSION
            if PDFRenderer:
                print >>sys.stderr, "PDF renderer:", PDFRenderer.name
            else:
                print >>sys.stderr, "PDF renderer: None"
            if GLVendor: print >>sys.stderr, "OpenGL vendor:", GLVendor
            if GLRenderer: print >>sys.stderr, "OpenGL renderer:", GLRenderer
            if GLVersion: print >>sys.stderr, "OpenGL version:", GLVersion
            if hasattr(os, 'uname'):
                uname = os.uname()
                print >>sys.stderr, "Operating system: %s %s (%s)" % (uname[0], uname[2], uname[4])
            else:
                print >>sys.stderr, "Python platform:", sys.platform
            if os.path.isfile("/usr/bin/lsb_release"):
                lsb_release = subprocess.Popen(["/usr/bin/lsb_release", "-sd"], stdout=subprocess.PIPE)
                print >>sys.stderr, "Linux distribution:", lsb_release.stdout.read().strip()
                lsb_release.wait()
            print >>sys.stderr, "Command line:", ' '.join(('"%s"'%arg if (' ' in arg) else arg) for arg in sys.argv)
            traceback.print_exc(file=sys.stderr)
    finally:
        StopMPlayer()
        # ensure that background rendering is halted
        Lrender.acquire()
        Lcache.acquire()
        # remove all temp files
        if 'CacheFile' in globals():
            del CacheFile
        for tmp in glob.glob(TempFileName + "*"):
            try:
                os.remove(tmp)
            except OSError:
                pass
        Platform.Quit()

    # release all locks
    try:
        if Lrender.locked():
            Lrender.release()
    except:
        pass
    try:
        if Lcache.locked():
            Lcache.release()
    except:
        pass
    try:
        if Loverview.locked():
            Loverview.release()
    except:
        pass


##### COMMAND-LINE PARSER AND HELP #############################################

def if_op(cond, res_then, res_else):
    if cond: return res_then
    else:    return res_else

def HelpExit(code=0):
    print """A nice presentation tool.

Usage: """+os.path.basename(sys.argv[0])+""" [OPTION...] <INPUT(S)...>

You may either play a PDF file, a directory containing image files or
individual image files.

Input options:
  -r,  --rotate <n>       rotate pages clockwise in 90-degree steps
       --scale            scale images to fit screen (not used in PDF mode)
       --supersample      use supersampling (only used in PDF mode)
  -s                      --supersample for PDF files, --scale for image files
  -I,  --script <path>    set the path of the info script
  -u,  --poll <seconds>   check periodically if the source file has been
                          updated and reload it if it did
  -X,  --shuffle          put input files into random order
  -h,  --help             show this help text and exit

Output options:
  -o,  --output <dir>     don't display the presentation, only render to .png
       --fullscreen       start in fullscreen mode
  -ff, --fake-fullscreen  start in "fake fullscreen" mode
  -f,  --windowed         start in windowed mode
  -g,  --geometry <WxH>   set window size or fullscreen resolution
  -A,  --aspect <X:Y>     adjust for a specific display aspect ratio (e.g. 5:4)
  -G,  --gamma <G[:BL]>   specify startup gamma and black level

Page options:
  -i,  --initialpage <n>  start with page <n>
  -p,  --pages <A-B>      only cache pages in the specified range;
                          implicitly sets -i <A>
  -w,  --wrap             go back to the first page after the last page
  -O,  --autooverview <x> automatically derive page visibility on overview page
                            -O first = show pages with captions
                            -O last  = show pages before pages with captions
  -Q,  --autoquit         quit after the last slide (no effect with --wrap)

Display options:
  -t,  --transition <trans[,trans2...]>
                          force a specific transitions or set of transitions
  -l,  --listtrans        print a list of available transitions and exit
  -F,  --font <file>      use a specific TrueType font file for the OSD
  -S,  --fontsize <px>    specify the OSD font size in pixels
  -C,  --cursor <F[:X,Y]> use a .png image as the mouse cursor
  -L,  --layout <spec>    set the OSD layout (please read the documentation)
  -z,  --zoom <factor>    set zoom factor (integer number, default: 2)
  -x,  --fade             fade in at start and fade out at end
       --spot-radius <px> set the initial radius of the spotlight, in pixels
       --invert           display slides in inverted colors
       --min-box-size <x> set minimum size of a highlight box, in pixels
       --darkness <p>     set highlight box mode darkness to <p> percent
       --noblur           use legacy blur implementation

Timing options:
  -M,  --minutes          display time in minutes, not seconds
       --clock            show current time instead of time elapsed
       --tracking         enable time tracking mode
  -a,  --auto <seconds>   automatically advance to next page after some seconds
  -d,  --duration <time>  set the desired duration of the presentation and show
                          a progress bar at the bottom of the screen
  -y,  --auto-auto        if a duration is set, set the default time-out so
                          that it will be reached exactly
  -k,  --auto-progress    shows a progress bar for each page for auto-advance
  -T,  --transtime <ms>   set transition duration in milliseconds
  -D,  --mousedelay <ms>  set mouse hide delay for fullscreen mode (in ms)
                          (0 = show permanently, 1 = don't show at all)
  -B,  --boxfade <ms>     set highlight box fade duration in milliseconds
  -Z,  --zoomtime <ms>    set zoom animation duration in milliseconds
  -q,  --page-progress    shows a progress bar based on the position in the
                          presentation (based on pages, not time)

Control options:
       --control-help     display help about control configuration and exit
  -e,  --bind             set controls (modify event/action bindings)
  -E,  --controls <file>  load control configuration from a file
       --noclicks         disable page navigation via left/right mouse click
  -W,  --nowheel          disable page navigation via mouse wheel
       --evtest           run Impressive in event test mode

Advanced options:
  -c,  --cache <mode>     set page cache mode:
                            -c none       = disable caching completely
                            -c memory     = store cache in RAM, uncompressed
                            -c compressed = store cache in RAM, compressed
                            -c disk       = store cache on disk temporarily
                            -c persistent = store cache on disk persistently
       --cachefile <path> set the persistent cache file path (implies -cp)
  -b,  --noback           don't pre-render images in the background
  -P,  --renderer <path>  set path to PDF renderer executable (GhostScript,
                          Xpdf/Poppler pdftoppm, or MuPDF mudraw/pdfdraw)
  -V,  --overscan <px>    render PDF files <px> pixels larger than the screen
       --nologo           disable startup logo and version number display
  -H,  --half-screen      show OSD on right half of the screen only
  -v,  --verbose          (slightly) more verbose operation

For detailed information, visit""", __website__
    sys.exit(code)

def ListTransitions():
    print "Available transitions:"
    standard = dict([(tc.__name__, None) for tc in AvailableTransitions])
    trans = [(tc.__name__, tc.__doc__) for tc in AllTransitions]
    trans.append(('None', "no transition"))
    trans.sort()
    maxlen = max([len(item[0]) for item in trans])
    for name, desc in trans:
        if name in standard:
            star = '*'
        else:
            star = ' '
        print star, name.ljust(maxlen), '-', desc
    print "(transitions with * are enabled by default)"
    sys.exit(0)

def TryTime(s, regexp, func):
    m = re.match(regexp, s, re.I)
    if not m: return 0
    return func(map(int, m.groups()))
def ParseTime(s):
    return TryTime(s, r'([0-9]+)s?$', lambda m: m[0]) \
        or TryTime(s, r'([0-9]+)m$', lambda m: m[0] * 60) \
        or TryTime(s, r'([0-9]+)[m:]([0-9]+)[ms]?$', lambda m: m[0] * 60 + m[1]) \
        or TryTime(s, r'([0-9]+)[h:]([0-9]+)[hm]?$', lambda m: m[0] * 3600 + m[1] * 60) \
        or TryTime(s, r'([0-9]+)[h:]([0-9]+)[m:]([0-9]+)s?$', lambda m: m[0] * 3600 + m[1] * 60 + m[2])

def opterr(msg, extra_lines=[]):
    print >>sys.stderr, "command line parse error:", msg
    for line in extra_lines:
        print >>sys.stderr, line
    print >>sys.stderr, "use `%s -h' to get help" % sys.argv[0]
    print >>sys.stderr, "or visit", __website__, "for full documentation"
    sys.exit(2)

def SetTransitions(list):
    global AvailableTransitions
    index = dict([(tc.__name__.lower(), tc) for tc in AllTransitions])
    index['none'] = None
    AvailableTransitions=[]
    for trans in list.split(','):
        try:
            AvailableTransitions.append(index[trans.lower()])
        except KeyError:
            opterr("unknown transition `%s'" % trans)

def ParseLayoutPosition(value):
    xpos = []
    ypos = []
    for c in value.strip().lower():
        if   c == 't': ypos.append(0)
        elif c == 'b': ypos.append(1)
        elif c == 'l': xpos.append(0)
        elif c == 'r': xpos.append(1)
        elif c == 'c': xpos.append(2)
        else: opterr("invalid position specification `%s'" % value)
    if not xpos: opterr("position `%s' lacks X component" % value)
    if not ypos: opterr("position `%s' lacks Y component" % value)
    if len(xpos)>1: opterr("position `%s' has multiple X components" % value)
    if len(ypos)>1: opterr("position `%s' has multiple Y components" % value)
    return (xpos[0] << 1) | ypos[0]
def SetLayoutSubSpec(key, value):
    global OSDTimePos, OSDTitlePos, OSDPagePos, OSDStatusPos
    global OSDAlpha, OSDMargin
    lkey = key.strip().lower()
    if lkey in ('a', 'alpha', 'opacity'):
        try:
            OSDAlpha = float(value)
        except ValueError:
            opterr("invalid alpha value `%s'" % value)
        if OSDAlpha > 1.0:
            OSDAlpha *= 0.01  # accept percentages, too
        if (OSDAlpha < 0.0) or (OSDAlpha > 1.0):
            opterr("alpha value %s out of range" % value)
    elif lkey in ('margin', 'dist', 'distance'):
        try:
            OSDMargin = float(value)
        except ValueError:
            opterr("invalid margin value `%s'" % value)
        if OSDMargin < 0:
            opterr("margin value %s out of range" % value)
    elif lkey in ('t', 'time'):
        OSDTimePos = ParseLayoutPosition(value)
    elif lkey in ('title', 'caption'):
        OSDTitlePos = ParseLayoutPosition(value)
    elif lkey in ('page', 'number'):
        OSDPagePos = ParseLayoutPosition(value)
    elif lkey in ('status', 'info'):
        OSDStatusPos = ParseLayoutPosition(value)
    else:
        opterr("unknown layout element `%s'" % key)
def SetLayout(spec):
    for sub in spec.replace(':', '=').split(','):
        try:
            key, value = sub.split('=')
        except ValueError:
            opterr("invalid layout spec `%s'" % sub)
        SetLayoutSubSpec(key, value)

def ParseCacheMode(arg):
    arg = arg.strip().lower()
    if "none".startswith(arg): return NoCache
    if "off".startswith(arg): return NoCache
    if "memory".startswith(arg): return MemCache
    if arg == 'z': return CompressedCache
    if "compressed".startswith(arg): return CompressedCache
    if "disk".startswith(arg): return FileCache
    if "file".startswith(arg): return FileCache
    if "persistent".startswith(arg): return PersistentCache
    opterr("invalid cache mode `%s'" % arg)

def ParseAutoOverview(arg):
    arg = arg.strip().lower()
    if "off".startswith(arg): return Off
    if "first".startswith(arg): return First
    if "last".startswith(arg): return Last
    try:
        i = int(arg)
        assert (i >= Off) and (i <= Last)
    except:
        opterr("invalid auto-overview mode `%s'" % arg)

def ParseOptions(argv):
    global FileName, FileList, Fullscreen, Scaling, Supersample, CacheMode
    global TransitionDuration, MouseHideDelay, BoxFadeDuration, ZoomDuration
    global ScreenWidth, ScreenHeight, InitialPage, Wrap, TimeTracking
    global AutoAdvance, RenderToDirectory, Rotation, DAR, Verbose
    global BackgroundRendering, UseAutoScreenSize, PollInterval, CacheFileName
    global PageRangeStart, PageRangeEnd, FontList, FontSize, Gamma, BlackLevel
    global EstimatedDuration, CursorImage, CursorHotspot, MinutesOnly, Overscan
    global PDFRendererPath, InfoScriptPath, EventTestMode
    global AutoOverview, ZoomFactor, FadeInOut, ShowLogo, Shuffle, PageProgress
    global QuitAtEnd, ShowClock, HalfScreen, SpotRadius, InvertPages
    global MinBoxSize, AutoAutoAdvance, AutoAdvanceProgress, BoxFadeDarkness
    global WindowPos, FakeFullscreen, UseBlurShader
    DefaultControls = True

    try:  # unused short options: jnJKNRUY
        opts, args = getopt.getopt(argv, \
            "vhfg:sc:i:wa:t:lo:r:T:D:B:Z:P:A:mbp:u:F:S:G:d:C:ML:I:O:z:xXqV:QHykWe:E:", \
           ["help", "fullscreen", "geometry=", "scale", "supersample", \
            "nocache", "initialpage=", "wrap", "auto=", "listtrans", "output=", \
            "rotate=", "transition=", "transtime=", "mousedelay=", "boxfade=", \
            "zoom=", "gspath=", "renderer=", "aspect=", "memcache", \
            "noback", "pages=", "poll=", "font=", "fontsize=", "gamma=",
            "duration=", "cursor=", "minutes", "layout=", "script=", "cache=",
            "cachefile=", "autooverview=", "zoomtime=", "fade", "nologo",
            "shuffle", "page-progress", "overscan=", "autoquit", "noclicks",
            "clock", "half-screen", "spot-radius=", "invert", "min-box-size=",
            "auto-auto", "auto-progress", "darkness=", "no-clicks", "nowheel",
            "no-wheel", "fake-fullscreen", "windowed", "verbose", "noblur",
            "tracking", "bind=", "controls=", "control-help", "evtest"])
    except getopt.GetoptError, message:
        opterr(message)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            HelpExit()
        if opt in ("-l", "--listtrans"):
            ListTransitions()
        if opt in ("-v", "--verbose"):
            Verbose = not(Verbose)
        if opt == "--fullscreen":      Fullscreen, FakeFullscreen = True,  False
        if opt == "--fake-fullscreen": Fullscreen, FakeFullscreen = True,  True
        if opt == "--windowed":        Fullscreen, FakeFullscreen = False, False
        if opt == "-f":
            if FakeFullscreen: Fullscreen, FakeFullscreen = True,  False
            elif   Fullscreen: Fullscreen, FakeFullscreen = False, False
            else:              Fullscreen, FakeFullscreen = True,  True
        if opt in ("-s", "--scale"):
            Scaling = not(Scaling)
        if opt in ("-s", "--supersample"):
            Supersample = 2
        if opt in ("-w", "--wrap"):
            Wrap = not(Wrap)
        if opt in ("-x", "--fade"):
            FadeInOut = not(FadeInOut)
        if opt in ("-O", "--autooverview"):
            AutoOverview = ParseAutoOverview(arg)
        if opt in ("-c", "--cache"):
            CacheMode = ParseCacheMode(arg)
        if opt == "--nocache":
            print >>sys.stderr, "Note: The `--nocache' option is deprecated, use `--cache none' instead."
            CacheMode = NoCache
        if opt in ("-m", "--memcache"):
            print >>sys.stderr, "Note: The `--memcache' option is deprecated, use `--cache memory' instead."
            CacheMode = MemCache
        if opt == "--cachefile":
            CacheFileName = arg
            CacheMode = PersistentCache
        if opt in ("-M", "--minutes"):
            MinutesOnly = not(MinutesOnly)
        if opt in ("-b", "--noback"):
            BackgroundRendering = not(BackgroundRendering)
        if opt in ("-t", "--transition"):
            SetTransitions(arg)
        if opt in ("-L", "--layout"):
            SetLayout(arg)
        if opt in ("-o", "--output"):
            RenderToDirectory = arg
        if opt in ("-I", "--script"):
            InfoScriptPath = arg
        if opt in ("-F", "--font"):
            FontList = [arg]
        if opt == "--nologo":
            ShowLogo = not(ShowLogo)
        if opt in ("--noclicks", "--no-clicks"):
            if not DefaultControls:
                print >>sys.stderr, "Note: The default control settings have been modified, the `--noclicks' option might not work as expected."
            BindEvent("lmb, rmb, ctrl+lmb, ctrl+rmb -= goto-next, goto-prev, goto-next-notrans, goto-prev-notrans")
        if opt in ("-W", "--nowheel", "--no-wheel"):
            if not DefaultControls:
                print >>sys.stderr, "Note: The default control settings have been modified, the `--nowheel' option might not work as expected."
            BindEvent("wheelup, wheeldown, ctrl+wheelup, ctrl+wheeldown -= goto-next, goto-prev, goto-next-notrans, goto-prev-notrans, overview-next, overview-prev")
        if opt in ("-e", "--bind"):
            BindEvent(arg, error_prefix="--bind")
            DefaultControls = False
        if opt in ("-E", "--controls"):
            ParseInputBindingFile(arg)
            DefaultControls = False
        if opt == "--control-help":
            EventHelp()
            sys.exit(0)
        if opt == "--evtest":
            EventTestMode = not(EventTestMode)
        if opt == "--clock":
            ShowClock = not(ShowClock)
        if opt == "--tracking":
            TimeTracking = not(TimeTracking)
        if opt in ("-X", "--shuffle"):
            Shuffle = not(Shuffle)
        if opt in ("-Q", "--autoquit"):
            QuitAtEnd = not(QuitAtEnd)
        if opt in ("-y", "--auto-auto"):
            AutoAutoAdvance = not(AutoAutoAdvance)
        if opt in ("-k", "--auto-progress"):
            AutoAdvanceProgress = not(AutoAdvanceProgress)
        if opt in ("-q", "--page-progress"):
            PageProgress = not(PageProgress)
        if opt in ("-H", "--half-screen"):
            HalfScreen = not(HalfScreen)
            if HalfScreen:
                ZoomDuration = 0
        if opt == "--invert":
            InvertPages = not(InvertPages)
        if opt in ("-P", "--gspath", "--renderer"):
            if any(r.supports(arg) for r in AvailableRenderers):
                PDFRendererPath = arg
            else:
                opterr("unrecognized --renderer",
                    ["supported renderer binaries are:"] +
                    ["- %s (%s)" % (", ".join(r.binaries), r.name) for r in AvailableRenderers])
        if opt in ("-S", "--fontsize"):
            try:
                FontSize = int(arg)
                assert FontSize > 0
            except:
                opterr("invalid parameter for --fontsize")
        if opt in ("-i", "--initialpage"):
            try:
                InitialPage = int(arg)
                assert InitialPage > 0
            except:
                opterr("invalid parameter for --initialpage")
        if opt in ("-d", "--duration"):
            try:
                EstimatedDuration = ParseTime(arg)
                assert EstimatedDuration > 0
            except:
                opterr("invalid parameter for --duration")
        if opt in ("-a", "--auto"):
            try:
                AutoAdvance = int(float(arg) * 1000)
                assert (AutoAdvance > 0) and (AutoAdvance <= 86400000)
            except:
                opterr("invalid parameter for --auto")
        if opt in ("-T", "--transtime"):
            try:
                TransitionDuration = int(arg)
                assert (TransitionDuration >= 0) and (TransitionDuration < 32768)
            except:
                opterr("invalid parameter for --transtime")
        if opt in ("-D", "--mousedelay"):
            try:
                MouseHideDelay = int(arg)
                assert (MouseHideDelay >= 0) and (MouseHideDelay < 32768)
            except:
                opterr("invalid parameter for --mousedelay")
        if opt in ("-B", "--boxfade"):
            try:
                BoxFadeDuration = int(arg)
                assert (BoxFadeDuration >= 0) and (BoxFadeDuration < 32768)
            except:
                opterr("invalid parameter for --boxfade")
        if opt in ("-Z", "--zoomtime"):
            try:
                ZoomDuration = int(arg)
                assert (ZoomDuration >= 0) and (ZoomDuration < 32768)
            except:
                opterr("invalid parameter for --zoomtime")
        if opt == "--spot-radius":
            try:
                SpotRadius = int(arg)
            except:
                opterr("invalid parameter for --spot-radius")
        if opt == "--min-box-size":
            try:
                MinBoxSize = int(arg)
            except:
                opterr("invalid parameter for --min-box-size")
        if opt in ("-r", "--rotate"):
            try:
                Rotation = int(arg)
            except:
                opterr("invalid parameter for --rotate")
            while Rotation < 0: Rotation += 4
            Rotation = Rotation & 3
        if opt in ("-u", "--poll"):
            try:
                PollInterval = int(arg)
                assert PollInterval >= 0
            except:
                opterr("invalid parameter for --poll")
        if opt in ("-g", "--geometry"):
            try:
                parts = arg.replace('+', '|+').replace('-', '|-').split('|')
                assert len(parts) in (1, 3)
                if len(parts) == 3:
                    WindowPos = (int(parts[1]), int(parts[2]))
                else:
                    assert len(parts) == 1
                ScreenWidth, ScreenHeight = map(int, parts[0].split("x"))
                assert (ScreenWidth  >= 320) and (ScreenWidth  < 32768)
                assert (ScreenHeight >= 200) and (ScreenHeight < 32768)
                UseAutoScreenSize = False
            except:
                opterr("invalid parameter for --geometry")
        if opt in ("-p", "--pages"):
            try:
                PageRangeStart, PageRangeEnd = map(int, arg.split("-"))
                assert PageRangeStart > 0
                assert PageRangeStart <= PageRangeEnd
            except:
                opterr("invalid parameter for --pages")
            InitialPage = PageRangeStart
        if opt in ("-A", "--aspect"):
            try:
                if ':' in arg:
                    fx, fy = map(float, arg.split(':'))
                    DAR = fx / fy
                else:
                    DAR = float(arg)
                assert DAR > 0.0
            except:
                opterr("invalid parameter for --aspect")
        if opt in ("-G", "--gamma"):
            try:
                if ':' in arg:
                    arg, bl = arg.split(':', 1)
                    BlackLevel = int(bl)
                Gamma = float(arg)
                assert Gamma > 0.0
                assert (BlackLevel >= 0) and (BlackLevel < 255)
            except:
                opterr("invalid parameter for --gamma")
        if opt in ("-C", "--cursor"):
            try:
                if ':' in arg:
                    arg = arg.split(':')
                    assert len(arg) > 1
                    CursorImage = ':'.join(arg[:-1])
                    CursorHotspot = map(int, arg[-1].split(','))
                else:
                    CursorImage = arg
                assert (BlackLevel >= 0) and (BlackLevel < 255)
            except:
                opterr("invalid parameter for --cursor")
        if opt in ("-z", "--zoom"):
            try:
                ZoomFactor = int(arg)
                assert ZoomFactor > 1
            except:
                opterr("invalid parameter for --zoom")
        if opt in ("-V", "--overscan"):
            try:
                Overscan = int(arg)
            except:
                opterr("invalid parameter for --overscan")
        if opt == "--darkness":
            try:
                BoxFadeDarkness = float(arg) * 0.01
            except:
                opterr("invalid parameter for --darkness")
        if opt == "--noblur":
            UseBlurShader = not(UseBlurShader)

    for arg in args:
        AddFile(arg)
    if not(FileList) and not(EventTestMode):
        opterr("no playable files specified")


# use this function if you intend to use Impressive as a library
def run():
    try:
        run_main()
    except SystemExit, e:
        return e.code

# use this function if you use Impressive as a library and want to call any
# Impressive-internal function from a second thread
def synchronize(func, *args, **kwargs):
    CallQueue.append((func, args, kwargs))
    if Platform:
        Platform.ScheduleEvent("$call", 1)

if __name__ == "__main__":
    try:
        ParseOptions(sys.argv[1:])
        run_main()
    finally:
        if not(CleanExit) and (os.name == 'nt') and getattr(sys, "frozen", False):
            print
            raw_input("<-- press ENTER to quit the program --> ")
