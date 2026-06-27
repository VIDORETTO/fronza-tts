import json
import uuid
from datetime import datetime
from pathlib import Path

from app.core.config import config
from app.utils.file_utils import ensure_dir, save_json_metadata
from app.utils.logging import logger


class AudioStorage:
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or config.app.audio_output_dir)

    def save_audio(self, audio_data: bytes, format: str = "mp3", metadata: dict | None = None) -> str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        day_dir = self.base_dir / date_str
        ensure_dir(day_dir)

        generation_id = str(uuid.uuid4())
        ext = format.lower().replace("audio/", "")
        file_path = day_dir / f"{generation_id}.{ext}"

        file_path.write_bytes(audio_data)

        if metadata:
            meta_path = day_dir / f"{generation_id}.json"
            save_json_metadata(meta_path, {
                **metadata,
                "generation_id": generation_id,
                "file_path": str(file_path),
                "created_at": datetime.utcnow().isoformat(),
            })

        logger.info(f"Audio saved: {file_path}")
        return str(file_path)

    def get_audio_path(self, generation_id: str) -> Path | None:
        for day_dir in self.base_dir.iterdir():
            if day_dir.is_dir():
                for f in day_dir.iterdir():
                    if f.stem == generation_id and f.suffix != ".json":
                        return f
        return None

    def delete_audio(self, generation_id: str) -> bool:
        path = self.get_audio_path(generation_id)
        if path:
            path.unlink()
            meta = path.with_suffix(".json")
            if meta.exists():
                meta.unlink()
            return True
        return False
