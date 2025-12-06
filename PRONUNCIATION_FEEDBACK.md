# Enhanced Pronunciation Feedback System

## Overview

The enhanced pronunciation feedback system provides users with specific, actionable feedback on their pronunciation, helping them improve through targeted practice and personalized recommendations.

## Features

### 1. Word-Level Analysis
- Uses Whisper's word-level timestamps for precise analysis
- Scores individual words (0-100)
- Identifies specific pronunciation issues per word

### 2. Common Mispronunciation Detection
- Database of 13+ commonly mispronounced words
- Detects patterns like:
  - TH → T/D substitution ("think" → "tink")
  - V/W confusion ("very" → "wery", "water" → "vater")
  - R/L confusion
  - Dropped final consonants ("good" → "goo")
  - Vowel errors

### 3. Specific, Actionable Tips
Each tip includes:
- **Word**: The problematic word
- **Issue**: What went wrong
- **Tip**: How to fix it (tongue placement, mouth shape, etc.)
- **Phonetic**: IPA pronunciation guide
- **Example**: Practice sentence or comparison

### 4. Improvement Tracking
- Stores pronunciation attempts in database
- Calculates improvement trends over time
- Identifies most improved sounds
- Highlights persistent problem areas

### 5. Personalized Recommendations
- Based on user's historical pronunciation data
- Focuses on consistently weak phonemes
- Generates targeted practice suggestions

## API Endpoints

### GET /api/pronunciation/stats

Get comprehensive pronunciation statistics for a user.

**Response Format:**
```json
{
  "total_attempts": 45,
  "current_average": 82.5,
  "overall_average": 78.3,
  "trend": 4.2,
  "most_improved": [
    {
      "phoneme": "θ",
      "improvement": 12.5,
      "current_score": 85.0
    }
  ],
  "areas_needing_work": [
    {
      "phoneme": "r",
      "avg_score": 65.0,
      "attempts": 15
    }
  ],
  "practice_suggestions": [
    "Practice the 'r' sound: Curl your tongue back without touching the roof of your mouth"
  ]
}
```

### POST /api/pronunciation/score

Score a pronunciation attempt (existing endpoint, enhanced with tracking).

### GET /api/pronunciation/summary

Get basic pronunciation summary statistics.

### GET /api/pronunciation/weak-phonemes

Get user's weakest phonemes based on recent attempts.

### GET /api/pronunciation/daily-phrase

Get a practice phrase targeting user's weak phonemes.

## Integration with Voice Sessions

### Enhanced VoiceSession Class

```python
from app.voice_session import VoiceSession
from app.db import Database

# Initialize with pronunciation feedback enabled
db = Database()
session = VoiceSession(
    user_level="A2",
    mode="free_chat",
    context={
        "reference_text": "I think this is very good"  # Optional reference
    },
    db=db,
    user_id="user-uuid-here",
    enable_pronunciation_feedback=True
)

# Process audio with pronunciation feedback
result = session.handle_audio_input(audio_bytes)

# Access pronunciation feedback in tutor response
if result.tutor_response.pronunciation_feedback:
    feedback = result.tutor_response.pronunciation_feedback
    print(f"Score: {feedback['overall_score']}/100")
    print(f"Tips: {feedback['tips']}")
```

### Tutor Response Format

The `TutorResponse` now includes a `pronunciation_feedback` field:

```python
{
  "message": "Good effort! You're pronouncing most words well.\n\nPronunciation tip: Place your tongue between your teeth for the 'th' sound.",
  "errors": [...],  # Grammar/vocabulary errors
  "micro_task": "...",
  "pronunciation_feedback": {
    "overall_score": 76.0,
    "encouragement": "Good effort! You're pronouncing most words well.",
    "tips": [
      {
        "word": "think",
        "issue": "Score: 40/100",
        "tip": "Place your tongue between your teeth for the 'th' sound.",
        "phonetic": "/θɪŋk/",
        "example": "Think starts with a soft 'th' sound, not 't'"
      }
    ],
    "problem_sounds": ["th"],
    "word_scores": [
      {"word": "i", "score": 100.0, "issues": []},
      {"word": "think", "score": 40.0, "issues": ["Pronounced like 'tink'"]}
    ]
  }
}
```

