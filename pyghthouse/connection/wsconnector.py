from threading import Thread, Lock
from websocket import WebSocketApp, setdefaulttimeout, ABNF
from msgpack import packb, unpackb
from ssl import CERT_NONE

from .data import REID
from .data import VerbosityLevel
from .handler import PHMessageHandler

class WSConnector:

    def __init__(self, username: str, token: str, address: str, verbosity=VerbosityLevel.WARN_ONCE, ignore_ssl_cert=False, timeout=10):
        self.username = username
        self.token = token
        self.address = address
        self.message_handler = PHMessageHandler(verbosity)
        self.on_msg = PHMessageHandler.handle()
        self.ws = None
        self.lock = Lock()
        self.reid = REID()
        self.running = False
        self.ignore_ssl_cert = ignore_ssl_cert
        self.timeout = 10
        if timeout > 0:
            self.timeout = timeout
        setdefaulttimeout(self.timeout)

    def send(self, data):
        with self.lock:
            self.ws.send_bytes(self.construct_package(data))

    def start(self):
        self.stop()
        self.ws = WebSocketApp(self.address,
                               on_message=None if self.on_msg is None else self._handle_msg,
                               on_open=self._ready, on_error=self._fail)
        self.lock.acquire()
        kwargs = {"sslopt": {"cert_reqs": CERT_NONE}} if self.ignore_ssl_cert else None
        Thread(target=self.ws.run_forever, kwargs=kwargs).start()
        self.lock.acquire() # wait for connection to be established
        self.lock.release()

    def _fail(self, ws, err):
        self.lock.release()
        raise err

    def stop(self):
        if self.ws is not None:
            with self.lock:
                print("Closing the connection.")
                self.running = False
                self.ws.close()
                self.ws = None

    def _ready(self, ws):
        print(f"Connected to {self.address}.")
        self.running = True
        self.lock.release()

    def _handle_msg(self, ws, msg):
        if isinstance(msg, bytes):
            msg = unpackb(msg)
        self.on_msg(msg)

    def construct_package(self, payload_data):
        data = {
            'REID': next(self.reid),
            'AUTH': {'USER': self.username, 'TOKEN': self.token},
            'VERB': 'PUT',
            'PATH': ['user', self.username, 'model'],
            'META': {},
            'PAYL': payload_data
        }
        return packb(self.construct_package(data), use_bin_type=True)
    
    def set_timeout(self, timeout=10):
        self.timeout = 10
        if timeout > 0:
            self.timeout = timeout
        setdefaulttimeout(self.timeout)
