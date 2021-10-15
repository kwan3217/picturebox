"""
Code for drawing animations. This is inspired by 3blue1brown's manim, but only in the sense that he uses Python
and I use Python. From what I can gather from his documentation, my concept of defining all of the actors, each with
their own timelines, then running the render loop explicitly, is quite different from his concept.

"""

import numpy as np
from typing import Callable, Iterable
from picturebox import PictureBox
from kwanmath.interp import linterp

shadowcolor='#a0a0c0'

def smooth(x):
    return -2*x**3+3*x**2

def tc(min,sec,frame):
    """
    Calculate frame number given timecode in minutes,seconds, and frames (24 frame/s exactly)
    :param min:
    :param sec:
    :param frame:
    :return:
    """
    return (min*60+sec)*24+frame

class Actor:
    """
    Life is but a walking shadow. A poor player who
    struts and frets his hour upon the stage
    and then is heard no more.

    An actor draws one coherent, animated graphic, such as an arrow, text, an equation,
    etc. It's performance goes through three stages:
      * Entrance, where the actor appears on stage. It might fade in, or it might
        draw itself in piece by piece gradually.
      * Acting, where the actor shows what it is intended to show. It might
        just stay in place, or it might do a dance or anything like that.
        The action may be in several phases, explained below
      * Exit, where the actor disappears from the stage. Once again, it might fade
        out or it might erase itself piece by piece gradually

    The timing of the Actor is determined by the ts array. This array consists
    of at least four time points -- the actor enters between the first two, and
    leaves between the last two. In the simplest case, we have something like this:
    ts[0]           ts[1]                 ts[2]          ts[3]
      |tt=0       tt=1|tt=0             tt=1|tt=0      tt=1|
      |<----Enter---->|<--------Act-------->|<----Leave--->|
    In each stage, the appropriate stage function is called with a time parameter
    which starts at 0 and ends at 1. Since it's scaled, there is no direct way for
    the actor to know the conversion from time parameter to real time.

    A more complicated action that comes in multiple phases can be described by
    a ts that is longer than four elements:
    ts[0]           ts[1]         ts[2]          ts[3]        ts[4]          ts[5]
      |tt=0       tt=1|tt=0     tt=1|tt=0     tt=1|tt=0     tt=1|tt=0      tt=1|
      |<----Enter---->|<-act(..,1)->|<-act(..,2)->|<-act(..,3)->|<----Leave--->|
    In this case, the act() function is passed a phase number, and a time parameter
    that varies from 0 to 1 over each phase.

    To add visual interest, an actor can be drawn in two passes. This is intended
    to draw a drop shadow on the actor. The intended calling sequence is to call
    all of the actors with shadow=True, and then all of the actors with shadow=False.
    This way all the shadows are under all the actors. Actors that are already
    intricate (like small text) might not have a drop shadow.

    In order to improve generality, an actor may take any number of parameters. These
    may either be constants, or themselves functions. The mechanism to actually do this
    is a bit weird and not something I've seen in Python before.

    * Any subclass of Actor calls the superclass __init__() as usual when it is itself
    constructed. This takes the ts array and whether or not this object has a shadow.
    It also takes the **kwargs argument, so it can accept any number of arbitrary keyword
    arguments. Each extra keyword passed in is examined to see if it is a callable, and
    those that are are separated from those that aren't into two dictionaries.
    * In the draw() method, all of the callables are called, passing them the current
    phase and time parameters. These results are caught in a dictionary, which is
    combined with the non-callable keyword arguments into one dictionary which is passed
    to enter(), act(), and leave() (collectively called the acting methods) as **kwargs.
    * In the acting methods of a concrete subclass, you define certain keyword arguments, and
    if you want, give them default values (give a default of None if the keyword is required).
    Also catch the **kwargs argument if you want -- typically this is used to pass such
    things as color parameters on to the picturebox methods and then ultimately to pyplot.
    The kwargs mechanism will then take the **kwargs parameter it is passed, separate out
    the arguments which are explicitly named, and end up with a kwargs dictionary that
    only has the things the acting method didn't name, suitable for passing along to
    pyplot etc.

    Therefore, you *define* the arguments you want in the acting methods but you *pass*
    the arguments to the constructor of the actor.

    To make a time-dependent argument, pass in anything that is callable and accepts two arguments,
    phase and time parameter within the phase. I know of the following 3 things, there may be others:

    * A lambda that takes two arguments
    * A named function that takes two arguments
    * An object of a class with a __call__() method that takes two arguments
      (in addition to self).

    The Actor class is abstract, and the three acting methods are intended to be overwritten:
      * act() MUST be overridden
      * enter() and leave() have sensible default actions: Place the actor where it is
      in phase 1, tt=0, and fade in or out as appropriate with alpha=

    Each method has an alpha= parameter, where alpha=0.0 represents completely
    transparent and alpha=1.0 represents completely opaque. This must always be
    respected -- if your actor calculates its own alpha, say because its enter()
    function just fades in and it calculates an alpha internally, it must multiply
    this internal alpha by the alpha= parameter, and pass that to the picture
    box commands. If alpha is exactly 0.0, you can optimize by doing an early return.
    """
    def __init__(self,ts,has_shadow=True,**kwargs):
        """
        Create an actor
        :param ts: Action time points
        :param kwargs: Will be passed to all PictureBox commands
        """
        self.ts=ts
        self.kwargs={}
        self.callables={}
        if callable(has_shadow):
            self.callables["has_shadow"]=has_shadow
        else:
             self.kwargs["has_shadow"]=has_shadow
        for k,v in kwargs.items():
            if callable(v):
                self.callables[k]=v
            else:
                self.kwargs[k]=v
        self.kwargs=kwargs
        self.has_shadow=has_shadow
    def _pop_kwargs(self,kwargs,ks):
        result=[]
        for k in ks:
            result.append(kwargs[k])
            del kwargs[k]
        return tuple(result)
    def _set_kwargs(self,phase,tt):
        for k,f in self.callables.items():
            self.kwargs[k]=f(phase,tt)
    def _enter(self,pb,tt,alpha=1.0,shadow=False,**kwargs):
        """
        Enter the stage. Generally the entrance is short. Good things to do
        are to fade in or draw the actor piece by piece.
        :param tt: 0.0 at beginning of entrance, 1.0 at ending
        :param alpha: 0.0 for fully transparent, 1.0 for fully opaque. If your
                      actor fades in, multiply your calculated fade factor by
                      this number.
        Default entrance is to fade in the initial state of act() at phase 0.
        """
        self._act(pb=pb, phase=0, tt=0,alpha=alpha*tt, shadow=shadow,**kwargs)
    def _act(self,pb,phase,tt,alpha=1.0,shadow=False,**kwargs):
        """
        Remain on the stage. If your actor dances or does something while on stage,
        this is the time to do it. This phase may be long and drawn out.
        :param phase:Phase, may be 0 (entrance), 1..len(self.ts)-2 (on stage) or -1 (leave)
        :param tt: 0.0 at beginning of phase, 1.0 at ending
        :param alpha: 0.0 for fully transparent, 1.0 for fully opaque.

        This one MUST be overridden
        """
        raise NotImplementedError
    def _leave(self,pb,tt,alpha=1.0,shadow=False,**kwargs):
        """
        Leave the stage. Generally the exit is short. Good things to do are to
        fade out or erase the actor piece by piece.
        :param tt: 0.0 at beginning of exit, 1.0 at ending
        :param alpha: 0.0 for fully transparent, 1.0 for fully opaque.

        Default act is to draw the final state of the action, but with alpha
        running from fully opaque to fully transparent.
        """
        self._act(pb,phase=-1,tt=1,alpha=alpha*(1-tt),shadow=shadow,**kwargs)
    def draw(self,pb,t,shadow=False):
        """
        Draw the actor on the stage

        :param pb: PictureBox to draw on
        :param t: Time in frames
        :param shadow: True if this is the shadow drawing pass, false otherwise
        :return: None, but draws the actor as a side-effect.
        """
        if t<self.ts[0] or t>=self.ts[-1] or (shadow and not self.has_shadow):
            return
        phase=None
        for i_phase in range(len(self.ts)-1):
            if t<self.ts[i_phase+1]:
                phase=i_phase
                tt = linterp(self.ts[i_phase], 0, self.ts[i_phase+1], 1, t)
                break
        if phase is None:
            phase=-1
            tt=1.0
        if  phase==len(self.ts)-2:
            phase=-1
        self._set_kwargs(phase, tt)
        if phase==0:
            self._enter(pb=pb,tt=tt,shadow=shadow,**self.kwargs)
        elif phase==-1:
            self._leave(pb=pb,tt=tt,shadow=shadow,**self.kwargs)
        else:
            self._act(pb=pb,phase=phase,tt=tt,shadow=shadow,**self.kwargs)

