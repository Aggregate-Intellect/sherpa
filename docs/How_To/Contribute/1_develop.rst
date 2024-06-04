
:tocdepth: 3

Development Basics
==================

Linting and formating
~~~~~~~~~~~~~~~~~~~~~

This project uses ``flake8`` for linting, ``black`` and ``isort`` for
formatting, and ``pytest`` for testing.

To format the project, run:

.. code:: bash

   make format

if you don’t have ``make`` installed, you can also run the following
commands:

.. code:: bash

   black .
   isort .

To lint the project, run:

.. code:: bash

   make lint

if you don’t have ``make`` installed, you can also run the following
commands:

.. code:: bash

   flake8 .

Testing
~~~~~~~

To run the tests, run:

.. code:: bash

   make test

or

.. code:: bash

   pytest .

Debugging
~~~~~~~~~

The Slackbot is built with Flask, which provides a built-in web server and debugger suitable for development use.

When Flask debug mode is enabled, ...

- the server automatically reloads when code is changed
- http://localhost:3000/ serves a web-based debugger which displays an interactive stack trace when an exception is raised
- http://localhost:3000/test_debug raises an exception so you can try out the debugger
- http://localhost:3000/console displays a web-based console where you can execute Python expressions in the context of the application
- stack traces are also displayed in your terminal console

When Flask debug mode is disabled, ...

- you must manually restart the server to pick up code changes
- the web-based debugger and console are not available
- stack traces are only displayed in your terminal console

To enable debug mode, set ``FLASK_DEBUG=True`` in your ``.env`` file.
To disable debug mode, comment out ``FLASK_DEBUG`` or set it to any value other than ``True``.

**Warning:**
Never use the development server or enable the debugger when deploying to production.
These tools are intended for use only during local development, and are not designed to
be particularly efficient, stable, or secure.
For more info on the debugger see Werkzeug: `Debugging Applications <https://werkzeug.palletsprojects.com/en/2.3.x/debug/>`__
and `Flask: Debugging Application Errors <https://flask.palletsprojects.com/en/2.3.x/debugging/>`__.

