"""Stage: the human approval gate. Replaced in week 8.

Week 8 gates exactly one step, the irreversible one, with a LangGraph
`interrupt` and a checkpoint that a second process resumes. In this
application the irreversible step is submitting a case, and it reaches the
gate through one function:

    request_approval(payload: dict, unattended: bool) -> dict

`payload` has the shape of week 8's interrupt: `action`, `case_id`,
`arguments` (the exact arguments, never a summary a model wrote),
`evidence`, `degraded`, and `missing`. The return value has the shape of
week 8's resume value: `verdict` ("approve", "edit", "reject", or
"timeout"), `by`, and, for an edit, the edited `arguments`.

`unattended` is True in batch mode, which is how week 10 runs the
application. Nobody is there to answer, so your gate must return what week
8 decided an unanswered approval does after its timeout, immediately,
instead of waiting for a human who is not coming.

Until you wire yours in, the gate refuses every submission. That is the
safe default for a stub, and it means nothing irreversible can happen.

This is a stage you write rather than copy, because week 8's graph runs over
its own toy tools. Take your `submit` node from `labs/week08/starter/graph.py`
with its `interrupt` call, give it a small graph and a `SqliteSaver` of its
own, and write `request_approval` around it. Keep week 8's rule: above the
interrupt, read only.
"""

from __future__ import annotations

from .stub import stub


from typing import Annotated, TypedDict

from .faults import ContractDrift, FaultPlan
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from .retry import StepPolicy, call_with_policy

from . import tools


def append(a: list, b: list) -> list:
    return a + b


class CaseState(TypedDict):
    case_id: str
    topic: str
    passages: list[str]
    fee: dict
    draft: str
    submitted: bool
    decision: str
    degraded: bool
    missing: Annotated[list[str], append]
    events: Annotated[list[str], append]
    side_effects: Annotated[list[str], append]


SEARCH_POLICY = StepPolicy(attempts=3, base_delay=0.05, jitter=True,
                           max_elapsed=3.0, on_exhausted="degrade")
FEES_POLICY = StepPolicy(attempts=3, base_delay=0.05, jitter=True,
                         max_elapsed=3.0, on_exhausted="degrade")


def validate_fee(value) -> None:
    """TODO 4. Where contract drift is caught.

    Drift is the fault no retry fixes, because the call succeeded. The only
    thing that catches it is a check on the SHAPE of what came back, run on
    the success path. If you have no validation, a renamed field flows all
    the way to the answer and the run reports success.
    """
    if not isinstance(value, dict):
        raise ContractDrift("Fee response must be a dictionary")
    if "amount" not in value and "fee_amount" in value:
        # Exemple de détection de dérive de contrat (champ renommé)
        raise ContractDrift("Contract drift: 'amount' field was renamed to 'fee_amount'")
    if "amount" not in value:
        raise ContractDrift("Missing required 'amount' field in fee response")
    raise NotImplementedError("TODO 4: validate the fee contract")


# --------------------------------------------------------------------------
# TODO 3. The nodes, each with its own policy.
# --------------------------------------------------------------------------

def gather(state: CaseState, plan: FaultPlan) -> dict:
    """TODO 3a. Search, with retries and a fallback.

    Three cases, and the middle one is the interesting one:

      the call failed after everything    -> degraded, say search is down
      the call SUCCEEDED and returned []  -> decide, and be able to defend it
      the call succeeded with passages    -> note if the fallback was used

    An empty result is not an error and it is not a success either. It is
    the tool saying it does not cover this. Treating it as a success is how
    a pipeline answers a question from nothing.

    Record what is absent in `missing` so `draft` can say it out loud, and
    append to `events` so the checkpoint has something to count.
    """
    from .retry import call_with_policy
    
    query = state.get("topic", "")
    
    # Fonction exécutée avec la politique de retry
    def do_search():
        # Utilisation de la table/plan de pannes injectée ou de l'outil de recherche
        return tools.search(query, plan=plan)

    fallback_fn = lambda: [] # Fallback renvoyant une liste vide
    
    res = call_with_policy(do_search, policy=SEARCH_POLICY, fallback=fallback_fn)
    
    passages = []
    missing = []
    events = [f"gather:outcome={res.outcome}"]
    degraded = False

    if res.ok:
        passages = res.value if isinstance(res.value, list) else [str(res.value)]
        if not passages:
            missing.append("No relevant passages found in documentation.")
    else:
        degraded = True
        missing.append("Search service unavailable (degraded mode).")

    return {
        "passages": passages,
        "missing": missing,
        "events": events,
        "degraded": degraded
    }
    raise NotImplementedError("TODO 3a: gather with a policy")


