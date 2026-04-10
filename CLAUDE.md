# CLAUDE.md — Control Plane

**icom-lan** v0.15.1 — Python 3.11+ asyncio library + Web UI for Icom transceivers over LAN/USB.
IC-7610 at `192.168.55.40`, CI-V `0x98`. Context: `AGENTS.md`, `docs/PROJECT.md`.

---

## Commands (always `uv run`)

```bash
uv run pytest tests/ -q --tb=short                    # all tests
uv run pytest tests/ -q --tb=short --ignore=tests/integration  # skip hw
uv run mypy src/                                       # type check
uv run ruff check src/ tests/ && uv run ruff format src/ tests/  # lint+format
```

Never bare `python` or `pytest`. Worktrees: `uv sync --all-extras` first.

---

## Architecture

Module map: @.claude/architecture/modules.md
Protocol/CI-V/gotchas: @.claude/architecture/protocol.md

**Layering (enforce):**
- Consumers → `radio_protocol.Radio` → `backends.factory` → CoreRadio → transport
- Web/rigctld must never call transport directly
- Backends must never import from `web/` or `rigctld/`
- New commands → `commands/` + `command_map.py` + `commander.py`
- New public API → `radio_protocol.py` first, then backend
- No new abstractions, layers, or refactors unless the issue explicitly requires it

**Hard protocol rules:**
- cmd29 does NOT work for freq/mode (`0x05`/`0x06`) on IC-7610
- Keep-alive: ~500ms control, ~100ms audio — never weaken
- MagicMock hides signature bugs — verify against real dataclasses

---

## Testing

- TDD — test first, implement second
- Batch all fixes, run tests once (not per fix)
- Audio tests: `FakeAudioBackend` only — no one-off mocks
- Details: @.claude/workflow/testing.md

---

## LightRAG

Query ONLY for: transport/CI-V, receiver routing, audio codec/bridge, prior bug refs.
Skip for: simple changes, test fixes, formatting, single-file edits.
Save: architectural decisions, confirmed hardware bugs, protocol gotchas.

---

## Language & Git

User-facing → **Russian**. Code/commits/docs/PR → **English**.
Commits: `feat(#N):` / `fix(#N):` / `refactor:` / `test:` / `docs:` / `chore:`
One change per commit. Full test suite before push.

---

## Completion criteria

Work is complete ONLY when ALL pass:
1. `uv run pytest tests/ -q --tb=short` — zero failures
2. `uv run ruff check src/ tests/` — zero violations
3. `git diff` — no unintended changes

Incomplete → continue or FAILED. Never skip.

---

## Autonomous pipeline

One issue, one phase at a time. No parallel steps. No phase jumping.

```
EXPLORE → PLAN → EXECUTE → tests → REVIEW → diff → TEST → PR
```

| Command | Action |
|---------|--------|
| `/scan-issues` | score open issues → `.claude/queue/queue.json` |
| `/solve-issue N` | full pipeline for issue #N |
| `/next` | pick highest-priority pending, solve it |

### Entry conditions (must ALL be true to start)

- Issue has clear expected outcome
- Scope fits guardrails (≤3 files, ≤200 LOC)
- No hardware dependency (unless mockable)
- Otherwise → SKIP

### Fast path

Skip PLAN if ALL true: single file, <20 LOC, no protocol/transport/state, no public API.
Never skip EXPLORE, REVIEW, or TEST.

### Phase state machine

| Phase | Agent | Owns | Gate to proceed |
|-------|-------|------|-----------------|
| EXPLORE | researcher | `research.md` | confidence ≥ 0.6 |
| PLAN | planner | `plan.md` | explicit steps written |
| EXECUTE | executor | `progress.md` | tests pass |
| REVIEW | reviewer | `review.md` | diff matches plan |
| TEST | qa | — | all checks green |

- Each phase writes ONLY its own file. Do not modify other phase files.
- Phase is complete ONLY when its output file is written AND gate condition met.
- Re-read CLAUDE.md before PLAN to prevent drift.
- PLAN is immutable during EXECUTE. Wrong plan → FAIL and restart, do not patch.
- EXECUTE: implement plan exactly. No extras, no refactors, no scope expansion.
- REVIEW: compare diff against plan. Reject unplanned changes.

Definitions: `.claude/agents/{researcher,planner,executor,reviewer,qa}.md`
Use subagents for large exploration/review — keep main session lean.

### Guardrails

| Limit | Value |
|-------|-------|
| Files per change | 3 |
| LOC delta | 200 |
| New abstractions/layers | forbidden unless issue requires |
| Speculative improvements | forbidden |
| Min confidence | 0.6 |

### Failure handling

- 2 consecutive failures or no progress → **STOP**, mark FAILED
- Max cycles: 2 execution, 2 review, 2 test-fix. Exceeded → FAILED.
- On FAILED, classify: `invalid_plan` / `impl_error` / `test_failure` / `env_issue`
- Log classification + reason to `.claude/knowledge/failures.md`
- Load `.claude/knowledge/` ONLY on keyword match or prior failure pattern — not by default
- State/queue/retry: @.claude/workflow/

---

## Context hygiene

- Repeated mistakes or inconsistent decisions → `/clear`
- 2+ corrections on same step → session reset
- Read only relevant files — never scan entire codebase
