from threading import Thread, Event, main_thread
from time import sleep, time

from .data.canvas import PyghthouseCanvas
from .connection.wsconnector import WSConnector, VerbosityLevel

class PHThread(Thread):
    """
        A Pyghthouse-Thread for the Pyghthouse routine.

        The Pyghthouse routine consists of the following phases:
        - Connection Phase: Connects the client to the webserver.
        - Main routine:     Loop for sending frames to the webserver.
        - Ending Phase:     Correctly closes the connection.

        Attributes
        ----------
        send_interval : float
            Time (in seconds) between each frame.
        
        canvas : PyghthouseCanvas
            Each frame will send the currently stored image in canvas.

        image_callback : function() -> image, optional
            Function to produce a new image each frame.
            When *None* given, the image saved in *canvas* will be used instead.
            Default is *None*.

        ready : Event
            Event flag is set to *True* after successful connection to the server. Frames will be frequently send in *True* state.

        stop_event : Event
            Indicates when the Pyghthouse routine should be stopped.
        """

    def __init__(self, send_interval, image_callback, canvas:PyghthouseCanvas, username:str, token:str, address:str, verbosity:VerbosityLevel, ignore_ssl_cert:bool):
        """
        Initialize thread for Pyghthouse routine.

        Parameters
        ----------
        send_interval : float
            Time (in seconds) between each frame.
        
        canvas : PyghthouseCanvas
            Each frame will send the currently stored image in canvas.

        image_callback : function() -> image, optional
            Function to produce a new image each frame.
            When *None* given, the image saved in *canvas* will be used instead.
            Default is *None*.
        """
        super().__init__()
        self.send_interval = send_interval
        self.callback = image_callback
        self.canvas = canvas

        self.connector = WSConnector(username, token, address, 
                                     verbosity, ignore_ssl_cert)
        
        self.ready = self.connector.connected
        self.stop_event = Event()
        
        # Used to react to unexpected end of main
        self.main_thread = main_thread()
        
        self.ignore_main = False
        if self.callback is not None:
            self.ignore_main = True


    def stop(self):
        """
        Ends Pyghthouse routine.
        """
        self._stop_event.set()


    def _close(self):
        """
        Ends Pyghthouse routine when *stop_event* is set or upon unexpected end of main.
        """
        if not self.ignore_main and not self.main_thread.is_alive():
            return True
       
        return self._stop_event.is_set()


    def run(self):
        """
        Starts Pyghthouse-Thread routine. This routine sends images in the selected interval.
        """
        self._connect()
        
        self.ready.set()
        while not self._close():
            sleep_time = self.send_interval - (time() % self.send_interval)
            sleep(sleep_time)
            self._send_image()
        
        self._disconnect()
        

    def _send_image(self):
        """
        Build and send current frame
        """
        if self.callback is not None:
            self._get_callback_image()

        bytes_image = self.canvas.get_bytes_image()
        self.connector.send(bytes_image)


    def _get_callback_image(self):
        """
        Get image from callback function.
        """
        image_from_callback = self.callback()
        try:
            self.canvas.set_image(image_from_callback)
        except:
            self._disconnect()
            raise


    def _connect(self):
        self.connector.open()
        self.connector.connected.wait()

    
    def _disconnect(self):
        self.connector.stop()