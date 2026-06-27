class AudioMerger:
    @staticmethod
    def merge(audio_paths: list[str], output_path: str) -> str:
        from pydub import AudioSegment

        combined = AudioSegment.empty()
        for path in audio_paths:
            segment = AudioSegment.from_file(path)
            combined += segment

        combined.export(output_path, format=output_path.split(".")[-1])
        return output_path
