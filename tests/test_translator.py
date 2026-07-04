"""Tests for the Translator service."""

from unittest.mock import patch, MagicMock
import pytest
from app.services import Translator


class TestTranslator:
    """Test suite for the Translator service."""

    def test_translate_calls_google_translator(self):
        """Translate should delegate to GoogleTranslator with correct args."""
        with patch("app.services.translator.GoogleTranslator") as mock_gt:
            instance = mock_gt.return_value
            instance.translate.return_value = "translated text"

            result = Translator.translate("Hola", source_language="es")

            mock_gt.assert_called_once_with(source="es", target="en")
            instance.translate.assert_called_once_with("Hola")
            assert result == "translated text"

    def test_translate_default_source_language(self):
        """Translate should default source_language to 'auto'."""
        with patch("app.services.translator.GoogleTranslator") as mock_gt:
            instance = mock_gt.return_value
            instance.translate.return_value = "translated text"

            Translator.translate("Bonjour")

            mock_gt.assert_called_once_with(source="auto", target="en")

    def test_translate_raises_on_error(self):
        """Translate should propagate exceptions from GoogleTranslator."""
        with patch("app.services.translator.GoogleTranslator") as mock_gt:
            instance = mock_gt.return_value
            instance.translate.side_effect = Exception("API error")

            with pytest.raises(Exception, match="API error"):
                Translator.translate("Hola")

    def test_translate_empty_string(self):
        """Translate should handle empty strings."""
        with patch("app.services.translator.GoogleTranslator") as mock_gt:
            instance = mock_gt.return_value
            instance.translate.return_value = ""

            result = Translator.translate("")
            assert result == ""

    def test_translate_special_characters(self):
        """Translate should handle special characters."""
        with patch("app.services.translator.GoogleTranslator") as mock_gt:
            instance = mock_gt.return_value
            instance.translate.return_value = "cafe"

            result = Translator.translate("café")
            assert result == "cafe"
