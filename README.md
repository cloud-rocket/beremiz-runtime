<!-- These are examples of badges you might want to add to your README:
     please update the URLs accordingly

[![Built Status](https://api.cirrus-ci.com/github/<USER>/beremiz-runtime.svg?branch=main)](https://cirrus-ci.com/github/<USER>/beremiz-runtime)
[![ReadTheDocs](https://readthedocs.org/projects/beremiz-runtime/badge/?version=latest)](https://beremiz-runtime.readthedocs.io/en/stable/)
[![Coveralls](https://img.shields.io/coveralls/github/<USER>/beremiz-runtime/main.svg)](https://coveralls.io/r/<USER>/beremiz-runtime)
[![PyPI-Server](https://img.shields.io/pypi/v/beremiz-runtime.svg)](https://pypi.org/project/beremiz-runtime/)
[![Conda-Forge](https://img.shields.io/conda/vn/conda-forge/beremiz-runtime.svg)](https://anaconda.org/conda-forge/beremiz-runtime)
[![Monthly Downloads](https://pepy.tech/badge/beremiz-runtime/month)](https://pepy.tech/project/beremiz-runtime)
[![Twitter](https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter)](https://twitter.com/beremiz-runtime)
-->

[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

# beremiz-runtime

> A runtime only derivative of [Beremiz](https://github.com/etisserant/beremiz)

Beremiz is a very much welcomed SoftPLC framework, yet original Beremiz project includes IDE and Runtime as a single application. This is an attempt to restructure the original project into several standardized Python packages having less global variables and non-standard Python practices.

## Runtime execution options

### Python script

#### Install
```commandline
$ pip install beremiz-runtime
```

#### Run
```commandline
$ br-runtime-cli
```

#### Command line help
```commandline
$ br-runtime-cli -h
```



### Docker container

Building

```commandline
docker build -t beremiz-runtime:latest -f ./docker/Dockerfile .
```

<!-- pyscaffold-notes -->

## Note

This project has been set up using PyScaffold 4.6. For details and usage
information on PyScaffold see https://pyscaffold.org/.
