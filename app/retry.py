"""Stage: retries, fallback, and the degrade path. Replaced in week 8.

Until you wire yours in, there is no policy: every step is called exactly
once, nothing is retried, no fallback is tried, and an exception propagates.
That is the week 8 baseline, the run you recorded before fixing anything.

To replace it, copy your `labs/week08/starter/retry.py` and `faults.py`
into `app/`, then change the sibling import in `retry.py`:

    from faults import ContractDrift, RateLimited, ServerError, ToolTimeout
    from .faults import ContractDrift, RateLimited, ServerError, ToolTimeout

Keep these names and signatures, because `pipeline.py` calls them:

    StepPolicy, Attempt, StepResult
    is_retryable(exc) -> bool
    call_with_policy(fn, *args, policy, fallback=None, validate=None,
                     **kwargs) -> StepResult

The policies themselves live in `pipeline.py`, one per step, because the
lecture's rule is to choose them per step, in advance, by consequence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .stub import stub


import random
import time
from dataclasses import dataclass, field

from .faults import ContractDrift, RateLimited, ServerError, ToolTimeout


@dataclass
class StepPolicy:
    attempts: int = 3
    base_delay: float = 0.05
    jitter: bool = True
    max_elapsed: float = 5.0
    on_exhausted: str = "degrade"       # or "escalate"


@dataclass
class Attempt:
    n: int
    error: str | None
    slept: float = 0.0


@dataclass
class StepResult:
    value: object = None
    ok: bool = False
    attempts: list[Attempt] = field(default_factory=list)
    used_fallback: bool = False
    outcome: str = "ok"                 # ok | fallback | degraded | escalated

    @property
    def tries(self) -> int:
        return len(self.attempts)


# --------------------------------------------------------------------------
# TODO 1. Which errors deserve a second call?
# --------------------------------------------------------------------------

def is_retryable(exc: BaseException) -> bool:
    """TODO 1. Draw a line you can defend.

    Three of the exceptions in faults.py say "the upstream is having a
    moment", and a moment is exactly what a retry buys. One of them does
    not, and putting it on the wrong side of this line is the mistake this
    session exists to catch: the call SUCCEEDED, the response was valid, and
    a field had been renamed. Retrying that produces the same valid, wrong
    response as fast as the network allows, and then reports a timeout that
    never happened.

    Record in DECISIONS.md which one you excluded and why. Then consider a
    401, which is not in this lab: retrying an authentication failure turns
    a broken credential into a slow broken credential, and on some upstreams
    into a locked account.
    """
    if isinstance(exc, ContractDrift):
        return False
    return isinstance(exc, (RateLimited, ServerError, ToolTimeout))
    raise NotImplementedError("TODO 1: which errors are retryable")


# --------------------------------------------------------------------------
# TODO 2. Backoff with jitter, capped twice.
# --------------------------------------------------------------------------

def call_with_policy(fn, *args, policy: StepPolicy, fallback=None,
                     validate=None, **kwargs) -> StepResult:
    """TODO 2. Call `fn`, retrying by policy, then falling back, then degrading.

    Fill in a StepResult as you go: every attempt with its error, whether
    the fallback was used, and the final outcome. You report those counts at
    the checkpoint, and "it retried a few times" is not a count.

    Four things to get right.

    Two caps, not one. `attempts` bounds how many times you try and
    `max_elapsed` bounds how long the whole ladder may take. Without the
    second, three attempts with exponential backoff can still block a user
    for a minute.

    Exponential backoff: the delay doubles each time.

    Jitter, and it is not decoration. Ask what happens when thirty laptops
    in a room retry a rate limited endpoint at exactly the same interval.
    They re-collide, in lockstep, every time.

    `validate` runs on SUCCESS and is how contract drift is caught. It
    raises ContractDrift, which your `is_retryable` should refuse, so the
    ladder skips past retrying straight to the fallback. If you find
    yourself retrying a drifted response, TODO 1 is wrong.
    """
    result = StepResult()
    t0 = time.perf_counter()

    for n in range(1, policy.attempts + 1):
        # 1. Vérification du temps écoulé global (max_elapsed)
        if time.perf_counter() - t0 >= policy.max_elapsed:
            result.attempts.append(Attempt(n=n, error="Max elapsed time exceeded", slept=0.0))
            break

        error_msg = None
        try:
            val = fn(*args, **kwargs)
            if validate is not None:
                validate(val)
            
            # Succès !
            result.value = val
            result.ok = True
            result.outcome = "ok"
            result.attempts.append(Attempt(n=n, error=None, slept=0.0))
            return result

        except BaseException as exc:
            error_msg = str(exc)
            
            # Si l'erreur n'est pas réessayable (ex: ContractDrift), on arrête les retries immédiatement
            if not is_retryable(exc):
                result.attempts.append(Attempt(n=n, error=error_msg, slept=0.0))
                break

            if n == policy.attempts:
                result.attempts.append(Attempt(n=n, error=error_msg, slept=0.0))
                break

            # Calcul du backoff exponentiel avec jitter
            delay = policy.base_delay * (2 ** (n - 1))
            if policy.jitter:
                delay = random.uniform(0, delay)

            if time.perf_counter() - t0 + delay >= policy.max_elapsed:
                result.attempts.append(Attempt(n=n, error=error_msg, slept=0.0))
                break

            time.sleep(delay)
            result.attempts.append(Attempt(n=n, error=error_msg, slept=delay))

    # Échec des retries : tentative de fallback si disponible
    if fallback is not None:
        try:
            result.value = fallback()
            result.ok = True
            result.used_fallback = True
            result.outcome = "fallback"
            return result
        except Exception:
            pass

    # Épuisement total : application de la politique d'échec (degrade ou escalate)
    result.ok = False
    if policy.on_exhausted == "escalate":
        result.outcome = "escalated"
    else:
        result.outcome = "degraded"
    return result
    raise NotImplementedError("TODO 2: the retry ladder")