## Pronunciation Tips Database

### Common Mispronunciations (Words)

```python
COMMON_MISPRONUNCIATIONS = {
    "the": {
        "common_errors": ["de", "da", "ze"],
        "tip": "Place your tongue between your teeth and blow air gently.",
        "phonetic": "/ðə/",
        "example": "Say 'the' like 'thuh', not 'duh'"
    },
    "think": {
        "common_errors": ["tink", "sink", "fink"],
        "tip": "Place your tongue between your teeth for the 'th' sound.",
        "phonetic": "/θɪŋk/",
        "example": "Think starts with a soft 'th' sound, not 't'"
    },
    # ... 11 more words
}
```

### Phoneme-Level Tips

```python
PHONEME_TIPS = {
    "th": "Place your tongue between your teeth and blow air gently",
    "r": "Curl your tongue back without touching the roof of your mouth",
    "v": "Touch your top teeth with your bottom lip and vibrate",
    "w": "Round your lips like you're about to whistle",
    # ... 12 more phonemes
}
```

## Scoring System

### Overall Score Calculation
- 90-100: Excellent pronunciation
- 80-89: Very good, clear pronunciation
- 70-79: Good effort, mostly clear
- 60-69: On the right track, needs practice
- 0-59: Needs work, focus on tips

### Word-Level Scoring
- **100**: Perfect match
- **70**: Partial match or close pronunciation
- **40**: Common mispronunciation detected
- **30**: Very different from target

### Improvement Tracking
- Compares recent 5 attempts vs previous 5 attempts
- Calculates percentage improvement
- Identifies phonemes with significant improvement (>5%)

## Example Feedback Messages

### High Score (90+)
```
"Excellent pronunciation! Keep up the great work!"
```

### Good Score (70-89)
```
"Very good! Your pronunciation is quite clear. Focus on: 'the'."
```

### Needs Work (Below 60)
```
"Don't worry - pronunciation takes practice! Focus on the tips below.
Focus on: 'think'.

Pronunciation tip: Place your tongue between your teeth for the 'th' sound.
Practice saying 'three, think, thought'."
```

### With Improvement
```
"Good effort! You're pronouncing most words well. Focus on: 'very'.
Your pronunciation has improved by 8% recently!"
```

## Files Modified

1. **`/Users/matuskalis/vorex-backend/app/pronunciation_analyzer.py`** (NEW)
   - Core pronunciation analysis engine
   - 650+ lines of comprehensive feedback logic
   - Common mispronunciation database
   - Improvement tracking algorithms

2. **`/Users/matuskalis/vorex-backend/app/asr_client.py`**
   - Enhanced to capture word-level timestamps from Whisper
   - Added `timestamp_granularities=["word"]` parameter
   - Extracts WordTiming objects from Whisper response

3. **`/Users/matuskalis/vorex-backend/app/voice_session.py`**
   - Integrated pronunciation analyzer
   - Added pronunciation feedback to voice session pipeline
   - Stores pronunciation attempts in database
   - Enhances tutor message with pronunciation tips

4. **`/Users/matuskalis/vorex-backend/app/models.py`**
   - Added `PronunciationFeedbackItem` model
   - Added `pronunciation_feedback` field to `TutorResponse`

5. **`/Users/matuskalis/vorex-backend/app/pronunciation.py`**
   - Added new `/api/pronunciation/stats` endpoint
   - Integrated `PronunciationAnalyzer`

6. **`/Users/matuskalis/vorex-backend/test_pronunciation_feedback.py`** (NEW)
   - Comprehensive test suite
   - Demonstrates all feedback features
   - Shows example outputs

## Database Schema

The system uses the existing `pronunciation_attempts` table:

```sql
CREATE TABLE pronunciation_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  phrase TEXT NOT NULL,
  phoneme_scores JSONB NOT NULL,
  overall_score REAL NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_pronunciation_user_created
  ON pronunciation_attempts (user_id, created_at DESC);
```

## Usage Examples

### 1. Basic Voice Session with Pronunciation Feedback

