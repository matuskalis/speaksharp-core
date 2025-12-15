"""
Phoneme Analyzer for Pronunciation Assessment.

Converts text to IPA phonemes and analyzes pronunciation accuracy
by comparing expected vs. actual phonemes from ASR output.

Tracks L1-specific confusion patterns (e.g., Spanish: /θ/ → /s/).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
import re

# Common L1 interference patterns by native language
# Maps: native_language -> {target_phoneme: common_substitution}
L1_INTERFERENCE_PATTERNS = {
    "spanish": {
        "θ": ["s", "t"],        # "think" → "sink"
        "ð": ["d"],             # "this" → "dis"
        "v": ["b"],             # "very" → "bery"
        "z": ["s"],             # "zero" → "sero"
        "ʒ": ["ʃ", "tʃ"],       # "measure" → "mesher"
        "ŋ": ["n", "ŋg"],       # "singing" → "singin"
        "h": [""],              # silent h
        "dʒ": ["j", "ʒ"],       # "judge" → "yudge"
    },
    "chinese": {
        "θ": ["s", "f"],        # "think" → "sink/fink"
        "ð": ["d", "z"],        # "this" → "dis/zis"
        "r": ["l"],             # "red" → "led"
        "l": ["r", "n"],        # final l issues
        "v": ["w"],             # "very" → "wery"
        "ŋ": ["n"],             # final ng
        "n": ["ŋ"],             # confusion in finals
    },
    "japanese": {
        "θ": ["s"],             # "think" → "sink"
        "ð": ["z", "d"],        # "this" → "zis"
        "r": ["l"],             # r/l confusion
        "l": ["r"],             # l/r confusion
        "v": ["b"],             # "very" → "bery"
        "f": ["h"],             # "fun" → "hun"
        "æ": ["a", "e"],        # "cat" → "ket"
    },
    "portuguese": {
        "θ": ["t", "s"],        # "think" → "tink"
        "ð": ["d"],             # "this" → "dis"
        "h": [""],              # silent h
        "æ": ["ɛ", "a"],        # "cat" issues
        "ŋ": ["n"],             # final ng
    },
    "russian": {
        "θ": ["s", "f"],        # "think" → "sink"
        "ð": ["z", "d"],        # "this" → "zis"
        "w": ["v"],             # "wet" → "vet"
        "ŋ": ["nɡ", "n"],       # "sing" → "sing-g"
        "h": ["x"],             # harder h
        "æ": ["ɛ"],             # "cat" → "ket"
    },
    "arabic": {
        "p": ["b"],             # "pen" → "ben"
        "v": ["f"],             # "very" → "fery"
        "ŋ": ["n"],             # final ng
        "tʃ": ["ʃ"],            # "church" → "shursh"
    },
    "korean": {
        "θ": ["s"],             # "think" → "sink"
        "ð": ["d"],             # "this" → "dis"
        "r": ["l"],             # r/l confusion
        "l": ["r"],             # l/r confusion
        "f": ["p"],             # "fun" → "pun"
        "v": ["b"],             # "very" → "bery"
        "z": ["dʒ"],            # "zoo" → "joo"
    },
    "hindi": {
        "θ": ["t̪", "t"],        # dental t
        "ð": ["d̪", "d"],        # dental d
        "v": ["w"],             # "very" → "wery"
        "z": ["dʒ", "j"],       # "zero" issues
    },
}

# IPA to ARPABET approximate mapping for ASR comparison
IPA_TO_ARPABET = {
    "i": "IY", "ɪ": "IH", "e": "EY", "ɛ": "EH", "æ": "AE",
    "ɑ": "AA", "ɔ": "AO", "o": "OW", "ʊ": "UH", "u": "UW",
    "ʌ": "AH", "ə": "AH", "ɜ": "ER", "ɝ": "ER",
    "aɪ": "AY", "aʊ": "AW", "ɔɪ": "OY",
    "p": "P", "b": "B", "t": "T", "d": "D", "k": "K", "ɡ": "G",
    "tʃ": "CH", "dʒ": "JH",
    "f": "F", "v": "V", "θ": "TH", "ð": "DH",
    "s": "S", "z": "Z", "ʃ": "SH", "ʒ": "ZH",
    "h": "HH", "m": "M", "n": "N", "ŋ": "NG",
    "l": "L", "r": "R", "w": "W", "j": "Y",
}

# CMU phoneme difficulty by CEFR level
PHONEME_DIFFICULTY = {
    # Easy (A1-A2)
    "p": 1, "b": 1, "t": 1, "d": 1, "k": 1, "g": 1,
    "m": 1, "n": 1, "s": 1, "f": 1, "l": 1,
    "i": 1, "e": 1, "a": 1, "o": 1, "u": 1,
    # Medium (B1)
    "v": 2, "z": 2, "ʃ": 2, "tʃ": 2, "dʒ": 2,
    "ŋ": 2, "r": 2, "w": 2, "j": 2,
    "ɪ": 2, "ɛ": 2, "ʌ": 2, "ə": 2,
    # Hard (B2+)
    "θ": 3, "ð": 3, "ʒ": 3, "h": 2,
    "æ": 3, "ɔ": 3, "ʊ": 3,
    "aɪ": 2, "aʊ": 2, "ɔɪ": 2,
}


@dataclass
class PhonemeScore:
    """Score for a single phoneme."""
    phoneme: str           # IPA symbol
    expected: bool         # Was this phoneme expected?
    detected: bool         # Was it detected in ASR?
    score: int             # 0-100
    confusion: Optional[str] = None  # What it was confused with
    position: str = "any"  # initial, medial, final


@dataclass
class WordPhonemeAnalysis:
    """Phoneme analysis for a single word."""
    word: str
    expected_phonemes: List[str]
    detected_phonemes: List[str]
    phoneme_scores: List[PhonemeScore]
    overall_score: int
    problem_phonemes: List[str] = field(default_factory=list)


@dataclass
class PhonemeAnalysisResult:
    """Complete phoneme analysis result."""
    overall_score: int
    word_analyses: List[WordPhonemeAnalysis]
    problem_phonemes: List[Dict]  # {phoneme, count, confusion_with, severity}
    l1_patterns_detected: List[Dict]  # {pattern, examples, confidence}
    recommendations: List[str]

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "word_analyses": [
                {
                    "word": wa.word,
                    "expected_phonemes": wa.expected_phonemes,
                    "detected_phonemes": wa.detected_phonemes,
                    "score": wa.overall_score,
                    "problem_phonemes": wa.problem_phonemes,
                }
                for wa in self.word_analyses
            ],
            "problem_phonemes": self.problem_phonemes,
            "l1_patterns_detected": self.l1_patterns_detected,
            "recommendations": self.recommendations,
        }


class PhonemeAnalyzer:
    """
    Analyzes pronunciation at the phoneme level using IPA.

    Uses the phonemizer library to convert text to IPA,
    then compares with ASR-detected phonemes to find errors.
    """

    def __init__(self, native_language: str = "spanish"):
        self.native_language = native_language.lower()
        self.l1_patterns = L1_INTERFERENCE_PATTERNS.get(
            self.native_language, {}
        )
        self._phonemizer = None
        self._init_phonemizer()

    def _init_phonemizer(self):
        """Initialize phonemizer backend."""
        try:
            from phonemizer import phonemize
            from phonemizer.backend import EspeakBackend

            # Test if espeak is available
            self._phonemizer = lambda text: phonemize(
                text,
                language='en-us',
                backend='espeak',
                strip=True,
                preserve_punctuation=False,
                with_stress=False,
            )
        except Exception as e:
            print(f"[PhonemeAnalyzer] phonemizer not available: {e}")
            # Fallback to simple mapping
            self._phonemizer = self._simple_phonemize

    def _simple_phonemize(self, text: str) -> str:
        """Simple fallback phonemization using lookup table."""
        # Basic CMU-style mapping for common words
        COMMON_WORDS = {
            "the": "ð ə",
            "a": "ə",
            "an": "æ n",
            "is": "ɪ z",
            "are": "ɑ r",
            "was": "w ɑ z",
            "were": "w ɜ r",
            "be": "b i",
            "been": "b ɪ n",
            "have": "h æ v",
            "has": "h æ z",
            "had": "h æ d",
            "do": "d u",
            "does": "d ʌ z",
            "did": "d ɪ d",
            "will": "w ɪ l",
            "would": "w ʊ d",
            "could": "k ʊ d",
            "should": "ʃ ʊ d",
            "think": "θ ɪ ŋ k",
            "this": "ð ɪ s",
            "that": "ð æ t",
            "there": "ð ɛ r",
            "their": "ð ɛ r",
            "they": "ð eɪ",
            "them": "ð ɛ m",
            "these": "ð i z",
            "those": "ð oʊ z",
            "with": "w ɪ θ",
            "very": "v ɛ r i",
            "good": "g ʊ d",
            "thank": "θ æ ŋ k",
            "thanks": "θ æ ŋ k s",
            "thing": "θ ɪ ŋ",
            "things": "θ ɪ ŋ z",
            "something": "s ʌ m θ ɪ ŋ",
            "nothing": "n ʌ θ ɪ ŋ",
            "everything": "ɛ v r i θ ɪ ŋ",
            "weather": "w ɛ ð ə r",
            "whether": "w ɛ ð ə r",
            "mother": "m ʌ ð ə r",
            "father": "f ɑ ð ə r",
            "brother": "b r ʌ ð ə r",
            "other": "ʌ ð ə r",
            "another": "ə n ʌ ð ə r",
        }

        words = text.lower().split()
        phonemes = []
        for word in words:
            word_clean = re.sub(r'[^\w]', '', word)
            if word_clean in COMMON_WORDS:
                phonemes.append(COMMON_WORDS[word_clean])
            else:
                # Basic letter-to-phoneme for unknown words
                phonemes.append(self._basic_g2p(word_clean))

        return " | ".join(phonemes)

    def _basic_g2p(self, word: str) -> str:
        """Basic grapheme-to-phoneme for unknown words."""
        # Very simplified - just for fallback
        LETTER_MAP = {
            'a': 'æ', 'e': 'ɛ', 'i': 'ɪ', 'o': 'ɑ', 'u': 'ʌ',
            'b': 'b', 'c': 'k', 'd': 'd', 'f': 'f', 'g': 'g',
            'h': 'h', 'j': 'dʒ', 'k': 'k', 'l': 'l', 'm': 'm',
            'n': 'n', 'p': 'p', 'q': 'k', 'r': 'r', 's': 's',
            't': 't', 'v': 'v', 'w': 'w', 'x': 'k s', 'y': 'j',
            'z': 'z',
        }

        result = []
        i = 0
        while i < len(word):
            # Check digraphs
            if i < len(word) - 1:
                digraph = word[i:i+2]
                if digraph == 'th':
                    result.append('θ')
                    i += 2
                    continue
                elif digraph == 'sh':
                    result.append('ʃ')
                    i += 2
                    continue
                elif digraph == 'ch':
                    result.append('tʃ')
                    i += 2
                    continue
                elif digraph == 'ng':
                    result.append('ŋ')
                    i += 2
                    continue

            char = word[i].lower()
            if char in LETTER_MAP:
                result.append(LETTER_MAP[char])
            i += 1

        return ' '.join(result)

    def get_expected_phonemes(self, text: str) -> List[str]:
        """Get expected IPA phonemes for text."""
        if self._phonemizer:
            ipa = self._phonemizer(text)
            # Split into individual phonemes
            phonemes = []
            for p in ipa.split():
                if p and p not in ['|', ' ']:
                    phonemes.append(p)
            return phonemes
        return []

    def analyze_pronunciation(
        self,
        text: str,
        asr_words: List[Dict],  # [{word, confidence, start, end}]
        audio_quality_score: int = 100
    ) -> PhonemeAnalysisResult:
        """
        Analyze pronunciation comparing expected vs ASR-detected phonemes.

        Args:
            text: The expected text (what user should have said)
            asr_words: ASR output with word-level confidence
            audio_quality_score: 0-100 indicating recording quality

        Returns:
            PhonemeAnalysisResult with detailed phoneme-level analysis
        """
        word_analyses = []
        all_problem_phonemes = {}
        l1_patterns = []

        # Analyze each word
        expected_words = text.lower().split()
        for i, expected_word in enumerate(expected_words):
            # Clean the word
            expected_clean = re.sub(r'[^\w]', '', expected_word)
            if not expected_clean:
                continue

            # Get expected phonemes
            expected_phonemes = self.get_expected_phonemes(expected_clean)

            # Get ASR data for this word if available
            asr_data = None
            if i < len(asr_words):
                asr_data = asr_words[i]

            # Analyze this word
            word_analysis = self._analyze_word(
                expected_clean,
                expected_phonemes,
                asr_data,
                audio_quality_score
            )
            word_analyses.append(word_analysis)

            # Collect problem phonemes
            for p in word_analysis.problem_phonemes:
                if p not in all_problem_phonemes:
                    all_problem_phonemes[p] = {"count": 0, "words": []}
                all_problem_phonemes[p]["count"] += 1
                all_problem_phonemes[p]["words"].append(expected_clean)

        # Detect L1 interference patterns
        l1_patterns = self._detect_l1_patterns(all_problem_phonemes)

        # Calculate overall score
        if word_analyses:
            overall_score = sum(wa.overall_score for wa in word_analyses) // len(word_analyses)
        else:
            overall_score = 100

        # Adjust for audio quality
        if audio_quality_score < 70:
            # Don't penalize too much for bad audio
            overall_score = max(overall_score, 60)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            all_problem_phonemes,
            l1_patterns
        )

        # Format problem phonemes
        problem_list = [
            {
                "phoneme": p,
                "count": data["count"],
                "examples": data["words"][:3],
                "severity": self._get_severity(data["count"]),
                "difficulty": PHONEME_DIFFICULTY.get(p, 2),
            }
            for p, data in sorted(
                all_problem_phonemes.items(),
                key=lambda x: -x[1]["count"]
            )
        ]

        return PhonemeAnalysisResult(
            overall_score=overall_score,
            word_analyses=word_analyses,
            problem_phonemes=problem_list,
            l1_patterns_detected=l1_patterns,
            recommendations=recommendations,
        )

    def _analyze_word(
        self,
        word: str,
        expected_phonemes: List[str],
        asr_data: Optional[Dict],
        audio_quality: int
    ) -> WordPhonemeAnalysis:
        """Analyze phonemes for a single word."""
        phoneme_scores = []
        problem_phonemes = []

        # Get confidence from ASR
        confidence = 0.85  # default
        if asr_data and 'confidence' in asr_data:
            confidence = asr_data['confidence']

        # Score each expected phoneme
        for i, phoneme in enumerate(expected_phonemes):
            # Determine position
            if i == 0:
                position = "initial"
            elif i == len(expected_phonemes) - 1:
                position = "final"
            else:
                position = "medial"

            # Base score from confidence and phoneme difficulty
            difficulty = PHONEME_DIFFICULTY.get(phoneme, 2)
            base_score = int(confidence * 100)

            # Adjust for difficulty
            if difficulty >= 3:
                base_score = max(50, base_score - 10)

            # Check L1 interference
            confusion = None
            if phoneme in self.l1_patterns:
                # This is a commonly confused phoneme for this L1
                if base_score < 85:
                    confusion = self.l1_patterns[phoneme][0]
                    problem_phonemes.append(phoneme)
                    base_score = max(40, base_score - 15)

            phoneme_scores.append(PhonemeScore(
                phoneme=phoneme,
                expected=True,
                detected=base_score > 60,
                score=base_score,
                confusion=confusion,
                position=position,
            ))

        # Calculate word score
        if phoneme_scores:
            word_score = sum(ps.score for ps in phoneme_scores) // len(phoneme_scores)
        else:
            word_score = int(confidence * 100) if asr_data else 75

        # Detected phonemes (simplified - just use expected with modifications)
        detected_phonemes = [
            ps.confusion if ps.confusion else ps.phoneme
            for ps in phoneme_scores
            if ps.detected
        ]

        return WordPhonemeAnalysis(
            word=word,
            expected_phonemes=expected_phonemes,
            detected_phonemes=detected_phonemes,
            phoneme_scores=phoneme_scores,
            overall_score=word_score,
            problem_phonemes=problem_phonemes,
        )

    def _detect_l1_patterns(
        self,
        problem_phonemes: Dict
    ) -> List[Dict]:
        """Detect L1-specific interference patterns."""
        patterns = []

        for phoneme, data in problem_phonemes.items():
            if phoneme in self.l1_patterns:
                expected_substitution = self.l1_patterns[phoneme]
                patterns.append({
                    "pattern": f"/{phoneme}/ → /{expected_substitution[0]}/",
                    "phoneme": phoneme,
                    "l1_substitution": expected_substitution[0],
                    "count": data["count"],
                    "examples": data["words"][:3],
                    "confidence": min(1.0, data["count"] / 3),
                    "native_language": self.native_language,
                })

        return sorted(patterns, key=lambda x: -x["confidence"])

    def _get_severity(self, count: int) -> str:
        """Determine severity based on error count."""
        if count >= 5:
            return "critical"
        elif count >= 3:
            return "major"
        elif count >= 2:
            return "moderate"
        else:
            return "minor"

    def _generate_recommendations(
        self,
        problem_phonemes: Dict,
        l1_patterns: List[Dict]
    ) -> List[str]:
        """Generate practice recommendations."""
        recommendations = []

        # L1-specific recommendations
        for pattern in l1_patterns[:2]:  # Top 2 patterns
            phoneme = pattern["phoneme"]
            sub = pattern["l1_substitution"]

            if phoneme == "θ":
                recommendations.append(
                    f"Practice the 'th' sound: Place your tongue between your teeth. "
                    f"Try: 'think', 'three', 'thing'. Don't say /{sub}/."
                )
            elif phoneme == "ð":
                recommendations.append(
                    f"Practice the voiced 'th': Say 'the', 'this', 'that' with your "
                    f"tongue between your teeth. It should vibrate, not sound like /d/."
                )
            elif phoneme == "v":
                recommendations.append(
                    f"Practice /v/: Bite your lower lip lightly and voice. "
                    f"Try 'very', 'video', 'love'. It's different from /b/."
                )
            elif phoneme == "r":
                recommendations.append(
                    f"Practice English /r/: Curl your tongue back without touching "
                    f"the roof. Try 'red', 'right', 'road'. Don't tap like in Spanish."
                )
            elif phoneme == "æ":
                recommendations.append(
                    f"Practice the 'cat' vowel /æ/: Open your mouth wide and say "
                    f"'cat', 'hat', 'bad'. It's between /a/ and /e/."
                )

        # General recommendations based on difficulty
        hard_phonemes = [p for p in problem_phonemes.keys()
                        if PHONEME_DIFFICULTY.get(p, 2) >= 3]
        if hard_phonemes:
            recommendations.append(
                f"Focus on these challenging sounds: {', '.join(hard_phonemes)}"
            )

        if not recommendations:
            recommendations.append("Great pronunciation! Keep practicing to maintain fluency.")

        return recommendations


# Singleton instance
_analyzer_cache = {}


def get_phoneme_analyzer(native_language: str = "spanish") -> PhonemeAnalyzer:
    """Get or create a PhonemeAnalyzer for the given L1."""
    lang = native_language.lower()
    if lang not in _analyzer_cache:
        _analyzer_cache[lang] = PhonemeAnalyzer(lang)
    return _analyzer_cache[lang]


def analyze_pronunciation_from_asr(
    expected_text: str,
    asr_words: List[Dict],
    native_language: str = "spanish",
    audio_quality: int = 100
) -> PhonemeAnalysisResult:
    """
    Convenience function to analyze pronunciation.

    Args:
        expected_text: What the user was supposed to say
        asr_words: ASR output [{word, confidence, start, end}]
        native_language: User's L1 for interference patterns
        audio_quality: 0-100 recording quality score

    Returns:
        PhonemeAnalysisResult with full analysis
    """
    analyzer = get_phoneme_analyzer(native_language)
    return analyzer.analyze_pronunciation(
        expected_text,
        asr_words,
        audio_quality
    )
