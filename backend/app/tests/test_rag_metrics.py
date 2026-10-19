def test_rag_metrics_are_deterministic():
    from app.evals.metrics import citation_precision, groundedness, mean_reciprocal_rank, recall_at_k

    assert recall_at_k({"a", "b"}, ["x", "a", "b"], 2) == 0.5
    assert mean_reciprocal_rank({"a"}, ["x", "a"]) == 0.5
    assert citation_precision(["policy", "unknown"], {"policy"}) == 0.5
    assert groundedness("black cotton", ["black cotton fabric"]) == 1.0
