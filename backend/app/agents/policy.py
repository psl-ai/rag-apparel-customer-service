from __future__ import annotations


def compose_answer(intent: str, question: str, evidence: list[str], *, live_value: str | None = None) -> str:
    if intent == "inventory" and live_value is not None:
        return f"当前实时可售库存为 {live_value}。"
    if not evidence:
        return "抱歉，我目前无法确认这个问题，已为你转人工客服进一步处理。"
    source_text = "；".join(evidence[:5])
    if intent == "size":
        return f"根据商品尺码表：{source_text}。如果你愿意提供身高、体重和偏好松紧度，我可以继续帮你判断。"
    if intent == "return_policy":
        return f"根据售后政策：{source_text}。具体订单仍以实际状态和平台规则为准。"
    return f"我找到的相关信息是：{source_text}。"
