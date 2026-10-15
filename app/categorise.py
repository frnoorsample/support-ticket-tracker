CATEGORY_KEYWORDS = {
    "account": ["password", "login", "log in", "locked", "account", "username", "reset"],
    "network": ["wifi", "wi-fi", "internet", "vpn", "network", "connection", "offline"],
    "hardware": ["laptop", "printer", "monitor", "keyboard", "mouse", "screen", "battery"],
    "software": ["install", "update", "crash", "error", "bug", "app", "excel", "outlook"],
    "billing": ["invoice", "payment", "charge", "refund", "billing", "subscription"],
}


def categorise(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    scores = {
        category: sum(keyword in text for keyword in keywords)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"