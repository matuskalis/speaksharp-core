from typing import List, Dict, Tuple, Optional
import numpy as np
from phonemizer import phonemize

from app.asr_client import ASRClient


# Common pronunciation issues and tips
PHONEME_TIPS = {
    "θ": "Place tongue between teeth for 'th' (think, three)",
    "ð": "Voiced 'th' - vibrate vocal cords (this, the)",
    "ɹ": "Curl tongue back without touching roof of mouth",
    "æ": "Open mouth wide, like 'a' in 'cat'",
    "ʌ": "Short 'u' sound, like 'cup' or 'but'",
    "ə": "Relax mouth for the schwa sound",
    "ŋ": "Use back of tongue for 'ng' sound",
    "w": "Round lips tightly, like blowing a candle",
    "v": "Touch lower lip to upper teeth",
    "z": "Like 's' but with voice (buzz)",
    "ʃ": "Push air through rounded lips (ship)",
    "ʒ": "Voiced 'sh' sound (measure)",
}


class PronunciationScorer:
    def __init__(self) -> None:
        self.asr_client = ASRClient()

    def score_audio(self, audio_path: str, reference_text: str) -> Dict:
        """
        Score pronunciation using word-level alignment:
        1. Transcribe audio with Whisper
        2. Align words using Levenshtein distance
        3. Score each word based on phoneme similarity
        4. Generate actionable tips for problem sounds
        """
        transcript_result = self.asr_client.transcribe_file(audio_path)
        transcript_text = transcript_result.text

        # Split into words
        ref_words = self._normalize_text(reference_text).split()
        asr_words = self._normalize_text(transcript_text).split()

        # Align words using edit distance
        word_alignments = self._align_words(ref_words, asr_words)

        # Score each word
        word_scores = []
        problem_sounds = set()

        for ref_word, asr_word in word_alignments:
            word_result = self._score_word(ref_word, asr_word)
            word_scores.append(word_result)

            # Track problem phonemes
            if word_result["status"] != "good":
                for phoneme in word_result.get("problem_phonemes", []):
                    problem_sounds.add(phoneme)

        # Calculate overall score
        if word_scores:
            overall_score = np.mean([w["score"] for w in word_scores])
        else:
            overall_score = 0.0

        # Generate tips for problem sounds
        tips = self._generate_tips(problem_sounds)

        return {
            "overall_score": round(overall_score, 1),
            "word_scores": word_scores,
            "problem_sounds": list(problem_sounds)[:5],  # Top 5
            "tips": tips[:3],  # Top 3 tips
            "transcript": transcript_text,
            "reference": reference_text,
        }

    def _normalize_text(self, text: str) -> str:
        """Remove punctuation and normalize for comparison."""
        import re
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        return " ".join(text.split())

    def _align_words(
        self, ref_words: List[str], asr_words: List[str]
    ) -> List[Tuple[str, Optional[str]]]:
        """
        Align reference words to ASR words using dynamic programming.
        Returns list of (reference_word, matched_asr_word or None).
        """
        if not ref_words:
            return []
        if not asr_words:
            return [(w, None) for w in ref_words]

        # Create alignment using edit distance
        m, n = len(ref_words), len(asr_words)

        # dp[i][j] = (cost, alignment_type)
        # alignment_type: 'M' match, 'I' insert, 'D' delete, 'S' substitute
        INF = float('inf')
        dp = [[INF] * (n + 1) for _ in range(m + 1)]
        dp[0][0] = 0

        # Fill first row (deletions from ASR)
        for j in range(1, n + 1):
            dp[0][j] = j

        # Fill first column (reference words not found)
        for i in range(1, m + 1):
            dp[i][0] = i

        # Fill rest of table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                ref_w = ref_words[i - 1]
                asr_w = asr_words[j - 1]

                # Match/substitute cost based on word similarity
                if ref_w == asr_w:
                    match_cost = 0
                else:
                    # Use character-level edit distance for similar words
                    similarity = self._word_similarity(ref_w, asr_w)
                    match_cost = 1 - similarity

                dp[i][j] = min(
                    dp[i - 1][j - 1] + match_cost,  # match/substitute
                    dp[i - 1][j] + 1,  # ref word not matched
                    dp[i][j - 1] + 1,  # extra ASR word
                )

        # Backtrack to find alignment
        alignments = []
        i, j = m, n
        while i > 0 or j > 0:
            if i > 0 and j > 0:
                ref_w = ref_words[i - 1]
                asr_w = asr_words[j - 1]

                if ref_w == asr_w:
                    match_cost = 0
                else:
                    similarity = self._word_similarity(ref_w, asr_w)
                    match_cost = 1 - similarity

                if dp[i][j] == dp[i - 1][j - 1] + match_cost:
                    # Match or substitution - pair them
                    alignments.append((ref_w, asr_w))
                    i -= 1
                    j -= 1
                elif dp[i][j] == dp[i - 1][j] + 1:
                    # Reference word not found in ASR
                    alignments.append((ref_w, None))
                    i -= 1
                else:
                    # Extra word in ASR, skip it
                    j -= 1
            elif i > 0:
                alignments.append((ref_words[i - 1], None))
                i -= 1
            else:
                j -= 1

        return list(reversed(alignments))

    def _word_similarity(self, word1: str, word2: str) -> float:
        """Calculate similarity between two words (0-1)."""
        if word1 == word2:
            return 1.0

        # Levenshtein distance
        m, n = len(word1), len(word2)
        if m == 0:
            return 0.0
        if n == 0:
            return 0.0

        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if word1[i - 1] == word2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],
                        dp[i][j - 1],
                        dp[i - 1][j - 1]
                    )

        max_len = max(m, n)
        return 1 - (dp[m][n] / max_len)

    def _score_word(self, ref_word: str, asr_word: Optional[str]) -> Dict:
        """
        Score a single word by comparing phonemes.
        Returns word score with status and problem phonemes.
        """
        if asr_word is None:
            return {
                "word": ref_word,
                "score": 0,
                "status": "missing",
                "tip": f"Word '{ref_word}' was not detected",
                "problem_phonemes": [],
            }

        # Get phonemes for both words
        ref_phonemes = self._get_phonemes(ref_word)
        asr_phonemes = self._get_phonemes(asr_word)

        if ref_word == asr_word:
            return {
                "word": ref_word,
                "score": 100,
                "status": "good",
                "problem_phonemes": [],
            }

        # Compare phonemes using edit distance
        score, problem_phonemes = self._compare_phonemes(ref_phonemes, asr_phonemes)

        # Determine status
        if score >= 80:
            status = "good"
        elif score >= 60:
            status = "needs_work"
        else:
            status = "focus"

        result = {
            "word": ref_word,
            "score": round(score, 1),
            "status": status,
            "problem_phonemes": problem_phonemes[:3],  # Top 3
        }

        # Add tip for the first problem phoneme
        if problem_phonemes:
            first_problem = problem_phonemes[0]
            if first_problem in PHONEME_TIPS:
                result["tip"] = PHONEME_TIPS[first_problem]

        return result

    def _get_phonemes(self, word: str) -> List[str]:
        """Get phoneme list for a word."""
        try:
            phoneme_str = phonemize(
                word,
                language="en-us",
                backend="espeak",
                strip=True,
                preserve_punctuation=False,
                with_stress=False,
            )
            # Split by whitespace and filter empty
            return [p for p in phoneme_str.split() if p]
        except Exception:
            return list(word)  # Fallback to characters

    def _compare_phonemes(
        self, ref_phonemes: List[str], asr_phonemes: List[str]
    ) -> Tuple[float, List[str]]:
        """
        Compare phoneme sequences and identify problems.
        Returns (score 0-100, list of problem phonemes).
        """
        if not ref_phonemes:
            return 100.0, []
        if not asr_phonemes:
            return 0.0, ref_phonemes

        # Use edit distance to align phonemes
        m, n = len(ref_phonemes), len(asr_phonemes)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ref_phonemes[i - 1] == asr_phonemes[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    # Check for similar phonemes
                    if self._phonemes_similar(ref_phonemes[i - 1], asr_phonemes[j - 1]):
                        dp[i][j] = dp[i - 1][j - 1] + 0.5
                    else:
                        dp[i][j] = 1 + min(
                            dp[i - 1][j],
                            dp[i][j - 1],
                            dp[i - 1][j - 1]
                        )

        # Score based on edit distance
        edit_distance = dp[m][n]
        max_len = max(m, n)
        score = max(0, 100 * (1 - edit_distance / max_len))

        # Identify problem phonemes by backtracking
        problem_phonemes = []
        i, j = m, n
        while i > 0 and j > 0:
            if ref_phonemes[i - 1] == asr_phonemes[j - 1]:
                i -= 1
                j -= 1
            elif self._phonemes_similar(ref_phonemes[i - 1], asr_phonemes[j - 1]):
                i -= 1
                j -= 1
            else:
                # Mismatch - add to problems
                problem_phonemes.append(ref_phonemes[i - 1])
                if dp[i][j] == dp[i - 1][j - 1] + 1:
                    i -= 1
                    j -= 1
                elif dp[i][j] == dp[i - 1][j] + 1:
                    i -= 1
                else:
                    j -= 1

        # Add remaining reference phonemes as problems
        while i > 0:
            problem_phonemes.append(ref_phonemes[i - 1])
            i -= 1

        return score, list(reversed(problem_phonemes))

    def _phonemes_similar(self, p1: str, p2: str) -> bool:
        """Check if two phonemes are acoustically similar."""
        # Groups of similar phonemes
        similar_groups = [
            {"p", "b"},
            {"t", "d"},
            {"k", "g"},
            {"f", "v"},
            {"s", "z"},
            {"θ", "ð"},
            {"ʃ", "ʒ"},
            {"m", "n", "ŋ"},
            {"i", "ɪ"},
            {"e", "ɛ"},
            {"æ", "ɛ"},
            {"u", "ʊ"},
            {"o", "ɔ"},
            {"ʌ", "ə"},
        ]

        for group in similar_groups:
            if p1 in group and p2 in group:
                return True
        return False

    def _generate_tips(self, problem_sounds: set) -> List[str]:
        """Generate pronunciation tips for problem sounds."""
        tips = []
        for sound in problem_sounds:
            if sound in PHONEME_TIPS:
                tips.append(f"Practice '{sound}': {PHONEME_TIPS[sound]}")

        if not tips and problem_sounds:
            tips.append("Practice speaking slowly and clearly")

        return tips
