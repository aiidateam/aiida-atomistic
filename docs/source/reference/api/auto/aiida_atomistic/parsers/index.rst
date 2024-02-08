:py:mod:`aiida_atomistic.parsers`
=================================

.. py:module:: aiida_atomistic.parsers

.. autoapi-nested-parse::

   Parsers provided by aiida_atomistic.

   Register parsers via the "aiida.parsers" entry point in setup.json.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.parsers.DiffParser




Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.parsers.DiffCalculation


.. py:data:: DiffCalculation

   

.. py:class:: DiffParser(node)


   Bases: :py:obj:`aiida.parsers.parser.Parser`

   Parser class for parsing output of calculation.

   .. py:method:: parse(**kwargs)

      Parse outputs, store results in database.

      :returns: an exit code, if parsing fails (or nothing if parsing succeeds)



