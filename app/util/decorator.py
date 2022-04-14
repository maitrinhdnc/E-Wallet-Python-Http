import functools
import signal

class Token:
    def token_required(func):
        @functools.wraps(func)
        def decorate(*args, **kargs):
            token = args[1]
            if not token:
                return {"message":"Token required"}
            return func(*args, **kargs)
        return decorate

class TimeoutError(Exception):
    def __init__(self, value = "Timed Out"):
        self.value = value
    def __str__(self):
        return repr(self.value)
    def timeout(seconds_before_timeout):
        def decorate(f):
            def handler(signum, frame):
                raise TimeoutError()
            def new_f(*args, **kwargs):
                old = signal.signal(signal.SIGALRM, handler)
                signal.alarm(seconds_before_timeout)
                try:
                    result = f(*args, **kwargs)
                finally:
                    signal.signal(signal.SIGALRM, old)
                signal.alarm(0)
                return result
            return new_f
        return decorate