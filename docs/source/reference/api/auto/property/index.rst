:py:mod:`property`
==================

.. py:module:: property

.. autoapi-nested-parse::

   Collection of all the classes and metaclasses used to define a
   property in the StructureData.    
   Requirements for the properties are:
   -
   -
   -



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   property.BaseProperty
   property.Pbc
   property.PropertyInfo
   property.PropertyMixinMetaclass
   property.HasPropertyMixin
   property.StructureMeta



Functions
~~~~~~~~~

.. autoapisummary::

   property.Property



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
      :type: aiida.orm.nodes.data.data.Data

      


.. py:class:: Pbc


   Bases: :py:obj:`BaseProperty`

   For now this property is not included in the StructureData. 
   I have doubt on if we really need to move it in the properties. 

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


   .. py:method:: _database_wise_setter(pname, pvalue)


   .. py:method:: get_valid_properties()


   .. py:method:: get_defined_properties()



.. py:class:: StructureMeta


   Bases: :py:obj:`type`\ (\ :py:obj:`HasPropertyMixin`\ ), :py:obj:`type`\ (\ :py:obj:`Data`\ )

   This metaclass is need in order to define the inherithance order.
   In particular, the properties require the order type(HasPropertyMixin)-->type(Data),
   so they can be initialised. 


