# Pronunciation Analysis Endpoint

## Overview

The `/api/speech/analyze-pronunciation` endpoint provides comprehensive pronunciation analysis for language learners. It uses OpenAI Whisper for transcription and phoneme-level analysis to provide detailed feedback.

## Endpoint Details

- **URL**: `POST /api/speech/analyze-pronunciation`
- **Authentication**: Required (JWT token)
- **Content-Type**: `multipart/form-data`

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `audio` | File | Yes | Audio file (WAV, MP3, M4A, WebM) containing the user's speech |
| `target_text` | string | Yes | The text the user was attempting to pronounce |

## Response Schema

```json
{
  "success": true,
  "transcript": "string",
  "overall_score": 85.5,
  "pronunciation_score": 85.5,
  "fluency_score": 78.3,
  "phoneme_analysis": [
    {
      "word": "string",
      "phoneme": "θ",
      "status": "correct|close|incorrect",
      "confidence": 0.85,
      "expected_ipa": "θ",
      "actual_ipa": "θ"
    }
  ],
  "word_scores": [
    {
      "word": "string",
      "score": 85.0,
      "issues": ["Problem sounds: θ, ð"]
    }
  ],
  "feedback": "Good pronunciation overall. A few sounds need refinement.",
  "words_per_minute": 125.5,
  "duration": 5.23,
  "word_count": 11
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the analysis was successful |
| `transcript` | string | What Whisper recognized from the audio |
| `overall_score` | float | Overall pronunciation score (0-100) |
| `pronunciation_score` | float | Pronunciation accuracy score (0-100) |
| `fluency_score` | float | Speech fluency score based on pace (0-100) |
| `phoneme_analysis` | array | Phoneme-level breakdown |
| `word_scores` | array | Word-level scores with specific issues |
| `feedback` | string | Human-readable feedback message |
| `words_per_minute` | float | Speaking rate |
| `duration` | float | Audio duration in seconds |
| `word_count` | integer | Number of words spoken |

## Phoneme Analysis Object

Each phoneme analysis entry includes:

- `word`: The word containing this phoneme
- `phoneme`: The IPA representation of the phoneme
- `status`: One of "correct", "close", or "incorrect"
- `confidence`: Score from 0.0 to 1.0
- `expected_ipa`: Expected IPA phoneme
- `actual_ipa`: Detected IPA phoneme

## Word Score Object

Each word score entry includes:

- `word`: The word being analyzed
- `score`: Score from 0-100
- `issues`: Array of specific pronunciation issues and tips

## Example Usage

### cURL Example

```bash
curl -X POST https://api.vorex.app/api/speech/analyze-pronunciation \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@recording.m4a" \
  -F "target_text=The quick brown fox jumps over the lazy dog"
```

### JavaScript/TypeScript Example

```typescript
const formData = new FormData();
formData.append('audio', audioBlob, 'recording.m4a');
formData.append('target_text', 'The quick brown fox jumps over the lazy dog');

