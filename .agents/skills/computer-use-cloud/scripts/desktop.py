#!/usr/bin/env python3
"""Local X11 screenshot and input helper. No browser DOM or remote service."""
import argparse, ctypes as C, ctypes.util, json, os, pathlib, subprocess, time
# Cloud portability: allow an isolated state directory while retaining the platform default.
ROOT=pathlib.Path(os.environ.get('CLOUD_SKILLS_STATE_DIR','/workspace/skill-platform'))/'desktop-tools'
os.environ.setdefault('DISPLAY', ':97')
os.environ.setdefault('XAUTHORITY', str(ROOT/'Xauthority'))
x=C.CDLL(ctypes.util.find_library('X11'))
t=C.CDLL(ctypes.util.find_library('Xtst'))
P=C.c_void_p; I=C.c_int; U=C.c_ulong
for name,restype,args in [('XOpenDisplay',P,[C.c_char_p]),('XCloseDisplay',I,[P]),('XDefaultScreen',I,[P]),('XDisplayWidth',I,[P,I]),('XDisplayHeight',I,[P,I]),('XFlush',I,[P]),('XSync',I,[P,I]),('XStringToKeysym',U,[C.c_char_p]),('XKeysymToKeycode',C.c_ubyte,[P,U]),('XDisplayKeycodes',I,[P,C.POINTER(I),C.POINTER(I)]),('XGetKeyboardMapping',C.POINTER(U),[P,C.c_ubyte,I,C.POINTER(I)]),('XChangeKeyboardMapping',I,[P,I,I,C.POINTER(U),I]),('XFree',I,[P])]:
 f=getattr(x,name); f.restype=restype; f.argtypes=args
for name,args in [('XTestFakeMotionEvent',[P,I,I,I,U]),('XTestFakeButtonEvent',[P,C.c_uint,I,U]),('XTestFakeKeyEvent',[P,C.c_uint,I,U])]:
 f=getattr(t,name); f.restype=I; f.argtypes=args

def connect():
 d=x.XOpenDisplay(None)
 if not d: raise SystemExit(f'Cannot open DISPLAY; run {ROOT.parent}/computer-start.sh first. Local socket access may require cloud execution approval.')
 return d

def key(d,name,down):
 aliases={'ctrl':'Control_L','alt':'Alt_L','shift':'Shift_L','enter':'Return','esc':'Escape','tab':'Tab','backspace':'BackSpace','super':'Super_L','space':'space'}
 name=aliases.get(name.lower(),name)
 sym=x.XStringToKeysym(name.encode())
 code=x.XKeysymToKeycode(d,sym)
 if not code: raise SystemExit('Unknown key: '+name)
 t.XTestFakeKeyEvent(d,code,int(down),0)

def type_text(d,value):
 # Native X11 UTF-8 clipboard avoids keyboard-map races and IME dependencies.
 from Xlib import X, Xatom, display, protocol
 import select
 data=value.encode('utf-8')
 if len(data)>60000: raise SystemExit('Paste text in chunks smaller than 60000 UTF-8 bytes.')
 peer=display.Display()
 win=peer.screen().root.create_window(0,0,1,1,0,peer.screen().root_depth,X.InputOutput,X.CopyFromParent,event_mask=X.PropertyChangeMask)
 clipboard=peer.intern_atom('CLIPBOARD'); utf8=peer.intern_atom('UTF8_STRING'); targets=peer.intern_atom('TARGETS')
 win.set_selection_owner(clipboard,X.CurrentTime); peer.sync()
 try:
  key(d,'ctrl',True); key(d,'v',True); key(d,'v',False); key(d,'ctrl',False); x.XSync(d,False)
  deadline=time.monotonic()+3; served=False
  while time.monotonic()<deadline:
   if not peer.pending_events():
    select.select([peer.fileno()],[],[],min(.1,max(0,deadline-time.monotonic())))
    continue
   event=peer.next_event()
   if event.type!=X.SelectionRequest: continue
   prop=event.property or event.target
   if event.target==targets:
    event.requestor.change_property(prop,Xatom.ATOM,32,[targets,utf8,Xatom.STRING])
   elif event.target in (utf8,Xatom.STRING):
    event.requestor.change_property(prop,event.target,8,data if event.target==utf8 else value.encode('latin-1','replace'))
    served=True; deadline=min(deadline,time.monotonic()+.3)
   else: prop=X.NONE
   reply=protocol.event.SelectionNotify(time=event.time,requestor=event.requestor,selection=event.selection,target=event.target,property=prop)
   event.requestor.send_event(reply,propagate=False); peer.flush()
  if not served: raise SystemExit('The focused application did not request clipboard text; click an editable field and retry.')
 finally:
  win.destroy(); peer.close()

def main():
 p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='action',required=True)
 sub.add_parser('status')
 s=sub.add_parser('screenshot'); s.add_argument('path')
 s=sub.add_parser('click'); s.add_argument('x',type=int); s.add_argument('y',type=int); s.add_argument('--button',type=int,default=1)
 s=sub.add_parser('move'); s.add_argument('x',type=int); s.add_argument('y',type=int)
 s=sub.add_parser('type'); s.add_argument('text')
 s=sub.add_parser('key'); s.add_argument('combo',help='ctrl+a, Return, Tab, Escape, etc.')
 s=sub.add_parser('scroll'); s.add_argument('steps',type=int)
 a=p.parse_args(); d=connect()
 try:
  if a.action=='status':
   screen=x.XDefaultScreen(d); print(json.dumps({'display':os.environ['DISPLAY'],'width':x.XDisplayWidth(d,screen),'height':x.XDisplayHeight(d,screen)}))
  elif a.action=='screenshot':
   out=pathlib.Path(a.path).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
   subprocess.run(['import','-display',os.environ['DISPLAY'],'-window','root',str(out)],check=True)
   print(str(out))
  elif a.action in ('click','move'):
   t.XTestFakeMotionEvent(d,-1,a.x,a.y,0)
   if a.action=='click': t.XTestFakeButtonEvent(d,a.button,True,0); t.XTestFakeButtonEvent(d,a.button,False,0)
  elif a.action=='type': type_text(d,a.text)
  elif a.action=='key':
   names=a.combo.split('+')
   for n in names: key(d,n,True)
   for n in reversed(names): key(d,n,False)
  elif a.action=='scroll':
   button=5 if a.steps>0 else 4
   for _ in range(abs(a.steps)): t.XTestFakeButtonEvent(d,button,True,0); t.XTestFakeButtonEvent(d,button,False,0)
  x.XSync(d,False)
 finally: x.XCloseDisplay(d)
if __name__=='__main__': main()
