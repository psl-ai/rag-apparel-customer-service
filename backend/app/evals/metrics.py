from collections.abc import Sequence


def recall_at_k(relevant: set[str], retrieved: Sequence[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(relevant.intersection(retrieved[:k])) / len(relevant)


def mean_reciprocal_rank(relevant: set[str], retrieved: Sequence[str]) -> float:
    for index, item in enumerate(retrieved, 1):
        if item in relevant:
            return 1.0 / index
    return 0.0


def citation_precision(answer_citations: Sequence[str], supported_citations: set[str]) -> float:
    if not answer_citations:
        return 0.0
    return sum(item in supported_citations for item in answer_citations) / len(answer_citations)


def groundedness(answer: str, evidence: Sequence[str]) -> float:
    if not answer.strip() or not evidence:
        return 0.0
    answer_tokens = set(answer.lower().split())
    evidence_tokens = set(" ".join(evidence).lower().split())
    return len(answer_tokens & evidence_tokens) / max(len(answer_tokens), 1)
