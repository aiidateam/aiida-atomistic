:py:mod:`aiida_atomistic.data`
==============================

.. py:module:: aiida_atomistic.data

.. autoapi-nested-parse::

   Data types provided by plugin

   Register data types via the "aiida.data" entry point in setup.json.



Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.DiffParameters




Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.cmdline_options


.. py:data:: cmdline_options

   

.. py:class:: DiffParameters(dict=None, **kwargs)


   Bases: :py:obj:`aiida.orm.Dict`

   Command line options for diff.

   This class represents a python dictionary used to
   pass command line options to the executable.

   .. py:attribute:: schema

      

   .. py:method:: validate(parameters_dict)

      Validate command line options.

      Uses the voluptuous package for validation. Find out about allowed keys using::

          print(DiffParameters).schema.schema

      :param parameters_dict: dictionary with commandline parameters
      :param type parameters_dict: dict
      :returns: validated dictionary


   .. py:method:: cmdline_params(file1_name, file2_name)

      Synthesize command line parameters.

      e.g. [ '--ignore-case', 'filename1', 'filename2']

      :param file_name1: Name of first file
      :param type file_name1: str
      :param file_name2: Name of second file
      :param type file_name2: str



   .. py:method:: __str__()

      String representation of node.

      Append values of dictionary to usual representation. E.g.::

          uuid: b416cbee-24e8-47a8-8c11-6d668770158b (pk: 590)
          {'ignore-case': True}




