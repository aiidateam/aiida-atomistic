# `aiida-atomistic` package


AiiDA plugin which contains data and methods for atomistic simulations within AiiDA.


## Installation

```shell
git clone https://github.com/aiidateam/aiida-atomistic .
pip install ./aiida-atomistic
verdi quicksetup  # better to set up a new profile
verdi plugin list aiida.data  # should now show your data plugins
```


## Development

```shell
git clone https://github.com/aiidateam/aiida-atomistic .
cd aiida-atomistic
pip install --upgrade pip
pip install -e .[pre-commit,testing]  # install extra dependencies
pre-commit install  # install pre-commit hooks
pytest -v  # discover and run all tests
```

## License

MIT

## Contact

mikibonacci@psi.ch
