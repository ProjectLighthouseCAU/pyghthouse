from enum import Enum
from time import time, sleep
from threading import Thread, Event, Lock
from signal import signal, SIGINT

from pyghthouse.data.canvas import PyghthouseCanvas
from pyghthouse.connection.wsconnector import WSConnector


class VerbosityLevel(Enum):
    NONE = 0
    WARN_ONCE = 1
    WARN = 2
    ALL = 3


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

    class PHMessageHandler:

        def __init__(self, verbosity=VerbosityLevel.WARN_ONCE):
            self.verbosity = verbosity
            self.warned_already = False

        def reset(self):
            self.warned_already = False

        def handle(self, msg):
            if msg['RNUM'] == 200:
                if self.verbosity == VerbosityLevel.ALL:
                    print(msg)
            elif self.verbosity == VerbosityLevel.WARN:
                self.print_warning(msg)
            elif self.verbosity == VerbosityLevel.WARN_ONCE and not self.warned_already:
                self.print_warning(msg)
                self.warned_already = True

        @staticmethod
        def print_warning(msg):
            print(f"Warning: {msg['RNUM']} {msg['RESPONSE']} {', '.join(msg['WARNINGS'])}")

    class PHThread(Thread):

        def __init__(self, parent):
            super().__init__()
            self.parent = parent
            self._stop_event = Event()

        def stop(self):
            self._stop_event.set()

        def stopped(self):
            return self._stop_event.is_set()

        def run(self):
            while not self.stopped():
                with self.parent.config_lock:
                    sleep_time = self.parent.send_interval - (time() % self.parent.send_interval)
                    sleep(sleep_time)
                    if self.parent.image_callback is not None:
                        image_from_callback = self.parent.image_callback()
                        self.parent.set_image(image_from_callback)
                    self.parent.connector.send(self.parent.canvas.get_image_bytes())

    def __init__(self, username: str, token: str, address: str = "wss://lighthouse.uni-kiel.de/websocket",
                 frame_rate: float = 30.0, image_callback=None, verbosity=VerbosityLevel.WARN_ONCE,
                 ignore_ssl_cert=False):
        if frame_rate > 60.0 or frame_rate <= 0:
            raise ValueError("Frame rate must be greater than 0 and at most 60.")
        self.username = username
        self.token = token
        self.address = address
        self.send_interval = 1.0 / frame_rate
        self.image_callback = image_callback
        self.canvas = PyghthouseCanvas()
        self.msg_handler = self.PHMessageHandler(verbosity)
        self.connector = WSConnector(username, token, address, on_msg=self.msg_handler.handle,
                                     ignore_ssl_cert=ignore_ssl_cert)
        self.config_lock = Lock()
        self.ph_thread = None
        signal(SIGINT, self._handle_sigint)

    def connect(self):
        self.connector.start()

    def start(self):
        if not self.connector.running:
            self.connect()
        self.stop()
        self.msg_handler.reset()
        self.ph_thread = self.PHThread(self)
        self.ph_thread.start()

    def stop(self):
        if self.ph_thread is not None:
            self.ph_thread.stop()
            self.ph_thread.join()

    def close(self):
        self.stop()
        self.connector.stop()

    def set_image(self, image):
        with self.connector.lock:
            self.canvas.set_image(image)

    def get_image(self):
        with self.connector.lock:
            return self.canvas.image

    @staticmethod
    def empty_image():
        return [[[0 for k in range(3)] for j in range(28)] for i in range(14)]

    def set_image_callback(self, image_callback):
        with self.config_lock:
            self.image_callback = image_callback

    def set_frame_rate(self, frame_rate):
        with self.config_lock:
            self.send_interval = 1.0 / frame_rate

    def _handle_sigint(self, sig, frame):
        self.close()
        raise SystemExit(0)
