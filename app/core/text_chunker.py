import re

from app.core.config import config
from app.utils.logging import logger


class TextChunker:
    MAX_CHARS_DEFAULT = 4000

    def __init__(self, chunk_limits: dict[str, int] | None = None):
        self.chunk_limits = chunk_limits or config.chunk_limits or {}

    def split(self, text: str, provider_id: str | None = None) -> list[str]:
        max_chars = self.chunk_limits.get(provider_id, self.MAX_CHARS_DEFAULT) if provider_id else self.MAX_CHARS_DEFAULT
        text = text.strip()
        if not text:
            return []

        if len(text) <= max_chars:
            return [text]

        chunks = []
        paragraphs = text.split("\n\n")

        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= max_chars:
                current_chunk = (current_chunk + "\n\n" + para).strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para

                if len(current_chunk) > max_chars:
                    sentences = re.split(r"(?<=[.!?])\s+", current_chunk)
                    current_chunk = ""
                    for sent in sentences:
                        if len(current_chunk) + len(sent) + 1 <= max_chars:
                            current_chunk = (current_chunk + " " + sent).strip()
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sent

                            if len(current_chunk) > max_chars:
                                clauses = re.split(r"(?<=[,;])\s+", current_chunk)
                                current_chunk = ""
                                for clause in clauses:
                                    if len(current_chunk) + len(clause) + 1 <= max_chars:
                                        current_chunk = (current_chunk + " " + clause).strip()
                                    else:
                                        if current_chunk:
                                            chunks.append(current_chunk)
                                        # Hard split clause if still too long
                                        while len(clause) > max_chars:
                                            chunks.append(clause[:max_chars])
                                            clause = clause[max_chars:]
                                        current_chunk = clause
                                if current_chunk:
                                    chunks.append(current_chunk)
                                    current_chunk = ""

        if current_chunk:
            chunks.append(current_chunk)

        logger.info(f"Split text into {len(chunks)} chunks (max {max_chars} chars each)")
        return chunks
