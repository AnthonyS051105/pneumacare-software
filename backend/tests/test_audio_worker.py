from threading import Event
import time

from backend.ingestion.audio_worker import AudioWorker, Cancelled


def test_bounded_queue_nonblocking_order_and_survives_failure(app):
    entered, release = Event(), Event()
    seen = []

    def process(job):
        if job.segment == 0:
            entered.set()
            assert release.wait(3)
            raise ValueError('one bad job')
        seen.append(job.segment)

    worker = AudioWorker(app, process, capacity=2)
    try:
        assert worker.submit(0, Event())
        assert entered.wait(2)
        start = time.monotonic()
        assert worker.submit(1, Event())
        assert worker.submit(2, Event())
        assert not worker.submit(3, Event())
        assert time.monotonic() - start < .1
        assert worker.snapshot()['queued'] == 2
        release.set()
        assert worker.wait_idle(3)
        stats = worker.snapshot()
        assert seen == [1, 2]
        assert stats['failed'] == 1
        assert stats['completed'] == 2
        assert stats['rejected'] == 1
        assert stats['high_water'] == 2
    finally:
        release.set()
        assert worker.stop(3)


def test_cancelled_session_never_processes_queued_jobs(app):
    entered, release, old = Event(), Event(), Event()
    seen = []
    def process(job):
        entered.set()
        release.wait(3)
        job.check_cancelled()
        seen.append(job.segment)
    worker = AudioWorker(app, process, capacity=2)
    assert worker.submit(1, old)
    assert entered.wait(2)
    assert worker.submit(2, old)
    old.set()
    release.set()
    assert worker.wait_idle(3)
    assert seen == []
    assert worker.snapshot()['cancelled'] == 2
    assert worker.stop(3)


def test_lazy_idempotent_start_and_bounded_shutdown(app):
    entered, release = Event(), Event()
    def process(job):
        entered.set()
        release.wait(3)
        job.check_cancelled()
    worker = AudioWorker(app, process, capacity=1)
    assert worker.thread is None
    worker.start()
    thread = worker.thread
    worker.start()
    assert worker.thread is thread
    worker.submit(1, Event())
    assert entered.wait(2)
    assert not worker.stop(.01)
    assert not worker.submit(2, Event())
    release.set()
    assert worker.stop(3)
