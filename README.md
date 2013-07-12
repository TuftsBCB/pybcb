This package provides a small framework for running experiments with Python as
the glue language.

The main contribution of the package is to centralize the definition of command
line options among a common suite of programs, and to provide a simple caching
mechanism to make step-wise debugging while experimenting easier. For example,
running an experiment may require multiple phases that each take a lot of time.
If a later phase fails, then pybcb can pick back up where it left off without
having to run the earlier phases.

## Documentation

None yet.


## Installation

As of right now, you'll need to clone the repository and add its path to your
`PYTHONPATH` environment variable:

    git clone git://github.com/TuftsBCB/pybcb
    cd pybcb
    export PYTHONPATH="$(pwd):$PYTHONPATH"

You should then be able to run `import pybcb` in a Python interpreter
successfully.

PyPI and distutils is forthcoming.

