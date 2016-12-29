Changelog
=========

Release 0.0.1 (Development)
---------------------------
* Create initial implementation of :class:`picklepipe.PicklePipe`.
* Create :meth:`picklepipe.make_pipe_pair` to create a connected pair of :class:`picklepipe.PicklePipe` instances.
* Added support for creating own serialization pipes with :class:`picklepipe.BaseSerializationPipe`.
* Added support for the ``marshal`` object serializer with :class:`picklepipe.MarshalPipe`
* :class:`picklepipe.PicklePipe` now uses ``cPickle`` module if available.
* Make all pipe types selectable using selectors.
* Add the ``max_size`` attribute for limiting memory usage of pipes.
