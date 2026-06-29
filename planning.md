# TakeMeter — Planning

**Project:** AI201 Project 3 (TakeMeter)
**Community:** r/AskReddit
**Classification task:** post-title classification by question type

---

## 1. Community

I chose **r/AskReddit**. It is one of the most active English-language text communities on the internet, with a steady stream of new post titles every minute and a consistent format (a question, typically one or two sentences, no body required). Discourse is interesting because the *question itself* signals what kind of answer the asker wants — and r/AskReddit askers use a few recurring question patterns that draw fundamentally different kinds of responses. Classifying by question type captures a meaningful structural distinction in the community: a "comparison" question gets ranked-list answers, an "experience" question gets first-hand stories, etc. Mods and frequent posters distinguish these patterns implicitly when they engage.

**Note on framing:** The TakeMeter project intro frames classification around "discourse quality." I am intentionally framing this as **question-type classification on post titles** rather than quality assessment. r/AskReddit's discourse quality varies but is dominated by the comment threads, not the questions; and question-type is a clean, mutually exclusive, grounded distinction that is well-suited to a 200-example labeled dataset. The "meaningful distinctions in your chosen community's discourse" wording in the rubric is satisfied by question typology.

---

## 2. Labels

Four labels, mutually exclusive, exhaustive enough to cover ≥90% of r/AskReddit post titles without an "other" bucket.

### `comparison`
**Definition:** The asker wants the reader to identify or rank an item from a publicly shared category (movies, songs, professions, historical figures, etc.). The answer is a noun phrase naming the item, often with a one-sentence justification. The question can be answered by anyone with knowledge of the category — no personal history required.

**Examples:**
- "What's the most overrated movie of all time?"
- "Who's the greatest athlete of the 21st century?"

### `speculation`
**Definition:** The asker wants the reader to predict a future state of the world — what will happen, what will change, what will become obsolete. The question is grounded in a future timeframe and seeks a claim that could in principle be right or wrong.

**Examples:**
- "What's a job that won't exist in 20 years?"
- "What businesses are likely to die out with the Baby Boomer generation?"

### `opinion`
**Definition:** The asker wants the reader to share a personal stance, value, preference, or feeling that is not tied to a single past event and is not a prediction about the future. The answer is a general view ("here's what I think/value/prefer"), not a specific story.

**Examples:**
- "What's something you 'waste' money on but it's totally worth it?"
- "What are you looking forward to in 2026?"

### `experience`
**Definition:** The asker wants the reader to recount a specific event from their own life or first-hand observation. The answer is a narrative. Superlative phrasing ("weirdest", "most embarrassing") functions as a *filter on which event to tell*, not as a ranking invitation. The question can only be answered by people with the relevant first-hand history.

**Examples:**
- "Doctors of Reddit, what's the most unusual reason a patient ended up in the ER?"
- "Divorced people, what was the exact moment you knew your marriage was over?"

---

## 3. Hard edge cases & decision rules

### Edge case A — Superlative + personal pronoun (`comparison` vs. `experience`)

Both labels can carry superlative language ("worst", "weirdest", "most"). The distinguisher is **the source of the answer**:

- **comparison** — Answer comes from a shared external space (films that exist, athletes who exist). Anyone could answer.
- **experience** — Answer comes from the answerer's own life. Only people with that history can answer.

**Decision rule:** Presence of `you've`, `you've ever`, `have you ever`, `your`, or a population vocative (`nurses of Reddit`, `people who've X`, `X-year-olds`) → label `experience`. Absence of these + a public category noun → label `comparison`.

- *"What's the worst movie of all time?"* → `comparison`
- *"What's the worst pain you've ever felt?"* → `experience`

### Edge case B — Future-oriented + personal framing (`speculation` vs. `opinion`)

A question can refer to the future and still be opinion-like if it asks about preferences rather than predictions.

**Decision rule:** If the question asks the reader to *predict the world* (what will be true, what will happen, what will emerge), label `speculation`. If it asks the reader to *share their personal stance toward the future* (what they want, anticipate enjoying, are excited about), label `opinion`.

- *"What's likely to happen in tech in the next 5 years?"* → `speculation`
- *"What are you looking forward to in 2026?"* → `opinion`

### Edge case C — General stance vs. specific event (`opinion` vs. `experience`)

Some questions blur stance and event ("what's something you've done that you're proud of"). **Decision rule:** If the natural answer is a general value ("I think X is worth it"), label `opinion`. If the natural answer is a specific event ("the time when..."), label `experience`. Ties go to `experience` when the question contains a temporal anchor ("the exact moment", "the time", "when did you").

---

