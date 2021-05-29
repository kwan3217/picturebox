import pytest
from picturebox import PictureBox

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