def price(state: CaseState, plan: FaultPlan) -> dict:
    """TODO 3b. The fee lookup, passing `validate_fee` to the policy.

    This is the step contract drift hits. Without a validator the renamed
    field flows into the answer and the run reports success.
    """
    from .retry import call_with_policy
    
    case_id = state.get("case_id", "")

    def do_price():
        return tools.get_fee(case_id, plan=plan)

    fallback_fn = lambda: {"amount": 0, "currency": "EUR", "note": "fallback fee"}

    res = call_with_policy(
        do_price, 
        policy=FEES_POLICY, 
        fallback=fallback_fn, 
        validate=validate_fee
    )

    fee_data = res.value if res.ok else fallback_fn()
    events = [f"price:outcome={res.outcome}"]

    return {
        "fee": fee_data,
        "events": events
    }
    raise NotImplementedError("TODO 3b: price with validation")

def request_approval(state: CaseState) -> dict:
    """Alias pour la fonction submit attendue par le pipeline global."""
    return submit(state)

def draft(state: CaseState) -> dict:
    """TODO 5. The goal predicate, and what a partial answer says.

    A degraded answer must name what is missing IN THE TEXT THE USER READS.
    An answer that quietly omits the fee is indistinguishable from one where
    there was no fee, and the reader has no way to know which they got.

    A degrade path that returns an empty string is technically graceful and
    completely useless.
    """
    topic = state.get("topic", "")
    passages = state.get("passages", [])
    fee = state.get("fee", {})
    missing = state.get("missing", [])
    
    # Construction du corps de la réponse
    lines = [f"Response regarding: {topic}\n"]
    
    if passages:
        lines.append("Found relevant information:")
        for p in passages:
            lines.append(f"- {p}")
    else:
        lines.append("No documentation passages could be retrieved.")
        
    if fee:
        amount = fee.get("amount", fee.get("fee_amount", 0))
        currency = fee.get("currency", "EUR")
        lines.append(f"\nAssociated fee: {amount} {currency}")
    
    # Si des éléments sont manquants (mode dégradé), on les liste clairement
    if missing:
        lines.append("\n[WARNING: Response is partial / degraded]")
        lines.append("The following components could not be retrieved:")
        for m in missing:
            lines.append(f"- {m}")
            
    draft_text = "\n".join(lines)
    return {"draft": draft_text}
    raise NotImplementedError(
        "TODO 5: assemble the answer and name what is missing")


def submit(state: CaseState) -> dict:
    """The gated step. Exactly one, chosen by consequence.

    Everything above the interrupt runs AGAIN on resume, because the node
    re-executes from its first line. Put nothing here that writes.

    And the part the state will not show you: the first execution never
    returns, so its return value is discarded while whatever it did to the
    outside world is not. A write above this line happens twice and appears
    once. `02_gate.py` demonstrates it.
    """
    decision = interrupt({
        "action": "submit_case",
        "case_id": state["case_id"],
        # The exact arguments, not a summary the model wrote. The model
        # whose judgment you are checking would also be writing the account
        # of it.
        "arguments": {"topic": state["topic"], "fee": state.get("fee", {})},
        "evidence": state.get("passages", []),
        "degraded": state.get("degraded", False),
        "missing": sorted(set(state.get("missing", []))),
    })

    verdict = decision.get("verdict")
    if verdict == "approve":
        return {"submitted": True, "decision": "approve",
                "side_effects": [f"SUBMITTED {state['case_id']}"],
                "events": [f"gate:approve:{decision.get('by', '?')}"]}
    if verdict == "edit":
        edited = decision.get("arguments", {})
        return {"submitted": True, "decision": "edit",
                "fee": edited.get("fee", state.get("fee", {})),
                "side_effects": [f"SUBMITTED {state['case_id']} (edited)"],
                "events": [f"gate:edit:{decision.get('by', '?')}"]}
    return {"submitted": False, "decision": verdict or "reject",
            "events": [f"gate:{verdict or 'reject'}:"
                       f"{decision.get('by', '?')}"]}


def build(plan: FaultPlan, saver):
    graph = StateGraph(CaseState)
    graph.add_node("gather", lambda s: gather(s, plan))
    graph.add_node("price", lambda s: price(s, plan))
    graph.add_node("draft", draft)
    graph.add_node("submit", submit)
    graph.add_edge(START, "gather")
    graph.add_edge("gather", "price")
    graph.add_edge("price", "draft")
    graph.add_edge("draft", "submit")
    graph.add_edge("submit", END)
    return graph.compile(checkpointer=saver)


def initial(case_id: str, topic: str) -> CaseState:
    return {"case_id": case_id, "topic": topic, "passages": [], "fee": {},
            "draft": "", "submitted": False, "decision": "",
            "degraded": False, "missing": [], "events": [],
            "side_effects": []}
