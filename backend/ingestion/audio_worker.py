"""One lazy, process-local FIFO consumer. Queue stores only bounded PCM segments.

Stop cancels queued/active work cooperatively; Python cannot interrupt a native
model call. A timed-out stop returns False and the daemon cannot prevent exit.
"""
import atexit
from collections import Counter, deque
from dataclasses import dataclass
import logging
import os
from threading import Condition, Event, Thread
from time import monotonic

from backend.models import db

logger = logging.getLogger(__name__)


class Cancelled(Exception):
    pass


@dataclass
class AudioJob:
    segment: object
    cancelled: Event
    ready_at: float

    def check_cancelled(self):
        if self.cancelled.is_set():
            raise Cancelled()


class AudioWorker:
    def __init__(self, app, process, capacity=8, max_wait_seconds=10):
        if capacity < 1 or max_wait_seconds <= 0:
            raise ValueError('audio queue capacity and max wait must be positive')
        self.app, self.process = app, process
        self.capacity, self.max_wait_seconds = capacity, max_wait_seconds
        self._condition = Condition()
        self._queue = deque()
        self._counts = Counter()
        self._stopping = False
        self._active = None
        self.thread = None
        self._pid = None
        atexit.register(self.stop)

    def start(self):
        with self._condition:
            if self._stopping:
                return
            if self.thread is not None:
                if self._pid != os.getpid():
                    raise RuntimeError('Do not fork after starting audio worker')
                return
            self._pid = os.getpid()
            self.thread = Thread(target=self._run, name='audio-inference', daemon=True)
            self.thread.start()

    def submit(self, segment, cancelled):
        self.start()
        with self._condition:
            self._counts['received'] += 1
            # Remove obsolete session work immediately, freeing PCM memory.
            kept = deque(j for j in self._queue if not j.cancelled.is_set())
            self._counts['cancelled'] += len(self._queue) - len(kept)
            self._queue = kept
            if self._stopping or len(self._queue) >= self.capacity:
                self._counts['rejected'] += 1
                logger.warning('audio_queue_rejected policy=reject_newest queued=%d', len(self._queue))
                return False
            self._queue.append(AudioJob(segment, cancelled, monotonic()))
            self._counts['accepted'] += 1
            self._counts['high_water'] = max(self._counts['high_water'], len(self._queue))
            self._condition.notify_all()
            return True

    def snapshot(self):
        with self._condition:
            keys = ('received', 'accepted', 'completed', 'failed', 'rejected', 'cancelled', 'high_water')
            return {**{k: self._counts[k] for k in keys}, 'queued': len(self._queue),
                    'active': int(self._active is not None),
                    'wait_max_ms': self._counts['wait_max_ms'],
                    'total_max_ms': self._counts['total_max_ms']}

    def _run(self):
        while True:
            with self._condition:
                self._condition.wait_for(lambda: self._queue or self._stopping)
                if self._stopping:
                    return
                job = self._queue.popleft()
                self._active = job
            started = monotonic()
            wait_ms = (started - job.ready_at) * 1000
            status = 'completed'
            reason = 'processed'
            try:
                job.check_cancelled()
                if wait_ms > self.max_wait_seconds * 1000:
                    raise Cancelled('queue deadline')
                # Session is scoped to THIS job, including exceptions and rollback.
                with self.app.app_context():
                    try:
                        self.process(job)
                    except BaseException:
                        db.session.rollback()
                        raise
                    finally:
                        db.session.remove()
            except Cancelled as exc:
                status = 'cancelled'
                reason = str(exc) or 'session_or_shutdown'
            except Exception:
                status = 'failed'
                reason = 'exception'
                logger.exception('audio_job_failed')
            finally:
                total_ms = (monotonic() - job.ready_at) * 1000
                with self._condition:
                    self._counts[status] += 1
                    self._counts['wait_max_ms'] = max(self._counts['wait_max_ms'], wait_ms)
                    self._counts['total_max_ms'] = max(self._counts['total_max_ms'], total_ms)
                    self._active = None
                    self._condition.notify_all()
                logger.info('audio_job status=%s reason=%s device=%s channel=%s wait_ms=%.3f processing_ms=%.3f total_ms=%.3f stats=%s',
                            status, reason, getattr(job.segment, 'device_id', None),
                            getattr(job.segment, 'channel_id', None), wait_ms, total_ms - wait_ms, total_ms, self.snapshot())
                job = None  # release PCM while waiting for next job

    def wait_idle(self, timeout=10):
        with self._condition:
            return self._condition.wait_for(lambda: not self._queue and self._active is None, timeout)

    def stop(self, timeout=2):
        with self._condition:
            self._stopping = True
            self._counts['cancelled'] += len(self._queue)
            self._queue.clear()
            if self._active is not None:
                self._active.cancelled.set()
            self._condition.notify_all()
        if self.thread is not None:
            self.thread.join(timeout)
            stopped = not self.thread.is_alive()
            if stopped:
                atexit.unregister(self.stop)
            return stopped
        atexit.unregister(self.stop)
        return True
