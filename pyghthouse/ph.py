from signal import signal, SIGINT

from .data.canvas import PyghthouseCanvas
from ._thread import PHThread
from .connection.wsconnector import VerbosityLevel

# TODO: Adjust description and example for more clarity
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
        lighthouse.uni-kiel.de, open the top-left rollover menu and click "API-Token anzeigen".

    address: str (optional, default: "wss://lighthouse.uni-kiel.de/websocket")
        URI of the WebSocket endpoint. You should not need to change this.

    frame_rate: float (optional; 0 < frame_rate <= 60, default: 30)
        Rate in 1/sec at which frames (images) are automatically sent to the lighthouse server. Also determines how
        often the image_callback function is called.

    image_callback: function (optional)
        A function that takes no arguments and generates a valid lighthouse image (cf Image Format). If set, this
        function is called before an image is sent and is used to determine said image.
        The function is guaranteed to be called frame_rate times each second *unless* its execution takes longer than
        1/frame_rate seconds, in which case execution will be slowed down accordingly.

    verbosity: pyghthouse.VerbosityLevel (optional, default: pyghthouse.VerbosityLevel.WARN_ONCE)
        How many reply messages from the server are printed to the console.
        Options:
        pyghthouse.VerbosityLevel.NONE:
            All messages are suppressed.
        pyghthouse.VerbosityLevel.WARN_ONCE:
            Only print the first warning. This is usually enough to diagnose common problems like invalid tokens.
        pyghthouse.VerbosityLevel.WARN:
            Print all warnings.
        pyghthouse.VerbosityLevel.ALL:
            Print all messages.

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

    Images can be either flat or nested lists, as long as they have 14*28*3=1176 elements overall. The
    Pyghthouse.empty_image() method returns a completely black image in the nested format, i.e.
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

    The following example creates a Pyghthouse and sets the 10th window of the 11th floor to orange.
    >>> from pyghthouse import Pyghthouse
    >>> p = Pyghthouse("YourUsername", "YourToken")
    >>> p.start() # not necessary to set image, but necessary for sending.
    >>> img = Pyghthouse.empty_image()
    >>> img[3][9] = [255, 127, 0]
    >>> p.set_image(img)

    Full Example
    ------------
    The following program renders a white dot that can be moved by up, down, left and right by typing W, S, A and D,
    respectively (and pressing ENTER).

    >>> from pyghthouse import Pyghthouse, VerbosityLevel
    >>> UNAME = "YourUsername"
    >>> TOKEN = "YourToken"
    >>> 
    >>> def clip(val, min_val, max_val):
    >>>     if val < min_val:
    >>>         return min_val
    >>>     if val > max_val:
    >>>         return max_val
    >>>     return val
    >>>
    >>> x = 0
    >>> y = 0
    >>> p = Pyghthouse(UNAME, TOKEN, verbosity=VerbosityLevel.NONE)
    >>> p.start()
    >>> while True:
    >>>     img = p.empty_image()
    >>>     img[y][x] = [255, 255, 255]
    >>>     p.set_image(img)
    >>>     s = input()
    >>>     for c in s.upper():
    >>>         if c == 'A':
    >>>             x -= 1
    >>>         elif c == 'D':
    >>>             x += 1
    >>>         elif c == 'W':
    >>>             y -= 1
    >>>         elif c == 'S':
    >>>             y += 1
    >>>     x = clip(x, 0, 27)
    >>>     y = clip(y, 0, 13)

    There are more code examples in the git repository 
    (https://github.com/ProjectLighthouseCAU/pyghthouse/tree/master/examples).
    """

    def __init__(self, username: str, token: str, address: str = "wss://lighthouse.uni-kiel.de/websocket",
                 frame_rate: float = 30.0, image_callback=None, verbosity=VerbosityLevel.WARN_ONCE,
                 ignore_ssl_cert=False):
        
        # Lower bound must be higher than default timeout of websocket
        if frame_rate > 60.0 or frame_rate <= 0.5:
            raise ValueError("Frame rate must be greater than 0.5 and at most 60.")
        
        self.send_interval = 1.0 / frame_rate
        self.timeout = 3
        
        self.canvas = PyghthouseCanvas()
        self.ph_thread = PHThread(self.send_interval, image_callback, self.canvas,
                                  username, token, address, verbosity, ignore_ssl_cert, self.timeout)
        
        signal(SIGINT, self._handle_sigint)


    def start(self):

        if not self.ph_thread.ready.is_set():
            self.ph_thread.start()
            
            if not self.ph_thread.ready.wait(self.timeout + self.send_interval + 0.5):
                raise RuntimeError("Unexpected library behaviour. Reached wait timeout before socket timeout.")
        
        else:

            self.close()
            raise RuntimeError("Pyghthouse can only be started once.")


    def set_image(self, image):
        
        # Check for errors
        if self.ph_thread.error.is_set():
            raise self.ph_thread.exception
        
        if self.ph_thread.connector.error.is_set():
            raise self.ph_thread.connector.exception
        
        # Check if Pyghthouse is running
        if not self.ph_thread.ready.is_set():
            raise RuntimeError("Cannot set an image before Pyghthouse has started.")
        
        # Setting the image
        try:
            self.canvas.set_image(image)
        except:
            self.close()
            raise


    def stop(self):
        """
        Stops Pyghthouse.

        Stops the Pyghthouse routine and closes the websocket connection. All
        threads used by Pyghthouse will be stopped in the process.

        When Pyghthouse isn't running, no changes will be made. 
        """
        if self.ph_thread.ready.is_set():
            self.ph_thread.stop()


    @staticmethod
    def empty_image():
        return [[[0 for k in range(3)] for j in range(28)] for i in range(14)]


    def _handle_sigint(self, sig, frame):
        self.close()
        raise SystemExit(0)


    def get_image(self):
        return self.canvas.copy_image()


    # Deprecated
    def get_image_raw(self):
        return self.get_image()

    # Deprecated
    @staticmethod
    def empty_image_raw():
        return Pyghthouse.empty_image()
    
    # Deprecated
    def set_image_callback(self, image_callback):
        self.ph_thread.callback = image_callback

    # Deprecated
    def set_frame_rate(self, frame_rate):
        if frame_rate > 60.0 or frame_rate <= 0:
            self.close()
            raise ValueError("frame rate must be greater than 0 and at most 60.")
        self.ph_thread.send_interval = 1.0 / frame_rate

    # Deprecated
    def connect(self):
        return self.start()

    # Deprecated
    def close(self):
        return self.stop()
