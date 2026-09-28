# Week 2: a structured-output extractor, measured

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 2

**Run conditions.** 
model: [   
qwen3:4b-instruct          0edcdef34593    2.5 GB    ] 
| temperature: 0.0 | prompt version: [week02-zero-shot-v1 ] |
served locally | date: [2026-09-28] | scored on: my own machine

### 1. The output contract

The conventions I chose, and why:

- due_date, when the message states no date: 
  none , so that "no date" is one single value the scorer can compare
- due_date, when the message states only a relative expression: 
  also null."Before the end of the month" is not a calendar date. Dates written as DD/MM/YYYY are read as European (15/09/2026 becomes 2026-09-15)
- quote, and what "verbatim" means in my scorer: 
  the string returned by the
  model must appear exactly inside the source text, with no
  lowercasing, no stripping, and no whitespace tolerance. An empty quote is not accepted.
- what my scorer does with a record that failed validation: 
  it counts it in 'total' and in 'invalid', and gives it no point on any field.

[One sentence on why the last one matters. A scorer that skips the records
it could not parse reports a number that improves as the model gets worse.]
A scorer that skips the records it could not parse reports a number that
improves as the model gets worse, so invalid records must count as wrong.

### 2. Zero-shot, per field

| field | correct | of |
| category |7 | 10 |
| urgency |10 | 10 |
| due_date |7 | 10 |
| quote |10 | 10 |
| invalid records |0 | 10 |

My prediction, written before block 3: 
examples will help most on urgency
because the boundary between "urgent" and "standard" is a judgment that is
hard to define in words, and an example shows it directly.

my prediction was wrong. Urgency was already 10/10 zero-shot, so the
examples had nothing to fix there. They moved category and due_date instead.

### 3. Few-shot

Examples chosen, and the job each one does:

| example | why it is in the block | field it should move |
| EX-06 (window, rain on the printer) | Boundary case between facilities and hardware: a printer is mentioned but the problem is the building | category |
| EX-03 (German, 20/09/2026) | Non-English message, and shows a European date converted to 2026-09-20 | due_date |
| EX-02 (French, no date) | Shows the null convention in practice, on an urgent message in French | due_date, urgency |
| EX-04 (information only) | The only "info" example, to mark the line with "standard" | urgency |


| field | zero-shot | few-shot | move |
| category | 7/10|8/10 |+1 |
| urgency |10/10 |10/10 |0 |
| due_date |7/10 |8/10 |+1 |
| quote |10/10 |10/10 |0 |

### 4. What got worse

[Name the field, if any, and diagnose it. If nothing got worse, say so and
say how you checked. Then look at the failure lines rather than the counts,
and say whether any error disappeared or merely changed shape. A wrong label
that became a different wrong label has not been fixed.]

a. category increased from 7/10 to 8/10 and due_date from 7/10 to 8/10.
   urgency (10/10) and quote (10/10) didnt change.

b. None champ has decreased, and no invalid record.
   quote stays at 10/10, so exemples didnt broke the verbatim. 

c. Two errors disappeared, one changed form, three didn't move.

- Disappeared: REQ-04 category (zero-shot said 'access', few-shot is correct)
  and REQ-05 due_date (zero-shot invented 2024-04-30, few-shot returns None).
- Changed shape, not fixed: REQ-01 due_date. '2023-10-05' became '2023-10-04',
  but the message only says "tomorrow", so the right value is None.
- Unchanged: REQ-08 category, REQ-09 category, REQ-10 due_date.
  None of my examples targets these.

d. Je pense que nous n'avons pas assez de preuves en effet :
   Gain : +1 sur category et +1 sur due_date, sur 10 documents 
   Coût : 294 tokens en plus par appel, soit 294 000 par 1000 appels
   Ce qui me ferait changer d'avis : le même gain sur davantage de documents.

### 5. What the examples cost

- extra input tokens per call: 294
- per thousand calls: 294 000
- estimated euros per thousand calls on the small tier: 0.06, against the
  price list dated 2026-08-10. Estimate, not a measurement.

### 6. Ship it or not

[Which variant, on what evidence, and what would change your mind. Ten
records is not enough to be confident and saying so is worth more than
claiming a win. If your answer is "keep one example and drop the rest", say
which one and why.]

I would not ship the few-shot variant on this evidence. It gains 2 correct
answers out of 40 (+1 category, +1 due_date) and adds 294 input tokens per
call (total tokens over the 10 documents went from 2917 to 5805). Ten records
is too few: one record moves a field by ten points. What would change my mind:
the same gain on the larger week 10 gold set, or a single example showing a
relative date with null (targeting REQ-01 and REQ-10) that gives the gain at
a fraction of the token cost.

### Sensitivity variant

Variant assigned: reordered. What I changed: the same four examples in reverse
order, nothing else.
What moved: only due_date, from 9/10 to 7/10 (-2). category 8/10, urgency
10/10 and quote 10/10 did not move, invalid stayed at 0. Cost is unchanged
(5795 -> 5833 tokens, 88.9s -> 91.6s). By language, field errors went en 2 -> 3,
fr 1 -> 2, de 0 -> 0.
[If nothing moved, say so. A knob that changes nothing measurable is a real
result, and it tells the room which knobs are worth arguing about.]

### The gold set

Ten cases written to `artifacts/goldset.json`, tagged by language.

One thing my scorer cannot currently detect: a quote that is copied verbatim
but does not support the urgency decision. "Hello" appears in the source, so it
scores as correct although it justifies nothing. It also cannot tell a
well-formed wrong date from a right one except by comparing strings.

[This is the most valuable line on the page. An example: "our scorer cannot
tell a correctly formatted date that is simply the wrong date from a
correctly extracted one, because it only compares strings."]

### Deferred

[Anything you did not get to, and why.]
