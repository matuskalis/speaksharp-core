-- Migration 016: Enhanced User Language Profile System
-- Tracks detailed language weaknesses for adaptive AI tutoring

-- =============================================================================
-- Grammar Weaknesses Table
-- Tracks specific grammar errors by type with frequency and improvement tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS grammar_weaknesses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,

  -- Error classification
  error_type VARCHAR(100) NOT NULL,  -- 'article_usage', 'past_perfect', 'subject_verb_agreement', etc.
  error_category VARCHAR(50) NOT NULL,  -- 'tense', 'articles', 'prepositions', 'word_order', etc.

  -- Tracking metrics
  error_count INTEGER DEFAULT 1,
  correct_count INTEGER DEFAULT 0,  -- Times used correctly after error was identified
  last_error_at TIMESTAMP DEFAULT NOW(),
  last_correct_at TIMESTAMP,
  first_seen_at TIMESTAMP DEFAULT NOW(),

  -- Learning status
  improving BOOLEAN DEFAULT FALSE,  -- True if error_rate is decreasing
  mastered BOOLEAN DEFAULT FALSE,   -- True if consistently correct

  -- Example tracking (for review)
  example_errors JSONB DEFAULT '[]'::JSONB,  -- Last 5 error examples

  -- Context
  native_language_related BOOLEAN DEFAULT FALSE,  -- L1 interference

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(user_id, error_type)
);

CREATE INDEX idx_grammar_weaknesses_user ON grammar_weaknesses(user_id);
CREATE INDEX idx_grammar_weaknesses_category ON grammar_weaknesses(user_id, error_category);

-- =============================================================================
-- Phonetic Weaknesses Table
-- Tracks pronunciation issues at the phoneme level (IPA-based)
-- =============================================================================
CREATE TABLE IF NOT EXISTS phonetic_weaknesses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,

  -- Phoneme data (IPA)
  target_phoneme VARCHAR(10) NOT NULL,  -- The correct phoneme, e.g., 'θ', 'ð', 'ɪ'
  confused_with VARCHAR(10)[],  -- Phonemes commonly substituted, e.g., ['f', 't'] for 'θ'

  -- Position in word
  position VARCHAR(20) DEFAULT 'any',  -- 'initial', 'medial', 'final', 'any'

  -- Tracking metrics
  error_count INTEGER DEFAULT 1,
  correct_count INTEGER DEFAULT 0,
  error_rate FLOAT DEFAULT 1.0,  -- error_count / (error_count + correct_count)

  -- Example words
  problem_words TEXT[] DEFAULT '{}',  -- Words where this phoneme is problematic

  -- L1 interference
  native_language_predicted BOOLEAN DEFAULT FALSE,  -- Expected based on native language

  last_practiced TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(user_id, target_phoneme, position)
);

CREATE INDEX idx_phonetic_weaknesses_user ON phonetic_weaknesses(user_id);

-- =============================================================================
-- CEFR Skill Tracking Table
-- Tracks CEFR level per skill (more granular than overall level)
-- =============================================================================
CREATE TABLE IF NOT EXISTS cefr_skill_levels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,

  -- Skill breakdown
  speaking_level VARCHAR(5) DEFAULT 'A1',
  listening_level VARCHAR(5) DEFAULT 'A1',
  grammar_level VARCHAR(5) DEFAULT 'A1',
  vocabulary_level VARCHAR(5) DEFAULT 'A1',
  pronunciation_level VARCHAR(5) DEFAULT 'A1',
  fluency_level VARCHAR(5) DEFAULT 'A1',

  -- Confidence scores (0-1) - how certain are we of these levels
  speaking_confidence FLOAT DEFAULT 0.3,
  listening_confidence FLOAT DEFAULT 0.3,
  grammar_confidence FLOAT DEFAULT 0.3,
  vocabulary_confidence FLOAT DEFAULT 0.3,
  pronunciation_confidence FLOAT DEFAULT 0.3,
  fluency_confidence FLOAT DEFAULT 0.3,

  -- Assessment history
  last_speaking_assessment TIMESTAMP,
  last_grammar_assessment TIMESTAMP,
  last_vocabulary_assessment TIMESTAMP,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(user_id)
);

