from .data import VerbosityLevel

# TODO: Rename? To WarningHandler?
class PHMessageHandler:

    def __init__(self, kwargs):
        self.verbosity = kwargs["verbosity"]
        self.warned_already = False

    def reset(self):
        self.warned_already = False

    def handle(self, msg):
        # TODO: Decide to print error to console and keep going or to close connection and stop pyghthouse routine
        if self.verbosity == VerbosityLevel.ALL:
            print(msg)
            return

        match msg["RNUM"]:
            case 200:
                pass
            case 401:
                self.print_warning(msg, "Are Username and Token correct?")
            case _:
                self.print_warning(msg)
        
    def print_warning(self, msg, hint=""):
        if self.verbosity == VerbosityLevel.WARN_ONCE and self.warned_already:
            return
        
        print(f"Warning: {msg['RNUM']} {msg['RESPONSE']} {', '.join(msg['WARNINGS'])}")
        if hint:
            print(hint)
        
        self.warned_already = True
