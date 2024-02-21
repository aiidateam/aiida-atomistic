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
    return ['cell', 'pbc', 'positions',  'symbols', 'mass', 'charge', 'custom']


@pytest.fixture
def example_properties():
    """
    Return the dictionary of properties as to be used in the standards tests.
    """
    unit_cell = [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]
    atomic_positions = [[0.0, 0.0, 0.0],[1.5, 1.5, 1.5]]
    symbols = ["Li"]*2
    mass = [6.941,6.941]
    charge = [1,0]

    properties = {
        "cell":{"value":unit_cell},
        "pbc":{"value":[True,True,True]},
        "positions":{"value":atomic_positions,},
        "symbols":{"value":symbols},
        "mass":{"value":mass,},
        "charge":{"value":charge}
        }
    
    return properties