```python
from app.voice_session import VoiceSession
from app.db import Database

db = Database()
session = VoiceSession(
    user_level="A2",
    db=db,
    user_id="user-123",
    enable_pronunciation_feedback=True
)

result = session.handle_audio_input(audio_bytes)
print(result.tutor_response.pronunciation_feedback)
```

### 2. Get User Pronunciation Statistics

```bash
curl -X GET \
  'http://localhost:8000/api/pronunciation/stats' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### 3. Standalone Pronunciation Analysis

```python
from app.pronunciation_analyzer import PronunciationAnalyzer
from app.models import ASRResult, WordTiming

analyzer = PronunciationAnalyzer(db=db)

asr_result = ASRResult(
    text="I tink dis is good",
    confidence=0.88,
    words=[...],
    provider="openai"
)

feedback = analyzer.analyze_pronunciation(
    asr_result=asr_result,
    reference_text="I think this is good",
    user_id="user-123"
)

print(f"Score: {feedback.overall_score}/100")
print(f"Tips: {feedback.tips}")
```

## Testing

Run the test suite:

```bash
cd /Users/matuskalis/vorex-backend
source venv/bin/activate
python test_pronunciation_feedback.py
```

Expected output:
- 4 test scenarios covering different pronunciation issues
- Common mispronunciation database display
- API response format examples
- All tests should pass with detailed feedback

## Best Practices

### For Developers

1. **Always enable pronunciation feedback for voice sessions** with user_id
2. **Provide reference text** when available (drills, lessons)
3. **Store pronunciation attempts** for long-term improvement tracking
4. **Handle errors gracefully** - continue without feedback if analysis fails

### For Users

1. **Practice consistently** - improvement tracking requires regular attempts
2. **Focus on one sound** at a time based on feedback
3. **Use the example sentences** provided in tips
4. **Track progress** through the stats endpoint

### For Content Creators

1. **Target specific phonemes** in practice phrases
2. **Align with user's weak areas** from pronunciation stats
3. **Provide reference text** for accurate comparison
4. **Create progressive exercises** based on improvement data

## Future Enhancements

Potential additions to the system:

1. **Audio playback of correct pronunciation**
   - Generate TTS for reference words
   - Side-by-side comparison

2. **Visual feedback**
   - Waveform comparison
   - Mouth position diagrams
   - Phoneme highlighting

3. **Expanded mispronunciation database**
   - Language-specific patterns (Spanish speakers, Chinese speakers, etc.)
   - More words and sounds

4. **AI-powered tips**
   - Use LLM to generate personalized explanations
   - Context-aware pronunciation guidance

5. **Practice mode**
   - Dedicated pronunciation drills
   - Gamified challenges
   - Achievement system

## Technical Details

### Pronunciation Analysis Pipeline

1. **ASR** → Transcribe with word-level timestamps
2. **Phoneme Scoring** → Convert text to phonemes, score alignment
3. **Word Analysis** → Compare transcribed vs reference words
4. **Pattern Detection** → Check against common mispronunciation database
5. **Historical Analysis** → Look up user's weak areas from database
6. **Tip Generation** → Select top 3 most relevant tips
7. **Encouragement** → Generate score-appropriate message
8. **Storage** → Save attempt to database for tracking

### Performance Considerations

- Pronunciation analysis adds ~100-200ms to voice session
- Database queries are optimized with indexes
- Caching of historical data could reduce latency
- Graceful degradation if analysis fails

### Error Handling

- Pronunciation analysis is non-blocking
- Falls back gracefully if:
  - Database unavailable
  - Phoneme scoring fails
  - No word-level timestamps
- Always returns valid TutorResponse

## Conclusion

The enhanced pronunciation feedback system provides users with:
- ✓ Specific, actionable pronunciation tips
- ✓ Detection of common mispronunciation patterns
- ✓ Word-level scoring and feedback
- ✓ Phonetic guidance and examples
- ✓ Encouraging but specific messages
- ✓ Long-term improvement tracking
- ✓ Personalized practice recommendations

This creates a comprehensive, user-friendly pronunciation learning experience that helps users improve their spoken English systematically.
