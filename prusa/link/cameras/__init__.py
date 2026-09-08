"""Camera drivers and the helpers they share"""
from functools import wraps


def serialized_capture(take_a_photo):
    """Serialise device access between the SDK and the live stream.

    The SDK triggers every photo in a thread of its own, while a live
    stream captures in a loop. A driver reuses a single request object
    per camera, so the two must never reach the device at once.
    """

    @wraps(take_a_photo)
    def inner(self):
        with self.capture_lock:
            return take_a_photo(self)

    return inner