const response = await fetch('https://api.vorex.app/api/speech/analyze-pronunciation', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const result = await response.json();
console.log('Pronunciation score:', result.pronunciation_score);
console.log('Feedback:', result.feedback);
```

### Python Example

```python
import requests

url = 'https://api.vorex.app/api/speech/analyze-pronunciation'
headers = {'Authorization': f'Bearer {token}'}

with open('recording.m4a', 'rb') as audio_file:
    files = {'audio': audio_file}
    data = {'target_text': 'The quick brown fox jumps over the lazy dog'}

    response = requests.post(url, headers=headers, files=files, data=data)
    result = response.json()

    print(f"Pronunciation score: {result['pronunciation_score']}")
    print(f"Feedback: {result['feedback']}")
```

## Implementation Details

### How It Works

1. **Audio Transcription**: Uses OpenAI Whisper to transcribe the audio with word-level timestamps
2. **Phoneme Analysis**: Uses the `phonemizer` library to convert words to IPA phonemes
3. **Word Alignment**: Aligns transcribed words with target text using edit distance
4. **Scoring**:
   - Compares phonemes between expected and actual pronunciation
   - Identifies similar phonemes (e.g., p/b, t/d, s/z)
   - Generates scores for each word and overall
5. **Fluency Calculation**: Analyzes words per minute (optimal: 100-180 WPM)
6. **Feedback Generation**: Provides specific tips based on common pronunciation issues
7. **Database Storage**: Saves attempts for progress tracking

### Key Components Used

- **ASR Client** (`app.asr_client`): Whisper transcription
- **Pronunciation Scorer** (`app.pronunciation_scorer`): Phoneme-level analysis
- **Pronunciation Analyzer** (`app.pronunciation_analyzer`): Enhanced feedback
- **Database**: Stores pronunciation attempts for historical analysis

### Database Integration

Each pronunciation attempt is stored in the `pronunciation_attempts` table:

```sql
INSERT INTO pronunciation_attempts (user_id, phrase, phoneme_scores, overall_score)
VALUES (user_id, target_text, phoneme_data, overall_score)
```

This enables:
- Progress tracking over time
- Identification of persistent weak phonemes
- Personalized practice recommendations

## Score Interpretation

### Overall Score Ranges

- **90-100**: Excellent - Near-native pronunciation
- **75-89**: Good - Clear and understandable with minor issues
- **60-74**: Fair - Understandable but needs improvement
- **0-59**: Needs Work - Significant pronunciation challenges

### Fluency Score (Words Per Minute)

- **100-180 WPM**: Optimal range (score: 70-95)
- **< 100 WPM**: Too slow (proportional score)
- **> 180 WPM**: Too fast (decreasing score)

### Phoneme Status

- **correct**: Phoneme pronounced accurately
- **close**: Minor deviation (e.g., voicing difference)
- **incorrect**: Significant mispronunciation

## Error Handling

### Client Errors (4xx)

- **400 Bad Request**: Empty audio file or missing target_text
- **401 Unauthorized**: Missing or invalid JWT token

### Server Errors (5xx)

- **500 Internal Server Error**:
  - ASR transcription failure
  - Pronunciation analysis failure
  - Database errors

Error responses include a descriptive message:

```json
{
  "detail": "Empty audio file"
}
```

## Performance Considerations

- **Average Response Time**: 2-5 seconds (depends on audio length and Whisper API)
- **Max Audio Length**: Limited by OpenAI Whisper (typically up to 25MB files)
- **Recommended Audio Length**: 5-30 seconds for best results
- **Supported Formats**: WAV, MP3, M4A, WebM, MPEG, MPGA

## Related Endpoints

- `POST /api/speech/transcribe` - Simple transcription only
- `POST /api/speech/analyze` - Basic pronunciation analysis (simpler version)
- `GET /pronunciation/stats` - Get user's pronunciation statistics
- `GET /pronunciation/weak-phonemes` - Get user's weak phonemes

## Dependencies

- OpenAI API (Whisper model)
- `phonemizer` library (espeak backend)
- `numpy` for numerical calculations
- PostgreSQL database for storage

## Future Enhancements

Potential improvements for future versions:

1. **Real IPA Comparison**: Compare actual vs expected IPA more accurately
2. **Intonation Analysis**: Analyze pitch patterns and stress
3. **Visual Feedback**: Generate spectrograms or waveforms
4. **Native Comparison**: Compare against native speaker examples
5. **Accent Detection**: Identify and provide accent-specific tips
6. **Multi-language Support**: Extend beyond English
7. **Real-time Feedback**: WebSocket-based streaming analysis
8. **Recording Quality Check**: Detect and warn about poor audio quality

## Testing

To test the endpoint locally:

```bash
# Start the server
cd /Users/matuskalis/vorex-backend
uvicorn app.api2:app --reload --port 8000

# In another terminal, test with curl
curl -X POST http://localhost:8000/api/speech/analyze-pronunciation \
  -H "Authorization: Bearer YOUR_TEST_TOKEN" \
  -F "audio=@test_audio.m4a" \
  -F "target_text=Hello world"
```

## Production Deployment

The endpoint is deployed on Railway and accessible at:

```
https://api.vorex.app/api/speech/analyze-pronunciation
```

Ensure environment variables are set:
- `OPENAI_API_KEY`: For Whisper transcription
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: For token verification

---

**Last Updated**: 2025-12-12
**Version**: 1.0.0
**Maintainer**: Vorex Backend Team
