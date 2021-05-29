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
which starts at 0 and ends at 1. Since it's scaled, there is no way for the
actor to know the conversion from time parameter to real time.

A more complicated action that comes in multiple phases can be described by
a ts that is longer than four elements:
ts[0]           ts[1]         ts[2]          ts[3]        ts[4]          ts[5]
  |tt=0       tt=1|tt=0     tt=1|tt=0     tt=1|tt=0     tt=1|tt=0      tt=1|
  |<----Enter---->|<-act(..,0)->|<-act(..,1)->|<-act(..,2)->|<----Leave--->|
In this case, the act() function is passed a phase number, and a time parameter
that varies from 0 to 1 over each phase.

To add visual interest, an actor can be drawn in two passes. This is intended
to draw a drop shadow on the actor. The intended calling sequence is to call
all of the actors with shadow=True, and then all of the actors with shadow=False.
This way all the shadows are under all the actors. Actors that are already
intricate (like small text) might not have a drop shadow.
"""
import numpy as np

shadowcolor='#a0a0c0'

def linterp(x0,y0,x1,y1,x):
    t=(x-x0)/(x1-x0)
    return (1-t)*y0+t*y1

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
    The Actor class is abstract, and has three methods intended to be overwritten:
      * enter() MUST be overridden
      * act() and leave() have sensible default actions, which freeze the actor
        on stage just as it was when it finished entering by calling self.enter(tt=1.0)
        then fade it out by calling self.enter(tt=1.0,alpha=1-tt)

    Each method has an alpha= parameter, where alpha=0.0 represents completely
    transparent and alpha=1.0 represents completely opaque. This must always be
    respected -- if your actor calculates its own alpha, say because its enter()
    function just fades in and it calculates an alpha internally, it must multiply
    this internal alpha by the alpha= parameter, and pass that to the picture
    box commands. If alpha is exactly 0.0, you can optimize by doing an early return.
    """
    def __init__(self,ts,**kwargs):
        """
        Create an actor
        :param ts: Action time points
        :param kwargs: Will be passed to all PictureBox commands
        """
        self.ts=ts
        self.kwargs=kwargs
    def enter(self,pb,tt,alpha=1.0,shadow=False):
        """
        Enter the stage. Generally the entrance is short. Good things to do
        are to fade in or draw the actor piece by piece.
        :param tt: 0.0 at beginning of entrance, 1.0 at ending
        :param alpha: 0.0 for fully transparent, 1.0 for fully opaque. If your
                      actor fades in, multiply your calculated fade factor by
                      this number.
        This one MUST be overridden.
        """
        raise NotImplementedError
    def act(self,pb,phase,tt,alpha=1.0,shadow=False):
        """
        Remain on the stage. If your actor dances or does something while on stage,
        this is the time to do it. This phase may be long and drawn out.
        :param phase:
        :param tt: 0.0 at beginning of phase, 1.0 at ending
        :param alpha: 0.0 for fully transparent, 1.0 for fully opaque.

        Default act is to draw the final state of the entrance.
        """
        self.enter(pb,1,alpha=alpha,shadow=shadow)
    def leave(self,pb,tt,alpha=1.0,shadow=False):
        """
        Leave the stage. Generally the exit is short. Good things to do are to
        fade out or erase the actor piece by piece.
        :param tt: 0.0 at beginning of exit, 1.0 at ending
        :param alpha: 0.0 for fully transparent, 1.0 for fully opaque.

        Default act is to draw the final state of the entrance, but with alpha
        running from fully opaque to fully transparent.
        """
        self.enter(pb,1,alpha=alpha*(1-tt),shadow=shadow)
    def draw(self,pb,t,shadow=False):
        if t<self.ts[0] or t>self.ts[-1]:
            return
        elif t<self.ts[1]:
            self.enter(pb,linterp(self.ts[0],0,self.ts[1],1,t),shadow=shadow)
        elif t>=self.ts[-2]:
            self.leave(pb,linterp(self.ts[-2],0,self.ts[-1],1,t),shadow=shadow)
        else:
            for phase in range(len(self.ts)-3):
                if t<self.ts[phase+2]:
                    self.act(pb,phase,linterp(self.ts[phase+1],0,self.ts[phase+2],1,t),shadow=shadow)
                    return

