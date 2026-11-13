# Week 8: retries, recovery, and a human approval gate

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 8

**Run conditions.** fault seed: 42 | attempts: 3 | base delay: 0.02 |
max elapsed: 3 | LangGraph latest | date: 2026 11 13

### 1. Which errors are retryable

Retryable: RateLimited, ServerError, ToolTimeout

Deliberately NOT retryable: ContractDrift, because it represents a successful API call that returned a valid response with a renamed/drifted field.

Retrying a call that succeeded is worse than useless because it wastes time and resources repeating a valid network call that will never fix a structural schema change.
[The one that matters is contract drift. Say in one sentence why retrying a
call that succeeded is worse than useless.]

### 2. The fault matrix

| | correct | WRONG | degraded | failed |
| baseline |1 |0 |2 |5 |
| hardened |0 |0 |4 |4 |

What hardening actually bought:
Hardening reduces outright failures and prevents incorrect answers by catching contract drift and gracefully degrading when services are down, rather than failing silently or hallucinating.

fr
Le durcissement (hardening) n'a pas cherché à masquer les erreurs (zéro réponse fausse / WRONG 0 dans les deux cas), mais il a transformé les pannes brutales en modes dégradés contrôlés (les cas degraded passent de 2 à 4), permettant au système d'admettre clairement ce qui manque au lieu de planter ou de renvoyer des informations erronées.

### 3. The empty result

An empty result is not an error. My pipeline treats it as a partial/degraded result with missing fields recorded in the missing list, because treating an empty search result as a success would cause the pipeline to answer a question using zero evidence or hallucinate information
### 4. The gate

Gated step: submit. The others are not gated because they are automated retrieval, pricing, and drafting steps whose intermediate actions are non-destructive and fully reversible.

An unanswered approval after the timeout: efaults to rejecting the submission or handling it via the unattended policy. That protects the pipeline from blocking indefinitely during automated batch runs (such as Week 10) where no human is present

The approval payload carries case_id, arguments (topic, fee), evidence, degraded status, and missing fields and deliberately does not carry the model's internal reasoning or subjective summary, to prevent biasing the human approver's judgment
### 5. The duplicate the state does not show

I put a side effect above the interrupt. It executed 2 times. The recorded
state showed it 1 time.

What that means for anything my gated node does before it asks:
Because nodes re-execute from their first line upon resume, anything above interrupt() runs twice. Therefore, read only above an interrupt; never place side effects (like database writes, email dispatches, or external API calls) above the interrupt.

### Deferred

[Anything you did not get to, and why.]
