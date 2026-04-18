def analyze_emotion(text: str) -> dict:
    keywords = {
        "开心": "positive",
        "高兴": "positive",
        "难过": "negative",
        "焦虑": "negative",
        "生气": "negative",
    }
    for word, emotion in keywords.items():
        if word in text:
            return {"emotion": emotion, "keyword": word}
    return {"emotion": "neutral", "keyword": ""}
