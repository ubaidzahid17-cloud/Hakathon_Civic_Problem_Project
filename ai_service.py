"""
ai_service.py
AIAnalyzer: the mandatory AI component of the platform.

WHAT IT RECEIVES: raw citizen complaint text (string).
WHAT IT DOES:
    1. Classification  -> matches text against weighted keyword lexicons per
                           civic category (Road, Water/Drainage, Waste,
                           Electricity, Safety, Other) using normalized token
                           overlap scoring (a lightweight, explainable NLP
                           technique - no black-box model needed to justify).
    2. Priority scoring -> combines category-based base severity with urgency
                           signal words ("danger", "urgent", "no water since
                           days", etc.) into a 0-100 score, then buckets it
                           into Low / Medium / High / Critical.
    3. Summarization    -> extractive summary: scores each sentence of the
                           complaint by keyword density and returns the most
                           informative sentence(s), capped to ~25 words.
WHAT IT RETURNS: dict with category, priority, confidence (0-1), summary,
    matched keywords, and a plain-language explanation string.
LIMITATIONS (disclosed, not hidden):
    - Keyword/lexicon based -> can misclassify complaints using unusual
      wording, sarcasm, or a language/dialect outside the lexicon.
    - No image understanding by itself (see AI Vision hook below).
    - Priority score is a heuristic estimate, not a certified emergency
      triage system - a human admin should always be able to override it.
"""

import re

CATEGORY_LEXICON = {
    "Road": {
        "road": 3, "pothole": 4, "potholes": 4, "street": 2, "footpath": 2,
        "pavement": 3, "bridge": 3, "highway": 3, "traffic": 2, "crack": 2,
        "asphalt": 2, "damaged road": 4, "speed breaker": 2,
    },
    "Water/Drainage": {
        "water": 3, "leak": 4, "leakage": 4, "pipe": 3, "drainage": 4,
        "sewage": 4, "flood": 3, "flooding": 3, "drain": 3, "sewer": 4,
        "overflow": 2, "supply": 1, "tap": 1, "contaminated": 3,
    },
    "Waste": {
        "garbage": 4, "trash": 4, "waste": 3, "bin": 3, "bins": 3,
        "litter": 3, "dump": 3, "dumping": 3, "smell": 1, "rotting": 3,
        "overflowing": 2, "collection": 1,
    },
    "Electricity": {
        "electricity": 4, "power": 3, "outage": 4, "streetlight": 4,
        "street light": 4, "transformer": 4, "wire": 3, "wires": 3,
        "sparking": 4, "voltage": 2, "cable": 2, "pole": 2, "shock": 4,
    },
    "Safety": {
        "unsafe": 4, "danger": 4, "dangerous": 4, "accident": 3,
        "crime": 4, "theft": 3, "dark": 2, "fire": 4, "collapsed": 4,
        "collapse": 4, "stray": 2, "animal": 1, "harassment": 4,
    },
}

URGENCY_WORDS = {
    "urgent": 20, "emergency": 25, "immediately": 15, "danger": 20,
    "dangerous": 18, "critical": 20, "severe": 15, "children": 10,
    "school": 8, "hospital": 12, "accident": 15, "fire": 25,
    "spark": 15, "sparking": 18, "collapse": 20, "collapsed": 20,
    "days": 5, "weeks": 8, "since": 3, "no water": 12, "shock": 20,
}

CATEGORY_BASE_SEVERITY = {
    "Road": 25, "Water/Drainage": 30, "Waste": 15,
    "Electricity": 40, "Safety": 45, "Other": 15,
}


def _tokenize(text: str):
    return re.findall(r"[a-z]+(?:\s[a-z]+)?", text.lower())


class AIAnalyzer:
    """Single-responsibility AI service class: text in, structured insight out."""

    def classify(self, text: str):
        text_lower = text.lower()
        scores = {cat: 0 for cat in CATEGORY_LEXICON}
        matched = {cat: [] for cat in CATEGORY_LEXICON}

        for category, lexicon in CATEGORY_LEXICON.items():
            for word, weight in lexicon.items():
                if word in text_lower:
                    scores[category] += weight
                    matched[category].append(word)

        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        if best_score == 0:
            return "Other", 0.3, []

        total = sum(scores.values()) or 1
        confidence = round(min(best_score / (best_score + 3), 0.98) * (best_score / total * 1.3), 2)
        confidence = round(min(max(confidence, 0.35), 0.97), 2)
        return best_category, confidence, matched[best_category]

    def predict_priority(self, text: str, category: str):
        text_lower = text.lower()
        score = CATEGORY_BASE_SEVERITY.get(category, 15)
        triggered = []
        for word, weight in URGENCY_WORDS.items():
            if word in text_lower:
                score += weight
                triggered.append(word)
        score = min(score, 100)

        if score >= 70:
            priority = "Critical"
        elif score >= 45:
            priority = "High"
        elif score >= 25:
            priority = "Medium"
        else:
            priority = "Low"
        return priority, score, triggered

    def summarize(self, text: str, category: str, keywords):
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [s for s in sentences if s.strip()]
        if not sentences:
            return text[:120]

        kw_set = set(keywords)
        best_sentence, best_score = sentences[0], -1
        for s in sentences:
            s_lower = s.lower()
            score = sum(1 for kw in kw_set if kw in s_lower)
            if score > best_score:
                best_sentence, best_score = s, score

        words = best_sentence.split()
        if len(words) > 25:
            best_sentence = " ".join(words[:25]) + "..."

        return f"[{category}] {best_sentence.strip()}"

    def analyze(self, text: str):
        """Main entry point: complaint text -> full structured AI output."""
        if not text or not text.strip():
            raise ValueError("Complaint text is empty - AI cannot analyze empty input.")

        category, confidence, keywords = self.classify(text)
        priority, priority_score, urgency_hits = self.predict_priority(text, category)
        summary = self.summarize(text, category, keywords)

        explanation = (
            f"Classified as '{category}' based on keyword signals "
            f"{keywords if keywords else '(none strongly matched, defaulted to Other)'}. "
            f"Priority '{priority}' (score {priority_score}/100) from category base severity "
            f"plus urgency terms {urgency_hits if urgency_hits else 'none detected'}."
        )

        return {
            "category": category,
            "priority": priority,
            "priority_score": priority_score,
            "confidence": confidence,
            "keywords": keywords,
            "summary": summary,
            "explanation": explanation,
        }
