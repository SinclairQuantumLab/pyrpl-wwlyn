"""
This file contains a number of methods for asynchronous operations.
"""
import logging
from qtpy import QtCore, QtWidgets
from timeit import default_timer
logger = logging.getLogger(name=__name__)

from . import APP  # APP is only created once at the startup of PyRPL
MAIN_THREAD = APP.thread()

from asyncio import Future, ensure_future, CancelledError, current_task, \
    get_running_loop, set_event_loop, TimeoutError
import qasync

try:
    # Modern IPython/ipykernel already owns a running asyncio loop. Replacing
    # it with a second qasync loop can stall the kernel after this import.
    LOOP = get_running_loop()
    _PYRPL_OWNS_LOOP = False
except RuntimeError:
    try:
        from IPython import get_ipython
        _IPYTHON = get_ipython()
    except ImportError:  # pragma: no cover - IPython is a runtime dependency
        _IPYTHON = None

    # Terminal IPython drives Qt through its GUI input hook but does not expose
    # a running asyncio loop while a command is evaluated.
    if _IPYTHON is not None:
        LOOP = qasync.QEventLoop(APP, already_running=True)
        _PYRPL_OWNS_LOOP = False
    else:
        LOOP = qasync.QEventLoop(APP)
        _PYRPL_OWNS_LOOP = True
    set_event_loop(LOOP)


def _inside_owned_asyncio_task():
    """Whether blocking would re-enter a Task driven by PyRPL's Qt loop."""
    return (_PYRPL_OWNS_LOOP and LOOP.is_running()
            and current_task(loop=LOOP) is not None)


class MainThreadTimer(QtCore.QTimer):
    """
    To be able to start a timer from any (eventually non Qt) thread,
    we have to make sure that the timer is living in the main thread (in Qt,
    each thread potentially has a distinct eventloop...).

    For example, this is required to use the timer within timeit.

    we might decide one day to allow 2 event loops to run concurrently in
    separate threads, but
    1. That should be QThreads and not python threads
    2. We would have to make sure that all the gui operations are performed
    in the main thread (for instance, by moving all widgets in the
    mainthread, and probably, we would have to change some connections in
    QueuedConnections)
    ==> but this is not a supported feature for the moment and I don't see
    the advantage because the whole point of using an eventloop is to
    avoid multi-threading.

    For conveniance, MainThreadTimer is also SingleShot by default and is
    initialized with an interval as only argument.

    Benchmark:

     1. keep starting the same timer over and over --> 5 microsecond/call::

            n = [0]
            tics = [default_timer()]
            timers = [None]
            N = 100000
            timer = MainThreadTimer(0)
            timer.timeout.connect(func)
            def func():
                n[0]+=1
                if n[0] > N:
                    print('done', (default_timer() - tics[0])/N)
                    return
                timer.start()
                timers[0] = timer
                return
            func() ---> 5 microseconds per call

     2. Instantiating a new timer at each call --> 15 microsecond/call::

            n = [0]
            tics = [default_timer()]
            timers = [None]
            N = 100000
            def func():
                n[0]+=1
                if n[0] > N:
                    print('done', (default_timer() - tics[0])/N)
                    return
                timer = MainThreadTimer(0)
                timer.timeout.connect(func)
                timer.start()
                timers[0] = timer
                return
            func() ---> 15 microseconds per call

    Moreover, no catastrophe occurs when instantiating >10e6 timers
    successively

    Conclusion: it is OK to instantiate a new timer every time it is needed
    as long as a 10 microsecond overhead is not a problem.
    """

    def __init__(self, interval):
        super(MainThreadTimer, self).__init__()
        self.moveToThread(MAIN_THREAD)
        self.setSingleShot(True)
        self.setInterval(max(0, int(round(interval))))




