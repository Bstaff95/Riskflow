# Riskflow Workflow

## Local Project

Project root:

```text
/Users/Shared/Riskflow
```

GitHub repo:

```text
https://github.com/Bstaff95/Riskflow.git
```

Obsidian vault:

```text
/Users/Shared/Riskflow/obsidian
```

## Codex Memory Workflow

At the start of future sessions, Codex should read:

1. `AGENTS.md`
2. `docs/PROJECT_CONTEXT.md`
3. `docs/ARCHITECTURE.md` for code work
4. `docs/ROADMAP.md` for planning work
5. `docs/WORKFLOW.md` for GitHub/Obsidian process

When major decisions are made, update the relevant docs file so future sessions inherit the decision.

## Git Workflow

Normal loop:

1. Make focused changes.
2. Run tests when code changes:

```bash
python3 -m pytest
```

3. Review git status:

```bash
git status --short
```

4. Commit only after user approval:

```bash
git add .
git commit -m "Clear commit message"
git push
```

## Obsidian Workflow

Obsidian is for research memory:

- concept definitions
- hypotheses
- experiment notes
- scan summaries
- decision logs
- postmortems

Python is for calculation:

- OHLCV loading
- basket construction
- signal calculation
- compression
- states
- scoring
- event studies

Do not store heavy data or generated report history in git unless explicitly requested.

## IDE Note

If the IDE opens `.pytest_cache/README.md`, ignore it.

The real project README is:

```text
README.md
```

The vault home note is:

```text
obsidian/Riskflow Home.md
```