-- =============================================================================
-- Vocabulary Gaps Table
-- Tracks words user has struggled with or looked up
-- =============================================================================
CREATE TABLE IF NOT EXISTS vocabulary_gaps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,

  word VARCHAR(100) NOT NULL,
  word_type VARCHAR(20),  -- 'noun', 'verb', 'adjective', etc.
  cefr_level VARCHAR(5),  -- Level of this word

  -- Context
  context_sentence TEXT,  -- Where they encountered/struggled
  definition TEXT,

  -- Tracking
  lookup_count INTEGER DEFAULT 1,
  usage_attempts INTEGER DEFAULT 0,
  correct_usage_count INTEGER DEFAULT 0,

  -- Status
  status VARCHAR(20) DEFAULT 'new',  -- 'new', 'learning', 'known'

  created_at TIMESTAMP DEFAULT NOW(),
  last_seen_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(user_id, word)
);

CREATE INDEX idx_vocabulary_gaps_user ON vocabulary_gaps(user_id);
CREATE INDEX idx_vocabulary_gaps_status ON vocabulary_gaps(user_id, status);

-- =============================================================================
-- L1 Interference Patterns (predefined by native language)
-- =============================================================================
CREATE TABLE IF NOT EXISTS l1_interference_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  native_language VARCHAR(50) NOT NULL,

  -- Expected difficulties
  phoneme_difficulties JSONB DEFAULT '[]'::JSONB,  -- Expected phoneme issues
  grammar_difficulties JSONB DEFAULT '[]'::JSONB,  -- Expected grammar issues
  word_order_issues JSONB DEFAULT '[]'::JSONB,
  false_friends JSONB DEFAULT '[]'::JSONB,  -- Words that look similar but mean different

  -- Tips for tutoring
  teaching_tips TEXT[],

  created_at TIMESTAMP DEFAULT NOW()
);

