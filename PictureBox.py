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
import pytest
import numpy as np

class PictureBox():
    def __init__(self,w,h,title=1,dpi=100,autodraw=True,**kwargs):
        self.w=w
        self.h=h
        self.fig=plt.figure(title,figsize=(w/dpi,h/dpi),dpi=dpi,**kwargs)
        self.autodraw=autodraw
        plt.pause(0.001)
    def stroke(self,xdata,ydata,**kwargs):
        """
        :param xdata: numpy array of x coordinates
        :param ydata: numpy array of y coordinates
        :param kwargs:
          Passed to the artist constructor. Consider adding things like "color" etc.
        :return: None
        """
        self.fig.lines.append(lines.Line2D(xdata, self.h-ydata, **kwargs))
        if self.autodraw:
            plt.pause(0.001)
    def fill(self,xdata,ydata,**kwargs):
        """
        :param path: Iterable of tuples, passed to translate_path
        :param kwargs:
          Passed to the artist constructor. Consider adding things like "color" etc.
        :return: None
        """
        self.fig.lines.append(patches.Polygon(np.array([xdata, self.h-ydata]).T, figure=self.fig, **kwargs))
        if self.autodraw:
            plt.pause(0.001)
    def image(self,x0,y0,x1,y1,imdata,**kwargs):
        bbox=transforms.Bbox(np.array([[x0,self.h-y0],[x1,self.h-y1]]))
        img=image.BboxImage(bbox,**kwargs)
        img.set_data(imdata)
        self.fig.images.append(img)
        if self.autodraw:
            plt.pause(0.001)
    def text(self,x,y,s,**kwargs):
        txt=text.Text(x,self.h-y,s,figure=self.fig,**kwargs)
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
    def savepng(self,oufn):
        self.fig.savefig(oufn)
    def clear(self):
        self.fig.clf()
    def update(self):
        plt.pause(0.001)

def test_PictureBox():
    pb=PictureBox(1280,720)
    pb.stroke(np.array([0,200]),np.array([0,90]),color="#ff0000")
    pb.fill(np.array([100,200,200,100]),np.array([100,100,200,200]),color="#ff8000")
    vel=np.arange(0,8000,10).reshape(1,-1)
    alt=np.arange(0,200000,1000).reshape(-1,1)
    h=11000 #m scale height
    rho0=1.2 #density at 0 altitude kg/m**3
    q=vel**2*rho0*np.exp(-alt/h)
    pb.image(200,200,300,300,np.flipud(np.log10(q)))
    pb.fill(np.array([201,201,299,299]),np.array([201,299,299,201]),color="#ffff00")
    pb.text(300,300,"Hello, World!")
    pb.savepng("test_PictureBox.png")
    plt.show()

if __name__=="__main__":
    test_PictureBox()


