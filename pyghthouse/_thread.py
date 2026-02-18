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
        - Ending Phase:     Closes the connection and cleanup threads.

        In the main routine, this thread will build and send frames from 
        **canvas**. The time between each frame is indicated by 
        **send_interval**.

        Attributes
        ----------
        send_interval : float
            Time (in seconds) between each frame.
        
        canvas : PyghthouseCanvas
            Each frame will send the currently stored image in **canvas**.

        image_callback : function() -> image, optional
            Function to produce a new image each frame.
            When *None* given, the image saved in **canvas** will be used instead.
            Default is *None*.

        connected : Event
            Event flag is set to *True* after successful connection to the server. 
            Frames will be frequently send in *True* state.

        ready : Event
            Event flag is set to *True* in the send process of a frame.
            This flag will always be *True* when connected is *True*, unless the even is unset Can be used for waiting operations.

        stop_event : Event
            Indicates when the Pyghthouse routine should be stopped.

        error : Event
            Event flag is set to *True* when an error accured inside the pyghthouse routine.
        """

    def __init__(self, send_interval, image_callback, canvas:PyghthouseCanvas, 
                 username:str, token:str, address:str, verbosity:VerbosityLevel, ignore_ssl_cert:bool, timeout=2.5):
        """
        Initialize thread for Pyghthouse routine.

        Parameters
        ----------
        send_interval : float
            Time (in seconds) between each frame.
        
        canvas : PyghthouseCanvas
            Each frame will send the currently stored image in **canvas**.

        image_callback : function() -> image, optional
            Function to produce a new image each frame.
            When *None* given, the image saved in **canvas** will be used instead.
            Default is *None*.
        """
        super().__init__()
        self.send_interval = send_interval
        self.callback = image_callback
        self.canvas = canvas
        self.verbosity = verbosity

        self.connector = WSConnector(username, token, address, 
                                     verbosity, ignore_ssl_cert, timeout=timeout)
        
        self.connected = Event()
        self.ready = Event()
        self.stop_event = Event()
        self.error = Event()
        self.exception = None
        
        # Used to react to unexpected end of main
        self.main_thread = main_thread()
        


    def stop(self):
        """
        Ends Pyghthouse routine.
        """
        self.stop_event.set()


    def _is_stop(self):
        """
        Ends Pyghthouse routine when **stop_event** is set or upon unexpected
        end of main.

        Errors inside the routine also results into the stopping process.
        """
        if self.stop_event.is_set():
            return True
        
        if self.connector.error.is_set():
            return True
        
        if not self.main_thread.is_alive():
            if self.verbosity == VerbosityLevel.ALL:
                print("Main thread dead.")
            
            return True
       
        return False


    def run(self):
        """
        Starts Pyghthouse-Thread routine. This routine sends images in the selected interval.
        """
        if self.verbosity == VerbosityLevel.ALL:
            print("Starting Pyghthouse routine.")
        
        self._connect()

        while not self._is_stop():

            self._send_image()

            sleep_time = self.send_interval - (time() % self.send_interval)
            sleep(sleep_time)
        
        if self.verbosity == VerbosityLevel.ALL:
            print("Ending Pyghthouse routine.")
        
        self._disconnect()
        

    def _send_image(self):
        """
        Build and send current frame.

        If error accures in sending process, the connection will be closed.
        """
        if self.callback is not None:
            self._get_callback_image()

        bytes_image = self.canvas.get_bytes_image()
        # Signal wait function in ph.py to continue
        self.ready.set()
        self.connector.send(bytes_image)


    def _get_callback_image(self):
        """
        Get image from callback function.
        """
        try:
            image_from_callback = self.callback()
            self.canvas.set_image(image_from_callback)
        
        except Exception as exception:
            self.exception = exception
            self.error.set()
            
            self.stop()


    def _connect(self):
        """
        Opens websocket connection.

        This function will also wait till the opening process has been finished
        """
        self.connector.open()
        self.connected.set()

    
    def _disconnect(self):
        """
        Closes the connection.

        Closing the connection also stops the websocket thread. So this 
        function allows the Pyghthouse thread to exit properly.
        """
        self.connected.clear()
        self.ready.set()
        self.connector.close()