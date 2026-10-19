# Week 5: a planner, an executor, and a second agent

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 5

**Run conditions.** model: qwen2.5:7b | framework: Pydantic AI 2.57.0 |
runs per architecture: 3 | served locally | date: 2026-10-19 |
table from: the recording (replay, recorded 2026-08-11)
### 1. The plan schema

What I tried first, and what happened:

"I did not try nested Step objects; I followed the warning in the starter."]

What I shipped, and why it is shaped that way:

`goal: str`, `steps: list[str]`, `suspect_file: str`. Everything is flat.
A list of strings still says "several ordered steps" through list order,
and it avoids the nested structure that makes this model exhaust its output
retries.
### 2. The validator

| check | what it catches |
| 2 to 6 steps | an empty or runaway plan; matches the planner's prompt |
| suspect_file in KNOWN_FILES | an invented or misspelled file name |
| a step mentions running tests | a plan with no way to verify itself |
| no step edits a test | a plan that games the verifier (apply_fix refuses it anyway) |

On a failed check my system repairs once (re-prompt the planner with the
list of problems), then refuses, because a plan is cheap to regenerate and
an invalid plan must never reach the executor.
### 3. The three-way table

| architecture | green | tokens (mean) | seconds (mean) |
| A baseline | 0/3 | 10470 | 40.1 |
| B planner | 2/3 | 1751 | 15.0 |
| C planner + reviewer | 0/3 | 3441 | 29.0 |

### 4. Why the baseline fails

Not the model and not the prompt: both are the same in A and B. What
changed is the action space and the context. In A the model must explore
with four free tools (list, read, replace, run) and decide the order
itself, and it spends ~10k tokens doing so without landing a fix. In B the
code reads the suspect file and the failing output and puts them in the
prompt, and the model only has to return one structured Fix that
`apply_fix` can check. The narrower the action, the more reliably the model
takes it, and the easier it is to verify before it happens.
### 5. The reviewer

Verdicts across my runs: 0 approve, 3 reject.

Would I ship it: no, not as written. In all three C runs it rejected a
fix that, as far as the truncated output shows, is the same
`start_hour > OFF_PEAK_FROM_HOUR -> ...` change that went green in B runs 2
and 3. That is how C ended at 0/3: it blocked correct fixes. Extra cost vs
B: about 1,700 tokens and 14 seconds per run (approximate: the two rows come
from different runs).

The case where it would earn its cost:

The plausible-wrong fix: lowering OFF_PEAK_FROM_HOUR from 20 to 19 makes
the failing test pass and is wrong. A reviewer that reliably rejected that
and approved `>=` would justify its cost. This recording gives no evidence
either way, because the reviewer rejected everything.

### 6. What my verifier cannot catch

The suite only checks cases someone wrote a test for. Changing
OFF_PEAK_FROM_HOUR to 19 goes green if no test covers 19:00, yet it gives
the discount to the wrong bookings. Special-casing `start_hour == 20` would
also pass. Week 10 comes back for this (see case W5-constant-trap)
### Deferred

[Anything you did not get to, and why.]
