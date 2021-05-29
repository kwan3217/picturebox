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

if __name__=="__main__":
    from tests.test_picturebox import test_PictureBox
    test_PictureBox()


