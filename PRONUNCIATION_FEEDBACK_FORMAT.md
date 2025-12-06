# Pronunciation Feedback Format

## Overview

This document describes the format of pronunciation feedback provided to users through the voice session API.

## Complete API Response Example

```json
{
  "recognized_text": "I tink dis is very good",
  "tutor_response": {
    "message": "Good effort! You're pronouncing most words well.\n\nPronunciation tip: Place your tongue between your teeth for the 'th' sound. Practice saying 'three, think, thought'. Think starts with a soft 'th' sound, not 't'",
    "errors": [],
    "micro_task": null,
    "scenario_complete": null,
    "success_evaluation": null,
    "pronunciation_feedback": {
      "overall_score": 76.0,
      "encouragement": "Good effort! You're pronouncing most words well. Focus on: think.",
      "tips": [
        {
          "word": "think",
          "issue": "Score: 40/100",
          "tip": "Place your tongue between your teeth for the 'th' sound. Practice saying 'three, think, thought'.",
          "phonetic": "/θɪŋk/",
          "example": "Think starts with a soft 'th' sound, not 't'"
        },
        {
          "word": "this",
          "issue": "Score: 40/100",
          "tip": "Tongue between teeth, make it vibrate: 'th-th-this'",
          "phonetic": "/ðɪs/",
          "example": "This, that, these, those - all start with tongue between teeth"
        }
      ],
      "problem_sounds": ["th"],
      "word_scores": [
        {
          "word": "i",
          "score": 100.0,
          "issues": []
        },
        {
          "word": "think",
          "score": 40.0,
          "issues": ["Pronounced like 'tink'"]
        },
        {
          "word": "this",
          "score": 40.0,
          "issues": ["Pronounced like 'dis'"]
        },
        {
          "word": "is",
          "score": 100.0,
          "issues": []
        },
        {
          "word": "very",
          "score": 100.0,
          "issues": []
        },
        {
          "word": "good",
          "score": 100.0,
          "issues": []
        }
      ]
    }
  },
  "tts_output_path": "/tmp/speaksharp/tts/tutor_response_1234567890.mp3",
  "asr_confidence": 0.88,
  "processing_time_ms": 1250
}
```

## Field Descriptions

### `pronunciation_feedback` Object

| Field | Type | Description |
|-------|------|-------------|
| `overall_score` | float | Overall pronunciation score (0-100) |
| `encouragement` | string | Personalized encouraging message |
| `tips` | array | Array of specific pronunciation tips (max 3) |
| `problem_sounds` | array | List of phonemes that need work |
| `word_scores` | array | Word-by-word pronunciation scores |

### `tips` Array Items

Each tip object contains:

| Field | Type | Description |
|-------|------|-------------|
| `word` | string | The word or sound being addressed |
| `issue` | string | What went wrong (e.g., "Score: 40/100") |
| `tip` | string | Specific, actionable advice |
| `phonetic` | string\|null | IPA phonetic notation |
| `example` | string\|null | Example sentence or comparison |

### `word_scores` Array Items

Each word score object contains:

| Field | Type | Description |
|-------|------|-------------|
| `word` | string | The word being scored |
| `score` | float | Score for this word (0-100) |
| `issues` | array | List of specific issues with this word |

## Score Interpretation

### Overall Score
- **90-100**: Excellent pronunciation
- **80-89**: Very good, clear pronunciation
- **70-79**: Good effort, mostly clear
- **60-69**: On the right track, needs practice
- **0-59**: Needs work, focus on tips

### Word Score
- **100**: Perfect pronunciation
- **70-99**: Close but slightly off
- **40-69**: Noticeable error but understandable
- **0-39**: Significant mispronunciation

## Example Scenarios

### Scenario 1: Perfect Pronunciation

**User says**: "I think this is very good"
**Transcribed**: "I think this is very good"

```json
{
  "overall_score": 100.0,
  "encouragement": "Excellent pronunciation! Keep up the great work!",
  "tips": [],
  "problem_sounds": [],
  "word_scores": [
    {"word": "i", "score": 100.0, "issues": []},
    {"word": "think", "score": 100.0, "issues": []},
    {"word": "this", "score": 100.0, "issues": []},
    {"word": "is", "score": 100.0, "issues": []},
    {"word": "very", "score": 100.0, "issues": []},
    {"word": "good", "score": 100.0, "issues": []}
  ]
}
```

### Scenario 2: TH Sound Issues

**User says**: "I think this is very good"
**Transcribed**: "I tink dis is very good"

```json
{
  "overall_score": 76.0,
  "encouragement": "Good effort! You're pronouncing most words well. Focus on: think.",
  "tips": [
    {
      "word": "think",
      "issue": "Score: 40/100",
      "tip": "Place your tongue between your teeth for the 'th' sound. Practice saying 'three, think, thought'.",
      "phonetic": "/θɪŋk/",
      "example": "Think starts with a soft 'th' sound, not 't'"
    }
  ],
  "problem_sounds": ["th"],
  "word_scores": [
    {"word": "i", "score": 100.0, "issues": []},
    {"word": "think", "score": 40.0, "issues": ["Pronounced like 'tink'"]},
    {"word": "this", "score": 40.0, "issues": ["Pronounced like 'dis'"]},
    {"word": "is", "score": 100.0, "issues": []},
    {"word": "very", "score": 100.0, "issues": []},
    {"word": "good", "score": 100.0, "issues": []}
  ]
}
```

