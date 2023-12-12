:py:mod:`example_01`
====================

.. py:module:: example_01

.. autoapi-nested-parse::

   Run a test calculation on localhost.

   Usage: ./example_01.py



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   example_01.test_run
   example_01.cli



Attributes
~~~~~~~~~~

.. autoapisummary::

   example_01.INPUT_DIR


.. py:data:: INPUT_DIR

   

.. py:function:: test_run(atomistic_code)

   Run a calculation on the localhost computer.

   Uses test helpers to create AiiDA Code on the fly.


.. py:function:: cli(code)

   Run example.

   Example usage: $ ./example_01.py --code diff@localhost

   Alternative (creates diff@localhost-test code): $ ./example_01.py

   Help: $ ./example_01.py --help