-- Insert common L1 interference patterns
INSERT INTO l1_interference_patterns (native_language, phoneme_difficulties, grammar_difficulties, teaching_tips)
VALUES
  ('spanish',
   '[{"phoneme": "v", "confused_with": ["b"], "note": "Spanish doesn''t distinguish v/b"},
     {"phoneme": "θ", "confused_with": ["s", "t"], "note": "th sound difficult"},
     {"phoneme": "ʃ", "confused_with": ["tʃ"], "note": "sh vs ch confusion"},
     {"phoneme": "dʒ", "confused_with": ["j", "ʒ"], "note": "j sound varies"},
     {"phoneme": "ɪ", "confused_with": ["iː"], "note": "Short i vs long ee"}]',
   '[{"type": "article_usage", "note": "Spanish uses articles differently with abstract nouns"},
     {"type": "adjective_position", "note": "Spanish places adjectives after nouns"},
     {"type": "ser_estar_confusion", "note": "Two verbs for to be causes is/am/are confusion"},
     {"type": "double_negative", "note": "Spanish allows double negatives"}]',
   ARRAY['Practice minimal pairs: bet/vet, ship/chip', 'Focus on th sounds in common words', 'Use adjective-noun order drills']
  ),
  ('chinese',
   '[{"phoneme": "θ", "confused_with": ["s", "f"], "note": "th sound doesn''t exist"},
     {"phoneme": "ð", "confused_with": ["d", "z"], "note": "Voiced th difficult"},
     {"phoneme": "r", "confused_with": ["l"], "note": "r/l distinction"},
     {"phoneme": "v", "confused_with": ["w"], "note": "v sound doesn''t exist"},
     {"phoneme": "ŋ", "confused_with": ["n"], "note": "Final ng sound"}]',
   '[{"type": "articles", "note": "No articles in Chinese - all articles are challenging"},
     {"type": "plurals", "note": "No plural markers in Chinese"},
     {"type": "verb_tenses", "note": "No tense marking in Chinese - all tenses challenging"},
     {"type": "prepositions", "note": "Preposition usage very different"}]',
   ARRAY['Extra focus on articles (a/an/the)', 'Practice plural forms', 'Verb tense timeline exercises']
  ),
  ('japanese',
   '[{"phoneme": "l", "confused_with": ["r"], "note": "No l/r distinction in Japanese"},
     {"phoneme": "θ", "confused_with": ["s"], "note": "th becomes s"},
     {"phoneme": "v", "confused_with": ["b"], "note": "No v sound"},
     {"phoneme": "f", "confused_with": ["h"], "note": "f is weak in Japanese"}]',
   '[{"type": "articles", "note": "No articles in Japanese"},
     {"type": "plurals", "note": "No plurals in Japanese"},
     {"type": "subject_omission", "note": "Japanese often drops subjects"}]',
   ARRAY['l/r minimal pairs practice', 'Subject practice - always include I/you/he/she']
  ),
  ('portuguese',
   '[{"phoneme": "h", "confused_with": ["silent"], "note": "h is often silent"},
     {"phoneme": "θ", "confused_with": ["t", "f"], "note": "th sound doesn''t exist"},
     {"phoneme": "æ", "confused_with": ["ɛ"], "note": "a in cat sound"}]',
   '[{"type": "present_continuous", "note": "Overuse of present continuous"},
     {"type": "do_support", "note": "Questions without do/does"},
     {"type": "prepositions", "note": "em vs in/on/at confusion"}]',
   ARRAY['Question formation drills', 'Present simple vs continuous practice']
  ),
  ('russian',
   '[{"phoneme": "θ", "confused_with": ["s", "f"], "note": "th sound doesn''t exist"},
     {"phoneme": "w", "confused_with": ["v"], "note": "No w sound in Russian"},
     {"phoneme": "ŋ", "confused_with": ["ng"], "note": "ng pronounced separately"}]',
   '[{"type": "articles", "note": "No articles in Russian - all articles challenging"},
     {"type": "be_verb", "note": "is/am/are often omitted"},
     {"type": "aspect", "note": "Verb aspect confusion with tenses"}]',
   ARRAY['Articles practice with every noun', 'To be drills']
  ),
  ('arabic',
   '[{"phoneme": "p", "confused_with": ["b"], "note": "No p sound - becomes b"},
     {"phoneme": "v", "confused_with": ["f"], "note": "No v sound"},
     {"phoneme": "ɪ", "confused_with": ["iː"], "note": "Short vowel distinction"}]',
   '[{"type": "be_verb", "note": "No present tense be verb in Arabic"},
     {"type": "articles", "note": "Different article system"},
     {"type": "word_order", "note": "VSO word order transfer"}]',
   ARRAY['p/b minimal pairs', 'To be practice']
  )
ON CONFLICT DO NOTHING;

-- =============================================================================
-- Functions for Language Profile Management
-- =============================================================================

-- Function: Record a grammar error
CREATE OR REPLACE FUNCTION record_grammar_error(
  p_user_id UUID,
  p_error_type VARCHAR,
  p_error_category VARCHAR,
  p_user_sentence TEXT,
  p_corrected_sentence TEXT,
  p_native_language_related BOOLEAN DEFAULT FALSE
)
RETURNS UUID
AS $$
DECLARE
  v_id UUID;
  v_example_errors JSONB;
BEGIN
  -- Get existing examples or empty array
  SELECT COALESCE(example_errors, '[]'::JSONB)
  INTO v_example_errors
  FROM grammar_weaknesses
  WHERE user_id = p_user_id AND error_type = p_error_type;

  -- Add new example (keep last 5)
  v_example_errors := (
    SELECT jsonb_agg(e)
    FROM (
      SELECT e FROM jsonb_array_elements(v_example_errors) e
      UNION ALL
      SELECT jsonb_build_object(
        'user', p_user_sentence,
        'correct', p_corrected_sentence,
        'at', NOW()
      )
      ORDER BY e->>'at' DESC
      LIMIT 5
    ) sub
  );

  -- Upsert the grammar weakness
  INSERT INTO grammar_weaknesses (
    user_id, error_type, error_category, example_errors, native_language_related
  )
  VALUES (
    p_user_id, p_error_type, p_error_category,
    COALESCE(v_example_errors, '[]'::JSONB), p_native_language_related
  )
  ON CONFLICT (user_id, error_type) DO UPDATE SET
    error_count = grammar_weaknesses.error_count + 1,
    last_error_at = NOW(),
    example_errors = EXCLUDED.example_errors,
    improving = CASE
      WHEN grammar_weaknesses.error_count > 5
        AND grammar_weaknesses.correct_count > grammar_weaknesses.error_count
      THEN TRUE
      ELSE FALSE
    END,
    updated_at = NOW()
  RETURNING id INTO v_id;

  RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Record correct grammar usage