### Scenario 3: Multiple Issues

**User says**: "I think the water is very good"
**Transcribed**: "I tink de wata is wery goo"

```json
{
  "overall_score": 59.3,
  "encouragement": "Don't worry - pronunciation takes practice! Focus on the tips below. Focus on: think.",
  "tips": [
    {
      "word": "think",
      "issue": "Score: 40/100",
      "tip": "Place your tongue between your teeth for the 'th' sound. Practice saying 'three, think, thought'.",
      "phonetic": "/θɪŋk/",
      "example": "Think starts with a soft 'th' sound, not 't'"
    },
    {
      "word": "the",
      "issue": "Score: 40/100",
      "tip": "Place your tongue between your teeth and blow air gently. It should feel like a soft vibration.",
      "phonetic": "/ðə/",
      "example": "Say 'the' like 'thuh', not 'duh'"
    },
    {
      "word": "water",
      "issue": "Score: 55/100",
      "tip": "Round your lips for 'w', then say 'aw' sound. Not 'v' sound.",
      "phonetic": "/ˈwɔtər/",
      "example": "Water, want, will - lips should be rounded for 'w'"
    }
  ],
  "problem_sounds": ["th", "v"],
  "word_scores": [
    {"word": "i", "score": 100.0, "issues": []},
    {"word": "think", "score": 40.0, "issues": ["Pronounced like 'tink'"]},
    {"word": "the", "score": 40.0, "issues": ["Pronounced like 'de'"]},
    {"word": "water", "score": 55.0, "issues": ["Several sounds were different"]},
    {"word": "is", "score": 100.0, "issues": []},
    {"word": "very", "score": 40.0, "issues": ["Pronounced like 'wery'"]},
    {"word": "good", "score": 40.0, "issues": ["Pronounced like 'goo'"]}
  ]
}
```

## UI Display Recommendations

### Overall Score Display
```
Score: 76/100
[=========>     ] 76%
```

### Encouragement Message
Display prominently as main feedback:
```
✓ Good effort! You're pronouncing most words well.
```

### Tips Display
Show as expandable cards:
```
┌─────────────────────────────────────────┐
│ 🎯 Focus on: "think"                    │
├─────────────────────────────────────────┤
│ Issue: Score 40/100                     │
│                                         │
│ Tip: Place your tongue between your    │
│ teeth for the 'th' sound. Practice     │
│ saying 'three, think, thought'.        │
│                                         │
│ Phonetic: /θɪŋk/                       │
│ Example: Think starts with a soft 'th' │
│ sound, not 't'                         │
└─────────────────────────────────────────┘
```

### Word Scores Display
Show as color-coded list:
```
Word Pronunciation:
✓ i         100/100  Perfect!
✗ think      40/100  Needs work
✗ this       40/100  Needs work
✓ is        100/100  Perfect!
✓ very      100/100  Perfect!
✓ good      100/100  Perfect!
```

Color scheme:
- Green (✓): Score >= 80
- Yellow (○): Score 60-79
- Red (✗): Score < 60

## Integration with Tutor Message

When pronunciation score is below 80, the system automatically enhances the tutor message with a pronunciation tip:

```
Original message: "Good effort! You're pronouncing most words well."

Enhanced message: "Good effort! You're pronouncing most words well.

Pronunciation tip: Place your tongue between your teeth for the 'th' sound.
Practice saying 'three, think, thought'. Think starts with a soft 'th' sound, not 't'"
```

This ensures users always receive immediate, actionable feedback in the natural conversation flow.

## Common Pronunciation Tips

### TH Sounds
- "Place your tongue between your teeth and blow air gently"
- Examples: the, think, this, three

### R Sound
- "Curl your tongue back without touching the roof of your mouth"
- Examples: right, very, water

### V/W Confusion
- V: "Touch your top teeth with your bottom lip and vibrate"
- W: "Round your lips like you're about to whistle"
- Examples: very vs. wery, water vs. vater

### L Sound
- "Touch your tongue to the ridge behind your top teeth"
- Examples: light, hello, world

### Final Consonants
- "Don't drop the final sound! Complete the word."
- Examples: good (not goo), want (not wan)

## Null Handling

If pronunciation feedback is unavailable (e.g., no user_id, analysis failed):
- `pronunciation_feedback` field will be `null`
- Tutor message will not include pronunciation tips
- Voice session continues normally without pronunciation analysis

```json
{
  "recognized_text": "Hello",
  "tutor_response": {
    "message": "Hi there!",
    "errors": [],
    "pronunciation_feedback": null
  }
}
```

## Performance Notes

- Pronunciation analysis adds ~100-200ms to voice session
- Analysis is non-blocking - failures don't affect main flow
- Word-level timestamps from Whisper are required for detailed analysis
- Database storage is async and doesn't block response

## Version History

- **v1.0** (2025-12-04): Initial implementation
  - Word-level analysis
  - Common mispronunciation detection
  - Specific tips with phonetics and examples
  - Improvement tracking
  - /api/pronunciation/stats endpoint
