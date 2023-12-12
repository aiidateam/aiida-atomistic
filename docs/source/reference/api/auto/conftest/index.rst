:py:mod:`conftest`
==================

.. py:module:: conftest

.. autoapi-nested-parse::

   pytest fixtures for simplified testing.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   conftest.clear_database_auto
   conftest.atomistic_code



Attributes
~~~~~~~~~~

.. autoapisummary::

   conftest.pytest_plugins


.. py:data:: pytest_plugins
   :value: ['aiida.manage.tests.pytest_fixtures']

   

.. py:function:: clear_database_auto(clear_database)

   Automatically clear database in between tests.


.. py:function:: atomistic_code(aiida_local_code_factory)

   Get a atomistic code.


