def test_policy_answer_requires_citation_and_refuses_missing_evidence():
    from app.agents.policy import compose_answer

    cited = compose_answer("return_policy", "退换货", ["policy.md § 退换货: 7天内可退换"])
    refused = compose_answer("return_policy", "退换货", [])

    assert "policy.md" in cited
    assert "无法确认" in refused
