# Riskflow Agent Instructions

These instructions are for Codex or any coding agent working in this repo.

## Project Identity

- The project name is Riskflow.
- The Python package name is `riskflow`.
- Do not rename the package back to `leaderflow`; that was an earlier naming error.

## Start Of Session

- Read this file first.
- Then read `docs/PRIME_COMMAND.md` when starting a fresh Codex session or recovering project context.
- Then read `docs/PROJECT_CONTEXT.md`.
- For code work, also read `docs/ARCHITECTURE.md`.
- For planning work, also read `docs/ROADMAP.md`.
- For lab-loop, indicator research, or grammar work, also read `docs/LAB_LOOP.md` and `docs/SIGNAL_GRAMMAR_LAB.md`.
- For workflow/git/Obsidian questions, also read `docs/WORKFLOW.md`.
- Treat these docs as the durable project memory between sessions.

## Core Workflow

- Make focused, explainable changes.
- Prefer simple, testable research code over clever abstractions.
- After meaningful code or documentation changes, remind the user to commit and push.
- Do not commit or push unless the user asks.
- Use clear commit messages when committing.
- If product direction or architecture changes, update the relevant `docs/` file in the same change.

## Verification

- Run `python3 -m pytest` before commits that touch code.
- For documentation-only changes, tests are optional unless the docs affect commands or package behavior.
- Mention clearly when tests were not run.

## Git And Files

- Do not commit generated caches, virtualenvs, raw market data, or generated reports.
- Keep `.pytest_cache/`, `__pycache__/`, `data/raw/`, `data/processed/`, `reports/`, and `obsidian/reports/` out of commits except for `.gitkeep` placeholders.
- Push to `origin main` only after explicit user approval.

## Riskflow Product Direction

- V1 is a local Python research lab for meme-coin relative leadership and compression.
- Do not build a live trading bot, web dashboard, ML system, Markov engine, or global macro platform in v1.
- Keep calculations transparent and outputs explainable.
- Focus on relative forward returns versus the relevant basket, not only absolute returns.
- Treat Obsidian as the research memory layer, not the calculation engine.

## User Environment Notes

- The real project README is `README.md` at the repo root.
- `.pytest_cache/README.md` is pytest internals and should not be edited.
