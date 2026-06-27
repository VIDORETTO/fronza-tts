import pytest
from app.core.text_chunker import TextChunker


class TestTextChunker:
    def setup_method(self):
        self.chunker = TextChunker()

    def test_empty_text(self):
        assert self.chunker.split("") == []
        assert self.chunker.split("   ") == []

    def test_short_text(self):
        result = self.chunker.split("Hello world", provider_id="elevenlabs")
        assert result == ["Hello world"]

    def test_splits_by_paragraph(self):
        text = "A" * 3000 + "\n\n" + "B" * 3000
        result = self.chunker.split(text, provider_id="elevenlabs")
        assert len(result) >= 2
        assert all(len(c) <= 4000 for c in result)

    def test_respects_provider_limit(self):
        text = "A" * 2500 + "\n\n" + "B" * 2500
        result = self.chunker.split(text, provider_id="inworld")
        assert len(result) >= 2
        assert all(len(c) <= 2000 for c in result)

    def test_custom_limit(self):
        chunker = TextChunker({"custom": 100})
        result = chunker.split("A" * 250, provider_id="custom")
        assert len(result) >= 2
        assert all(len(c) <= 100 for c in result)
