# Mobile App Integration Guide - Pronunciation Analysis

## Quick Start for Mobile Developers

This guide shows how to integrate the pronunciation analysis endpoint into the Vorex mobile app.

## Endpoint Overview

**Endpoint**: `POST /api/speech/analyze-pronunciation`

**Purpose**: Analyze user pronunciation and provide detailed feedback with phoneme-level analysis.

**Use Cases**:
- Pronunciation practice exercises
- Speaking drills
- Real-time pronunciation feedback
- Progress tracking

## Mobile Integration Flow

```
1. User reads target text
   ↓
2. App records audio
   ↓
3. App uploads audio + target_text to endpoint
   ↓
4. Backend analyzes pronunciation
   ↓
5. App displays scores and feedback
   ↓
6. User sees improvement tips
```

## React Native / TypeScript Example

### 1. Setup API Client

```typescript
// api/pronunciation.ts

interface PronunciationAnalysisRequest {
  audio: File | Blob;
  targetText: string;
}

interface PronunciationAnalysisResponse {
  success: boolean;
  transcript: string;
  overall_score: number;
  pronunciation_score: number;
  fluency_score: number;
  phoneme_analysis: PhonemeAnalysis[];
  word_scores: WordScore[];
  feedback: string;
  words_per_minute: number;
  duration: number;
  word_count: number;
}

interface PhonemeAnalysis {
  word: string;
  phoneme: string;
  status: 'correct' | 'close' | 'incorrect';
  confidence: number;
  expected_ipa: string;
  actual_ipa: string;
}

interface WordScore {
  word: string;
  score: number;
  issues: string[];
}

export async function analyzePronunciation(
  audioBlob: Blob,
  targetText: string,
  token: string
): Promise<PronunciationAnalysisResponse> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.m4a');
  formData.append('target_text', targetText);

  const response = await fetch(`${API_BASE_URL}/api/speech/analyze-pronunciation`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Pronunciation analysis failed');
  }

  return response.json();
}
```

### 2. Recording Audio Component

```typescript
// components/PronunciationRecorder.tsx

import { Audio } from 'expo-av';
import { useState } from 'react';

export function PronunciationRecorder({ targetText, onAnalysisComplete }) {
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const startRecording = async () => {
    try {
      // Request permissions
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) {
        alert('Please grant microphone permissions');
        return;
      }

      // Configure audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Start recording
      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );

      setRecording(recording);
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };

  const stopRecording = async () => {
    if (!recording) return;

    try {
      setIsRecording(false);
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();

      if (uri) {
        await analyzeRecording(uri);
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
    }
  };

  const analyzeRecording = async (uri: string) => {
    setIsAnalyzing(true);

    try {
      // Convert URI to blob
      const response = await fetch(uri);
      const blob = await response.blob();

      // Get auth token
      const token = await getAuthToken(); // Your auth method

      // Analyze pronunciation
      const result = await analyzePronunciation(blob, targetText, token);

      onAnalysisComplete(result);
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Failed to analyze pronunciation. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <View>
      <Text style={styles.targetText}>{targetText}</Text>

      {!isRecording && !isAnalyzing && (
        <Button title="Start Recording" onPress={startRecording} />
      )}

      {isRecording && (
        <Button title="Stop & Analyze" onPress={stopRecording} />
      )}

      {isAnalyzing && (
        <ActivityIndicator size="large" />
      )}
    </View>
  );
}
```

### 3. Results Display Component