## 4. Data collection plan

**Source:** r/AskReddit post titles, scraped from the public Reddit JSON endpoints (top, hot, and new feeds across multiple time windows: week, month, year). Comments are not included — only the post title is the unit of classification.

**Target:** 200 examples minimum. Aim for ~50 per label (25% each). The PDF advises ≥20% per label; ~50 each gives a margin.

**Per-label collection strategy:**
- `comparison` — search for titles containing "best", "worst", "greatest", "favorite", "overrated", "of all time"
- `speculation` — search for "will", "going to die out", "in 20 years", "next decade", "future of"
- `opinion` — search for "what do you think", "what's something you", "do you prefer", "unpopular opinion"
- `experience` — search for "of Reddit," "you've ever", "have you ever", "your weirdest/dumbest/most"

**If a label is underrepresented after 200 examples:** Use targeted search-and-filter for that label specifically (e.g., search r/AskReddit for "of Reddit," to surface experience posts). Do not synthetically pad — collect real posts.

**Train/val/test split:** 70/15/15, stratified on label, `random_state=42`. The starter notebook already handles this.

---

## 5. Evaluation metrics

**Primary:** Overall accuracy + macro-F1 across all four classes.

**Per-class:** precision, recall, F1 for each label.

**Confusion matrix:** 4×4 over the test set. The most informative comparison will be the off-diagonal between `comparison` and `experience` — that is the boundary where the model is most likely to err, based on the superlative-trap analysis in §3.

**Why these:** Accuracy alone hides class imbalance. With ~50 examples per label and 15% test split, the test set is ~30 examples — every wrong prediction shifts accuracy by ~3 points. Macro-F1 weights all classes equally, so a model that nails `comparison` and `speculation` but botches `experience` is penalized appropriately. Per-class F1 surfaces which boundary the model failed on.

**Baseline:** Zero-shot prompt to Groq `llama-3.3-70b-versatile` using the same label definitions, on the same test set. Reported side-by-side.

---

## 6. Definition of success

A classifier is "good enough" for deployment in a community tool if:

- **Overall accuracy ≥ 75%** on a held-out test set (random baseline for 4 balanced classes is 25%; trained baseline is what we measure against).
- **Macro-F1 ≥ 0.70**
- **No single class has F1 < 0.55** — i.e., the model is not pathologically blind to any one label.
- **Fine-tuned model beats the Groq baseline by ≥ 5 accuracy points.** If fine-tuning doesn't beat zero-shot prompting, the labeled dataset wasn't worth collecting.

If none of these are hit, the failure modes go into the evaluation report and likely point to label-boundary problems (most likely the `comparison`/`experience` boundary).

---

## 7. AI Tool Plan

### Label stress-testing
**Done during planning (this document).** I generated 10 boundary-test post titles in conversation with Claude, then labeled each under the four-label taxonomy. The boundary cases that exercised the `comparison`/`experience` superlative trap (#1, #3, #8 in the stress-test table) all resolved cleanly under the decision rule in §3.A. The `speculation`/`opinion` boundary (#4 vs. #7) also resolved cleanly.

If during annotation I encounter posts I cannot classify under the current rules, I will pause, document the example, and tighten the §3 decision rules before continuing — rather than ad-hoc labeling.

### Annotation assistance
**Decision:** Annotate the 200 examples by hand without LLM pre-labeling.

**Rationale:** The boundaries between these four labels — especially comparison/experience — depend on subtle grammatical cues that an LLM may apply inconsistently. With only 200 examples, the time saved by pre-labeling is small, and the cost of an LLM systematically miscategorizing one boundary (and me not noticing) is high: it would teach the fine-tuned model the LLM's biases rather than mine.

**Exception:** I will use an LLM to *flag* posts in my dataset whose classification differs from a quick re-read pass — i.e., a second-opinion check after I have annotated, not a first-pass labeler. Posts where I disagree with the LLM get a third read.

### Failure analysis
After running the evaluation in Section 4 of the starter notebook, I will:
1. Export the wrong predictions to a list (post title, true label, predicted label, confidence).
2. Feed the list to Claude and ask it to identify systematic patterns ("the model misclassifies superlative-experience as comparison", "short titles get defaulted to opinion", etc.).
3. **Verify each proposed pattern by hand** — count how many wrong predictions actually exhibit the pattern, vs. how many are described that way only because the LLM pattern-matched on a few examples. Patterns that don't survive verification do not go into the evaluation report.

The evaluation report will name at least one verified systematic failure pattern, with the supporting count.

---

## 8. Stretch features

I am not committing to stretch features yet. Will update this section before starting any.
