import torch
import gigaam


class STTService:

    def __init__(self):
        self._model = gigaam.load_model("rnnt",
                                        device="cuda")

    def transcribe(self, audio_path: str) -> str:
        with torch.inference_mode():
            transcription = self._model.transcribe(audio_path)
        return transcription
