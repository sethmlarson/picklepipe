PicklePipe 🥒
=============

.. toctree::
    :hidden:
    :maxdepth: 2

    api
    changelog
    contributing
    about

Python pickling and marshal protocol over any network interface.
Also provides a basic interface to implement your own serializing pipes.

Getting Started with PicklePipe
-------------------------------

PicklePipe is available on PyPI can be installed with `pip <https://pip.pypa.io>`_.::

    $ python -m pip install picklepipe

To install the latest development version from `Github <https://github.com/SethMichaelLarson/picklepipe>`_::

    $ python -m pip install git+git://github.com/SethMichaelLarson/picklepipe.git


If your current Python installation doesn't have pip available, try `get-pip.py <bootstrap.pypa.io>`_
Please read the security considerations before using PicklePipe.

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

Security Considerations
-----------------------

Un-pickling or un-marshaling data from an untrusted source is a security hazard and can lead to arbitrary code execution.
When using PicklePipe to receive objects from an external source one should be very careful to verify that
the source of the data is trustworthy. This includes using SSL/TLS (both client and server side verification)
to verify the connection is who we intend to receive data from if the pipes are not local.

`See the warnings within the pickle module for more information <https://docs.python.org/2/library/pickle.html>`_.

Support / Report Issues
-----------------------

All support requests and issue reports should be
`filed on Github as an issue <https://github.com/SethMichaelLarson/picklepipe/issues>`_.
Make sure to follow the template so your request may be as handled as quickly as possible.
Please respect contributors by not using personal contacts for support requests.

Contributing
------------

We happily welcome contributions, please see :doc:`contributing` for details.

License
-------

PicklePipe is made available under the MIT License. For more details, see :doc:`about`.
