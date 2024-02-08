:py:mod:`aiida_atomistic.helpers`
=================================

.. py:module:: aiida_atomistic.helpers

.. autoapi-nested-parse::

   Helper functions for automatically setting up computer & code.
   Helper functions for setting up

    1. An AiiDA localhost computer
    2. A "diff" code on localhost

   Note: Point 2 is made possible by the fact that the ``diff`` executable is
   available in the PATH on almost any UNIX system.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.helpers.get_path_to_executable
   aiida_atomistic.helpers.get_computer
   aiida_atomistic.helpers.get_code



Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.helpers.LOCALHOST_NAME
   aiida_atomistic.helpers.executables


.. py:data:: LOCALHOST_NAME
   :value: 'localhost-test'

   

.. py:data:: executables

   

.. py:function:: get_path_to_executable(executable)

   Get path to local executable.
   :param executable: Name of executable in the $PATH variable
   :type executable: str
   :return: path to executable
   :rtype: str


.. py:function:: get_computer(name=LOCALHOST_NAME, workdir=None)

   Get AiiDA computer.
   Loads computer 'name' from the database, if exists.
   Sets up local computer 'name', if it isn't found in the DB.

   :param name: Name of computer to load or set up.
   :param workdir: path to work directory
       Used only when creating a new computer.
   :return: The computer node
   :rtype: :py:class:`aiida.orm.computers.Computer`


.. py:function:: get_code(entry_point, computer)

   Get local code.
   Sets up code for given entry point on given computer.

   :param entry_point: Entry point of calculation plugin
   :param computer: (local) AiiDA computer
   :return: The code node
   :rtype: :py:class:`aiida.orm.nodes.data.code.installed.InstalledCode`


