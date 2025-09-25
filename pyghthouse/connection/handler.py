from .data import VerbosityLevel

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