CREATE OR REPLACE FUNCTION record_grammar_correct(
  p_user_id UUID,
  p_error_type VARCHAR
)
RETURNS VOID
AS $$
BEGIN
  UPDATE grammar_weaknesses
  SET
    correct_count = correct_count + 1,
    last_correct_at = NOW(),
    improving = CASE
      WHEN correct_count > error_count * 2 THEN TRUE
      ELSE improving
    END,
    mastered = CASE
      WHEN correct_count > error_count * 5 AND error_count > 3 THEN TRUE
      ELSE FALSE
    END,
    updated_at = NOW()
  WHERE user_id = p_user_id AND error_type = p_error_type;
END;
$$ LANGUAGE plpgsql;

-- Function: Record phoneme error
CREATE OR REPLACE FUNCTION record_phoneme_error(
  p_user_id UUID,
  p_target_phoneme VARCHAR,
  p_confused_with VARCHAR,
  p_problem_word TEXT,
  p_position VARCHAR DEFAULT 'any'
)
RETURNS UUID
AS $$
DECLARE
  v_id UUID;
  v_confused_with VARCHAR[];
  v_problem_words TEXT[];
BEGIN
  -- Get existing data
  SELECT confused_with, problem_words
  INTO v_confused_with, v_problem_words
  FROM phonetic_weaknesses
  WHERE user_id = p_user_id AND target_phoneme = p_target_phoneme AND position = p_position;

  -- Add to arrays if not exists
  IF p_confused_with IS NOT NULL AND NOT (p_confused_with = ANY(COALESCE(v_confused_with, '{}'))) THEN
    v_confused_with := array_append(COALESCE(v_confused_with, '{}'), p_confused_with);
  END IF;

  IF p_problem_word IS NOT NULL AND NOT (p_problem_word = ANY(COALESCE(v_problem_words, '{}'))) THEN
    v_problem_words := array_append(COALESCE(v_problem_words, '{}'), p_problem_word);
    -- Keep last 10 problem words
    IF array_length(v_problem_words, 1) > 10 THEN
      v_problem_words := v_problem_words[array_length(v_problem_words, 1)-9:];
    END IF;
  END IF;

  -- Upsert
  INSERT INTO phonetic_weaknesses (
    user_id, target_phoneme, confused_with, problem_words, position
  )
  VALUES (
    p_user_id, p_target_phoneme, COALESCE(v_confused_with, ARRAY[p_confused_with]),
    COALESCE(v_problem_words, ARRAY[p_problem_word]), p_position
  )
  ON CONFLICT (user_id, target_phoneme, position) DO UPDATE SET
    error_count = phonetic_weaknesses.error_count + 1,
    confused_with = EXCLUDED.confused_with,
    problem_words = EXCLUDED.problem_words,
    error_rate = (phonetic_weaknesses.error_count + 1)::FLOAT /
                 (phonetic_weaknesses.error_count + 1 + phonetic_weaknesses.correct_count),
    last_practiced = NOW(),
    updated_at = NOW()
  RETURNING id INTO v_id;

  RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Get user language profile for AI prompt injection
CREATE OR REPLACE FUNCTION get_user_language_profile(p_user_id UUID)
RETURNS JSONB
AS $$
DECLARE
  v_profile JSONB;
  v_user_record RECORD;
  v_grammar_weaknesses JSONB;
  v_phonetic_weaknesses JSONB;
  v_cefr_levels JSONB;
  v_l1_patterns JSONB;
