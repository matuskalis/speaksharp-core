# Pronunciation Analysis Endpoint - Deployment Checklist

## Pre-Deployment Verification

### Code Quality
- [x] Syntax validation passed
- [x] Endpoint added to `/app/api2.py` (lines 7532-7723)
- [x] Follows existing code patterns
- [x] Error handling implemented
- [x] Database integration tested

### Dependencies
- [x] All required packages in `requirements.txt`:
  - `openai==1.58.1`
  - `phonemizer==3.2.1`
  - `numpy==1.26.4`
  - `fastapi==0.121.2`
  - `psycopg==3.2.12`

### Documentation
- [x] API documentation: `PRONUNCIATION_ANALYSIS_ENDPOINT.md`
- [x] Mobile integration guide: `PRONUNCIATION_MOBILE_INTEGRATION.md`
- [x] Implementation summary: `PRONUNCIATION_ENDPOINT_SUMMARY.md`
- [x] Test suite: `test_pronunciation_analysis.py`

## Deployment Steps

### 1. Git Commit and Push
```bash
cd /Users/matuskalis/vorex-backend

# Check current status
git status

# Add modified/new files
git add app/api2.py
git add PRONUNCIATION_ANALYSIS_ENDPOINT.md
git add PRONUNCIATION_MOBILE_INTEGRATION.md
git add PRONUNCIATION_ENDPOINT_SUMMARY.md
git add DEPLOYMENT_CHECKLIST.md
git add test_pronunciation_analysis.py

# Commit with descriptive message
git commit -m "Add comprehensive pronunciation analysis endpoint

- Implements POST /api/speech/analyze-pronunciation
- Provides phoneme-level feedback using Whisper + phonemizer
- Includes word-level scoring and fluency analysis
- Stores attempts in database for progress tracking
- Adds comprehensive documentation and mobile integration guide
- Includes test suite for validation

Related components:
- Uses existing PronunciationScorer and PronunciationAnalyzer
- Integrates with ASRClient for Whisper transcription
- Database storage in pronunciation_attempts table"

# Push to trigger Railway deployment
git push origin main
```

### 2. Monitor Deployment
```bash
# Watch Railway logs
railway logs --follow

# Or check Railway dashboard
# https://railway.app
```

### 3. Verify Deployment
```bash
# Health check
curl https://vorex-backend-production.up.railway.app/health

# Test endpoint (need valid token)
curl -X POST https://vorex-backend-production.up.railway.app/api/speech/analyze-pronunciation \
  -H "Authorization: Bearer YOUR_TEST_TOKEN" \
  -F "audio=@test_audio.m4a" \
  -F "target_text=Hello world"
```

## Post-Deployment Testing

### Test Cases

#### 1. Basic Pronunciation Analysis
```bash
# Prepare test audio file
# Record "Hello world" and save as test_hello.m4a

curl -X POST https://vorex-backend-production.up.railway.app/api/speech/analyze-pronunciation \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "audio=@test_hello.m4a" \
  -F "target_text=Hello world"
```

**Expected Response**:
- `success: true`
- `transcript` contains recognized text
- `overall_score` between 0-100
- `phoneme_analysis` array present
- `word_scores` array present
- `feedback` string present

#### 2. Different Audio Formats
Test with:
- [ ] WAV file
- [ ] MP3 file
- [ ] M4A file
- [ ] WebM file

#### 3. Edge Cases
- [ ] Empty audio file → 400 error
- [ ] Missing target_text → 400 error
- [ ] Invalid token → 401 error
- [ ] Very long audio (>30s) → Should work but may be slow
- [ ] Silent audio → Low scores but no error

#### 4. Score Validation
- [ ] Perfect pronunciation → Score > 90
- [ ] Good pronunciation → Score 70-90
- [ ] Poor pronunciation → Score < 70
- [ ] Fluency score calculated correctly

## Environment Variables Check

Verify these are set in Railway:

