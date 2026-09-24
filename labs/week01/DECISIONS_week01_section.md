# Week 1: the stack, the first call, and what it costs

Copy this into your `DECISIONS.md` and fill it in. Keep the headings. In
week 13 this becomes a section of your project report that you do not have
to write.

---

## Week 1

**Run conditions.** Everything below was produced on:
HP Laptop 15s-fq5xxx
Type du système:                            x64-based PC
Processeur(s):                              1 processeur(s) installé(s).
                                            [01] : Intel64 Family 6 Model 154 Stepping 4 GenuineIntel ~1300 MHz
- machine: [HP ,HP Laptop 15s-fq5xxx, 16go DDR4]
- model: [
    qwen2.5:7b                 845dbda0ea48    4.7 GB    35 hours ago    
    nomic-embed-text:latest    0a109f422b47    274 MB    35 hours ago    
    qwen3:4b-instruct          0edcdef34593    2.5 GB    35 hours ago
    ]
- served by: Ollama, one request at a time, locally
- date: [17/09/2026]

Every number in this file is meaningless without those four lines, so they
are stated once here and referred to rather than repeated.

### 1. Machine and model set

I am running the [required] model set.

[If you could not run the optional models, say so and say what you will do
before week 9. This is a constraint on your project, not a failure, and
naming it now is worth more than discovering it in week 9.]

### 2. The first call

| | |
| finish reason | stop |
| prompt tokens | 24 |
| completion tokens | 49 |
| elapsed | 8.5 |

One sentence on the finish reason: what my program would do differently if
it came back as a truncation rather than a normal stop.

--> It would be 'length' to signify that the model reach the max token output inserted as parameters

[...]

### 3. Variance

| cell | distinct (recording) | distinct (mine) | median latency |
| closed_short, t=0.0 | 1/12 |1/6 |0.31 |
| closed_short, t=1.0 | 1/12 |1/6 |0.26 |
| open_list, t=0.0 | 1/12 |1/6 |4.30 |
| open_list, t=1.0 | 11/12 |6/6 |3.78 |

Which cell still returns a single answer at temperature 1.0, and why that
one: it is the closed_short because the model focus on a single answer so this answer has a very high probability compare to other even if the model has a high level of creativity

[...]

Which cells a test asserting exact string equality would pass on, and what
that tells me about testing this system:
It would pass on closed_short because the result remains the same at each execution, but will fail for open_list with temp=1
So a test asserting exact string equality does not depend on the temperature but maybe on the question 

[...]

**The sentence that carries into week 10.** [One sentence about when you can
and cannot rely on repeating an output. Week 10 will ask you to find this
again. It should not say "the model is random", because your own table shows
otherwise in most cells.]

### 4. The cold start

- cold call: 6.245 s
- warm call: 0.332 s
- ratio: 18.776

What this implies for a system that uses more than one model, and what I
will do about it:
This can imply that maybe there will be a cold start when I want to use an other model and return to the original because this will at each time free the memory of the model and so the response time will be much larger than usual with only one model or just keep multiple models running in RAM
[...]

### 5. Cost, estimated

A 200-case golden set, at the token cost of my long case:

| | one run | nightly for the semester |
| small tier |0.0335 |0 |
| large tier |2.4912 |28 |

Estimates against the price list dated [date in `project/prices.py`], not
measurements. Running locally, my actual monetary cost was zero.

Which tier I would run nightly, which I would run before a release, and why
not the same one for both:
I would run the small one nightly and the large one before a release and not the same for both situation because we could either have no real results/ undetailed results or paid for too much even if we ask a simple thing, this will cost way more with the large than the small
[...]

### Deferred

[Anything you did not get to, and why. An explicit deferral with a reason is
engineering. Silence is not, and the project rubric can tell the
difference.]