class EnterActor(Actor):
    """
    This one does something special on entrance, but is basically static
    while on stage and fades out normally on exit
    """
    def _enter(self,pb,tt,alpha=1.0,shadow=False,**kwargs):
        """
        Enter the stage.
        :param tt: 0.0 at beginning of entrance, 1.0 at ending
        :param alpha: 0.0 for fully transparent, 1.0 for fully opaque. If your
                      actor fades in, multiply your calculated fade factor by
                      this number.
        """
        raise NotImplementedError
    def _act(self,pb,phase,tt,alpha=1.0,shadow=False,**kwargs):
        self._enter(pb,1,alpha=alpha,shadow=shadow,**kwargs)

class Axis(EnterActor):
    def __init__(self,ts,x0=None,y0=None,x1=None,y1=None,**kwargs):
        """
        Interesting kwargs:

        :param x0: left
        :param y0: up
        :param x1: right
        :param y1: bottom
        :param dx0: leftmost data value
        :param dx1: rightmost data value
        :param xticks: locations of ticks on horizontal axis
        :param dy0: bottom data value
        :param dy1: top data value
        :param yticks: location of ticks on vertical axis
        """
        super().__init__(ts,x0=x0,y0=y0,x1=x1,y1=y1,**kwargs)
        self.x0=x0
        self.y0=y0
        self.x1=x1
        self.y1=y1
    def _enter(self,pb,tt,x0=None,y0=None,x1=None,y1=None,alpha=1.0,shadow=False,**kwargs):
        if shadow:
            xofs=5
            yofs=5
            kwargs["color"]=shadowcolor
        else:
            xofs=0
            yofs=0
        if tt<2/3:
            pb.line(x0+xofs,y1+yofs,x0+xofs,yofs+linterp(0,y1,2/3,y0,tt),alpha=alpha,**kwargs)
