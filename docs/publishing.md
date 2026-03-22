# Publishing

This document explains how to publish `nicegui-builder` to TestPyPI and PyPI.

## Publishing Strategy

Recommended workflow:

- use TestPyPI for development and packaging validation
- use PyPI only for stable releases
- use `develop` as the integration branch
- use `main` as the stable release branch
- publish development releases manually from `develop`
- publish stable releases from tagged versions on `main`

## Versioning

Use PEP 440 compatible versions.

Suggested pattern:

- stable release: `0.1.0`
- development/test release: `0.1.1.dev1`
- later development/test release: `0.1.1.dev2`

Important:

- every upload must use a new version
- TestPyPI also rejects re-uploading the same file/version combination

The version currently lives in `pyproject.toml`.

## One-Time Setup

### 1. Create accounts

Create an account on:

- PyPI
- TestPyPI

### 2. Create the project on both registries

The first publication usually creates the project automatically if the name is free.
The package name is:

`nicegui-builder`

### 3. Configure Trusted Publishing

In both PyPI and TestPyPI:

1. open the project settings
2. configure a Trusted Publisher
3. point it to this GitHub repository:
   `onclefranck/nicegui-builder`

Recommended mapping:

- TestPyPI:
  - workflow: `publish-testpypi.yml`
  - environment: `testpypi`
- PyPI:
  - workflow: `publish-pypi.yml`
  - environment: `pypi`

This avoids storing API tokens in GitHub secrets.

## Local Validation

Before publishing, run:

```bash
python -m pytest tests
```

If needed, install release tooling:

```bash
pip install -r requirements-dev.txt
```

Then validate the build locally:

```bash
python -m build
python -m twine check dist/*
```

## Changelog Management

This repository is configured for `git-cliff`.

The default project configuration runs `git-cliff` in offline mode for GitHub metadata.
That avoids API errors on a private repository when no GitHub token is configured.

Install it with the development tooling:

```bash
pip install -r requirements-dev.txt
```

Generate the changelog from the full history:

```bash
git-cliff -o CHANGELOG.md
```

Preview only the unreleased changes:

```bash
git-cliff --unreleased
```

If you later want GitHub-enriched metadata for a private repository, provide a token and disable offline mode in `cliff.toml`.

Recommended release habit:

1. update the version in `pyproject.toml`
2. run `git-cliff -o CHANGELOG.md`
3. review the generated changelog
4. commit the version bump and changelog together
5. tag the release

## TestPyPI Release Flow

Use this for development and packaging validation.

### Recommended steps

1. update the version in `pyproject.toml` to a development version
2. commit the change on `develop`
3. push the branch
4. trigger the `Publish TestPyPI` workflow manually in GitHub Actions
5. verify installation from TestPyPI

Example install:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple nicegui-builder
```

## Production PyPI Release Flow

Use this for stable releases only.

### Recommended steps

1. make sure tests pass
2. update the version in `pyproject.toml` to a stable version
3. commit the release version
4. merge the approved release PR into `main`
5. create and push a git tag like `v0.1.0` from `main`
6. let the `Publish PyPI` workflow publish the package
7. verify installation from PyPI

Example:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Example install:

```bash
pip install nicegui-builder
```

## What Has Been Prepared In This Repository

The repository now includes:

- package metadata in `pyproject.toml`
- package-data inclusion for YAML files
- `MANIFEST.in` for source distribution completeness
- build tooling in `requirements-dev.txt`
- `git-cliff` configuration in `cliff.toml`
- `CHANGELOG.md`
- GitHub Actions workflows for TestPyPI and PyPI

## Practical Advice

- publish to TestPyPI first
- always bump the version before each upload
- keep stable releases rare and intentional
- do not publish directly from experimental work without validating the built artifacts

## GitHub Branch Workflow

Recommended branch model:

- feature branches are temporary and disposable
- open pull requests from feature branches into `develop`
- use `develop` for integration and TestPyPI validation
- open pull requests from `develop` into `main`
- create release tags only from `main`

Recommended protection posture:

- require pull requests for both `develop` and `main`
- require the CI workflow to pass before merge
- block direct pushes to both protected branches
- keep merge permissions limited to you while the project is still effectively single-maintainer

For a one-person team, this gives you the discipline of pull requests and CI without forcing an impossible self-approval workflow.
