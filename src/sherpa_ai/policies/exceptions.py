import traceback


class SherpaPolicyException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.stacktrace = traceback.format_stack()
