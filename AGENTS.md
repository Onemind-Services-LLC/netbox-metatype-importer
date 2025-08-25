# Repository Guidelines

## Project Structure & Module Organization
- Source: `netbox_metatype_importer/` — Django app for the NetBox plugin.
  - `api/`, `graphql/`, `jobs/`, `migrations/`, `templates/`, `tests/` submodules.
- Tests: `netbox_metatype_importer/tests/` (Django TestCase unit tests).
- Local test settings: `testing_configuration/configuration.py` (do not commit secrets).

## Build, Test, and Development Commands
- Install (editable): `pip install -e .`
- Pre-commit hooks: `pip install pre-commit && pre-commit install && pre-commit run -a`
- Format: `black . && isort .`
- Lint/type checks (optional): `pylint netbox_metatype_importer` and `pyright`
- Run tests (Docker-based): `./test.sh`
  - What it does: runs `manage.py makemigrations --check` and Django tests in a NetBox container, then cleans up.

## Coding Style & Naming Conventions
- Python formatting: Black (line length 120) and isort (profile=black).
- Linting: follow Pylint guidance (max line length 120).
- Types: Pyright configured for `netbox_metatype_importer/`.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants. Django apps and modules use `snake_case`.
- Templates, migrations, jobs: keep names descriptive and consistent with existing patterns.

## Testing Guidelines
- Framework: Django `TestCase` (see examples in `tests/`).
- Location & pattern: files named `test_*.py` under `netbox_metatype_importer/tests/`.
- Scope: add tests for models, filters, views, and utilities you change.
- Running: prefer `./test.sh`; if embedded in a NetBox dev instance, use `python manage.py test netbox_metatype_importer`.

## Commit & Pull Request Guidelines
- Branching: base work on `dev`; do not target `master` for feature work.
- Commits: write clear, imperative messages; group related changes; keep diffs focused.
- PRs: use `.github/pull_request_template.md`.
  - Include: description, linked Jira (e.g., `OMS-1234`), tests, screenshots when UI changes.
  - CI expectations: syntax/lint checks and unit tests must pass.

## Security & Configuration Tips
- Do not commit tokens. Provide `PLUGINS_CONFIG` via environment or local settings; example: `testing_configuration/configuration.py` with `github_token`.
- Review changes for secrets and security implications before opening a PR.

