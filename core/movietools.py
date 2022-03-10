import subprocess
import os
import glob
import parameters
import matplotlib as mpl
from matplotlib import pyplot as plt
import schwimmbad

param = parameters.Param()

videosize = {480: 640,
             720: 1080,
             1080: 1920}

class HorizMap():
    def __init__(self, height, verbose=True):
        assert height in [480, 720, 1080]
        self.verbose = verbose
        width = videosize[height]
        figsize = (width, height)
        self.figsize = figsize
        self.dpi = 100

        if height == 1080:
            mpl.rcParams["font.size"] = 16
        elif height == 720:
            mpl.rcParams["font.size"] = 13
        
        fig, ax = plt.subplots(figsize=(width/self.dpi, height/self.dpi),
                               dpi=self.dpi)
        fig.canvas.get_renderer()
        self.fig = fig
        self.ax = ax
        self.has_colorbar = False

        self.axposition = [0.06, 0.08,
                           0.80, 0.88]
        self.cbposition = [0.87, 0.08,
                           0.10, 0.88]
        
        ax.set_position(self.axposition)

        self.dirname = f"{param.dirscratch}/frames"
        self.isdirchecked = False
        self.datehour = ("9999-99-99", 99)
        
    def _createdir(self):
        if not os.path.isdir(self.dirname):
            if self.verbose:
                print(f"create {self.dirname}")
            os.makedirs(self.dirname)
        self.isdirchecked = True
        pngfiles = glob.glob(f"{self.dirname}/*.png")
        if len(pngfiles) > 0:
            if self.verbose:
                print(f"remove {self.dirname}/*png")
            for file in pngfiles:
                os.remove(file)

    def setup_domain(self, args):
        #self.domain_args = args
        self.axis, self.lons, self.lats = args

    def setup_colorbar(self, args):
        #self.colorbar_args = args
        self.vmin, self.vmax, self.cmap = args
        
    def plot_frame(self, data_args):
        data, date, hour = data_args

        if self.verbose:
            print(f"do_frame {date}-{hour:02}")

        fig = self.fig
        ax = self.ax
        ax.cla()
        for lon, lat, datum in zip(self.lons, self.lats, data):
            im = ax.pcolormesh(lon, lat, datum,
                               vmin=self.vmin, vmax=self.vmax, cmap=self.cmap)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(f"{date} : {hour:02}:00")
        ax.axis(self.axis)
        ax.set_position(self.axposition)
        ax.grid()
        if not self.has_colorbar:
            cb = fig.colorbar(im)
            cb.ax.set_position(self.cbposition)
            self.has_colorbar = True
            fig.canvas.draw()
        self.datehour = (date, hour)

    def save_frame(self):
        assert self.isdirchecked
        date, hour = self.datehour
        filename = f"img_{date}_{hour:02}.png"
        pngfile = f"{self.dirname}/{filename}"
        if self.verbose:
            print(f"save {pngfile}")        
        self.fig.savefig(pngfile)
    
   
def proceed_frame(args):
    hmap, domain_args, data_args = args
    hmap.setup_domain(domain_args)
    hmap.plot_frame(data_args)
    hmap.save_frame()
    

class ThreadedHorizMap():
    def __init__(self, height, nthreads):
        self.hmaps = [HorizMap(height)
                      for _ in range(nthreads)]
        self.nthreads = nthreads
        self.index = 0
        self.videotasks = []
        #self.pool = schwimmbad.MultiPool(processes=nthreads+1)

    def _createdir(self):
        self.hmaps[0]._createdir()

    def check(self):
        for hmap in self.hmaps:
            hmap.isdirchecked = True

    def setup_colorbar(self, args):
        for hmap in self.hmaps:
            hmap.setup_colorbar(args)
    
    def proceed_frame(self, data_args):
        data, date, hour = data_args
        hmap = self.hmaps[index]
        domain_args = (hmap.axis, hmap.lons, hmap.lats)
        # hmap.setup_domain(domain_args)
        hmap.plot_frame(domain_args, args)
        hmap.save_frame()
        
    def do_frame(self,domain_args,  data_args):
        task = (self.hmaps[self.index], domain_args, data_args)
        self.videotasks += [task]#data_args]
        self.index += 1
        if self.index == self.nthreads:
            pool = schwimmbad.MultiPool(processes=self.nthreads+1)
            pool.map(proceed_frame, self.videotasks)
            pool.close()
            self.index = 0
            self.videotasks = []

    def close(self):
        [hmaps.fig.close() for hmap in self.hmaps]

class Movie():
    """ Home made class to generate mp4 """

    def __init__(self, fig, name='mymovie', framerate=30):
        """ input: fig is the handle to the figure """
        self.fig = fig
        canvas_width, canvas_height = self.fig.canvas.get_width_height()
        # Open an ffmpeg process
        outf = '%s.mp4' % name
        videoencoder = None
        for v in ['ffmpeg', 'avconv']:
            if subprocess.call(['which', v], stdout=subprocess.PIPE) == 0:
                videoencoder = v

        if videoencoder is None:
            print('\n')
            print('Neither avconv or ffmpeg was found')
            print('Install one or set param.generate_mp4 = False')
            raise ValueError('Install avconv or ffmpeg')

        cmdstring = (videoencoder,
                     '-y', '-r', str(framerate),  # overwrite, 30fps
                     # size of image string
                     '-s', '%dx%d' % (canvas_width, canvas_height),
                     '-pix_fmt', 'argb',  # format
                     '-f', 'rawvideo',
                     # tell ffmpeg to expect raw video from the pipe
                     '-i', '-',
                     '-vcodec', 'libx264', outf)  # output encoding

        devnull = open(os.devnull, 'wb')
        self.process = subprocess.Popen(cmdstring,
                                        stdin=subprocess.PIPE,
                                        stdout=devnull,
                                        stderr=devnull)

    def addframe(self):
        string = self.fig.canvas.tostring_argb()
        self.process.stdin.write(string)

    def finalize(self):
        self.process.communicate()


if __name__ == '__main__':
    """

    Below is an example of how to use this module

    1/ prepare a figure (get the handles of it)
    2/ create the movie instance
    3/ do a loop and update all the handles
    4/ add each frame
    5/ finalize at then end of the loop

    """
    import numpy as np
    import matplotlib.pyplot as plt

    def f(t):
        """ the function to animate """
        return np.sin(2*np.pi*(x-t))

    # Create the plot
    x = np.linspace(-1, 1, 201)
    t = 0.
    template = 'time = %.2f'
    fig = plt.figure()
    p = plt.plot(x, f(t))
    plt.axis([-1, 1, -1, 1])
    p = p[0]
    plt.xlabel('x')
    plt.grid()
    ti = plt.title(template % t)

    # note that you don't even need to plot on the screen
    # to generate the movie!

    # create a Movie instance
    movie = Movie(fig, name='test_moving_sine')

    nt = 100
    dt = 1./nt
    for kt in range(nt):
        t = kt*dt
        # it's faster to update handles
        # than to recreate a plot!
        p.set_data(x, f(t))
        ti.set_text(template % t)
        fig.canvas.draw()
        # add the frame
        movie.addframe()

    # close the movie cleanly (mandatory)
    movie.finalize()
