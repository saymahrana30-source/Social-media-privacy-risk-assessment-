"""Strict input validation (allow-list). Anything not on the list is rejected,
so a client cannot smuggle extra personal data (e.g. "phone_number") into the app."""
from backend.questionnaire import QUESTION_BY_ID, QUESTIONS


class ValidationError(Exception):
    """Raised with a list of human-readable problems."""

    def __init__(self, problems):
        self.problems = problems if isinstance(problems, list) else [problems]
        super().__init__("; ".join(self.problems))


def normalise_answer(value):
    """'not sure' / 'Not Sure' / 'NOT_SURE' -> 'NOT_SURE'. Non-strings are rejected."""
    if not isinstance(value, str):
        return None
    return value.strip().upper().replace(" ", "_").replace("-", "_")


def validate_answers(answers, require_all=True):
    """Return a cleaned {question_id: ANSWER} dict or raise ValidationError."""
    problems = []
    if not isinstance(answers, dict):
        raise ValidationError("'answers' must be an object of question_id -> answer")
    cleaned = {}
    for qid, raw in answers.items():
        question = QUESTION_BY_ID.get(qid)
        if question is None:
            problems.append(f"Unknown question id: {str(qid)[:40]!r}")
            continue
        value = normalise_answer(raw)
        if value not in question.options:
            problems.append(f"Invalid answer for '{qid}': expected one of {question.options}")
            continue
        cleaned[qid] = value
    if require_all:
        missing = [q.id for q in QUESTIONS if q.id not in answers]
        if missing:
            problems.append(f"Missing answers for {len(missing)} question(s): {missing[:5]}{'...' if len(missing) > 5 else ''}")
    if problems:
        raise ValidationError(problems)
    return cleaned
