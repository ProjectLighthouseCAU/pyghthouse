from signal import signal, SIGINT
from time import sleep

from .data.canvas import PyghthouseCanvas
from ._thread import PHThread
from .connection.wsconnector import VerbosityLevel

# TODO: Adjust example for more clarity
class Pyghthouse:
    """
    A Python Lighthouse adapter.

    This class is the single interface for communicating with the Lighthouse server. It takes images and
    automatically, regularly and asynchronously sends them to the server.

    The image is either set explicitly or retrieved from a callback function.

    During the lifetime of your program, it should not be necessary to instantiate this class more than once.

    Parameters
    ----------
    username: str
        A valid lighthouse.uni-kiel.de user name.

    token: str
        A valid API token belonging to the user name. This is *not* your password. To obtain a token, login to
        lighthouse.uni-kiel.de, open the rollover menu "API Token" on the right side and click "Reveal Token" or use
        the copy button next to it.

    address: str (optional, default: "wss://lighthouse.uni-kiel.de/websocket")
        URI of the WebSocket endpoint. You should not need to change this.

    frame_rate: float (optional; 0 < frame_rate <= 60, default: 30)
        Rate in 1/sec at which frames (images) are automatically sent to the lighthouse server. Also determines the
        rate of how often the image_callback function is called.

    image_callback: function (optional)
        Takes a function with no arguments and generates a valid lighthouse image. If set, this function is called
        to generate an image for sending each frame.
        The function is guaranteed to be called frame_rate times each second *unless* its execution takes longer than
        1/frame_rate seconds, in which case execution will be slowed down accordingly.

    verbosity: pyghthouse.VerbosityLevel (optional, default: pyghthouse.VerbosityLevel.WARN_ONCE)
        How many log messages and reply messages from the server are printed to the console.
        Options:
        pyghthouse.VerbosityLevel.NONE:
            All messages are suppressed.
        pyghthouse.VerbosityLevel.WARN_ONCE:
            Only print the first warning. This is usually enough to diagnose common problems like invalid tokens.
        pyghthouse.VerbosityLevel.WARN:
            Print all warnings.
        pyghthouse.VerbosityLevel.ALL:
            Print all log and reply messages.

    Image Format
    ------------
    Conceptually, each window of the highrise represents a pixel of a 28x14 RGB image.

    Values are stored in (row, column, channel) order with the origin at the top-left of the highrise.
    The color channels are 0 = red, 1 = green, 2 = blue. Note that columns are 0-indexed, so column 0 is the
    first window, column 7 is the 8th window, etc. Also note that because the row-origin is at the 14th floor, the first
    floor of the highrise corresponds with the row index 13, the second with index 12, and generally the k-th floor
    has index 14-k.
    For example, the coordinates (3, 9, 1) address the 1=green channel of the 9+1=10th window of the 14-3=11th floor.

    Each color channel has a depth of 8 bits, i.e. is represented by a number between 0 and 255, inclusively. For
    instance, [255, 127, 0] is 100% red, 50% green and 0% blue, a.k.a. orange.

    Images are nested lists with 14*28*3=1176 elements overall. The Pyghthouse.empty_image() method returns a 
    completely black image in the nested format, i.e.
    [
      [
        [0, 0, 0,],
        ..., <-- 26 pixels
        [0, 0, 0]
      ],
      ..., <-- 12 rows
      [
        [0, 0, 0,],
        ..., <-- 26 pixels
        [0, 0, 0]
      ]
    ]

    Example
    ------------
    The following example creates a Pyghthouse and sets the 10th window of the 11th floor to orange.
    >>> from pyghthouse import Pyghthouse
    >>> p = Pyghthouse("YourUsername", "YourToken")
    >>> p.start() # necessary to set image and for sending.
    >>> img = Pyghthouse.empty_image()
    >>> img[3][9] = [255, 127, 0]
    >>> p.set_image(img)
    >>> p.wait() # ensures sending of the last image set by *set_image*

    There are more code examples in the git repository 
    (https://github.com/ProjectLighthouseCAU/pyghthouse/tree/master/examples).
    """

    def __init__(self, username: str, token: str, address: str = "wss://lighthouse.uni-kiel.de/websocket",
                 frame_rate: float = 30.0, image_callback=None, verbosity=VerbosityLevel.WARN_ONCE,
                 ignore_ssl_cert=False):
        
        self.canvas = PyghthouseCanvas()

        """
        The timeout of the lamp controllers is 5 seconds, so to prevent unexpected behaviour of the light
        installation, our libraries timeout needs to be faster than the timeout of our lamp controller.
        To be more precise, we need to be faster than:
        (socket) timeout + send_interval + network delay < 5
        
        The socket timeout consists of the full send process from the libraries websocket thread to our model server
        beacon. So for the network delay, we only need to consider the streaming of the model inside the Lighthouse 
        infrastructure. 
        We can approximate this delay to a range from 0.1 to 0.5 seconds,
        depending on the servers load.

        With a frame rate of 0.5, we get a send_interval of 2 seconds.

        So we get a total worst-case of:
        (socket) timeout + send_interval + network delay = total delay
                2.5      +      2.0      +      0.5      ~    5.0
        """
        if frame_rate <= 0.5 or frame_rate > 60.0:
            raise ValueError("Frame rate must be greater than 0.5 and at most 60.")
        
        self.send_interval = 1.0 / frame_rate
        self.timeout = 2.5
        
        self.ph_thread = PHThread(self.send_interval, image_callback, self.canvas,
                                  username, token, address, verbosity, ignore_ssl_cert, self.timeout)


    def start(self):
        """
        Starts Pyghthouse routine.

        The pyghthouse routine can only be started once. A RuntimeError will be raised when trying to start an already
        running instance of pyghthouse, causing the running instance to be stopped.
        """
        if not self.ph_thread.connected.is_set():
            self.ph_thread.start()
            
            # Wait is not optional due to error checking of other functions
            if not self.ph_thread.connected.wait(self.timeout + 0.3):
                raise RuntimeError("Unexpected behaviour. Reached wait timeout before socket timeout.")
        
        else:
            self.stop()
            raise RuntimeError("Pyghthouse can only be started once.")


    def set_image(self, image):
        """
        Sets pyghthouse canvas to a new image.

        This function overwrites the old image. Only the newest image will be converted to a frame by the pyghthouse
        routine. To prevent the loss of an image, use **wait()** after **set_image()** call.

        Raises a RuntimeError upon trying to set an image when no pyghthouse routine is running.

        :param image: A 3D array where every entry is accessed via image[y][x][rgb].
                      The dimension sizes are 14x28x3, meaning the last entry should be accessed with image[13][27][2].
                      RGB entries only allow values in a range of 0 to 255 (one byte).
        """
        if not self._routine_is_running():
            raise RuntimeError("Cannot set an image before Pyghthouse has started.")
        
        self.canvas.set_image(image)


    def wait(self):
        """
        Wait for finalization of the current frame.

        This function blocks the called thread until the current frame has been constructed.

        Recommended to prevent skipping/losing of important frames. 

        **set_image()** sets the image as fast as possible. On the other hand, the pyghthouse routine creates a frame
        every 1/frame_rate seconds with the last image set.
        This will result into skipping/losing images, when we create our images faster than the frame rate.
        To prevent the loss of an image, we use **wait()** to wait until the current frame has been finalized, so we
        can guarantee that the last image set will be send.
        
        **Do not use for fast interactive games** because waiting can result into delayed or ignored inputs! 
        For fast interactive games it is recommended to set the image as soon as an input is received.
        """
        if not self._routine_is_running():
            raise RuntimeError("Cannot wait without a Pyghthouse routine running.")
        
        self.ph_thread.ready.clear()

        if not self.ph_thread.ready.wait(self.timeout + self.send_interval + 0.2):
            raise RuntimeError("Unexpected behaviour. Reached wait timeout before socket timeout.")


    def keep_running(self):
        """
        Keeps the main thread alive.

        This function blocks the main thread. This will keep the pyghthouse routine running.

        Recommended for the use of callback functions which should run until error or keyboard interrupt.
        """
        while self._routine_is_running():
            self.wait()


    def stop(self):
        """
        Stops Pyghthouse routine.

        Stops the Pyghthouse routine and closes the websocket connection. All threads used by Pyghthouse will be
        stopped in the process. This process can take more time with lower frame rate.

        When Pyghthouse isn't running, no changes will be made.
        """
        if self.ph_thread.connected.is_set():
            self.ph_thread.stop()


    @staticmethod
    def empty_image():
        """
        Returns an empty image.

        An empty image is a fully black image, meaning every RGB value is set to 0. 
        """
        return [[[0 for k in range(3)] for j in range(28)] for i in range(14)]


    def get_image(self):
        """
        Returns a copy of the current canvas image.
        """
        return self.canvas.copy_image()

    
    def set_image_callback(self, image_callback=None):
        """
        Sets a new callback function for image creation.

        This function is async to the pyghthouse routine, so non-deterministic behaviour is possible.

        To prevent image loss, it is recommended to synchronize with the pyghthouse routine by using **wait()** for x
        times where x is the amount of images send before calling this function.

        When the image_callback is set to *None*, the Pyghthouse routine will stop using the callback function for 
        image generation. 
        """
        self.ph_thread.callback = image_callback


    def _routine_is_running(self):
        # Check for errors
        if self.ph_thread.error.is_set():
            raise self.ph_thread.exception
        
        if self.ph_thread.connector.error.is_set():
            raise self.ph_thread.connector.exception
        
        # Check if Pyghthouse routine is running
        return self.ph_thread.connected.is_set()


    ## Support of old features ##

    def close(self):
        """
        Same as **stop()**. 
        
        Stops Pyghthouse routine.

        Stops the Pyghthouse routine and closes the websocket connection. All threads used by Pyghthouse will be
        stopped in the process. This process can take more time with lower frame rate.

        When Pyghthouse isn't running, no changes will be made.
        """
        self.stop()


    def set_frame_rate(self, frame_rate:float):
        """
        Set frame_rate to a new value.

        The frame_rate must be greater than 0.5 and at most 60.

        This function executes asynchronous to the pyghthouse routine. It's not possible to guarantee a deterministic
        behaviour of this function.
        """
        if frame_rate <= 0.5 or frame_rate > 60.0:
            self.stop()
            raise ValueError("frame rate must be greater than 0.5 and at most 60.")
        
        self.ph_thread.send_interval = 1.0 / frame_rate