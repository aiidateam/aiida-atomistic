"""Pytest fixtures for aiida-atomistic tests."""

import numpy as np
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
    """Basic structure dictionary with one site."""
    return {
        "pbc": [True, True, True],
        "cell": [[2.7, 0.0, 0.0], [0.0, 2.7, 0.0], [0.0, 0.0, 1.6]],
        "sites": [
            {
                "symbol": "Cu",
                "position": [0.0, 0.0, 0.0],
                "mass": 63.546,
                "charge": 1.0,
                "kind_name": "Cu1",
            }
        ],
    }


@pytest.fixture
def example_dumped_structure_dict():
    """Expected dictionary after to_dict() method."""
    return {
        "pbc": [True, True, True],
        "cell": np.array([[2.7, 0.0, 0.0], [0.0, 2.7, 0.0], [0.0, 0.0, 1.6]]),
        "sites": [
            {
                "symbol": "Cu",
                "position": np.array([0.0, 0.0, 0.0]),
                "mass": 63.546,
                "charge": 1.0,
                "kind_name": "Cu1",
            }
        ],
    }


@pytest.fixture
def example_wrong_structure_dict():
    """Structure dictionary with validation errors (sites too close)."""
    return {
        "pbc": [True, True, True],
        "cell": [[2.7, 0.0, 0.0], [0.0, 2.7, 0.0], [0.0, 0.0, 1.6]],
        "sites": [
            {
                "symbol": "Cu",
                "position": [0.0, 0.0, 0.0],
                "mass": 63.546,
                "charge": 1.0,
            },
            {
                "symbol": "Cu",
                "position": [0.0, 0.0, 0.0001],  # Too close to first site
                "mass": 63.546,
                "charge": 1.0,
            },
        ],
    }


@pytest.fixture
def example_nomass_structure_dict():
    """Structure dictionary without explicit mass (should be auto-filled)."""
    return {
        "pbc": [True, True, True],
        "cell": [[2.7, 0.0, 0.0], [0.0, 2.7, 0.0], [0.0, 0.0, 1.6]],
        "sites": [
            {
                "symbol": "Cu",
                "position": [0.0, 0.0, 0.0],
                "kind_name": "Cu1",
            }
        ],
    }