```typescript
// components/PronunciationResults.tsx

export function PronunciationResults({ result }: { result: PronunciationAnalysisResponse }) {
  return (
    <ScrollView style={styles.container}>
      {/* Overall Score */}
      <View style={styles.scoreCard}>
        <Text style={styles.scoreTitle}>Overall Score</Text>
        <Text style={styles.scoreValue}>{result.overall_score.toFixed(1)}</Text>
        <ProgressBar progress={result.overall_score / 100} />
      </View>

      {/* Pronunciation & Fluency */}
      <View style={styles.detailScores}>
        <ScoreBox
          label="Pronunciation"
          score={result.pronunciation_score}
          color="#4CAF50"
        />
        <ScoreBox
          label="Fluency"
          score={result.fluency_score}
          color="#2196F3"
        />
      </View>

      {/* Feedback */}
      <View style={styles.feedbackCard}>
        <Text style={styles.feedbackTitle}>Feedback</Text>
        <Text style={styles.feedbackText}>{result.feedback}</Text>
      </View>

      {/* What You Said */}
      <View style={styles.transcriptCard}>
        <Text style={styles.sectionTitle}>What You Said</Text>
        <Text style={styles.transcriptText}>{result.transcript}</Text>
        <Text style={styles.metaText}>
          {result.word_count} words • {result.words_per_minute.toFixed(0)} WPM
        </Text>
      </View>

      {/* Word-by-Word Analysis */}
      <View style={styles.wordsSection}>
        <Text style={styles.sectionTitle}>Word Analysis</Text>
        {result.word_scores.map((word, index) => (
          <WordAnalysisItem key={index} word={word} />
        ))}
      </View>

      {/* Problem Sounds */}
      {result.phoneme_analysis.length > 0 && (
        <View style={styles.phonemesSection}>
          <Text style={styles.sectionTitle}>Sounds to Practice</Text>
          {result.phoneme_analysis
            .filter(p => p.status !== 'correct')
            .map((phoneme, index) => (
              <PhonemeItem key={index} phoneme={phoneme} />
            ))}
        </View>
      )}
    </ScrollView>
  );
}

function ScoreBox({ label, score, color }) {
  return (
    <View style={styles.scoreBox}>
      <Text style={styles.scoreBoxLabel}>{label}</Text>
      <Text style={[styles.scoreBoxValue, { color }]}>
        {score.toFixed(0)}
      </Text>
    </View>
  );
}

function WordAnalysisItem({ word }: { word: WordScore }) {
  const getColor = (score: number) => {
    if (score >= 80) return '#4CAF50'; // Green
    if (score >= 60) return '#FFC107'; // Yellow
    return '#F44336'; // Red
  };

  return (
    <View style={styles.wordItem}>
      <Text style={styles.wordText}>{word.word}</Text>
      <Text style={[styles.wordScore, { color: getColor(word.score) }]}>
        {word.score.toFixed(0)}
      </Text>
      {word.issues.length > 0 && (
        <Text style={styles.wordIssues}>{word.issues.join(', ')}</Text>
      )}
    </View>
  );
}

function PhonemeItem({ phoneme }: { phoneme: PhonemeAnalysis }) {
  const statusColor = {
    correct: '#4CAF50',
    close: '#FFC107',
    incorrect: '#F44336'
  };

  return (
    <View style={styles.phonemeItem}>
      <View style={[styles.statusDot, { backgroundColor: statusColor[phoneme.status] }]} />
      <Text style={styles.phonemeWord}>{phoneme.word}</Text>
      <Text style={styles.phonemeSymbol}>{phoneme.phoneme}</Text>
      <Text style={styles.phonemeStatus}>{phoneme.status}</Text>
    </View>
  );
}
```

## Swift/iOS Example

### 1. API Service

```swift
// PronunciationService.swift

import Foundation

struct PronunciationAnalysisResponse: Codable {
    let success: Bool
    let transcript: String
    let overallScore: Double
    let pronunciationScore: Double
    let fluencyScore: Double
    let phonemeAnalysis: [PhonemeAnalysis]
    let wordScores: [WordScore]
    let feedback: String
    let wordsPerMinute: Double
    let duration: Double
    let wordCount: Int

    enum CodingKeys: String, CodingKey {
        case success, transcript, feedback, duration
        case overallScore = "overall_score"
        case pronunciationScore = "pronunciation_score"
        case fluencyScore = "fluency_score"
        case phonemeAnalysis = "phoneme_analysis"
        case wordScores = "word_scores"
        case wordsPerMinute = "words_per_minute"
        case wordCount = "word_count"
    }
}

struct PhonemeAnalysis: Codable {
    let word: String
    let phoneme: String
    let status: String
    let confidence: Double
    let expectedIpa: String
    let actualIpa: String

    enum CodingKeys: String, CodingKey {
        case word, phoneme, status, confidence
        case expectedIpa = "expected_ipa"
        case actualIpa = "actual_ipa"
    }
}

struct WordScore: Codable {
    let word: String
    let score: Double
    let issues: [String]
}

class PronunciationService {
    static let shared = PronunciationService()
    private let baseURL = "https://api.vorex.app"

    func analyzePronunciation(
        audioURL: URL,
        targetText: String,
        token: String
    ) async throws -> PronunciationAnalysisResponse {
        let endpoint = "\(baseURL)/api/speech/analyze-pronunciation"

        var request = URLRequest(url: URL(string: endpoint)!)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        // Create multipart form data
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // Add audio file
        let audioData = try Data(contentsOf: audioURL)
        body.append("--\(boundary)\r\n")
        body.append("Content-Disposition: form-data; name=\"audio\"; filename=\"recording.m4a\"\r\n")
        body.append("Content-Type: audio/m4a\r\n\r\n")
        body.append(audioData)
        body.append("\r\n")

        // Add target text
        body.append("--\(boundary)\r\n")
        body.append("Content-Disposition: form-data; name=\"target_text\"\r\n\r\n")
        body.append(targetText.data(using: .utf8)!)
        body.append("\r\n")

        body.append("--\(boundary)--\r\n")

        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw NSError(domain: "PronunciationService", code: httpResponse.statusCode, userInfo: [
                NSLocalizedDescriptionKey: errorMessage
            ])
        }

        let decoder = JSONDecoder()
        return try decoder.decode(PronunciationAnalysisResponse.self, from: data)
    }
}

extension Data {
    mutating func append(_ string: String) {
        if let data = string.data(using: .utf8) {
            append(data)
        }
    }
}
```