#            if self.xticks is not None:
#                this_dx1=linterp(0,self.dx0,2/3,self.dx1,tt)
#                for xtick in self.xticks:
#                    if this_dx1>xtick:
#                        pass
        else:
            pb.line(x0+xofs,y1+yofs,x0+xofs,yofs+y0,alpha=alpha,**kwargs)
        if tt>1/3:
            pb.line(x0+xofs,y1+yofs,xofs+linterp(1/3,x0,1,x1,tt),yofs+y1,alpha=alpha,**kwargs)

class TableColumn(EnterActor):
    def _enter(self,pb,tt,shadow=False,x=None,y0=None,dy=None,header=None,data=None,**kwargs):
        #Don't draw shadows on text, it makes it hard to read
        if header is not None:
            data=[header]+list(data)
        if shadow:
            return
        for i,item in enumerate(data):
                tt_this=i/len(data)
                if tt_this<tt:
                    pb.text(x,y0+dy*i,item if type(item)==str else f"{item:,}",**kwargs)

class TableGrid(Actor):
    def _act(self,pb,phase,tt,alpha=1.0,shadow=False,x0=None,x1=None,yt=None,y0=None,yb=None,xs=None,**kwargs):
        if shadow:
            return
        pb.line(x0,y0,x1,y0,alpha=alpha,**kwargs)
        for x in xs:
            pb.line(x,yt,x,yb,alpha=alpha,**kwargs)

class Text(EnterActor):
    def __init__(self,ts,**kwargs):
        """

        :param ts:
        :param kwargs:

        Special kwargs
        :param x: x coordinate of text reference point
        :param y: y coordinate of text reference point
        :param s: string to print
        """
        super().__init__(ts,**kwargs)
    def _enter(self,pb,tt,x=None,y=None,s=None,alpha=1.0,shadow=False,**kwargs):
        if shadow:
            xofs=5
            yofs=5
            kwargs["color"]=shadowcolor
        else:
            xofs=0
            yofs=0
        if "alpha" in kwargs:
            kwargs["alpha"]*=tt*alpha
        else:
            kwargs["alpha"]=tt*alpha
        pb.text(xofs+x,yofs+y,s,**kwargs)

