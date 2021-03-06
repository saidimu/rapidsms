#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import time
import Queue
from ..utils.modules import try_import, get_class
from ..messages.incoming import IncomingMessage
from ..log.mixin import LoggerMixin


class BackendBase(object, LoggerMixin):
    """
    """

    @classmethod
    def find(cls, module_name):
        module = try_import(module_name)
        if module is None: return None
        return get_class(module, cls)


    def __init__ (self, router, name, **kwargs):
        self._queue = Queue.Queue()
        self._running = False
        self.router = router
        self.name = name

        self._config = kwargs
        if hasattr(self, "configure"):
            self.configure(**kwargs)

    def _logger_name(self): # pragma: no cover
        return "backend/%s" % self.name

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return "<backend: %s>" %\
            self.name

    @property
    def running (self):
        return self._running


    def start(self, legacy_behavior=False):
        """
        Start the backend.  Normally just sets self._running to ``True``.  If
        legacy behavior is desired (i.e., if you want ``start()`` wait until
        the router sets the backend's ``_running`` attribute to ``False``, ')
        pass ``legacy_behavior=True``
        """
        self._running = True
        if legacy_behavior:
            while self._running:
                time.sleep(1)


    def run (self):
        pass


    def stop(self):
        self._running = False


    @property
    def model(self):
        """
        Return the Django stub model representing this backend in the
        database. This is useful when you want to to link a model to a
        backend, since it enforced a foreign key constraint.
        """

        from rapidsms.models import Backend as B
        backend, created = B.objects.get_or_create(
            name=self.name)

        return backend


    def message(self, identity, text, received_at=None):

        # import the models here, rather than at the top, to give the
        # orm a chance to initialize. (avoids SETTINGS_MODULE errors.)
        from ..models import Connection

        # ensure that a persistent connection instance exists for this
        # backend+identity pair. silently create one, if not.
        conn, created = Connection.objects.get_or_create(
            backend=self.model,
            identity=identity)

        return IncomingMessage(
            conn, text, received_at)


    def route(self, msg):
        return self.router.incoming_message(msg)


    # TODO: what on earth is this for?
    def next_message (self): # pragma: no cover
        """
        Returns the next incoming message waiting to be processed, or
        None if there are none pending.
        """

        try:
            return self._queue.get(False)

        except Queue.Empty:
            return None
