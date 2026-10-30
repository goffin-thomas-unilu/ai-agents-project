# Week 7: a RAG pipeline you can score

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 7
**Run conditions.** embedding model: nomic-embed-text | dimensionality: 768 |
chunk size: 600 | overlap: 80 | k: 5 | store: Chroma | date: 2026-10-30 |
table from: my own index

### 1. The chunker

size 600, overlap 80, because [ta phrase, voir plus bas]. The section heading
is prepended to every chunk, since it is often the only place the topic word
appears.

### 2. The index

84 chunks, 768 dimensions, [secondes] seconds for one full indexing run.
My chunker gives 84 chunks where the recorded run has 95, and my keyword
retriever counts distinct query terms only, so my ranks differ from the
recorded ones.

### 3. The table

| qid | dense rank | keyword rank | recall@5 | tags |
| Q01 | 1 | 2 | 1.00 | distractor, superseded |
| Q02 | 1 | 1 | 1.00 | rare-token |
| Q03 | 1 | 1 | 1.00 | easy |
| Q04 | 1 | 1 | 1.00 | vocabulary |
| Q05 | 22 | 7 | 0.00 | multi-document |
| Q06 | 1 | 16 | 1.00 | negation |
| Q07 | 1 | 3 | 1.00 | easy |
| Q08 | 1 | 1 | 1.00 | numeric |
| Q09 | 1 | 2 | 1.00 | distractor |
| Q10 | 1 | 1 | 1.00 | easy |
| Q11 | 1 | 5 | 1.00 | easy |
| Q12 | n/a | n/a | n/a | unanswerable |

recall@5 is the dense retriever's. Q12 has no gold section, so it is not scored.

### 4. Good pipeline, or easy task?

[Ten of eleven questions rank the gold chunk first. Say which of the two
that is evidence for. One sentence, and be honest.]

### 5. The question that fails on both

Question: [ ]. Dense rank [ ], keyword rank [ ].

Why it fails:

[...]

Would any chunk size fix it? [ ], because [ ].

### 6. The gold-set correction

The note said: [ ]

My measurement said: [ ]

The corrected note:

[...]

[What it cost you to find this: one measurement. What it would have cost to
not find it: a stretch exercise built on a false premise, and a term in
which nobody noticed.]

### Deferred

[Anything you did not get to, and why.]