class Axis(Actor):
    def __init__(self,ts,x0,y0,x1,y1,dx0=None,dx1=None,dy0=None,xticks=None,dy1=None,yticks=None,**kwargs):
        """
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
        super().__init__(ts,**kwargs)
        self.x0=x0
        self.y0=y0
        self.x1=x1
        self.y1=y1
        self.dx0=dx0
        self.dx1=dx1
        self.xticks=xticks
        self.dy0 = dy0
        self.dy1 = dy1
        self.yticks = yticks
    def enter(self,pb,tt,alpha=1.0,shadow=False):
        this_kwargs=self.kwargs.copy()
        if shadow:
            xofs=5
            yofs=5
            this_kwargs["color"]=shadowcolor
        else:
            xofs=0
            yofs=0
        if tt<2/3:
            pb.line(self.x0+xofs,self.y1+yofs,self.x0+xofs,yofs+linterp(0,self.y1,2/3,self.y0,tt),alpha=alpha,**this_kwargs)
#            if self.xticks is not None:
#                this_dx1=linterp(0,self.dx0,2/3,self.dx1,tt)
#                for xtick in self.xticks:
#                    if this_dx1>xtick:
#                        pass
        else:
            pb.line(self.x0+xofs,self.y1+yofs,self.x0+xofs,yofs+self.y0,alpha=alpha,**this_kwargs)
        if tt>1/3:
            pb.line(self.x0+xofs,self.y1+yofs,xofs+linterp(1/3,self.x0,1,self.x1,tt),yofs+self.y1,alpha=alpha,**this_kwargs)

class TableColumn(Actor):
    def __init__(self,ts,header,data,x,y0,dy,**kwargs):
        super().__init__(ts,**kwargs)
        self.x=x
        self.y0=y0
        self.header=header
        self.data=data
        if self.header is not None:
            self.data=[self.header]+list(self.data)
        self.dy=dy
    def enter(self,pb,tt,alpha=1.0,shadow=False):
        #Don't draw shadows on text, it makes it hard to read
        if shadow:
            return
        for i,item in enumerate(self.data):
                tt_this=i/len(self.data)
                if tt_this<tt:
                    pb.text(self.x,self.y0+self.dy*i,str(item),alpha=alpha,**self.kwargs)

class TableGrid(Actor):
    def __init__(self,ts,x0,x1,yt,y0,yb,xs,**kwargs):
        super().__init__(ts,**kwargs)
        self.x0=x0
        self.x1=x1
        self.yt=yt
        self.y0=y0
        self.yb=yb
        self.xs=xs
    def enter(self,pb,tt,alpha=1.0,shadow=False):
        if shadow:
            return
        pb.line(self.x0,self.y0,self.x1,self.y0,alpha=tt*alpha,**self.kwargs)
        for x in self.xs:
            pb.line(x,self.yt,x,self.yb,alpha=tt*alpha,**self.kwargs)

class Text(Actor):
    def __init__(self,ts,x,y,s,**kwargs):
        super().__init__(ts,**kwargs)
        self.x=x
        self.y=y
        self.s=s
    def enter(self,pb,tt,alpha=1.0,shadow=False):
        this_kwargs=self.kwargs.copy()
        if shadow:
            xofs=5
            yofs=5
            this_kwargs["color"]=shadowcolor
        else:
            xofs=0
            yofs=0
        if "alpha" in this_kwargs:
            this_kwargs["alpha"]*=tt*alpha
        else:
            this_kwargs["alpha"]=tt*alpha
        pb.text(xofs+self.x,yofs+self.y,self.s,**this_kwargs)

class Plot(Actor):
    """
    Draw a this vs that line plot
    """
    def __init__(self,ts,px0,dx0,px1,dx1,data_x,py0,dy0,py1,dy1,data_y,t0,t1,data_t,**kwargs):
        super().__init__(ts,**kwargs)
        self.t0=t0
        self.t1=t1
        self.data_t=data_t
        self.px0=px0
        self.px1=px1
        self.dx0=dx0
        self.dx1=dx1
        self.data_x=data_x
        self.py0=py0
        self.py1=py1
        self.dy0=dy0
        self.dy1=dy1
        self.data_y=data_y
    def enter(self,pb,tt,alpha=1.0,shadow=False):
        this_kwargs=self.kwargs.copy()
        if "alpha" in this_kwargs:
            this_kwargs["alpha"]*=alpha
        else:
            this_kwargs["alpha"]=alpha
        if shadow:
            xofs=5
            yofs=5
            this_kwargs["color"]=shadowcolor
        else:
            xofs=0
            yofs=0
        this_t=linterp(0,self.t0,1,self.t1,tt)
        for i,t in enumerate(self.data_t):
            if t>this_t:
                break
            newx = linterp(self.dx0, self.px0, self.dx1, self.px1, self.data_x[i])
            newy = linterp(self.dy0, self.py0, self.dy1, self.py1, self.data_y[i])
            if i>0 and t>=self.t0:
                pb.line(oldx+xofs,oldy+yofs,newx+xofs,newy+yofs,**this_kwargs)
            oldx=newx
            oldy=newy

class Image(Actor):
    """
    Draw 2D field
    """
    def __init__(self,ts,px0,dx0,px1,dx1,nx,py0,dy0,py1,dy1,ny,f,ffade,**kwargs):
        super().__init__(ts,**kwargs)
        self.px0=px0
        self.px1=px1
        self.py0=py0
        self.py1=py1
        x=linterp(0,dx0,nx,dx1,np.arange(nx).reshape(1,-1))
        y=linterp(0,dy0,ny,dy1,np.arange(ny).reshape(-1,1))
        self.image=f(x,y)
        self.fade=ffade(x,y)
        self.fade=linterp(np.min(self.fade),0,np.max(self.fade),1,self.fade)
    def enter(self,pb,tt,alpha=1.0,shadow=False):
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

def perform(pb,actors,f0,f1,oufn_pat,shadow=True):
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