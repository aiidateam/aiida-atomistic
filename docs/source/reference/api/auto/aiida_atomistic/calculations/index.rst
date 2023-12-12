:py:mod:`aiida_atomistic.calculations`
======================================

.. py:module:: aiida_atomistic.calculations

.. autoapi-nested-parse::

   Calculations provided by aiida_atomistic.

   Register calculations via the "aiida.calculations" entry point in setup.json.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.calculations.DiffCalculation




Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.calculations.DiffParameters


.. py:data:: DiffParameters

   

.. py:class:: DiffCalculation(*args, **kwargs)


   Bases: :py:obj:`aiida.engine.CalcJob`

   AiiDA calculation plugin wrapping the diff executable.

   Simple AiiDA plugin wrapper for 'diffing' two files.

   .. py:method:: define(spec)
      :classmethod:

      Define inputs and outputs of the calculation.


   .. py:method:: prepare_for_submission(folder)

      Create input files.

      :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files
          needed by the calculation.
      :return: `aiida.common.datastructures.CalcInfo` instance



