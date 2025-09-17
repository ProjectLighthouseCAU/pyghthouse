from threading import Thread, Event, main_thread
from time import sleep, time

from pyghthouse.data.canvas import PyghthouseCanvas
from pyghthouse.connection.wsconnector import WSConnector
from ..ph import VerbosityLevel

class PHThread(Thread):

    def __init__(self, send_interval, image_callback, canvas:PyghthouseCanvas, username:str, token:str, address:str, verbosity:VerbosityLevel, ignore_ssl_cert:bool):
        super().__init__()
        self.send_interval = send_interval
        self.callback = image_callback
        self.canvas = canvas
        self.connector = WSConnector(username, token, address, 
                                     verbosity, ignore_ssl_cert)
        self._stop_event = Event()
        self.main_thread = main_thread()
        
        self.ignore_main = False
        if self.callback is not None:
            self.ignore_main = True


    def stop(self):
        self._stop_event.set()


    def stopped(self):

        if not self.ignore_main and not self.main_thread.is_alive():
            return True
       
        return self._stop_event.is_set()


    def run(self):
        self.connect()
        
        while not self.stopped():
            sleep_time = self.send_interval - (time() % self.send_interval)
            sleep(sleep_time)
            self.send_image()
        
        self.disconnect()
        

    def send_image(self):

        if self.callback is not None:
            self.set_callback_image()

        bytes_image = self.canvas.get_bytes_image()
        self.connector.send(bytes_image)


    def set_callback_image(self):
            
        image_from_callback = self.callback()
        try:
            self.canvas.set_image(image_from_callback)
        except:
            self.disconnect()
            raise


    # TODO: Start websocket connection and wait until websocket is open
    def connect(self):
        pass

    
    # TODO: Signal websocket to close connection
    def disconnect(self):
        pass