from threading import Thread, Event
from time import sleep, time

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