class PyrplFuture(Future):
    """
    A promise object compatible with the Qt event loop.

    We voluntarily use an object that is different from the native QFuture
    because we want a promise object that is compatible with the python 3.5+
    asyncio patterns (for instance, it implements an __await__ method...).

    Attributes:
        cancelled: Returns whether the promise has been cancelled.
        exception: Blocks until:
                a. the result is ready --> returns None
                b. an exception accured in the execution --> returns the exception the Qt event-loop is allowed to run in parallel.
        done: Checks whether the result is ready or not.
        add_done_callback (callback function): add a callback to execute when result becomes available. The callback function takes 1 argument (the result of the promise).

    Methods to implement in derived class:
        _set_data_as_result(): set
    """

    def __init__(self):
        super(PyrplFuture, self).__init__(loop=LOOP)
        self._timer_timeout = None  # timer that will be instantiated if
        #  result(timeout) is called with a >0 value

    def result(self):
        """
        Blocks until the result is ready while running the event-loop in the background.

        Returns:
            The result of the future.
        """
        return super(PyrplFuture, self).result()

    def _set_timeout(self):
        if not self.done():
            self.set_exception(TimeoutError("timeout occurred"))

    def _wait_for_done(self, timeout):
        """
        Will not return until either timeout expires or future becomes "done".
        Coroutine callers must await the future instead of blocking on
        await_result().
        """
        if self.cancelled():
            raise CancelledError("Future was cancelled")  # pragma: no-cover
        if not self.done():
            self._timer_timeout = None
            if (timeout is not None) and timeout > 0:
                self._timer_timeout = MainThreadTimer(timeout*1000)
                self._timer_timeout.timeout.connect(self._set_timeout)
                self._timer_timeout.start()
            try:
                if _PYRPL_OWNS_LOOP and not LOOP.is_running():
                    LOOP.run_until_complete(self)
                else:
                    if _inside_owned_asyncio_task():
                        raise RuntimeError(
                            "await_result() cannot block inside an asyncio "
                            "Task; use 'await future' instead")

                    # A host loop such as ipykernel cannot run re-entrantly.
                    # Keep Qt responsive and poll the Future's synchronous
                    # done state until its Qt-backed acquisition completes.
                    wait_loop = QtCore.QEventLoop()
                    poll_timer = QtCore.QTimer()
                    poll_timer.setInterval(1)
                    poll_timer.timeout.connect(
                        lambda: wait_loop.quit() if self.done() else None)
                    poll_timer.start()
                    try:
                        wait_loop.exec_()
                    finally:
                        poll_timer.stop()
            finally:
                if (self._timer_timeout is not None
                        and self._timer_timeout.isActive()):
                    self._timer_timeout.stop()

    def await_result(self, timeout=None):
        """
        Return the result of the call that the future represents.
        Will not return until either timeout expires or future becomes "done".

        Coroutine callers should use ``await future``. Blocking an active
        asyncio Task would re-enter that Task on Python 3.14 and is rejected
        with an actionable error.

        Args:
            timeout: The number of seconds to wait for the result if the future
                isn't done. If None, then there is no limit on the wait time.

        Returns:
            The result of the call that the future represents.

        Raises:
            CancelledError: If the future was cancelled.
            TimeoutError: If the future didn't finish executing before the
                          given timeout.
            Exception: If the call raised then that exception will be raised.
        """

        self._wait_for_done(timeout)
        return self.result()

    def await_exception(self, timeout=None):  # pragma: no-cover
        """
        Return the exception raised by the call that the future represents.

        Args:
            timeout: The number of seconds to wait for the exception if the
                future isn't done. If None, then there is no limit on the wait
                time.

        Returns:
            The exception raised by the call that the future represents or None
            if the call completed without raising.

        Raises:
            CancelledError: If the future was cancelled.
            TimeoutError: If the future didn't finish executing before the
            given  timeout.
        """
        self._wait_for_done(timeout)
        return self.exception()

    def cancel(self):
        """
        Cancels the future.
        """
        if self._timer_timeout is not None:
            self._timer_timeout.stop()
        super(PyrplFuture, self).cancel()


def sleep(delay):
    """
    Sleeps for :code:`delay` seconds + runs the event loop in the background.

        * This function will never return until the specified delay in seconds is elapsed.
        * During execution, the Qt event loop remains responsive. In a plain
          synchronous process, native asyncio tasks also continue to progress.
        * Contrary to time.sleep() or async.sleep(), this function will try to achieve a precision much better than 1 millisecond (of course, occasionally, the real delay can be longer than requested), but on average, the precision is in the microsecond range.
        * Finally, care has been taken to use low level system-functions to reduce CPU-load when no events need to be processed.

    More details on the implementation can be found on the page: `<https://github.com/lneuhaus/pyrpl/wiki/Benchmark-asynchronous-sleep-functions>`_.

    In a coroutine or modern notebook cell, use ``await asyncio.sleep(...)``
    when sibling asyncio tasks must progress. A synchronous function cannot
    re-enter its already-running host Task using public asyncio APIs.
    """
    if LOOP.is_running():
        if _inside_owned_asyncio_task():
            raise RuntimeError(
                "sleep() cannot block inside an asyncio Task; use "
                "'await asyncio.sleep(...)' instead")
        return _sleep_with_qt(delay)

    if not _PYRPL_OWNS_LOOP:
        return _sleep_with_qt(delay)

    # In scripts and notebooks without an outer qasync runner, use a Qt timer
    # as the completion signal for the shared loop.  No asyncio Task may stay
    # on the stack while the loop runs, because Python 3.14 rejects re-entering
    # one Task while another Task is executing.
    end_time = default_timer() + delay
    waiter = LOOP.create_future()
    timer = MainThreadTimer(max(0, (delay - 1e-3) * 1000))
    timer.timeout.connect(lambda: waiter.set_result(None))
    timer.start()
    LOOP.run_until_complete(waiter)

    # Preserve the original sub-millisecond finish without keeping the CPU
    # busy for the longer portion of the delay.
    while default_timer() < end_time:
        pass


def _sleep_with_qt(delay):
    tic = default_timer()
    end_time = tic + delay

    # 1. CPU-free sleep for delay - 1ms
    if delay > 1e-3:
        new_delay = delay - 1e-3
        loop = QtCore.QEventLoop()
        timer = MainThreadTimer(new_delay * 1000)
        timer.timeout.connect(loop.quit)
        timer.start()
        try:
            loop.exec_()
        except KeyboardInterrupt as e:  # pragma: no-cover
            # try to recover from KeyboardInterrupt by finishing the current task
            timer.setInterval(1)
            timer.start()
            loop.exec_()
            raise e
    # 2. For high-precision, manually process events 1-by-1 during the last ms
    while default_timer() < end_time:
        APP.processEvents()
