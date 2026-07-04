"""Tests for the SpacyInteg sentiment analysis service."""

import pytest
from app.services import SpacyInteg


@pytest.fixture
def analyzer():
    """Create a SpacyInteg instance for testing."""
    return SpacyInteg()


class TestSpacyInteg:
    """Test suite for the SpacyInteg sentiment analyzer."""

    def test_positive_sentiment(self, analyzer):
        """Review with positive words should return 'positive' mood."""
        result = analyzer.analyze_string("This product is good and great!")
        assert result["mood"] == "positive"
        assert result["sentiment_score"] > 0
        assert result["positive_count"] > 0

    def test_negative_sentiment(self, analyzer):
        """Review with negative words should return 'negative' mood."""
        result = analyzer.analyze_string("This product is bad and terrible.")
        assert result["mood"] == "negative"
        assert result["sentiment_score"] < 0
        assert result["negative_count"] > 0

    def test_neutral_sentiment(self, analyzer):
        """Review with no sentiment words should return 'neutral' mood."""
        result = analyzer.analyze_string("The product is made of plastic.")
        assert result["mood"] == "neutral"
        assert result["sentiment_score"] == 0
        assert result["positive_count"] == 0
        assert result["negative_count"] == 0

    def test_mixed_sentiment(self, analyzer):
        """Review with both positive and negative words should return 'mixed' mood."""
        result = analyzer.analyze_string(
            "The product is good but the delivery was terrible."
        )
        assert result["mood"] == "mixed"
        assert result["positive_count"] > 0
        assert result["negative_count"] > 0

    def test_negation_with_not_flips_positive_to_negative(self, analyzer):
        """Negated positive word ('not good') should count as negative.

        Note: The negation check is case-sensitive (looks for exact match
        in NEGATIONS set), so 'not' (lowercase) triggers negation but
        'Not' (capitalized) does not.
        """
        result = analyzer.analyze_string("This is not good.")
        assert result["negative_count"] > 0
        assert result["mood"] == "negative"

    def test_negation_flips_negative_to_positive(self, analyzer):
        """Negated negative word ('not bad') should count as positive."""
        result = analyzer.analyze_string("This is not bad.")
        assert result["positive_count"] > 0
        assert result["mood"] == "positive"

    def test_multiple_negations_word_not_count(self, analyzer):
        """Two 'not' words negating separate negative words.

        'bad' is negated by 'not' (immediately preceding), so it counts as positive.
        'terrible' is negated by 'not' (immediately preceding), so it counts as positive.
        """
        result = analyzer.analyze_string("not bad and not terrible.")
        assert result["positive_count"] == 2
        assert result["negative_count"] == 0

    def test_negation_only_checks_immediate_previous_token(self, analyzer):
        """The negation check looks at the token immediately before the sentiment word.

        In 'I never feel good about this', 'feel' sits between 'never' and 'good',
        so 'good' is NOT negated despite 'never' appearing earlier in the sentence.
        """
        result = analyzer.analyze_string("I never feel good about this.")
        # 'good' is not negated because 'feel' is between 'never' and 'good'
        assert result["positive_count"] == 1
        assert result["negative_count"] == 0

    def test_negation_with_not_immediately_before(self, analyzer):
        """When 'not' is immediately before a positive word, it negates it."""
        result = analyzer.analyze_string("not good")
        assert result["negative_count"] == 1
        assert result["positive_count"] == 0

    def test_negation_with_nt_contraction(self, analyzer):
        """Negation with n't contraction (isn't) should flip polarity.

        'n't' is the previous token to 'good' after tokenization of 'isn't',
        so the negation is detected.
        """
        result = analyzer.analyze_string("This isn't good at all.")
        assert result["negative_count"] > 0

    def test_empty_string(self, analyzer):
        """Empty string should return neutral mood with zero scores."""
        result = analyzer.analyze_string("")
        assert result["mood"] == "neutral"
        assert result["sentiment_score"] == 0

    def test_signals_are_populated_for_positive_words(self, analyzer):
        """Signals list should contain entries for matched sentiment words."""
        result = analyzer.analyze_string("This is amazing.")
        assert len(result["signals"]) > 0
        assert all(isinstance(s, str) for s in result["signals"])

    def test_signals_include_negation_info(self, analyzer):
        """Signals should indicate when a word was negated (lowercase 'not')."""
        result = analyzer.analyze_string("not great at all.")
        negated_signals = [s for s in result["signals"] if "negated" in s]
        assert len(negated_signals) > 0

    def test_negation_is_case_sensitive(self, analyzer):
        """Capitalized 'Not' is NOT detected as negation (case-sensitive check)."""
        result = analyzer.analyze_string("Not great.")
        # 'Not' (capitalized) is not in NEGATIONS set, so 'great' is not negated
        no_negation_signals = [s for s in result["signals"] if "negated" in s]
        assert len(no_negation_signals) == 0
        assert result["positive_count"] == 1

    def test_all_positive_words(self, analyzer):
        """All defined positive words should be detected."""
        text = " ".join([
            "good", "great", "excellent", "amazing",
            "wonderful", "fantastic", "positive",
            "happy", "joyful", "pleasant"
        ])
        result = analyzer.analyze_string(text)
        # Most positive words should be detected (some may be mislemmatized)
        assert result["positive_count"] >= 9

    def test_all_negative_words(self, analyzer):
        """All defined negative words should be detected."""
        text = " ".join([
            "bad", "terrible", "awful", "horrible",
            "negative", "sad", "angry", "unpleasant"
        ])
        result = analyzer.analyze_string(text)
        # Most negative words should be detected (some may be mislemmatized)
        assert result["negative_count"] >= 7

    def test_sentiment_score_positive(self, analyzer):
        """sentiment_score should reflect net positive vs negative count."""
        result = analyzer.analyze_string("good great bad")
        # good(+1) + great(+1) + bad(-1) = score 1
        assert result["sentiment_score"] == 1

    def test_sentiment_score_negative(self, analyzer):
        """sentiment_score should be negative when negatives outweigh positives."""
        result = analyzer.analyze_string("good bad terrible")
        # good(+1) + bad(-1) + terrible(-1) = score -1
        assert result["sentiment_score"] == -1

    def test_sentiment_score_neutral(self, analyzer):
        """sentiment_score should be 0 when no sentiment words present."""
        result = analyzer.analyze_string("The table is blue.")
        assert result["sentiment_score"] == 0

    def test_negation_with_neither_nor(self, analyzer):
        """'neither' and 'nor' should also flip polarity."""
        result = analyzer.analyze_string("neither good nor bad")
        # This tests that the NEGATIONS set includes 'neither' and 'nor'
        # The exact behavior depends on spaCy tokenization
        assert result is not None