@pytest.fixture
def example_structure_dict_for_kinds():
    """Structure for testing kinds detection with magnetic moments."""
    return {
        "pbc": [True, True, True],
        "cell": [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
        "sites": [
            {
                "symbol": "Fe",
                "position": [0.0, 0.0, 0.0],
                "magmom": [2.5, 0.1, 0.1],
                "kind_name": "Fe1",
            },
            {
                "symbol": "Fe",
                "position": [1.5, 1.5, 1.5],
                "magmom": [2.4, 0.1, 0.1],
                "kind_name": "Fe2",
            },
        ],
    }


@pytest.fixture
def complex_example_structure_dict_for_kinds():
    """Complex structure for testing kinds with multiple elements and magnetic patterns."""
    return {
        "pbc": [True, True, True],
        "cell": [[5.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 5.0]],
        "sites": [
            {
                "symbol": "Mn",
                "position": [0.0, 0.0, 0.0],
                "magmom": [1.5, 2.5981, 0.0],
                "kind_name": "Mn1",
            },
            {
                "symbol": "Mn",
                "position": [1.0, 0.0, 0.0],
                "magmom": [-3.0, 0.0, 0.0],
                "kind_name": "Mn2",
            },
            {
                "symbol": "Mn",
                "position": [2.0, 0.0, 0.0],
                "magmom": [1.5, 2.5981, 0.0],
                "kind_name": "Mn1",
            },
            {
                "symbol": "Mn",
                "position": [3.0, 0.0, 0.0],
                "magmom": [-3.0, 0.0, 0.0],
                "kind_name": "Mn2",
            },
            {
                "symbol": "Mn",
                "position": [0.0, 2.0, 0.0],
                "magmom": [1.5, -2.5981, 0.0],
                "kind_name": "Mn3",
            },
            {
                "symbol": "Mn",
                "position": [1.0, 2.0, 0.0],
                "magmom": [1.5, -2.5981, 0.0],
                "kind_name": "Mn3",
            },
            {
                "symbol": "Sn",
                "position": [0.0, 0.0, 2.0],
                "magmom": [0.0, 0.0, 0.0],
                "kind_name": "Sn",
            },
            {
                "symbol": "Sn",
                "position": [1.0, 0.0, 2.0],
                "magmom": [0.0, 0.0, 0.0],
                "kind_name": "Sn",
            },
        ],
    }


@pytest.fixture
def example_structure_dict_alloy():
    """Structure dictionary with alloy site."""
    return {
        "pbc": [True, True, True],
        "cell": [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
        "sites": [
            {
                "symbol": ["Cu", "Al"],
                "position": [0.0, 0.0, 0.0],
                "weight": (0.5, 0.5),
                "kind_name": "CuAl",
            }
        ],
    }


@pytest.fixture
def example_structure_dict_vacancy():
    """Structure dictionary with vacancy."""
    return {
        "pbc": [True, True, True],
        "cell": [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
        "sites": [
            {
                "symbol": ["Cu"],
                "position": [0.0, 0.0, 0.0],
                "weight": (0.8,),  # 20% vacancy
                "kind_name": "CuX",
            }
        ],
    }


@pytest.fixture
def magnetic_structure_collinear():
    """Collinear magnetic structure (simple ferromagnet)."""
    return {
        "pbc": [True, True, True],
        "cell": [[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]],
        "sites": [
            {
                "symbol": "Fe",
                "position": [0.0, 0.0, 0.0],
                "magmom": [0.0, 0.0, 2.2],
                "kind_name": "Fe_up",
            },
            {
                "symbol": "Fe",
                "position": [2.0, 2.0, 2.0],
                "magmom": [0.0, 0.0, 2.2],
                "kind_name": "Fe_up",
            },
        ],
    }


@pytest.fixture
def magnetic_structure_noncollinear():
    """Non-collinear magnetic structure."""
    return {
        "pbc": [True, True, True],
        "cell": [[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]],
        "sites": [
            {
                "symbol": "Mn",
                "position": [0.0, 0.0, 0.0],
                "magmom": [2.0, 0.0, 0.0],
                "kind_name": "Mn1",
            },
            {
                "symbol": "Mn",
                "position": [2.0, 0.0, 0.0],
                "magmom": [-1.0, 1.732, 0.0],  # 120° rotation
                "kind_name": "Mn2",
            },
            {
                "symbol": "Mn",
                "position": [1.0, 1.732, 0.0],
                "magmom": [-1.0, -1.732, 0.0],  # 240° rotation
                "kind_name": "Mn3",
            },
        ],
    }


@pytest.fixture
def structure_with_charges():
    """Structure with different charges on sites."""
    return {
        "pbc": [True, True, True],
        "cell": [[5.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 5.0]],
        "sites": [
            {
                "symbol": "Na",
                "position": [0.0, 0.0, 0.0],
                "charge": 1.0,
                "kind_name": "Na",
            },
            {
                "symbol": "Cl",
                "position": [2.5, 2.5, 2.5],
                "charge": -1.0,
                "kind_name": "Cl",
            },
        ],
        "tot_charge": 0.0,
    }


@pytest.fixture
def ase_silicon_structure():
    """ASE silicon structure for conversion tests."""
    from ase.build import bulk

    return bulk("Si", "diamond", a=5.43)


@pytest.fixture
def ase_magnetic_structure():
    """ASE structure with magnetic moments."""
    from ase.build import bulk

    atoms = bulk("Fe", "bcc", a=2.87)
    atoms.set_initial_magnetic_moments([2.2, 2.2])
    return atoms


@pytest.fixture
def pymatgen_structure():
    """Pymatgen structure for conversion tests."""
    try:
        from pymatgen.core import Lattice, Structure

        coords = [[0, 0, 0], [0.75, 0.5, 0.75]]
        lattice = Lattice.from_parameters(
            a=3.84, b=3.84, c=3.84, alpha=120, beta=90, gamma=60
        )
        return Structure(lattice, ["Si", "Si"], coords)
    except ImportError:
        pytest.skip("pymatgen not installed")
