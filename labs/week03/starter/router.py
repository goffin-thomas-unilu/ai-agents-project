"""The classifier and the policy layer. TODO 2 and 3.

Two calls per request in the routed system: one to decide, one to answer.
The first is cheap and its output is inspectable. The second is the work.

The policy layer between them is about three lines of code and three design
decisions, and the decisions are where the marks are.
"""

from __future__ import annotations

import time
from typing import Literal
from openai import OpenAI
import json
from project.models import API_KEY, BASE_URL
from pydantic import BaseModel, Field, ValidationError
from queries import QUERIES
from routes import ROUTES, SPECIALISTS, SYSTEM_ROUTER
from project.models import BASE_URL, API_KEY, SMALL


class Decision(BaseModel):
    route: Literal["request", "info", "status", "complaint", "other"]
    confidence: float = Field(ge=0, le=1)
    evidence: str = Field(max_length=200)


class Routed(BaseModel):
    """What the policy layer decided, and why."""

    decision: Decision
    applied_route: str
    policy_fired: str | None = None      # None means the decision stood
    evidence_ok: bool = True


# --------------------------------------------------------------------------
# TODO 2. The classifying call.
# --------------------------------------------------------------------------

def classify(client, text: str, model: str = SMALL.name,
             temperature: float = 0.0) -> tuple[Decision | None, dict]:
    """One cheap call whose only job is to pick a route.

    Build it the same way as week 2's extractor: a schema-constrained call
    with SYSTEM_ROUTER as the system message and `text` as the user message.
    Return (Decision or None, meta), where meta carries seconds,
    prompt_tokens, completion_tokens, and the raw string.

    Return None rather than raising when validation fails. You need to be
    able to count how often that happens, and an exception is not a count.

    Note what this call does not get: no tools, no reference material, and
    no instruction about how to answer. It decides and it stops. That is
    what makes it cheap enough to be worth adding, and it is what makes its
    output inspectable.
    """
    t0 = time.perf_counter()
    
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},  # Force le modèle à sortir du JSON pur
            messages=[
                {"role": "system", "content": SYSTEM_ROUTER},
                {"role": "user", "content": text}
            ]
        )
        
        raw_text = response.choices[0].message.content.strip()
        meta = {
            "seconds": time.perf_counter() - t0,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "raw": raw_text,
        }
        
        # Nettoyage des balises markdown si présentes
        cleaned_text = raw_text
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            
        # Chargement et validation
        data = json.loads(cleaned_text)
        
        # Sécurité : troncature de l'evidence si elle dépasse 200 caractères
        if "evidence" in data and isinstance(data["evidence"], str):
            data["evidence"] = data["evidence"][:200]
            
        decision = Decision(**data)
        return decision, meta

    except Exception as e:
        return None, {
            "seconds": time.perf_counter() - t0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "raw": str(e),
        }
    raise NotImplementedError("TODO 2: the classifying call")


# --------------------------------------------------------------------------
# TODO 3. The policy layer.
# --------------------------------------------------------------------------

# TODO 3a. Pick a number, but look at the distribution before you pick it.
#
# Choosing a threshold because 0.7 sounds reasonable is the mistake this
# exercise exists to catch. Run the classifier over the twenty four queries
# first, print the confidences, and then decide. On one of the two course
# models the answer will surprise you.


CONFIDENCE_FLOOR = 0.7 # TODO 3a

# TODO 3b. Where does anything the policy rejects go?
#
# Not every route is equally safe to be wrong into. Ask what each specialist
# DOES on the sender's behalf, and pick the one whose actions are easiest to
# undo. One of the five logs a ticket, one escalates to a human, and one
# only answers. That should decide it.
SAFE_DEFAULT = 'info'          # TODO 3b


def apply_policy(decision: Decision | None, text: str) -> Routed:
    """Take a Decision and return what will actually happen.

    Three checks. Each one is a design decision that goes in DECISIONS.md
    with a reason.

    1. The call produced no valid decision at all. Rare, and it still has to
       be handled, because the alternative is a crash on the one message
       unusual enough to break the schema.

    2. The evidence check, inherited from week 2 and still free. Is the
       evidence span actually in `text`? A router that invents its
       justification is a router you cannot audit. Note that this checks
       honesty, not correctness: a route can be right with fabricated
       evidence, and that is still a defect, because the evidence is what a
       human reviewing a misroute will read.

    3. The confidence floor from TODO 3a.

    Set `policy_fired` to a short string naming which check fired, or leave
    it None when the decision stood. You will count these at the checkpoint,
    and "the policy fired sometimes" is not a count.
    """
    # 1. Pas de décision valide produite
    if decision is None:
        fallback = Decision(route=SAFE_DEFAULT, confidence=0.0, evidence="")
        return Routed(
            decision=fallback,
            applied_route=SAFE_DEFAULT,
            policy_fired="no_decision",
            evidence_ok=False,
        )

    # 2. Evidence absente du texte d'origine
    if decision.evidence not in text:
        return Routed(
            decision=decision,
            applied_route=SAFE_DEFAULT,
            policy_fired="bad_evidence",
            evidence_ok=False,
        )

    # 3. Confiance sous le seuil minimal
    if decision.confidence < CONFIDENCE_FLOOR:
        return Routed(
            decision=decision,
            applied_route=SAFE_DEFAULT,
            policy_fired="low_confidence",
            evidence_ok=True,
        )

    # Tout est OK
    return Routed(
        decision=decision,
        applied_route=decision.route,
        policy_fired=None,
        evidence_ok=True,
    )
    raise NotImplementedError("TODO 3: the policy layer")

# --------------------------------------------------------------------------
# Given. The answering call.
# --------------------------------------------------------------------------

def respond(client, system: str, text: str,
            model: str = SMALL.name) -> tuple[str, dict]:
    t0 = time.perf_counter()
    reply = client.chat.completions.create(
        model=model, temperature=0.0, max_tokens=250,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": text}])
    return reply.choices[0].message.content, {
        "seconds": time.perf_counter() - t0,
        "prompt_tokens": reply.usage.prompt_tokens,
        "completion_tokens": reply.usage.completion_tokens,
    }
from project.models import SMALL, LARGE

print("Petit modèle :", SMALL.name)
print("Grand modèle :", LARGE.name)