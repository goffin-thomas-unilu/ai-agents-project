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
Easy task. Dense ranks the gold chunk first on 10 of 11 answerable questions,
but my crude keyword retriever also puts it first on 5 and in the top 5 on 9,
so the questions share their vocabulary with the answer and rank one is what
almost any retriever achieves here; it cannot tell a good pipeline from a
mediocre one.

Largest dense advantage: Q06 (negation), dense rank 1 against keyword rank 16.
The document says travel is free of charge and the question asks whether I
have to pay, so the words barely overlap while the meaning (fares for the
shuttle) is the same.


### 5. The question that fails on both

Question: Q05, "I have just moved to Remerbaach and I own a car. What do I
have to do at the commune?" Dense rank 22, keyword rank 7.

Why it fails:

No single section answers it. The gold is two sections in two documents
(RB-ARRIVEE::Deadline and RB-VIGNETTE::How to apply), and the question names
neither topic in the words of either document: "moved" and "own a car" are
two intentions folded into one vague sentence. Dense retrieval embeds the
question as one point that sits near neither section, so no gold chunk reaches
the top 5 (recall@5 0.00).

Would any chunk size fix it? No, because the chunker splits each section on
its own and never merges two sections, so a bigger chunk cannot put an
arrival declaration and a parking vignette into the same chunk. The fix
belongs in the retrieval step (split the question into two sub-queries, or
retrieve with a larger k), not in the chunker. 
Confirmed by the sweep: dense rank of Q05 is 32 at size 300, 22 at 600 and 20
at 1200, and keyword rank is 12, 7 and 8. The rank moves with the size but
never gets near the top 5 (recall@5 stays 0.00), because the two gold
sections sit in two different documents and the chunker never merges sections.

### Chunk sweep (300, 600, 1200)

Chunks: 161, 84, 57. Dense ranks the gold chunk first on the same 10
questions at every size, and dense gets the gold chunk into the top 5 on 10 of
11 questions at every size. What moves is keyword search: Q02 (8, 1, 1), Q06
(11, 16, 4) and Q11 (18, 5, 6). Q05 fails at all three sizes (dense 32, 22,
20). The average barely shifts, the individual questions do.
### 6. The gold-set correction

The note said: "The query carries the string RB-1140b. Rare, exact, and
semantically empty, so dense retrieval is the wrong tool for it and keyword
search is the right one."

The sweep makes it clearer: dense ranks the gold chunk of Q02 first at sizes
300, 600 and 1200, while keyword search ranks it 8th, 1st and 1st.

My measurement said: on Q02, dense rank 1 and keyword rank 1 on my index.
Dense did not lose and keyword did not win. On the recorded run dense ranked
the gold chunk first and keyword ranked it 14th.

The corrected note:
The query carries the string RB-1140b. It is rare and exact, but dense
retrieval still ranked the gold chunk first, on my index and on the recorded
run, while keyword search tied it on my index (rank 1) and lost to it on the
recorded run (rank 14). A rare token is not a reliable case where keyword
search beats dense retrieval on this corpus. Note that a superseded page
carries the near-identical string RB-1140a.

What it cost me to find this: one measurement. What it would have cost to not
find it: a stretch exercise built on a false premise, and a term in which
nobody noticed.

### Deferred

[Anything you did not get to, and why.]
