---
name: git-commit-standards
description: Enforce Conventional Commits standards
---

# Git Commit Standards

## Format

`<type>(<scope>): <subject>`

## Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools and libraries

## Rules

1. **Subject**:
   - Use imperative, present tense: "change" not "changed" nor "changes".
   - Don't capitalize the first letter.
   - No dot (.) at the end.
2. **Body (Optional)**:
   - Use imperative, present tense.
   - Include motivation for the change and contrast with previous behavior.

3. **Footer (Optional)**:
   - Reference issues: "Closes #123".
   - Breaking changes start with "BREAKING CHANGE:".

## Examples

- `feat(scanner): add stochastic indicator calculation`
- `fix(fetcher): handle API rate limit errors gracefully`
- `docs: update readme with new indicator list`
- `chore: add .gitignore for venv and cache files`