### 2. SwiftUI View

```swift
// PronunciationPracticeView.swift

import SwiftUI
import AVFoundation

struct PronunciationPracticeView: View {
    let targetText: String
    @StateObject private var recorder = AudioRecorder()
    @State private var result: PronunciationAnalysisResponse?
    @State private var isAnalyzing = false
    @State private var error: String?

    var body: some View {
        VStack(spacing: 20) {
            // Target text
            Text(targetText)
                .font(.title2)
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(10)

            // Recording button
            if !recorder.isRecording && result == nil {
                Button(action: startRecording) {
                    Label("Start Recording", systemImage: "mic.fill")
                        .font(.headline)
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }
            }

            if recorder.isRecording {
                Button(action: stopAndAnalyze) {
                    Label("Stop & Analyze", systemImage: "stop.fill")
                        .font(.headline)
                        .padding()
                        .background(Color.red)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }
            }

            if isAnalyzing {
                ProgressView("Analyzing pronunciation...")
            }

            // Results
            if let result = result {
                PronunciationResultsView(result: result)
            }

            if let error = error {
                Text(error)
                    .foregroundColor(.red)
                    .padding()
            }
        }
        .padding()
    }

    func startRecording() {
        recorder.startRecording()
    }

    func stopAndAnalyze() {
        recorder.stopRecording()

        guard let audioURL = recorder.recordingURL else { return }

        isAnalyzing = true
        error = nil

        Task {
            do {
                let token = try await AuthService.shared.getToken()
                let analysisResult = try await PronunciationService.shared.analyzePronunciation(
                    audioURL: audioURL,
                    targetText: targetText,
                    token: token
                )
                await MainActor.run {
                    self.result = analysisResult
                    self.isAnalyzing = false
                }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                    self.isAnalyzing = false
                }
            }
        }
    }
}
```

## Best Practices

### 1. Audio Recording
- Use high quality recording settings (44.1kHz, AAC)
- Keep recordings between 5-30 seconds
- Ensure quiet environment for best results
- Handle microphone permissions gracefully

### 2. Error Handling
```typescript
try {
  const result = await analyzePronunciation(audioBlob, targetText, token);
  // Success
} catch (error) {
  if (error.message.includes('Empty audio')) {
    showError('Please record some audio first');
  } else if (error.message.includes('target_text')) {
    showError('Invalid exercise text');
  } else if (error.message.includes('401')) {
    // Re-authenticate
    await refreshToken();
  } else {
    showError('Analysis failed. Please try again.');
  }
}
```

### 3. Progress Tracking
Store results locally for progress visualization:

```typescript
// Store result in local storage or state management
const storeResult = async (result: PronunciationAnalysisResponse) => {
  const history = await getPronunciationHistory();
  history.push({
    timestamp: Date.now(),
    targetText: targetText,
    score: result.overall_score,
    weakPhonemes: result.phoneme_analysis
      .filter(p => p.status !== 'correct')
      .map(p => p.phoneme)
  });
  await savePronunciationHistory(history);
};
```

### 4. Offline Handling
```typescript
const analyzePronunciationWithRetry = async (blob: Blob, text: string, token: string) => {
  if (!navigator.onLine) {
    // Queue for later
    await queuePronunciationAnalysis({ blob, text, timestamp: Date.now() });
    throw new Error('You are offline. Analysis will be processed when connection is restored.');
  }

  try {
    return await analyzePronunciation(blob, text, token);
  } catch (error) {
    // Queue for retry
    await queuePronunciationAnalysis({ blob, text, timestamp: Date.now() });
    throw error;
  }
};
```

## UI/UX Recommendations

1. **Visual Feedback**: Use colors to indicate score ranges (green/yellow/red)
2. **Progressive Disclosure**: Show overall score first, then details on tap
3. **Encouragement**: Always include positive feedback, even for low scores
4. **Practice Tips**: Display specific, actionable tips from the `word_scores` issues
5. **Progress Charts**: Show improvement over time using historical data
6. **Audio Playback**: Let users replay their recording
7. **Compare**: Show target text vs transcript side-by-side

## Performance Tips

- Compress audio before upload (if > 1MB)
- Show loading state immediately on upload
- Cache results for recently practiced phrases
- Use pagination for pronunciation history
- Implement request timeout (30 seconds recommended)

---

**Need Help?** Check the main documentation at `PRONUNCIATION_ANALYSIS_ENDPOINT.md`
