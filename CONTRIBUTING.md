# Contributing to Lucas' Game

Thanks for your interest. This is a small project with one unusual constraint
that shapes most of the rules below: it is a **kiosk application for a young
child**. It runs fullscreen and unattended, and the only way out is a keyboard
shortcut a parent has to know. Anything that can leave the child stuck in a
running game, or a parent unable to exit, is treated as a serious defect here
even when it looks cosmetic.

## Branches

| Branch  | Purpose |
|---------|---------|
| `devel` | Default branch. **All pull requests target `devel`.** |
| `main`  | Release branch. Updated by promoting `devel` when a version is cut. |

```
git switch devel
git pull
git switch -c my-change
# ...work...
git push origin HEAD:refs/heads/my-change
gh pr create --base devel
```

Push with an **explicit refspec** (`HEAD:refs/heads/my-change`) rather than
`git push -u origin my-change`. If your git has `push.default = upstream`, the
short form pushes into the branch you *branched from* — and it exits 0, so it
reads as success.

Direct pushes to `main` are not accepted; use a PR.

## Setting up

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -e ".[dev,audio]"
```

macOS additionally needs SDL2 from Homebrew and pygame built against it — see
the "Installation → macOS" section of [README.md](README.md). Python 3.10+ is
required (3.11+ if you want audio); the floor comes from the dependencies, not
from the game's own code.

## Tests

```bash
pytest
```

101 tests, all headless — `tests/conftest.py` sets `SDL_VIDEODRIVER=dummy`
before `lucas_game` is imported, so the suite will not take over your screen.
That ordering is load-bearing: the module opens a fullscreen display at import
time.

**There is no CI.** Nothing runs these tests except a person choosing to. Please
run them before opening a PR, and say in the PR that you did.

Three things to know before adding tests:

- `check_exit_shortcut()` reads **live** modifier state via
  `pygame.key.get_mods()`, not `event.mod`. A synthetic event carrying `mod=...`
  is silently ignored — use the `mods` fixture.
- `main()` ends with `pygame.quit()`, which tears down the video subsystem
  process-wide. The autouse `pygame_ready` fixture puts it back; without it every
  test ordered after the end-to-end one fails with "video system not initialized".
- Anything that starts a thread must assert it is dead before the test ends. A
  leaked thread keeps consuming the shared pygame event queue and turns its own
  failure into a later test's unexplained hang.

### A test that has never failed is not yet a test

If you fix a bug, **watch your new test fail against the unfixed code** before
you trust it, and say so in the PR. This is not ceremony. A committee review on
2026-08-31 mutated 22 behaviours in this repo and 7 mutations survived a fully
green suite — including two that deleted the macOS build fix outright. Among the
survivors was a regression test that passed with *either half* of its own fix
reverted, so neither half was actually verified.

Reverting your fix and re-running the one test takes a minute and is the only
thing that distinguishes a guard from a decoration.

## Style

- `black` for formatting, `ruff` for linting, `codespell` for prose.
- Formatting-only changes go in their **own commit**, separate from behaviour.
- Comments should carry the *why* — the failure mode, the non-obvious
  constraint, the reason a broad `except` or an odd guard is deliberate. Commit
  messages stay short; the explanation belongs in the code, where the next
  person to touch the line will actually see it.

## Versioning

Semantic versioning. A version bump must update **all five** locations:

```
setup.py         CFBundleVersion
setup.py         CFBundleShortVersionString
setup.py         version=
pyproject.toml   version
web/package.json version          <- the browser port; easy to miss
```

`tests/test_packaging.py::test_all_five_version_locations_agree` enforces this.
It exists because the rule previously named only four and `web/package.json`
had silently drifted.

## Things that need extra care

- **The exit shortcut.** It is the parent's only way out. A change that makes
  the on-screen hint disagree with the key that actually exits is a bug, not a
  cosmetic issue.
- **`hidutil` media-key suppression (macOS).** This mutates *system-wide*
  keyboard state. macOS has a single mapping list and setting it replaces the
  whole thing, so the game refuses to suppress when the user has mappings of
  their own rather than destroying them. Do not make this path run on import,
  and do not let it raise out of an exit handler.
- **`load_config()`.** It runs at module scope and it writes to the user's real
  config file. It must never propagate an exception, and it must never discard a
  file a parent hand-edited without keeping a copy.
- **`build_macos.sh`.** `dist/Applications` is a symlink to `/Applications`.
  `rm -rf dist/*/` — with a trailing slash — resolves it and deletes the
  contents of `/Applications`. Do not remove the guard around it.

## Pull requests

Include: what changed, why, how you verified it, and anything you did *not*
check. An honest "I did not test this on the Raspberry Pi" is worth more than
silence — it tells a reviewer where to look.

## Licence

MIT. By contributing you agree your contributions are licensed under it. New
source files should carry the copyright header used by the existing files.
