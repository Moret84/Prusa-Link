"""Continuous frame capture feeding the camera live stream"""
import logging
from threading import Condition, Lock, Thread
from time import monotonic, sleep
from typing import Dict, Optional

from ..util import prctl_name

log = logging.getLogger(__name__)


class FrameBroadcaster:
    """Captures frames while somebody watches and hands the latest one
    to every subscriber.

    A single capture thread serves all the subscribers of a camera, so
    the device is read once per frame however many clients are
    connected, and not at all when there are none.
    """

    def __init__(self, driver, frame_interval):
        self.driver = driver
        self._frame_interval = frame_interval
        self._condition = Condition()
        self._frame: Optional[bytes] = None
        self._sequence = 0
        self._subscribers = 0
        self._capturing = False

    @property
    def subscribers(self):
        """Return how many clients are being served right now"""
        with self._condition:
            return self._subscribers

    def subscribe(self):
        """Yield every frame captured while the caller keeps iterating"""
        with self._condition:
            self._subscribers += 1
            last_seen = self._sequence
            start_capturing = not self._capturing
            self._capturing = True

        if start_capturing:
            Thread(target=self._capture_loop,
                   name="FrameBroadcaster",
                   daemon=True).start()

        try:
            while True:
                frame, last_seen = self._next_frame(last_seen)
                if frame is None:
                    return
                yield frame
        finally:
            with self._condition:
                self._subscribers -= 1

    def _next_frame(self, last_seen):
        """Wait for a frame newer than last_seen.

        Returns a None frame once the capture loop has stopped.
        """
        with self._condition:
            self._condition.wait_for(
                lambda: not self._capturing
                or (self._frame is not None and self._sequence != last_seen))
            if not self._capturing:
                return None, last_seen
            return self._frame, self._sequence

    def _capture_loop(self):
        """Capture frames until the last subscriber has left"""
        prctl_name()
        try:
            while self._keep_capturing():
                started_at = monotonic()
                self._publish(self.driver.take_a_photo())
                self._wait_for_next_frame(started_at)
        except Exception:  # pylint: disable=broad-except
            log.exception("Camera %s broke while streaming",
                          self.driver.camera_id)
        finally:
            with self._condition:
                self._capturing = False
                self._condition.notify_all()

    def _wait_for_next_frame(self, started_at):
        """Sleep off whatever is left of the frame interval.

        A camera slower than the requested rate is left to run
        flat out rather than being slowed down further.
        """
        remaining = self._frame_interval - (monotonic() - started_at)
        if remaining > 0:
            sleep(remaining)

    def _keep_capturing(self):
        """Tell whether to capture another frame, stopping if nobody
        is watching any more"""
        with self._condition:
            if self._subscribers > 0:
                return True
            self._capturing = False
            self._condition.notify_all()
            return False

    def _publish(self, frame):
        """Hand a freshly captured frame to the subscribers"""
        with self._condition:
            self._frame = frame
            self._sequence += 1
            self._condition.notify_all()


class BroadcasterRegistry:
    """Keeps one broadcaster per camera"""

    def __init__(self):
        self._lock = Lock()
        self._broadcasters: Dict[str, FrameBroadcaster] = {}

    def for_driver(self, driver, frame_interval):
        """Return the broadcaster of a driver, creating it when needed.

        A reconnected camera comes back as a new driver instance, whose
        frames the previous broadcaster cannot capture any more.
        """
        with self._lock:
            broadcaster = self._broadcasters.get(driver.camera_id)
            if broadcaster is None or broadcaster.driver is not driver:
                broadcaster = FrameBroadcaster(driver, frame_interval)
                self._broadcasters[driver.camera_id] = broadcaster
            return broadcaster


broadcasters = BroadcasterRegistry()
