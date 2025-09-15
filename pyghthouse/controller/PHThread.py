from threading import Thread, Event
from time import sleep, time

from pyghthouse.data.canvas import PyghthouseCanvas
from pyghthouse.connection.wsconnector import WSConnector
from ..ph import VerbosityLevel

class PHThread(Thread):

    def __init__(self, image_callback, canvas:PyghthouseCanvas, username, token, address, ignore_ssl_cert=False):
        super().__init__()
        self.callback = image_callback
        self.canvas = canvas
        self.connector = WSConnector(username, token, address, verbosity=VerbosityLevel.WARN_ONCE,
                                     ignore_ssl_cert=ignore_ssl_cert)
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
                if self.callback is not None:
                    image_from_callback = self.callback()
                    self.canvas.set_image(image_from_callback)
                self.connector.send(self.parent.canvas.get_image_bytes())