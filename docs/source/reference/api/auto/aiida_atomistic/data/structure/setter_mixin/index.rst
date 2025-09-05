:py:mod:`aiida_atomistic.data.structure.setter_mixin`
=====================================================

.. py:module:: aiida_atomistic.data.structure.setter_mixin


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.setter_mixin.SetterMixin




Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.setter_mixin.has_ase
   aiida_atomistic.data.structure.setter_mixin.has_pymatgen
   aiida_atomistic.data.structure.setter_mixin._MASS_THRESHOLD
   aiida_atomistic.data.structure.setter_mixin._SUM_THRESHOLD
   aiida_atomistic.data.structure.setter_mixin._DEFAULT_CELL
   aiida_atomistic.data.structure.setter_mixin._DEFAULT_PROPERTIES
   aiida_atomistic.data.structure.setter_mixin._valid_symbols
   aiida_atomistic.data.structure.setter_mixin._atomic_masses
   aiida_atomistic.data.structure.setter_mixin._atomic_numbers
   aiida_atomistic.data.structure.setter_mixin._DEFAULT_VALUES
   aiida_atomistic.data.structure.setter_mixin._DEFAULT_THRESHOLDS


.. py:data:: has_ase
   :value: True



.. py:data:: has_pymatgen
   :value: True



.. py:data:: _MASS_THRESHOLD
   :value: 0.001



.. py:data:: _SUM_THRESHOLD
   :value: 1e-06



.. py:data:: _DEFAULT_CELL



.. py:data:: _DEFAULT_PROPERTIES



.. py:data:: _valid_symbols



.. py:data:: _atomic_masses



.. py:data:: _atomic_numbers



.. py:data:: _DEFAULT_VALUES



.. py:data:: _DEFAULT_THRESHOLDS



.. py:class:: SetterMixin


   Bases: :py:obj:`aiida_atomistic.data.structure.hubbard_mixin.HubbardSetterMixin`

   .. py:method:: _validate_properties()

      Validate the structure.

      This method performs a series of checks to ensure that the structure's properties are consistent and valid.
      It raises a ValueError if any inconsistency is found.

      Returns:
          None


   .. py:method:: set_pbc(value)

      Set the periodic boundary conditions.


   .. py:method:: set_cell(value)

      Set the cell.


   .. py:method:: set_cell_lengths(value)
      :abstractmethod:


   .. py:method:: set_cell_angles(value)
      :abstractmethod:


   .. py:method:: update_site(site_indices: Union[list[int], int], **kwargs)

      Update the site at the given index.


   .. py:method:: update_kind(kind_name, **kwargs)

      Update all sites with the given kind name.


   .. py:method:: append_atom(index=-1, **atom_info)


   .. py:method:: pop_atom(index=-1)


   .. py:method:: clear_sites()

      Clear the sites, i.e. every property except pbc, cell and custom.


   .. py:method:: remove_property(property_name)

      Clear the given property.


   .. py:method:: set_charges(charges: numpy.ndarray[float])


   .. py:method:: remove_charges()


   .. py:method:: set_masses(masses: numpy.ndarray[float])


   .. py:method:: remove_masses()


   .. py:method:: set_magmoms(magmoms: numpy.ndarray[numpy.ndarray[float]])


   .. py:method:: remove_magmoms()


   .. py:method:: set_magnetizations(magnetizations: numpy.ndarray[float])


   .. py:method:: remove_magnetizations()


   .. py:method:: set_weights(weights: numpy.ndarray[numpy.ndarray[float]])


   .. py:method:: remove_weights()


   .. py:method:: set_tot_charge(value: float)

      Set the total charge of the cell.


   .. py:method:: remove_tot_charge()


   .. py:method:: set_tot_magnetization(value: float)

      Set the total magnetic moment of the cell.


   .. py:method:: remove_hubbard()


   .. py:method:: set_kind_names(value: list)
