:py:mod:`tests.test_cli`
========================

.. py:module:: tests.test_cli

.. autoapi-nested-parse::

   Tests for command line interface.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   tests.test_cli.TestDataCli




.. py:class:: TestDataCli


   Test verdi data cli plugin.

   .. py:method:: setup_method()

      Prepare nodes for cli tests.


   .. py:method:: test_data_diff_list()

      Test 'verdi data atomistic list'

      Tests that it can be reached and that it lists the node we have set up.


   .. py:method:: test_data_diff_export()

      Test 'verdi data atomistic export'

      Tests that it can be reached and that it shows the contents of the node
      we have set up.



