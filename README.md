# Lexer Python SDK

[![Build status](https://badge.buildkite.com/b9df0354cc5093b82d30c8288acb624ca7739986dd8e2035b1.svg)](https://buildkite.com/lexerai/lexer-sdk)

## Introduction

## Quick Start Guide

### Cloning the Repository

1. `git clone` this repository.
2. You'd also want to install Git LFS. Please follow the instructions
[here](https://git-lfs.github.com/) for more information on how to do it
on your system. NOTE: Remember to run `git lfs install` before using it!

### Docker

We find that Docker is the best way for individual contributors to build and develop software in a reproducible manner.
Please install it before proceeding to the steps below.

### Other Tools

#### Shellcheck

Please install `shellcheck` for linting your Bash shell scripts. You can do this on MacOS via Homebrew with:

```bash
brew install shellcheck
```

## Branching Strategy

1. `main` - shall always contain the latest, stable snapshot of the codebase. In practice, this will be where staging/prod releases are cut. Manual pushes to this branch are not allowed!

2. `develop` - this is where all code gets merged to after code reviews and successful CI runs.

3. `develop-stable`? (TBD)

## Getting Started

To run a local instance of the stack for development purposes:

```bash
docker compose --profile dev up
```

For example, if you'd like to run the Lexer Python SDK for local development
purposes (and stay in the shell session), you can do:

```bash
docker compose run -it lexer_python_sdk_local_dev bash
```

Great, now you're up and running!

## Guides

We maintain a set of [guides](/guides/README.md)
on how to contribute effectively as a Lexer engineer.
Please take the time to read through them and adhere to these processes as much as possible.
That said, we welcome new suggestions on how we can make these even better, so feel free
to open a pull request!

## Linting

Please run the following commands and make sure each are passing before sending it out for PR reviews!

For Python files:

```bash
black ./**/*.py
flake8 ./**/*.py
```

For Bash files:

```bash
shellcheck ./**/*.sh
```
