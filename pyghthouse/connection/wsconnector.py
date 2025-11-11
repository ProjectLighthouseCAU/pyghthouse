from threading import Thread, Event
from websocket import WebSocketApp, setdefaulttimeout, WebSocketConnectionClosedException
from msgpack import packb, unpackb
from ssl import CERT_NONE

from .data import VerbosityLevel, ReID
from .handler import PHMessageHandler

class WSConnector:
    """
    A connector to the Lighthouse API with websocket thread.

    Attributes
    ----------
    connected : Event
        Event flag is set to *True* when websocket thread is connected to the
        webserver and **send** can be used.
    
    error : Event
        Event flag is set to *True* when error accured and connection is closed.
        
    The flag **error** has a higher priotiy than the **connected** flag.
    Meaning when **error** is set to *True*, the connection is closed
    even when **connected** can be set to *True*.

    For further invastigation, check developer notes in **on_error**
    """
    
    def __init__(self, username:str, token:str, address:str, 
                 verbosity=VerbosityLevel.WARN_ONCE, ignore_ssl_cert:bool=False, 
                 handler=PHMessageHandler, timeout=3):
        """
        WSConnector initialization.

        Parameters
        ----------
        username: str
            Username
        token: str
            API-Token
        address: str
            Address of webserver.
        verbosity: VerbosityLevel
            Indicate level of displayed informations.
        ignore_ssl_cert: bool
            Ignores ssl certification when set to *True*. Default ssl
            certification is none, so no certificates from the other side are
            required (or will be looked at if provided).
        handler: PHMessageHandler
            Handles the messages received from the network.
        timeout: int or float
            Set timeout of WebSocket connection.
        """
        
        self.username = username
        self.token = token
        self.address = address
        self.reID = ReID()
        self.verbosity = verbosity
        
        self.connected = Event()
        self.error = Event()
        self.exception = None
        
        kwargs = {"verbosity": self.verbosity}
        handler = handler(kwargs)
        self.handle_message = handler.handle
        
        # TODO: Maybe move functions for state handeling to handler class?
        self.ws = WebSocketApp(address, 
                               on_open=self._on_open, 
                               on_message=self._on_message, 
                               on_error=self._on_error, 
                               on_close=self._on_close)
        
        kwargs = {"sslopt": {"cert_reqs": CERT_NONE}}
        if ignore_ssl_cert:
            kwargs = None
        
        self.timeout = 3
        if timeout > 0:
            self.timeout = timeout
        setdefaulttimeout(self.timeout)
        
        self.thread = Thread(target=self.ws.run_forever, kwargs=kwargs)


    def open(self):
        """
        Opens websocket connection.

        Starts websocket thread which will open the websocket connection.
        
        After opening the websocket, the websocket thread sets the 
        **connected** event flag to *True* and is ready to send data.

        When an error accured upon opening, the **error** flag will be set to
        *True* and **on_error** will be called. In this case, the connection
        will be closed again and the **connected** flag will cleared to *False*
        again.
        """
        if self.verbosity == VerbosityLevel.ALL:
            print("Opening websocket connection.")
        
        self.thread.start()
        
        if not self.connected.wait(self.timeout+0.5):
            raise RuntimeError("Unexpected library behaviour. Reached wait timeout before socket timeout.")
        
        if self.error.is_set():
            self.connected.clear()
            
            if self.verbosity == VerbosityLevel.ALL:
                print(f"Error upon connecting to {self.address}")



    def send(self, data):
        """
        Send data via websocket connection.

        Raises a *WebSocketConnectionClosedException* when no connection is
        present.
        """
        if self.error.is_set():
            return
    
        if self.connected.is_set():
            try:
                if self.verbosity == VerbosityLevel.ALL:
                    print("Sending frame.")
                
                self.ws.send_bytes(self.construct_package(data))
            
            except Exception as e:
                if self.verbosity == VerbosityLevel.ALL:
                    print("Failed send process.")
                
                self.close()

        else:
            self.exception = WebSocketConnectionClosedException("Cannot send frames. Connection is closed.")
            self.error.set()
                


    def close(self):
        """
        Close websocket connection.

        This function can still be used when no connection is present.
        """
        if self.verbosity == VerbosityLevel.ALL:
            print("Closing connection.")
        
        self.connected.clear()
        self.ws.close()


    def construct_package(self, payload_data):
        data = {
            'REID': next(self.reID),
            'AUTH': {'USER': self.username, 'TOKEN': self.token},
            'VERB': 'PUT',
            'PATH': ['user', self.username, 'model'],
            'META': {},
            'PAYL': payload_data
        }
        return packb(data, use_bin_type=True)


    def set_timeout(self, timeout=10):
        self.timeout = 3
        if timeout > 0:
            self.timeout = timeout
        setdefaulttimeout(self.timeout)


    # Functions used by the websocket thread:

    def _on_open(self, ws: WebSocketApp):
        """
        Called directly after websocket has been successfully opened.
        """
        if self.verbosity == VerbosityLevel.ALL:
            print(f"Connected to {self.address}")
        
        self.connected.set()


    def _on_message(self, ws: WebSocketApp, message):
        if self.verbosity == VerbosityLevel.ALL:
            print("Received message:")
        
        if isinstance(message, bytes):
            message = unpackb(message)
        self.handle_message(message)


    def _on_close(self, ws: WebSocketApp, close_status_code, close_msg):
        """
        Called after websocket connection fully closed.

        ----------------
        Developer notes:

        When the websocket thread has been started, **on_close** will always be
        called, even when an error accured upon opening the connection. This is
        a result of the **teardown** function in WebSocketApp.

        So its possible that **on_close** will be called even when **on_open**
        hasn't been called yet.
        
        For further invastigation, check the developer notes in **on_error**.
        """
        if self.verbosity == VerbosityLevel.ALL:
            print("Connection closed.")
        
        self.connected.clear()


    def _on_error(self, ws: WebSocketApp, err: Exception):
        """
        Further handeling of errors outside of WebSocketApp.

        This function will save the **exception** and set the flag **error**
        to *True*.

        This function also sets the flag **connected** to *True* to avoid
        blocking of **open** when an error accured upon opening the connection.
        
        ----------------
        Developer notes:

        This method is used by WebSocketApp as callback function.
        The intend is to signal that an error accured in WebSocketApp and to
        allow further error handeling outside of WebSocketApp.

        Because we use **run_forever** without a parameter for **reconnect**, 
        we use the standard of *0* from the websocket-client library.
        This will always force a teardown of the connection without an attempt
        to reconnect upon error. 
        
        A teardown of the connection will also call the **_on_close** callback
        function, even when **_on_error** has been the called. **_on_close**
        will even be called when an error accured on the attempt to open the 
        websocket.
        Meaning, **_on_close** can be called even when **_on_open** hasn't been
        called yet.

        Do not raise the exception here!
        --------------------------------
        This function will be called from the websocket thread. Raising an 
        exception here stops the teardown process and could result into 
        unexpected behaviour.
        """
        
        if self.verbosity == VerbosityLevel.ALL:
            print(err)
        
        self.exception = err
        self.error.set()
        self.connected.set()