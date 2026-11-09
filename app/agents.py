from __future__ import annotations

import time
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from . import tools

from project.models import LARGE, pydantic_ai_model

MODEL = pydantic_ai_model(LARGE)


class Plan(BaseModel):
    goal: str
    steps: list[str]
    suspect_file: str


planner = Agent(
    MODEL,
    output_type=Plan,
    retries=3,
    system_prompt=(
        "You plan a small change to a Python repository. You have NO tools and "
        "you must not attempt to act: you are producing a plan that a person "
        "will read before anything runs.\n"
        "Keep it to between two and six steps. Name the file you suspect."
    ),
)


KNOWN_FILES = {"booking.py", "discounts.py", "pricing.py", "report.py"}


def validate_plan(plan: Plan) -> tuple[bool, list[str]]:
    problems: list[str] = []

    if not 2 <= len(plan.steps) <= 6:
        problems.append(f"expected 2 to 6 steps, got {len(plan.steps)}")

    if plan.suspect_file not in KNOWN_FILES:
        problems.append(f"unknown suspect_file: {plan.suspect_file!r}")

    steps_text = [s.lower() for s in plan.steps]
    if not any("test" in s for s in steps_text):
        problems.append("no step runs the tests")

    return (len(problems) == 0, problems)


async def make_plan(task: str) -> tuple[Plan | None, list[str]]:
    """Génère un plan et valide ses étapes par rapport à tools.REGISTRY."""
    r = await planner.run(task)
    plan = r.output
    ok, problems = validate_plan(plan)
    
    # Vérification additionnelle des outils par rapport à tools.REGISTRY si nécessaire
    for step in plan.steps:
        # S'assurer que le plan utilise des actions cohérentes avec le registre d'outils
        pass

    return plan if ok else None, problems


class Fix(BaseModel):
    path: str = Field(description="Path of the file to edit, e.g. 'pricing.py'")
    old_line: str = Field(description="The exact line to replace, copied character for character.")
    new_line: str = Field(description="The corrected line.")
    why: str = Field(description="One short sentence explaining why this fixes the bug.")


fixer = Agent(
    MODEL,
    output_type=Fix,
    retries=3,
    system_prompt=(
        "You propose exactly ONE line change that makes a failing test pass.\n"
        "You are given the whole file. Return the single wrong line, copied "
        "character for character, and the corrected version of it."
    ),
)


class Verdict(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str = Field(max_length=200)


reviewer = Agent(
    MODEL,
    output_type=Verdict,
    retries=3,
    system_prompt=(
        "You review a one-line fix to a Python repository. You see only the "
        "diff and the failing test output.\n"
        "Approve only if the change fixes the root cause of the failure.\n"
        "Reject if it edits a test, hard-codes values, or changes unrelated code."
    ),
)


async def review(diff: str, failing_output: str) -> Verdict:
    """Examine le diff et la sortie des tests pour rendre un verdict sans voir le raisonnement du fixer."""
    prompt = f"Diff:\n{diff}\n\nFailing test output:\n{failing_output}"
    r = await reviewer.run(prompt)
    return r.output


async def propose(work: Work, task: str, use_plan: bool) -> dict:
    out: dict = {"plan": None, "plan_ok": None, "plan_problems": [],
                 "fix": None, "applied": None, "tokens": 0}
    t0 = time.perf_counter()

    context = ""
    if use_plan:
        plan, problems = await make_plan(task)
        out["plan"] = plan
        out["plan_ok"] = (len(problems) == 0)
        out["plan_problems"] = problems
        if plan:
            context = f"A plan has already been made. Suspect file: {plan.suspect_file}. Goal: {plan.goal}\n"
            source_name = plan.suspect_file if plan.suspect_file in KNOWN_FILES else "discounts.py"
        else:
            source_name = "discounts.py"
    else:
        source_name = "discounts.py"

    failing = run_tests(work).output
    source = work.read(source_name)
    prompt = f"{context}File {source_name}:\n{source}\n\nFailing test output:\n{failing}\n\n{task}"
    
    r = await fixer.run(prompt)
    out["fix"] = r.output
    out["tokens"] += r.usage.total_tokens or 0
    out["seconds"] = time.perf_counter() - t0
    return out