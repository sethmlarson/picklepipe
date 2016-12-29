PicklePipe
==========

.. image:: https://img.shields.io/travis/SethMichaelLarson/picklepipe/master.svg
    :target: https://travis-ci.org/SethMichaelLarson/picklepipe
    :alt: Linux and MacOS Build Status
.. image:: https://img.shields.io/appveyor/ci/SethMichaelLarson/picklepipe/master.svg
    :target: https://ci.appveyor.com/project/SethMichaelLarson/picklepipe
    :alt: Windows Build Status
.. image:: https://img.shields.io/codecov/c/github/SethMichaelLarson/picklepipe/master.svg
    :target: https://codecov.io/gh/SethMichaelLarson/picklepipe
    :alt: Test Suite Coverage
.. image:: https://img.shields.io/codeclimate/github/SethMichaelLarson/picklepipe.svg
    :target: https://codeclimate.com/github/SethMichaelLarson/picklepipe
    :alt: Code Health
.. image:: https://readthedocs.org/projects/picklepipe/badge/?version=latest
    :target: http://picklepipe.readthedocs.io
    :alt: Documentation Build Status
.. image:: https://pyup.io/repos/github/sethmichaellarson/picklepipe/shield.svg
     :target: https://pyup.io/repos/github/sethmichaellarson/picklepipe/
     :alt: Dependency Versions
.. image:: https://img.shields.io/pypi/v/picklepipe.svg
    :target: https://pypi.python.org/pypi/picklepipe
    :alt: PyPI Version
.. image:: https://img.shields.io/badge/say-thanks-ff69b4.svg
    :target: https://saythanks.io/to/SethMichaelLarson
    :alt: Say Thanks to the Maintainers

Python pickling protocol over any network interface. Also provides a basic interface to implement your own serializing pipes.

This project was started and released in under 24 hours while I was on holiday break.

Getting Started with PicklePipe
-------------------------------

PicklePipe is available on PyPI can be installed with `pip <https://pip.pypa.io>`_.::

    $ python -m pip install picklepipe

To install the latest development version from `Github <https://github.com/SethMichaelLarson/picklepipe>`_::

    $ python -m pip install git+git://github.com/SethMichaelLarson/picklepipe.git


If your current Python installation doesn't have pip available, try `get-pip.py <bootstrap.pypa.io>`_

After installing PicklePipe you can use it like any other Python module.
Here's a very simple demonstration of scheduling a single job on a farm.

.. code-block:: python

    import picklepipe

    # Create a pair of connected pipes.
    pipe1, pipe2 = picklepipe.make_pipe_pair(picklepipe.PicklePipe)

    # Send an object in one end.
    pipe1.send_object('Hello, world!')

    # And retrieve it from the other.
    obj = pipe2.recv_object(timeout=1.0)

    assert obj == 'Hello, world!'

    # Also can be used to send objects to remote locations!
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('host', 12345))
    pipe = picklepipe.PicklePipe(sock)
    pipe.send_object('Hello, world!')
    pipe.close()

API Reference
-------------

The `API Reference on readthedocs.io <http://picklepipe.readthedocs.io>`_ provides API-level documentation.

Support / Report Issues
-----------------------

All support requests and issue reports should be
`filed on Github as an issue <https://github.com/SethMichaelLarson/picklepipe/issues>`_.
Make sure to follow the template so your request may be as handled as quickly as possible.
Please respect contributors by not using personal contacts for support requests.

Contributing
------------

We happily welcome contributions, please see `our guide for Contributors <http://picklepipe.readthedocs.io/en/latest/contributing.html>`_ for the best places to start and help.

License
-------

PicklePipe is made available under the MIT License. For more details, see `LICENSE.txt <https://github.com/SethMichaelLarson/picklepipe/blob/master/LICENSE.txt>`_.
