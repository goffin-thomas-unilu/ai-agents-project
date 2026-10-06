# Week 3: a router in front of the extractor

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 3

**Run conditions.** classifier model: [qwen3:4b-instruct ] | answering model: [qwen2.5:7b ] |
temperature: 0.0 | served locally | date: [YYYY-MM-DD] | scored on: [my own machine]

### 1. The five route definitions

| route | definition, one sentence, in terms of what the help desk must do |
| request |The sender asks the commune to take a concrete action it has not yet taken: create an account, fix equipment, process a payment, grant access |
| info |The sender asks a question and expects an answer, with no action required from the commune beyond replying |
| status |The sender asks about something already in progress or already submitted, and wants to know where it stands |
| complaint |The sender reports that something already done or already failed went wrong, and expects it to be acknowledged, not fixed on the spot |
| other |The message needs no action and no answer: it only informs the help desk of something, or is a suggestion with no request attached |

My convention for the four ambiguous queries:
I agree with the four ambiguous queries

[Two defensible conventions exist. Neither is discoverable from the data.
What matters is that yours was written down before you measured, not which
one you picked.]

Do my definitions match the ones in `queries.py`? [yes]

### 2. The policy layer

Before choosing a threshold, the confidence values I saw were: min 0.00,
max 0.99, 3 distinct values (0.00, 0.95, 0.99) across 24 queries.

- confidence floor: [0.7], because [it catches low-confidence edge cases without false positives.]
- evidence check: fallback to safe default, because it can indicate a bad routing decision
- safe default: [info ], because that specialist general inquiries with minimal risk of executing unwanted actions or mutating system states.

How often each check fired: below_threshold 0, evidence_not_verbatim 0,
invalid_decision 1 Q22.

[If a check fired zero times, say what that tells you. A threshold that
never fires is either a very good classifier or a useless signal, and the
confidence distribution above tells you which.]

### 3. Route accuracy

| route | correct | of |
| request |2 |2 |
| info |6 |7 |
| status |7 |7 |
| complaint |7 |7 |
| other |1 |1 |

Overall 23/24. Excluding the four ambiguous: 19/20.

Confusion pairs, with direction:

| gold | applied | count |
| | info|1 |

The route carrying most of the error is no_decision. The fix is to enforce output format rules with a better prompt maybe.

### 4. What routing cost

- monolith: [ ] tokens over 24 queries
- router: [ ] tokens over 24 queries
- the classifying call alone: [ ] tokens, which is [ ] per cent of the
  routed total

I predicted that share would be [ ] before measuring it.

[If the share surprised you, say why. The classifier's prompt carries every
route definition on every call, and the specialists carry only their own.]

### 5. What routing bought

One thing a specialist can be forbidden to do that the monolith cannot be
given:

[...]

Would I ship the router: [ ]. Evidence: [ ]. What would change my mind: [ ].

### 6. Stretch variant

Variant assigned: [ ]. Result: [ ].

[For model routing: report both models on accuracy, evidence verbatim, the
confidence range, and resident memory. If the smaller model won, say so
plainly and say what you think that means.]

[For voting: report the split-vote count at each temperature. If nothing
ever disagreed, that is the result. Say what it cost and what it bought.]

### The gold set

`artifacts/goldset.json` now holds [ ] cases: 10 from week 2 and 24 added
today, with the four ambiguous ones tagged.

### Deferred

[Anything you did not get to, and why.]
