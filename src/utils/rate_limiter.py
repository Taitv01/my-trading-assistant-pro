"""Rate limiting utility for API requests"""
import time
from collections import deque

class RateLimiter:
    """
    Token bucket rate limiter.

    Usage:
        limiter = RateLimiter(requests_per_minute=60)
        limiter.wait()  # Blocks if rate limit would be exceeded
        # make request
    """

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests allowed per minute
        """
        self.rpm = requests_per_minute
        self.window = 60.0  # seconds
        self.timestamps = deque()

    def wait(self):
        """
        Wait if necessary to respect rate limit.
        Call before each API request.
        """
        now = time.time()

        # Remove timestamps older than window
        while self.timestamps and self.timestamps[0] < now - self.window:
            self.timestamps.popleft()

        # If at limit, wait until oldest timestamp expires
        if len(self.timestamps) >= self.rpm:
            sleep_time = self.timestamps[0] - (now - self.window) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.timestamps.append(time.time())

    @property
    def current_rate(self) -> int:
        """Current requests in window"""
        now = time.time()
        while self.timestamps and self.timestamps[0] < now - self.window:
            self.timestamps.popleft()
        return len(self.timestamps)
