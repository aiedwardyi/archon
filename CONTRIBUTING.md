# Contributing

Thanks for contributing to Archon.

## Good First Steps

1. Read the [README](README.md) for the product overview.
2. Read the [technical reference](docs/TECHNICAL_REFERENCE.md) for repo layout and key surfaces.
3. Check [CURRENT_SPRINT.md](CURRENT_SPRINT.md) before starting larger work.

## Development Setup

Use the install and run steps in [README.md](README.md).

Core local surfaces:

- backend: `python backend/app.py`
- studio UI: `frontend-studio/`
- consumer UI: `frontend-consumer/`
- enterprise UI: `frontend/`

## Contribution Guidelines

- Prefer small, reviewable pull requests.
- Keep changes scoped to one problem.
- Do not bundle unrelated cleanup into a feature PR.
- Preserve existing user data and generated artifacts unless the change explicitly targets them.
- If you change model-routing, scoring, or governance behavior, update the relevant docs.
- If you change build-repair logic, include regression coverage where practical.

## Pull Request Expectations

Include:

- what changed
- why it changed
- how it was verified
- any follow-up risks or gaps

When relevant, include:

- screenshots
- before/after behavior
- affected archetypes or providers
- commands used for validation

## Branching

- Use descriptive branch names.
- Rebase or merge from `main` before opening large PRs if your branch is stale.
- Avoid force-pushing shared branches unless the branch is clearly personal or coordination has already happened.

## Docs

If a change affects public behavior, keep these in sync where relevant:

- [README.md](README.md)
- [docs/ENGINEERING_OVERVIEW.md](docs/ENGINEERING_OVERVIEW.md)
- [docs/TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md)

## Issues

Bug reports are most useful when they include:

- environment
- reproduction steps
- expected behavior
- actual behavior
- logs or screenshots
