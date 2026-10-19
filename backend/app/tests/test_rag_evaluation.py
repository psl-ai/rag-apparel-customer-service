def test_evaluation_reports_pass_rate_and_case_details():
    from app.evals.grounded import EvaluationCase, run_evaluation

    summary = run_evaluation([EvaluationCase("citation", lambda: True), EvaluationCase("refusal", lambda: False)])

    assert summary["passed"] == 1
    assert summary["total"] == 2
    assert summary["pass_rate"] == 0.5
    assert summary["cases"][1]["name"] == "refusal"


def test_rag_metric_helpers_are_available():
    from app.evals.metrics import citation_precision, groundedness, mean_reciprocal_rank, recall_at_k

    assert recall_at_k({"a", "b"}, ["x", "a", "b"], 2) == 0.5
    assert mean_reciprocal_rank({"a"}, ["x", "a"]) == 0.5
    assert citation_precision(["policy", "unknown"], {"policy"}) == 0.5
    assert groundedness("black cotton", ["black cotton fabric"]) == 1.0
