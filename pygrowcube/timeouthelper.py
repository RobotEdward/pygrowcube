from time import perf_counter


class TimeoutHelper:
    def __init__(self, timeout_in_seconds: float):
        self.start = perf_counter()
        self.timeout = timeout_in_seconds

    @property
    def remaining(self) -> float:
        return self.timeout - (perf_counter() - self.start)

    @property
    def timed_out(self) -> bool:
        return (perf_counter() - self.start) > self.timeout

    @property
    def elapsed(self) -> float:
        return perf_counter() - self.start
