:py:mod:`prototype`
===================

.. py:module:: prototype


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   prototype.Data
   prototype.BaseProperty
   prototype.Magnetization
   prototype.Pbc
   prototype.PropertyInfo
   prototype.PropertyMixinMetaclass
   prototype.HasPropertyMixin
   prototype.StructureData



Functions
~~~~~~~~~

.. autoapisummary::

   prototype.Property



Attributes
~~~~~~~~~~

.. autoapisummary::

   prototype.structure
   prototype.pbc


.. py:class:: Data



.. py:class:: BaseProperty


   Bases: :py:obj:`pydantic.BaseModel`

   .. py:class:: Config


      .. py:attribute:: frozen
         :value: True

         

      .. py:attribute:: extra
         :value: 'forbid'

         

      .. py:attribute:: arbitrary_types_allowed
         :value: True

         


   .. py:attribute:: parent
      :type: Data

      


.. py:class:: Magnetization


   Bases: :py:obj:`BaseProperty`

   .. py:attribute:: value
      :type: List[float]

      


.. py:class:: Pbc


   Bases: :py:obj:`BaseProperty`

   .. py:attribute:: value
      :type: List[bool]

      

   .. py:method:: set_from_string(dimensionality: str = '3D')



.. py:class:: PropertyInfo



.. py:function:: Property()


.. py:class:: PropertyMixinMetaclass


   Bases: :py:obj:`abc.ABCMeta`

   Metaclass for defining Abstract Base Classes (ABCs).

   Use this metaclass to create an ABC.  An ABC can be subclassed
   directly, and then acts as a mix-in class.  You can also register
   unrelated concrete classes (even built-in classes) and unrelated
   ABCs as 'virtual subclasses' -- these and their descendants will
   be considered subclasses of the registering ABC by the built-in
   issubclass() function, but the registering ABC won't show up in
   their MRO (Method Resolution Order) nor will method
   implementations defined by the registering ABC be callable (not
   even via super()).


.. py:class:: HasPropertyMixin


   .. py:attribute:: _valid_properties
      :value: []

      

   .. py:method:: _template_property(type_hint, attr)


   .. py:method:: _set_property(pname=None, pvalue=None, from_set_property=False)


   .. py:method:: get_valid_properties()


   .. py:method:: get_defined_properties()



.. py:class:: StructureData


   Bases: :py:obj:`Data`, :py:obj:`HasPropertyMixin`

   .. py:attribute:: magnetization
      :type: Magnetization

      

   .. py:attribute:: pbc
      :type: Pbc

      

   .. py:method:: get_property_attribute(key)


   .. py:method:: set_property(pname=None, pvalue=None)



.. py:data:: structure

   

.. py:data:: pbc

   

