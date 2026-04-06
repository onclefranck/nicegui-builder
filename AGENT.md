# Agent Policy

This repository prioritizes structural clarity over compatibility shims.

## Refactoring Policy

- Do not add backward-compatibility aliases unless the user explicitly requests them.
- Do not add silent fallbacks, compatibility layers, or transitional shims to smooth over inconsistencies.
- Prefer exposing broken references and fixing them explicitly over masking them.
- When code is reorganized, update all affected references directly instead of preserving the old path through aliases.
- If a change has non-obvious migration cost, pause and surface it clearly rather than hiding it behind compatibility code.

## Quality Bar

- Treat hidden compatibility code as a design smell by default.
- Prefer explicit, strict structure even if it requires touching more files.
- If a cleanup reveals inconsistencies elsewhere in the codebase, keep them visible and report them rather than covering them up.

## Communication

- If compatibility code seems useful, ask before adding it.
- If there is a tradeoff between strictness and short-term convenience, default to strictness unless instructed otherwise.

## Commit Policy

- All commits must use the Conventional Commits format.
- Use commit messages shaped like `type(scope): summary`.
- Prefer standard Conventional Commit types such as `feat`, `fix`, `refactor`, `docs`, `test`, `build`, and `chore`.
- Do not create free-form commit messages when making repository changes.
