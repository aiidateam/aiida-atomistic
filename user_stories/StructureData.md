# User stories for the StructureData

The main new feature of StructureData is the __properties__ (magnetization, hubbard...) definition. So, the focus of these stories is this topic.

The user can be: 
 - standard user (or user) that wants to use the StructureData without knowing about the underneath implementation;
 - advanced user that will also have a look at the implementation and will try to define something like custom properties/functionalities on top of StructureData;
 - a plugin developer, similar to an advanced user but more focused on the integration of StructureData in its own plugin, and handling possible exceptions or unsupported features; 
 - an AiiDA developer, devoted to the back-end management: storage in db/repository and details of the implementation

In principle, a user story should be as much informal as possible, i.e. described with non-technical and natural language as much as possible. The more expertise the user will have, the more technical the stories could be.

### Templates

- As a __type of user__, I want __some goal__ so that __some reason__
- As a __role__ I can __capability__, so that __receive benefit__
- In order to __receive benefit__ as a __role__, I can __goal/desire__
- As __who__ __when__ __where__, I want __what__ because __why__

There is also other templates, named "Evil User Story", more focused on improve security (maybe here is not so important). For example:

- As a disgruntled employee, I want to wipe out the user database to hurt the company

## As a user...

1. I want to __create a minimal instance of the StructureData without setting any property__, so that I am able to run a very simple simulation. This means that I want to know the minimal set of properties needed and their default values, if any.
2. I want __to know the full set of properties__ which are supported in the StructureData class, so that I can understand what kind of properties should I consider to belong to the StructureData instance in a simulation. It would be nice to have a unique attribute to gather all the properties. 
3. I want __to set/change in a simple way the value of a property before the StructureData is stored__, in such a way I can work interactively with it (for example in jupyter notebooks).
4. I want to know __how to set a property__, in terms of available constructors/methods and how to provide data (units, types...), so that I can easily automate StructureData instantiations.
5. I want to know __what properties are set in a given StructureData instance__, so that if I do not remember I can easily know it.
6. I want __to access easily a property__ to check its value, so that I can write simple scripts to analyze a set of StructureData instances.
7. I want __tab completion for properties and related methods__, so that I can interactively work with it in jupyter notebooks.
8. I want to have __data validations__ at the property definition stage, so I can understand if I am doing something wrong and not submitting a calculation which is doomed to except.
9.  I want to have a clear documentation with all the above cases, provided with examples.


### So...

- [ ] Minimal default settings
- [ ] Methods to list the supported properties
- [ ] Method to list the defined properties
- [ ] Methods to set a given property
- [ ] Tab completion for properties and related methods
- [ ] Unique attribute that gathers all the properties (and access them easily via tab completion)
- [ ] Documentation on 
  - [ ] StructureData instance creation
  - [ ] how to set a property, example on simple property like PBC.
  - [ ] all the supported properties, format, default values, methods. How to list and access them.

## As an advanced user...

1. I want to have the possiblity to define __custom properties__, so that I can use the StructureData in advanced ad-hoc workflows and propagate novel properties needed for my own case.
2. I want to have the possiblity __to easily query the properties__, so that I can quicly analyze large datasets (for example in high-throughput). I want __to know what are the queryable properties__ (i.e. what properties are in the db and what are in the repository).
3. I want to be able __to skip some of the defined properties in my job__, so that I can use the same StructureData node for different purposes, e.g. magnetic and non-magnetic simulations. I would like to be able to define it in the plugin inputs.
4. I want a __unified format for the definition in the StructureData node___, so that it is straightforward to use the same StructureData in multiple workchains belonging to different plugins.
5. I want, however, __multiple ways to set a property, i.e. different methods to store the property starting from different input data__, so I can easily interface with different outputs. For example, magnetization can be provided as list of floats, vectors...
6. I do __not want to set directly a property__ (`structure.property.pbc = [1, 1, 1]`), so that I have always type/data validation enbaled.

## As a plugin developer...

1. I want to have a clear documentation on __how properties are defined in the StructureData (units, data types...)__, in such a way to be used in my plugin to generate input files for the submission of my job.
2. I want to be able to define new StructureData as output of my calculation starting from the initial input one, and set the changed properties in an easy way. This means that I would like to have an abstract method `from_structure` which provides a non-stored StructureData instance starting from another one.

## As an AiiDA developer...

1. I want to know exactly where the property will be stored (db or repository), so that...
2. I want to be able to...
