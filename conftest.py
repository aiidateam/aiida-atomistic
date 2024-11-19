"""pytest fixtures for simplified testing."""
import pytest

pytest_plugins = ["aiida.manage.tests.pytest_fixtures"]


@pytest.fixture(scope="function", autouse=True)
def clear_database_auto(clear_database):  # pylint: disable=unused-argument
    """Automatically clear database in between tests."""


@pytest.fixture(scope="function")
def atomistic_code(aiida_local_code_factory):
    """Get a atomistic code."""
    return aiida_local_code_factory(executable="diff", entry_point="atomistic")


@pytest.fixture
def supported_properties():
    """
    Should be updated every time I add properties.
    """
    return [
        "cell",
        "pbc",
        "positions",
        "symbols",
        "masses",
        "charges",
        "magmoms",
        "kinds",
        "weights",
    ]


@pytest.fixture
def example_structure_dict():
    """
    Return the dictionary of properties as to be used in the standards tests.
    """
    structure_dict = {
        "pbc": [True, True, True],
        "cell": [[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]],
        "sites": [
            {
                "symbols": "Cu",
                "kinds": "Cu2",
                "positions": [0.0, 0.0, 0.0],
                "masses": 63.546,
                "charges": 1.0,
                "magmoms": [0.0,0.0,0.0],
                "weights": (1,)
            }
        ],
    }

    return structure_dict

@pytest.fixture
def example_dumped_structure_dict():

    # the dumped structure is the same as the example_structure_dict, but with additional computed fields and default ones.

    dumped_dict = {
        'pbc': [True, True, True],
        'cell': [[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]],
        'custom': None,
        'symbols': ['Cu'],
        'positions': [[0.0, 0.0, 0.0]],
        'kinds': ['Cu2'],
        'weights': [(1.0,)],
        'masses': [63.546],
        'charges': [1.0],
        'magmoms': [[0.0, 0.0, 0.0]],
        'hubbard': {
            'parameters': [],
            'projectors': 'ortho-atomic',
            'formulation': 'dudarev'
        },
        'cell_volume': 11.664000000000001,
        'dimensionality': {
            'dim': 3,
            'label': 'volume',
            'value': 11.664000000000001
        },
        'sites': [{
            'symbols': 'Cu',
            'kinds': 'Cu2',
            'positions': [0.0, 0.0, 0.0],
            'masses': 63.546,
            'charges': 1.0,
            'magmoms': [0.0, 0.0, 0.0],
            'weights': (1.0,)
        }],
        'formula': 'Cu'
    }
    return dumped_dict

@pytest.fixture
def example_nomass_structure_dict():
    """
    Return the dictionary of properties as to be used in the standards tests.
    """
    structure_dict = {
        "pbc": [True, True, True],
        "cell": [[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]],
        "sites": [
            {
                "symbols": "Cu",
                "kinds": "Cu2",
                "positions": [0.0, 0.0, 0.0],
                #"mass": 63.546,
                "charges": 1.0,
                "magmoms": [0,0,0],
            }
        ],
    }

    return structure_dict

@pytest.fixture
def example_wrong_structure_dict():
    """
    Return the dictionary of properties as to be used in the standards tests.
    """
    structure_dict = {
        "pbc": [True, True, True],
        "cell": [[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]],
        "sites": [
            {
                "symbol": "Cu",
                "kinds": "Cu2",
                "position": [0.0, 0.0, 0.0],
                "mass": 63.546,
                "charge": 1.0,
                "magmom": [0,0,0],
            },
            {
                "symbol": "Cu",
                "kinds": "Cu2",
                "position": [0.0, 0.0, 0.0],
                "mass": 63.546,
                "charge": 1.0,
                "magmom": [0,0,0],
            }
        ],
    }

    return structure_dict

@pytest.fixture
def example_structure_dict_for_kinds():
    """
    Return the dictionary of properties as to be used in the standards tests.
    """
    structure_dict = {'pbc': (True, True, True),
        'cell': [[2.8403, 0.0, 1.7391821518091137e-16],
        [-1.7391821518091137e-16, 2.8403, 1.7391821518091137e-16],
        [0.0, 0.0, 2.8403]],
        'sites': [{'symbols': 'Fe',
        'masses': 55.845,
        'positions': [0.0, 0.0, 0.0],
        'charges': 0.0,
        'magmoms': [2.5, 0.1, 0.1],
        'kinds': 'Fe'},
        {'symbols': 'Fe',
        'masses': 55.845,
        'positions': [1.42015, 1.42015, 1.4201500000000002],
        'charges': 0.0,
        'magmoms': [2.4, 0.1, 0.1],
        'kinds': 'Fe'}]}

    return structure_dict

@pytest.fixture
def complex_example_structure_dict_for_kinds():
    """
    Return the dictionary of properties as to be used in the standards tests.
    the structure is here: aiida-atomistic/examples/structure/data/0.199_Mn3Sn.mcif
    """
    from pymatgen.core import Structure
    from aiida_atomistic import StructureData
    smag1 = Structure.from_file('./examples/structure/data/'+"0.199_Mn3Sn.mcif", primitive=True)

    return StructureData.from_pymatgen(smag1).to_dict()

@pytest.fixture
def example_structure_dict_alloy():
    """
    Return the dictionary of properties as to be used in the standards tests.
    """
    structure_dict ={
        'pbc': [True, True, True],
        'cell': [[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]],
        'sites': [{'symbols': 'CuAl',
        'positions': [0.0, 0.0, 0.0],
        'weights': (0.5,0.5)
        }],}

    return structure_dict
