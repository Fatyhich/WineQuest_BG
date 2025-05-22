import gigaam


class STTService:

    def __init__(self):
        self._model = gigaam.load_model("rnnt",
                                        device="cuda")

    def transcribe(self, audio_path: str) -> str:
        transcription = self._model.transcribe(audio_path)
        return transcription