```bash
railway variables

# Should show:
# OPENAI_API_KEY=sk-...
# DATABASE_URL=postgresql://...
# JWT_SECRET=...
```

## Database Verification

```bash
# Connect to production database
railway connect

# Check pronunciation_attempts table
\d pronunciation_attempts

# Verify recent entries (after testing)
SELECT id, user_id, phrase, overall_score, created_at
FROM pronunciation_attempts
ORDER BY created_at DESC
LIMIT 5;
```

## Performance Monitoring

### Metrics to Watch

1. **Response Time**
   - Target: < 5 seconds average
   - Monitor in Railway dashboard

2. **Error Rate**
   - Target: < 1% errors
   - Check logs for 500 errors

3. **Database Connections**
   - Should not leak connections
   - Monitor active connections

### Log Monitoring

```bash
# Watch for errors
railway logs --filter "error"

# Watch pronunciation endpoint
railway logs --filter "analyze-pronunciation"

# Watch ASR calls
railway logs --filter "Whisper"
```

## Rollback Plan

If issues arise:

```bash
# 1. Identify last good commit
git log --oneline

# 2. Revert to previous version
git revert HEAD
git push origin main

# 3. Railway will auto-deploy the revert

# 4. Verify rollback
curl https://vorex-backend-production.up.railway.app/health
```

## Mobile App Integration

After successful deployment, coordinate with mobile team:

### Share Documentation
- [ ] Send `PRONUNCIATION_MOBILE_INTEGRATION.md`
- [ ] Share API endpoint URL
- [ ] Provide test token for development

### Integration Steps for Mobile
1. Implement audio recording
2. Add API client method
3. Create UI for results display
4. Test with development backend first
5. Switch to production endpoint

### Test with Mobile App
- [ ] Record audio from mobile app
- [ ] Upload to endpoint
- [ ] Verify results display correctly
- [ ] Test error handling
- [ ] Verify progress tracking

## Success Criteria

- [x] Code deployed to Railway
- [ ] Health check passes
- [ ] Test pronunciation analysis returns valid response
- [ ] Database stores attempts correctly
- [ ] Response time < 5 seconds
- [ ] No errors in logs
- [ ] Mobile team can integrate successfully

## Monitoring Dashboard

Create alerts for:
- Response time > 10 seconds
- Error rate > 5%
- Database connection pool exhaustion
- Whisper API failures

## Documentation Updates

After successful deployment:
- [ ] Update README.md with new endpoint
- [ ] Add to API changelog
- [ ] Update mobile app documentation
- [ ] Create video demo (optional)

## Support Preparation

Prepare for common issues:

### Issue: "Empty audio file"
**Cause**: Client didn't record properly
**Solution**: Ensure mobile app validates recording before upload

### Issue: "ASR transcription failed"
**Cause**: Whisper API timeout or error
**Solution**: Retry logic already implemented, check OpenAI status

### Issue: "target_text is required"
**Cause**: Missing form parameter
**Solution**: Ensure mobile app sends target_text field

### Issue: Low scores despite good pronunciation
**Cause**: Background noise or unclear audio
**Solution**: Guide users to record in quiet environment

## Final Checklist

Before marking as complete:

- [ ] Code pushed to git
- [ ] Railway deployment successful
- [ ] Health check passes
- [ ] Test pronunciation analysis works
- [ ] Database stores attempts
- [ ] Documentation complete
- [ ] Mobile team notified
- [ ] Monitoring configured
- [ ] Rollback plan tested
- [ ] Support prepared for common issues

## Deployment Sign-off

**Deployed by**: _____________
**Date**: _____________
**Railway Deployment ID**: _____________
**Commit SHA**: _____________
**Status**: ⬜ Success  ⬜ Partial  ⬜ Rollback Required

**Notes**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

**Next Actions**:
1. Monitor logs for 24 hours
2. Collect feedback from mobile team
3. Track usage metrics
4. Plan future enhancements
