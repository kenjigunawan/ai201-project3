# TakeMeter — r/AskReddit Question Type Classifier

AI201 Project 3. A fine-tuned DistilBERT classifier that labels r/AskReddit post titles by question type: `comparison`, `speculation`, `opinion`, or `experience`.

## Status

| Milestone | Status |
|---|---|
| 1 — Community & label taxonomy | ✅ — see [`planning.md`](./planning.md) |
| 2 — Planning doc | ✅ — see [`planning.md`](./planning.md) |
| 3 — Dataset collection (200 examples) | ⬜ |
| 4 — Fine-tuning + baseline | ⬜ |
| 5 — Evaluation report | ⬜ |

## Repo contents

- `planning.md` — label definitions, decision rules, evaluation criteria, AI tool plan
- `ai201_project3_takemeter_starter_clean.ipynb` — fine-tuning + baseline notebook (starter)
- `data/` — labeled dataset CSV (to be added in Milestone 3)
- `evaluation_results.json`, `confusion_matrix.png` — outputs from notebook (to be added)

## Setup (local)

The starter notebook is designed for Google Colab (T4 GPU). For local editing / inspection:

```bash
.venv/bin/jupyter lab ai201_project3_takemeter_starter_clean.ipynb
```

Then select the kernel **Python (ai201-project3)** in the notebook.

Local CPU fine-tuning will be much slower than Colab T4 (PDF estimate: 5–15 min on T4 → likely 1–2 hr on Mac CPU). Use Colab for the actual training run.

## Labels (summary)

See `planning.md` for full definitions, examples, and decision rules.

| Label | One-line definition |
|---|---|
| `comparison` | Asks reader to identify/rank an item from a publicly shared category |
| `speculation` | Asks reader to predict a future state of the world |
| `opinion` | Asks reader to share a personal stance, value, or preference |
| `experience` | Asks reader to recount a specific first-hand event from their life |
