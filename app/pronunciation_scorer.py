from typing import List, Dict
import numpy as np
from phonemizer import phonemize

from app.asr_client import ASRClient


class PronunciationScorer:
    def __init__(self) -> None:
        self.asr_client = ASRClient()

    def score_audio(self, audio_path: str, reference_text: str) -> Dict:
        """
        1. Transcribe audio with Whisper.
        2. Phonemize reference text and transcript.
        3. Do a dumb positional alignment and compute per-phoneme scores.
        """

        transcript_result = self.asr_client.transcribe_file(audio_path)
        transcript_text = transcript_result.text

        # Phonemize; we keep spaces between phonemes
        reference_phonemes_str = phonemize(
            reference_text,
            language="en-us",
            backend="espeak",
            strip=True,
            preserve_punctuation=False,
            with_stress=False,
        )

        actual_phonemes_str = phonemize(
            transcript_text,
            language="en-us",
            backend="espeak",
            strip=True,
            preserve_punctuation=False,
            with_stress=False,
        )

        ref_phonemes = reference_phonemes_str.split()
        act_phonemes = actual_phonemes_str.split()

        phoneme_scores = self._align_and_score(ref_phonemes, act_phonemes)

        if phoneme_scores:
            overall_score = float(np.mean([p["score"] for p in phoneme_scores]))
        else:
            overall_score = 0.0

        return {
            "overall_score": round(overall_score, 2),
            "phoneme_scores": phoneme_scores,
            "transcript": transcript_text,
        }

    def _align_and_score(
        self, ref_phonemes: List[str], act_phonemes: List[str]
    ) -> List[Dict]:
        """
        Really simple positional scoring:
        - 100 if same phoneme at same position
        - 70 if phoneme exists somewhere else in actual
        - 30 if missing
        """

        scores: List[Dict] = []
        act_len = len(act_phonemes)

        for i, ref_ph in enumerate(ref_phonemes):
            if i < act_len and ref_ph == act_phonemes[i]:
                score = 100.0
            elif ref_ph in act_phonemes:
                score = 70.0
            else:
                score = 30.0

            scores.append(
                {
                    "phoneme": ref_ph,
                    "score": score,
                    "position": i,
                }
            )

        return scores
