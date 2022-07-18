"""
Pixel-scaled drawing canvas, similar to the old VB canvas. This is a thin layer on top of matplotlib, so
much of that documentation (particularly **kwargs) apply here.
"""

import matplotlib.pyplot as plt
import matplotlib.lines as lines
import matplotlib.patches as patches
import matplotlib.image as image
import matplotlib.text as text
import matplotlib.transforms as transforms
import matplotlib.path as path
import numpy as np
from kwanmath.vector import vcomp, vdecomp
from kwanmath.bezier import arc_l90

class PictureBox():
    def __init__(self,w,h,title=1,dpi=100,autodraw=True,origin='upper',**kwargs):
        self.w=w
        self.h=h
        self.fig=plt.figure(title,figsize=(w/dpi,h/dpi),dpi=dpi,**kwargs)
        self.autodraw=autodraw
        self.resetM(origin=origin)
        plt.pause(0.001)
    def __enter__(self):
        return self
    def __exit__(self,exc_type,exc_value,exc_traceback):
        plt.close(self.fig)
    @staticmethod
    def Mtransform(M,xdata,ydata):
        rdata = vcomp((xdata, ydata, 1))
        Mrdata = M @ rdata
        return vdecomp(Mrdata, m=2)
    def transform(self,xdata,ydata,transform=True):
        if transform:
            return self.Mtransform(self.M,xdata,ydata)
        else:
            return xdata,ydata
    def plot(self,xdata,ydata,transform=True,**kwargs):
        Mxdata,Mydata=self.transform(xdata,ydata,transform=transform)
        plt.plot(Mxdata,Mydata,**kwargs)
        if self.autodraw:
            plt.pause(0.001)
    def stroke(self,xdata,ydata,transform=True,**kwargs):
        """
        :param xdata: numpy array of x coordinates
        :param ydata: numpy array of y coordinates
        :param kwargs:
          Passed to the artist constructor. Consider adding things like "color" etc.
        :return: None
        """
        Mxdata,Mydata=self.transform(xdata,ydata,transform=transform)
        self.fig.lines.append(lines.Line2D(Mxdata, Mydata, **kwargs))
        if self.autodraw:
            plt.pause(0.001)
    def fill(self,xdata,ydata,transform=True,**kwargs):
        """
        :param path: Iterable of tuples, passed to translate_path
        :param kwargs:
          Passed to the artist constructor. Consider adding things like "color" etc.
        :return: None
        """
        Mxdata,Mydata=self.transform(xdata,ydata,transform=transform)
        self.fig.lines.append(patches.Polygon(np.array([Mxdata, Mydata]).T, figure=self.fig, **kwargs))
        if self.autodraw:
            plt.pause(0.001)
    def image(self,x0,y0,x1,y1,imdata,transform=True,**kwargs):
        Mx,My=self.transform(np.array([x0,x1]),np.array([y0,y1]),transform=transform)
        bbox=transforms.Bbox(np.array([[Mx[0],My[0]],[Mx[1],My[1]]]))
        img=image.BboxImage(bbox,**kwargs)
        img.set_data(imdata)
        self.fig.images.append(img)
        if self.autodraw:
            plt.pause(0.001)
    def text(self,x,y,s,**kwargs):
        Mx,My=self.transform(x,y)
        txt=text.Text(Mx,My,s,figure=self.fig,**kwargs)
        self.fig.texts.append(txt)
        if self.autodraw:
            plt.pause(0.001)
    def line(self,x0,y0,x1,y1,**kwargs):
        self.stroke(np.array([x0,x1]),np.array([y0,y1]),**kwargs)
    def rectangle(self,x0,y0,x1,y1,fill=False,**kwargs):
        if fill:
            self.fill(np.array([x0,x0,x1,x1]),np.array([y0,y1,y1,y0]),**kwargs)
        else:
            self.stroke(np.array([x0,x0,x1,x1,x0]),np.array([y0,y1,y1,y0,y0]),**kwargs)
    def arc(self,xc:float,yc:float,r:float,theta0:float,theta1:float,**kwargs):
        while (theta1-theta0)>90:
            self.arc(xc,yc,r,theta0,theta0+90,**kwargs)
            theta0+=90
        M=self.M @ self.Mtranslate(xc,yc) @ self.Mscale(r,r) @ self.Mrotate(theta0)
        Px,Py=vdecomp(arc_l90(np.radians(theta1-theta0)))
        P=M @ vcomp((Px,Py,1))
        curve=path.Path(P[0:2,:].T,np.array((path.Path.MOVETO,path.Path.CURVE4,path.Path.CURVE4,path.Path.CURVE4)))
        self.fig.lines.append(patches.PathPatch(curve,**kwargs))
        if self.autodraw:
            plt.pause(0.001)
    def bezier(self,x0:float,y0:float,x1:float,y1:float,x2:float,y2:float,x3:float,y3:float,**kwargs):
        x=np.array((x0,x1,x2,x3))
        y=np.array((x0,x1,x2,x3))
        Mx,My=self.transform(x,y)
        P=np.zeros((4,2))
        P[:,0]=Mx
        P[:,1]=My
        curve=path.Path(P,np.array((path.Path.MOVETO,path.Path.CURVE4,path.Path.CURVE4,path.Path.CURVE4)))
        self.fig.lines.append(patches.PathPatch(curve,**kwargs))
        if self.autodraw:
            plt.pause(0.001)
    def savepng(self,oufn,**kwargs):
        self.fig.savefig(oufn,**kwargs)
    def clear(self):
        self.fig.clf()
    def update(self):
        plt.pause(0.001)
    def resetM(self,origin='upper'):
        """
        Set M back to aligned with the axes and 1 unit=1 pixel
        :param origin: set to 'upper' (default) to have the origin in the upper-left and +Y be downward
                       (like origin='upper' for plt.imshow())
                       any other value to have the origin in the lower left, +Y pointing up
        """
        if origin=='upper':
            self.M=np.array([[1.0, 0.0,    0.0],
                             [0.0,-1.0, self.h],
                             [0.0, 0.0,    1.0]])
        else:
            self.M=np.array([[1.0, 0.0,    0.0],
                             [0.0, 1.0,    0.0],
                             [0.0, 0.0,    1.0]])
    @staticmethod
    def Mscale(sx,sy):
        return np.array([[sx, 0, 0],
                         [ 0,sy, 0],
                         [ 0, 0, 1]])
    def scale(self,sx,sy):
        self.M=self.Mscale(sx,sy) @ self.M
    @staticmethod
    def Mtranslate(tx,ty):
        return np.array([[ 1, 0,tx],
                         [ 0, 1,ty],
                         [ 0, 0, 1]])
    def translate(self,tx,ty):
        """
        Move the origin by this many pixels
        :param tx: Move the origin this many units left
        :param ty: Move the origin this many units up
        """
        self.M=self.Mtranslate(tx,ty) @ self.M
    @staticmethod
    def Mrotate(theta):
        c=np.cos(np.radians(theta))
        s=np.sin(np.radians(theta))
        return np.array([[ c,-s, 0],
                         [ s, c, 0],
                         [ 0, 0, 1]])
    def rotate(self,theta):
        self.M= self.Mrotate(theta)@ self.M
    def center(self,s,origin='upper'):
        """
        Set the matrix such that the origin is at the center

        :param s: Size of one data unit in pixels
        :param origin: 'upper' to have +Y in the downward direction (like origin='upper' for plt.imshow()),
                       anything else to have +Y in the upward direction
        :return: None
        """
        if origin=='upper':
            self.M=np.array([[s, 0,self.w/2],
                             [0,-s,self.h/2],
                             [0, 0,1]])
        else:
            self.M=np.array([[s, 0,self.w/2],
                             [0, s,self.h/2],
                             [0, 0,1]])

def exercise_center():
    pb=PictureBox(1280,720)
    pb.center(10)
    xo,yo=pb.transform(0,0)
    assert xo==pb.w/2
    assert yo==pb.h/2
    x1,y1=pb.transform(1,1)
    assert x1==xo+10
    assert y1==yo+10
    pb.center(10,origin='lower')
    x2,y2=pb.transform(1,1)
    assert x2==xo+10
    assert y2==yo-10

def exercise_arc():
    pb=PictureBox(1280,720)
    pb.arc(640,360,100,45,315,linewidth=10,fill=False)
    pass


if __name__=="__main__":
    exercise_arc()


