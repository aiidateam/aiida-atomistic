:py:mod:`magnetic_qe_utils`
===========================

.. py:module:: magnetic_qe_utils

.. autoapi-nested-parse::

   Utility class for handling the :class:`aiida_atomistic.data.structure.structure.StructureData` if
   magnetization property is set and used in the aiida-quantumespresso plugin.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   magnetic_qe_utils.MagneticUtils




Attributes
~~~~~~~~~~

.. autoapisummary::

   magnetic_qe_utils.StructureData


.. py:data:: StructureData

   

.. py:class:: MagneticUtils(structure: StructureData)


   Utility class for handling `Magnetization` properties for QuantumESPRESSO.
   At the moment we support only kind-based collinear magnetization.

   .. py:method:: get_magnetic_card(collinear=True)