BEGIN
  -- Get user basic info
  SELECT native_language, level
  INTO v_user_record
  FROM user_profiles
  WHERE user_id = p_user_id;

  -- Get top 5 grammar weaknesses (most frequent, not mastered)
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'type', error_type,
    'category', error_category,
    'count', error_count,
    'improving', improving,
    'example', example_errors->0
  ) ORDER BY error_count DESC), '[]'::JSONB)
  INTO v_grammar_weaknesses
  FROM (
    SELECT * FROM grammar_weaknesses
    WHERE user_id = p_user_id AND mastered = FALSE
    ORDER BY error_count DESC
    LIMIT 5
  ) g;

  -- Get phonetic weaknesses
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'phoneme', target_phoneme,
    'confused_with', confused_with,
    'error_rate', ROUND(error_rate::NUMERIC, 2),
    'problem_words', problem_words[1:3]
  ) ORDER BY error_rate DESC), '[]'::JSONB)
  INTO v_phonetic_weaknesses
  FROM (
    SELECT * FROM phonetic_weaknesses
    WHERE user_id = p_user_id AND error_rate > 0.3
    ORDER BY error_rate DESC
    LIMIT 5
  ) p;

  -- Get CEFR levels
  SELECT jsonb_build_object(
    'speaking', speaking_level,
    'listening', listening_level,
    'grammar', grammar_level,
    'vocabulary', vocabulary_level,
    'pronunciation', pronunciation_level,
    'fluency', fluency_level
  )
  INTO v_cefr_levels
  FROM cefr_skill_levels
  WHERE user_id = p_user_id;

  -- Get L1 patterns if native language known
  IF v_user_record.native_language IS NOT NULL THEN
    SELECT jsonb_build_object(
      'expected_phoneme_issues', phoneme_difficulties,
      'expected_grammar_issues', grammar_difficulties,
      'teaching_tips', teaching_tips
    )
    INTO v_l1_patterns
    FROM l1_interference_patterns
    WHERE LOWER(native_language) = LOWER(v_user_record.native_language);
  END IF;

  -- Build complete profile
  v_profile := jsonb_build_object(
    'user_id', p_user_id,
    'native_language', v_user_record.native_language,
    'overall_level', v_user_record.level,
    'cefr_by_skill', COALESCE(v_cefr_levels, '{}'::JSONB),
    'grammar_weaknesses', v_grammar_weaknesses,
    'phonetic_weaknesses', v_phonetic_weaknesses,
    'l1_patterns', COALESCE(v_l1_patterns, '{}'::JSONB)
  );

  RETURN v_profile;
END;
$$ LANGUAGE plpgsql;

-- Create CEFR levels entry for new users (trigger)
CREATE OR REPLACE FUNCTION create_cefr_levels_for_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO cefr_skill_levels (user_id, speaking_level, listening_level, grammar_level, vocabulary_level)
  VALUES (NEW.user_id, NEW.level, NEW.level, NEW.level, NEW.level)
  ON CONFLICT (user_id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_create_cefr_levels ON user_profiles;
CREATE TRIGGER trigger_create_cefr_levels
  AFTER INSERT ON user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION create_cefr_levels_for_new_user();

-- Comments
COMMENT ON TABLE grammar_weaknesses IS 'Tracks specific grammar errors by type with frequency, improvement status, and examples';
COMMENT ON TABLE phonetic_weaknesses IS 'Tracks pronunciation issues at the IPA phoneme level';
COMMENT ON TABLE cefr_skill_levels IS 'Per-skill CEFR level tracking (speaking, grammar, vocabulary, etc.)';
COMMENT ON TABLE vocabulary_gaps IS 'Words the user has struggled with or looked up';
COMMENT ON TABLE l1_interference_patterns IS 'Predefined L1 interference patterns by native language';
COMMENT ON FUNCTION get_user_language_profile IS 'Returns complete user language profile for AI prompt injection';