class Function(EnterActor):
    """
    Draw a function
    """
    def _enter(self,pb:PictureBox,tt,shadow=False,px0=None,dx0=None,px1=None,dx1=None,py0=None,dy0=None,py1=None,dy1=None,f:callable=None,**kwargs):
        """
        Do the main action for a plot -- draw it in gradually.

        :param pb: Picture box to draw upon
        :param tt: Time parameter
        :param shadow: True if this is a shadow, false otherwise
        :param px0: Pixel x0 - location where left end will be drawn
        :param dx0: Data x0 - independent value to draw at x0
        :param px1: Pixel x1 - location where right end will be drawn
        :param dx1: Data x1 - independent value to draw at x1
        :param py0: Pixel y0 - location where lowest dependent value will be drawn
        :param dy0: Data y0 - dependent value to draw at y0, will be min(f) if not passed.
        :param py1: Pixel y1 - location where highest dependent value will be drawn
        :param dy1: Data y1 - dependent value to draw at y1, will be max(f) if not passed.
        :param f: function to calculate dependent values from independent values,
                   will be passed phase, time parameter in this phase, and independent values.
                   Must be passed inside a 1-element tuple, must be able to take a numpy 1d array
        :param kwargs: Passed to stroke

        Since f is a callable, it is treated as keyframable and therefore called with phase and tt outside. This
        function must therefore itself return a function which can be called on a 1D array of independent variables.
        For instance:
            Function(f=lambda phase,tt:lambda x:x**2)
        """
        if shadow:
            xofs=5
            yofs=5
            kwargs["color"]=shadowcolor
        else:
            xofs=0
            yofs=0
        if dy0 is None or dy1 is None:
            px=np.arange(px0,px1)
            x=linterp(px0,dx0,px1,dx1,px)
            y=f(x)
            if dy0 is None:
                dy0=np.min(y)
            if dy1 is None:
                dy1=np.max(y)
        frame_px=linterp(0,px0,1,px1,tt)
        if frame_px==px0:
            return
        px=np.arange(px0,frame_px)
        x=linterp(px0,dx0,px1,dx1,px)
        y=f(x)
        py=linterp(dy0,py0,dy1,py1,y)
        pb.stroke(px,py,**kwargs)

class Plot(EnterActor):
    """
    Draw a this vs that line plot
    """
    def _enter(self,pb,tt,shadow=False,px0=None,dx0=None,px1=None,dx1=None,data_x=None,py0=None,dy0=None,py1=None,dy1=None,data_y=None,t0=None,t1=None,data_t=None,**kwargs):
        """
        Do the main action for a plot -- draw it in gradually.
        :param pb: Picture box to draw upon
        :param tt: Time parameter
        :param shadow: True if this is a shadow, false otherwise
        :param px0:
        :param dx0:
        :param px1:
        :param dx1:
        :param data_x:
        :param py0:
        :param dy0:
        :param py1:
        :param dy1:
        :param data_y:
        :param t0:
        :param t1:
        :param data_t:
        :param kwargs:
        :return:
        """
        if shadow:
            xofs=5
            yofs=5
            kwargs["color"]=shadowcolor
        else:
            xofs=0
            yofs=0
        this_t=linterp(0,t0,1,t1,tt)
        for i,t in enumerate(data_t):
            if t>this_t:
                break
            newx = linterp(dx0, px0, dx1, px1, data_x[i])
            newy = linterp(dy0, py0, dy1, py1, data_y[i])
            if i>0 and t>=t0:
                pb.line(oldx+xofs,oldy+yofs,newx+xofs,newy+yofs,**kwargs)
            oldx=newx
            oldy=newy

class Field(Actor):
    """
    Draw 2D field
    """
    def __init__(self,ts,px0,dx0,px1,dx1,nx,py0,dy0,py1,dy1,ny,f,ffade,**kwargs):
        super().__init__(ts,**kwargs)
        self.px0=px0
        self.px1=px1
        self.py0=py0
        self.py1=py1
        self.x=linterp(0,dx0,nx,dx1,np.arange(nx).reshape(1,-1))
        self.y=linterp(0,dy0,ny,dy1,np.arange(ny).reshape(-1,1))
        self.f=f
        self.ffade=ffade
    def _enter(self,pb,tt,alpha=1.0,shadow=False):
        if shadow:
            return
        fadetop=linterp(0,0,0.8,1,tt)
        fadebot=linterp(0.2,0,1,1,tt)
        this_fade=linterp(fadebot,alpha,fadetop,0,self.fade)
        w=np.where(this_fade<0)
        this_fade[w]=0
        w=np.where(this_fade>alpha)
        this_fade[w]=alpha
        this_fade=smooth(this_fade)
        pb.image(self.px0,self.py0,self.px1,self.py1,self.image,alpha=this_fade)


def perform(pb:PictureBox,actors:Iterable[Actor],f0:int,f1:int,oufn_pat:str,shadow:bool=True):
    """
    Draw a collection of actors on a picture box

    :param pb: PictureBox to draw on
    :param actors: Iterable of actors
    :param f0: Initial frame to draw
    :param f1: Final frame to draw. In typical Python fashion, this frame number is not actually drawn.
    :param oufn_pat: Pattern for output filenames. Will be used with the % operator with the frame number
    :param shadow: If true, draw the shadow pass in addition to the normal pass.
    """
    for i_frame in range(f0,f1):
        print(f0,i_frame,f1)
        pb.clear()
        if shadow:
            for actor in actors:
                actor.draw(pb,i_frame,shadow=True)
        for actor in actors:
            actor.draw(pb,i_frame,shadow=False)
        pb.update()
        if True:
            pb.savepng(oufn_pat%i_frame)
    print("Done")