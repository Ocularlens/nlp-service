from collections import defaultdict

import spacy

POSITIVE_WORDS = {
  'good', 'great', 'excellent', 'amazing', 
  'wonderful', 'fantastic', 'positive', 
  'happy', 'joyful', 'pleasant'
}

NEGATIVE_WORDS = {
  'bad', 'terrible', 'awful', 'horrible',
  'negative', 'sad', 'angry', 'unpleasant'
}

NEGATIONS = {"not", "never", "no", "n't", "neither", "nor"}

class SpacyInteg:
  def __init__(self):
    self.nlp = spacy.load("en_core_web_sm")

  def analyze_string(self, text: str) -> dict:
    doc = self.nlp(text)
    
    scores = defaultdict(int)
    signals = []

    for token in doc:
        # check if previous token is a negation
        negated = any(t.text in NEGATIONS for t in token.lefts) or \
                  (token.i > 0 and doc[token.i - 1].text in NEGATIONS)

        word = token.lemma_

        if word in POSITIVE_WORDS:
            if negated:
                scores["negative"] += 1
                signals.append(f"negated positive: '{token.text}'")
            else:
                scores["positive"] += 1
                signals.append(f"positive: '{token.text}'")

        elif word in NEGATIVE_WORDS:
            if negated:
                scores["positive"] += 1
                signals.append(f"negated negative: '{token.text}'")
            else:
                scores["negative"] += 1
                signals.append(f"negative: '{token.text}'")

    total = scores["positive"] + scores["negative"]

    if total == 0:
        mood = "neutral"
    elif scores["positive"] > 0 and scores["negative"] > 0:
        mood = "mixed"
    elif scores["positive"] > scores["negative"]:
        mood = "positive"
    else:
        mood = "negative"

    return {
        "mood": mood,
        "positive_count": scores["positive"],
        "negative_count": scores["negative"],
        "signals": signals,
    }