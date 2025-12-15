"""
Skill-Based Unlocks System.

Gamified progression system that:
- Tracks skill mastery across grammar, vocabulary, pronunciation
- Unlocks new content as users demonstrate competency
- Awards achievements for milestones
- Provides clear progression paths
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timedelta
from enum import Enum
import json


class SkillCategory(str, Enum):
    """Main skill categories."""
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    PRONUNCIATION = "pronunciation"
    FLUENCY = "fluency"
    LISTENING = "listening"
    CONVERSATION = "conversation"


class UnlockType(str, Enum):
    """Types of unlockable content."""
    SCENARIO = "scenario"
    LESSON = "lesson"
    TOPIC = "topic"
    FEATURE = "feature"
    ACHIEVEMENT = "achievement"


@dataclass
class SkillRequirement:
    """A single requirement for unlocking content."""
    skill_id: str
    min_level: int = 1
    min_xp: int = 0
    min_accuracy: float = 0.0  # 0-100


@dataclass
class UnlockableContent:
    """Content that can be unlocked."""
    id: str
    name: str
    description: str
    unlock_type: UnlockType
    requirements: List[SkillRequirement]
    xp_reward: int = 0
    icon: str = "🔒"
    unlocked_icon: str = "✨"
    order: int = 0  # For sorting in UI

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.unlock_type.value,
            "requirements": [
                {
                    "skill_id": r.skill_id,
                    "min_level": r.min_level,
                    "min_xp": r.min_xp,
                    "min_accuracy": r.min_accuracy,
                }
                for r in self.requirements
            ],
            "xp_reward": self.xp_reward,
            "icon": self.icon,
            "unlocked_icon": self.unlocked_icon,
            "order": self.order,
        }


@dataclass
class Achievement:
    """User achievement/badge."""
    id: str
    name: str
    description: str
    icon: str
    category: SkillCategory
    criteria: Dict[str, Any]  # Flexible criteria
    xp_reward: int = 50
    rarity: str = "common"  # common, uncommon, rare, epic, legendary

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category.value,
            "criteria": self.criteria,
            "xp_reward": self.xp_reward,
            "rarity": self.rarity,
        }


@dataclass
class SkillProgress:
    """User's progress in a specific skill."""
    skill_id: str
    category: SkillCategory
    level: int = 1
    xp: int = 0
    xp_to_next_level: int = 100
    total_attempts: int = 0
    successful_attempts: int = 0
    streak_days: int = 0
    last_practiced: Optional[datetime] = None

    @property
    def accuracy(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_attempts / self.total_attempts) * 100

    @property
    def progress_percent(self) -> float:
        return min(100, (self.xp / self.xp_to_next_level) * 100)

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "category": self.category.value,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next_level": self.xp_to_next_level,
            "progress_percent": self.progress_percent,
            "accuracy": round(self.accuracy, 1),
            "streak_days": self.streak_days,
            "last_practiced": self.last_practiced.isoformat() if self.last_practiced else None,
        }


@dataclass
class UserSkillProfile:
    """Complete skill profile for a user."""
    user_id: str
    total_xp: int = 0
    overall_level: int = 1
    skills: Dict[str, SkillProgress] = field(default_factory=dict)
    unlocked_content: Set[str] = field(default_factory=set)
    earned_achievements: Set[str] = field(default_factory=set)
    daily_xp: int = 0
    daily_xp_cap: int = 500
    last_daily_reset: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "total_xp": self.total_xp,
            "overall_level": self.overall_level,
            "skills": {k: v.to_dict() for k, v in self.skills.items()},
            "unlocked_content": list(self.unlocked_content),
            "earned_achievements": list(self.earned_achievements),
            "daily_xp": self.daily_xp,
            "daily_xp_cap": self.daily_xp_cap,
        }


# =============================================================================
# Skill Definitions
# =============================================================================

SKILL_DEFINITIONS = {
    # Grammar Skills
    "grammar_tenses": {
        "name": "Verb Tenses",
        "category": SkillCategory.GRAMMAR,
        "description": "Master past, present, and future tenses",
        "base_xp_per_level": 100,
    },
    "grammar_articles": {
        "name": "Articles & Determiners",
        "category": SkillCategory.GRAMMAR,
        "description": "Use a, an, the correctly",
        "base_xp_per_level": 80,
    },
    "grammar_prepositions": {
        "name": "Prepositions",
        "category": SkillCategory.GRAMMAR,
        "description": "Master in, on, at, and more",
        "base_xp_per_level": 90,
    },
    "grammar_conditionals": {
        "name": "Conditionals",
        "category": SkillCategory.GRAMMAR,
        "description": "If clauses and hypotheticals",
        "base_xp_per_level": 120,
    },
    "grammar_modals": {
        "name": "Modal Verbs",
        "category": SkillCategory.GRAMMAR,
        "description": "Can, could, should, would, etc.",
        "base_xp_per_level": 100,
    },

    # Pronunciation Skills
    "pronunciation_vowels": {
        "name": "Vowel Sounds",
        "category": SkillCategory.PRONUNCIATION,
        "description": "Clear vowel pronunciation",
        "base_xp_per_level": 100,
    },
    "pronunciation_consonants": {
        "name": "Consonant Sounds",
        "category": SkillCategory.PRONUNCIATION,
        "description": "Tricky consonant clusters",
        "base_xp_per_level": 100,
    },
    "pronunciation_stress": {
        "name": "Word Stress",
        "category": SkillCategory.PRONUNCIATION,
        "description": "Emphasize the right syllables",
        "base_xp_per_level": 110,
    },
    "pronunciation_intonation": {
        "name": "Intonation",
        "category": SkillCategory.PRONUNCIATION,
        "description": "Natural speech melody",
        "base_xp_per_level": 120,
    },

    # Vocabulary Skills
    "vocabulary_basics": {
        "name": "Essential Words",
        "category": SkillCategory.VOCABULARY,
        "description": "Most common 1000 words",
        "base_xp_per_level": 80,
    },
    "vocabulary_business": {
        "name": "Business English",
        "category": SkillCategory.VOCABULARY,
        "description": "Professional vocabulary",
        "base_xp_per_level": 100,
    },
    "vocabulary_academic": {
        "name": "Academic English",
        "category": SkillCategory.VOCABULARY,
        "description": "Formal and scholarly terms",
        "base_xp_per_level": 110,
    },
    "vocabulary_idioms": {
        "name": "Idioms & Expressions",
        "category": SkillCategory.VOCABULARY,
        "description": "Common phrases and sayings",
        "base_xp_per_level": 100,
    },

    # Fluency Skills
    "fluency_speed": {
        "name": "Speaking Speed",
        "category": SkillCategory.FLUENCY,
        "description": "Natural conversation pace",
        "base_xp_per_level": 100,
    },
    "fluency_coherence": {
        "name": "Coherence",
        "category": SkillCategory.FLUENCY,
        "description": "Organize thoughts clearly",
        "base_xp_per_level": 110,
    },

    # Conversation Skills
    "conversation_casual": {
        "name": "Casual Chat",
        "category": SkillCategory.CONVERSATION,
        "description": "Everyday conversations",
        "base_xp_per_level": 80,
    },
    "conversation_formal": {
        "name": "Formal Situations",
        "category": SkillCategory.CONVERSATION,
        "description": "Professional and formal dialogue",
        "base_xp_per_level": 100,
    },
    "conversation_debate": {
        "name": "Discussion & Debate",
        "category": SkillCategory.CONVERSATION,
        "description": "Express and defend opinions",
        "base_xp_per_level": 120,
    },
}


# =============================================================================
# Unlockable Content Definitions
# =============================================================================

UNLOCKABLE_CONTENT = [
    # Beginner scenarios (unlocked by default)
    UnlockableContent(
        id="scenario_cafe",
        name="Coffee Shop",
        description="Order drinks and chat with the barista",
        unlock_type=UnlockType.SCENARIO,
        requirements=[],
        icon="☕",
        unlocked_icon="☕",
        order=1,
    ),
    UnlockableContent(
        id="scenario_greetings",
        name="Meeting People",
        description="Introduce yourself and make small talk",
        unlock_type=UnlockType.SCENARIO,
        requirements=[],
        icon="👋",
        unlocked_icon="👋",
        order=2,
    ),

    # Intermediate scenarios
    UnlockableContent(
        id="scenario_job_interview",
        name="Job Interview",
        description="Practice professional interview skills",
        unlock_type=UnlockType.SCENARIO,
        requirements=[
            SkillRequirement("conversation_formal", min_level=2),
            SkillRequirement("vocabulary_business", min_level=2),
        ],
        xp_reward=50,
        icon="💼",
        unlocked_icon="💼",
        order=10,
    ),
    UnlockableContent(
        id="scenario_restaurant",
        name="Fine Dining",
        description="Navigate a fancy restaurant experience",
        unlock_type=UnlockType.SCENARIO,
        requirements=[
            SkillRequirement("conversation_formal", min_level=2),
            SkillRequirement("vocabulary_basics", min_level=3),
        ],
        xp_reward=30,
        icon="🍽️",
        unlocked_icon="🍽️",
        order=11,
    ),
    UnlockableContent(
        id="scenario_doctor",
        name="Doctor's Visit",
        description="Describe symptoms and understand medical advice",
        unlock_type=UnlockType.SCENARIO,
        requirements=[
            SkillRequirement("vocabulary_basics", min_level=3),
            SkillRequirement("grammar_tenses", min_level=2),
        ],
        xp_reward=40,
        icon="🏥",
        unlocked_icon="🏥",
        order=12,
    ),

    # Advanced scenarios
    UnlockableContent(
        id="scenario_negotiation",
        name="Business Negotiation",
        description="Negotiate deals and contracts",
        unlock_type=UnlockType.SCENARIO,
        requirements=[
            SkillRequirement("conversation_formal", min_level=4),
            SkillRequirement("vocabulary_business", min_level=4),
            SkillRequirement("grammar_conditionals", min_level=3),
        ],
        xp_reward=100,
        icon="🤝",
        unlocked_icon="🤝",
        order=20,
    ),
    UnlockableContent(
        id="scenario_presentation",
        name="Business Presentation",
        description="Present ideas to an audience",
        unlock_type=UnlockType.SCENARIO,
        requirements=[
            SkillRequirement("fluency_coherence", min_level=3),
            SkillRequirement("vocabulary_business", min_level=3),
            SkillRequirement("pronunciation_stress", min_level=3),
        ],
        xp_reward=80,
        icon="📊",
        unlocked_icon="📊",
        order=21,
    ),
    UnlockableContent(
        id="scenario_debate",
        name="Debate Club",
        description="Argue different perspectives on topics",
        unlock_type=UnlockType.SCENARIO,
        requirements=[
            SkillRequirement("conversation_debate", min_level=3),
            SkillRequirement("fluency_coherence", min_level=4),
            SkillRequirement("vocabulary_academic", min_level=3),
        ],
        xp_reward=100,
        icon="🎭",
        unlocked_icon="🎭",
        order=22,
    ),

    # Feature unlocks
    UnlockableContent(
        id="feature_replay",
        name="Conversation Replay",
        description="Review and replay your conversations with coaching",
        unlock_type=UnlockType.FEATURE,
        requirements=[
            SkillRequirement("conversation_casual", min_level=2),
        ],
        xp_reward=25,
        icon="🔄",
        unlocked_icon="🔄",
        order=100,
    ),
    UnlockableContent(
        id="feature_advanced_analytics",
        name="Advanced Analytics",
        description="Detailed progress charts and insights",
        unlock_type=UnlockType.FEATURE,
        requirements=[
            SkillRequirement("grammar_tenses", min_level=3),
            SkillRequirement("pronunciation_vowels", min_level=3),
        ],
        xp_reward=50,
        icon="📈",
        unlocked_icon="📈",
        order=101,
    ),
]


# =============================================================================
# Achievement Definitions
# =============================================================================

ACHIEVEMENTS = [
    # Starter achievements
    Achievement(
        id="first_conversation",
        name="First Words",
        description="Complete your first conversation",
        icon="🎉",
        category=SkillCategory.CONVERSATION,
        criteria={"conversations_completed": 1},
        xp_reward=25,
        rarity="common",
    ),
    Achievement(
        id="streak_3",
        name="Getting Started",
        description="Practice 3 days in a row",
        icon="🔥",
        category=SkillCategory.FLUENCY,
        criteria={"streak_days": 3},
        xp_reward=50,
        rarity="common",
    ),
    Achievement(
        id="streak_7",
        name="Week Warrior",
        description="Practice 7 days in a row",
        icon="⭐",
        category=SkillCategory.FLUENCY,
        criteria={"streak_days": 7},
        xp_reward=100,
        rarity="uncommon",
    ),
    Achievement(
        id="streak_30",
        name="Dedicated Learner",
        description="Practice 30 days in a row",
        icon="🏆",
        category=SkillCategory.FLUENCY,
        criteria={"streak_days": 30},
        xp_reward=500,
        rarity="rare",
    ),

    # Grammar achievements
    Achievement(
        id="grammar_master_1",
        name="Grammar Apprentice",
        description="Reach level 5 in any grammar skill",
        icon="📚",
        category=SkillCategory.GRAMMAR,
        criteria={"any_grammar_skill_level": 5},
        xp_reward=100,
        rarity="uncommon",
    ),
    Achievement(
        id="perfect_grammar",
        name="Perfect Grammar",
        description="Complete a conversation with no grammar errors",
        icon="✨",
        category=SkillCategory.GRAMMAR,
        criteria={"conversation_no_grammar_errors": True},
        xp_reward=75,
        rarity="uncommon",
    ),

    # Pronunciation achievements
    Achievement(
        id="clear_speaker",
        name="Clear Speaker",
        description="Achieve 90%+ pronunciation score in a conversation",
        icon="🎯",
        category=SkillCategory.PRONUNCIATION,
        criteria={"pronunciation_score_min": 90},
        xp_reward=100,
        rarity="uncommon",
    ),
    Achievement(
        id="tongue_twister",
        name="Tongue Twister",
        description="Master 5 difficult pronunciation patterns",
        icon="👅",
        category=SkillCategory.PRONUNCIATION,
        criteria={"pronunciation_patterns_mastered": 5},
        xp_reward=150,
        rarity="rare",
    ),

    # Vocabulary achievements
    Achievement(
        id="word_collector",
        name="Word Collector",
        description="Learn 100 new words",
        icon="📖",
        category=SkillCategory.VOCABULARY,
        criteria={"words_learned": 100},
        xp_reward=100,
        rarity="uncommon",
    ),
    Achievement(
        id="vocabulary_variety",
        name="Variety Speaker",
        description="Use 50 different words in a single conversation",
        icon="🌈",
        category=SkillCategory.VOCABULARY,
        criteria={"unique_words_in_conversation": 50},
        xp_reward=75,
        rarity="uncommon",
    ),

    # Conversation achievements
    Achievement(
        id="chatterbox",
        name="Chatterbox",
        description="Complete 10 conversations",
        icon="💬",
        category=SkillCategory.CONVERSATION,
        criteria={"conversations_completed": 10},
        xp_reward=100,
        rarity="common",
    ),
    Achievement(
        id="social_butterfly",
        name="Social Butterfly",
        description="Complete 50 conversations",
        icon="🦋",
        category=SkillCategory.CONVERSATION,
        criteria={"conversations_completed": 50},
        xp_reward=300,
        rarity="rare",
    ),
    Achievement(
        id="long_talker",
        name="Long Talker",
        description="Have a 10+ minute conversation",
        icon="⏱️",
        category=SkillCategory.CONVERSATION,
        criteria={"conversation_duration_min": 600},
        xp_reward=100,
        rarity="uncommon",
    ),

    # Level achievements
    Achievement(
        id="level_10",
        name="Rising Star",
        description="Reach overall level 10",
        icon="⭐",
        category=SkillCategory.FLUENCY,
        criteria={"overall_level": 10},
        xp_reward=200,
        rarity="uncommon",
    ),
    Achievement(
        id="level_25",
        name="Intermediate",
        description="Reach overall level 25",
        icon="🌟",
        category=SkillCategory.FLUENCY,
        criteria={"overall_level": 25},
        xp_reward=500,
        rarity="rare",
    ),
    Achievement(
        id="level_50",
        name="Advanced Speaker",
        description="Reach overall level 50",
        icon="💫",
        category=SkillCategory.FLUENCY,
        criteria={"overall_level": 50},
        xp_reward=1000,
        rarity="epic",
    ),
]


# =============================================================================
# Skill Unlock Manager
# =============================================================================

class SkillUnlockManager:
    """
    Manages skill progression, unlocks, and achievements.
    """

    def __init__(self, db=None):
        self.db = db
        self._content_map = {c.id: c for c in UNLOCKABLE_CONTENT}
        self._achievement_map = {a.id: a for a in ACHIEVEMENTS}

    def get_or_create_profile(self, user_id: str) -> UserSkillProfile:
        """Get user's skill profile or create a new one."""
        if self.db:
            profile = self._load_profile(user_id)
            if profile:
                return profile

        # Create new profile with default skills
        profile = UserSkillProfile(user_id=user_id)
        for skill_id, skill_def in SKILL_DEFINITIONS.items():
            profile.skills[skill_id] = SkillProgress(
                skill_id=skill_id,
                category=skill_def["category"],
                xp_to_next_level=skill_def["base_xp_per_level"],
            )

        # Unlock default content
        for content in UNLOCKABLE_CONTENT:
            if not content.requirements:
                profile.unlocked_content.add(content.id)

        return profile

    def add_xp(
        self,
        profile: UserSkillProfile,
        skill_id: str,
        xp_amount: int,
        successful: bool = True
    ) -> Dict[str, Any]:
        """
        Add XP to a skill and check for level ups/unlocks.

        Returns dict with level_ups, new_unlocks, new_achievements.
        """
        result = {
            "xp_added": 0,
            "level_ups": [],
            "new_unlocks": [],
            "new_achievements": [],
        }

        if skill_id not in profile.skills:
            return result

        # Check daily XP cap
        self._check_daily_reset(profile)
        if profile.daily_xp >= profile.daily_xp_cap:
            return result

        # Apply daily cap
        available_xp = min(xp_amount, profile.daily_xp_cap - profile.daily_xp)
        if available_xp <= 0:
            return result

        skill = profile.skills[skill_id]
        skill.xp += available_xp
        skill.total_attempts += 1
        if successful:
            skill.successful_attempts += 1
        skill.last_practiced = datetime.utcnow()

        profile.total_xp += available_xp
        profile.daily_xp += available_xp
        result["xp_added"] = available_xp

        # Check for level up
        while skill.xp >= skill.xp_to_next_level:
            skill.xp -= skill.xp_to_next_level
            skill.level += 1
            skill.xp_to_next_level = self._calculate_xp_for_level(
                skill_id, skill.level
            )
            result["level_ups"].append({
                "skill_id": skill_id,
                "new_level": skill.level,
            })

        # Update overall level
        old_level = profile.overall_level
        profile.overall_level = self._calculate_overall_level(profile)
        if profile.overall_level > old_level:
            result["level_ups"].append({
                "skill_id": "overall",
                "new_level": profile.overall_level,
            })

        # Check for new unlocks
        new_unlocks = self._check_unlocks(profile)
        result["new_unlocks"] = new_unlocks

        # Check for new achievements
        new_achievements = self._check_achievements(profile)
        result["new_achievements"] = new_achievements

        # Persist if we have a database
        if self.db:
            self._save_profile(profile)

        return result

    def update_streak(self, profile: UserSkillProfile) -> Dict[str, Any]:
        """Update user's streak and check for streak achievements."""
        result = {"streak_updated": False, "new_achievements": []}

        now = datetime.utcnow()
        if profile.skills:
            # Get the most recent practice time
            last_practice = None
            for skill in profile.skills.values():
                if skill.last_practiced:
                    if not last_practice or skill.last_practiced > last_practice:
                        last_practice = skill.last_practiced

            if last_practice:
                days_since = (now.date() - last_practice.date()).days
                if days_since == 0:
                    # Already practiced today
                    pass
                elif days_since == 1:
                    # Practiced yesterday, increment streak
                    for skill in profile.skills.values():
                        skill.streak_days += 1
                    result["streak_updated"] = True
                else:
                    # Streak broken
                    for skill in profile.skills.values():
                        skill.streak_days = 1
                    result["streak_updated"] = True

        # Check for streak achievements
        new_achievements = self._check_achievements(profile)
        result["new_achievements"] = new_achievements

        return result

    def get_available_content(self, profile: UserSkillProfile) -> Dict[str, List[dict]]:
        """Get all content with unlock status."""
        result = {
            "unlocked": [],
            "locked": [],
            "next_unlocks": [],  # Content close to being unlocked
        }

        for content in sorted(UNLOCKABLE_CONTENT, key=lambda x: x.order):
            content_dict = content.to_dict()
            is_unlocked = content.id in profile.unlocked_content

            if is_unlocked:
                content_dict["status"] = "unlocked"
                result["unlocked"].append(content_dict)
            else:
                # Check progress toward unlock
                progress = self._calculate_unlock_progress(profile, content)
                content_dict["status"] = "locked"
                content_dict["progress"] = progress

                if progress >= 0.5:  # 50% or more progress
                    result["next_unlocks"].append(content_dict)
                else:
                    result["locked"].append(content_dict)

        return result

    def get_achievements(self, profile: UserSkillProfile) -> Dict[str, List[dict]]:
        """Get all achievements with earned status."""
        result = {
            "earned": [],
            "available": [],
        }

        for achievement in ACHIEVEMENTS:
            ach_dict = achievement.to_dict()
            if achievement.id in profile.earned_achievements:
                ach_dict["earned"] = True
                ach_dict["earned_at"] = None  # Would need to track this
                result["earned"].append(ach_dict)
            else:
                ach_dict["earned"] = False
                ach_dict["progress"] = self._calculate_achievement_progress(
                    profile, achievement
                )
                result["available"].append(ach_dict)

        return result

    def _calculate_xp_for_level(self, skill_id: str, level: int) -> int:
        """Calculate XP needed for next level."""
        skill_def = SKILL_DEFINITIONS.get(skill_id, {})
        base_xp = skill_def.get("base_xp_per_level", 100)
        # XP increases by 10% per level
        return int(base_xp * (1.1 ** (level - 1)))

    def _calculate_overall_level(self, profile: UserSkillProfile) -> int:
        """Calculate overall level from total XP."""
        # Simple formula: level = sqrt(total_xp / 100) + 1
        import math
        return int(math.sqrt(profile.total_xp / 100)) + 1

    def _check_unlocks(self, profile: UserSkillProfile) -> List[dict]:
        """Check for newly unlocked content."""
        new_unlocks = []

        for content in UNLOCKABLE_CONTENT:
            if content.id in profile.unlocked_content:
                continue

            if self._check_requirements_met(profile, content.requirements):
                profile.unlocked_content.add(content.id)
                # Award bonus XP for unlock
                if content.xp_reward > 0:
                    profile.total_xp += content.xp_reward
                new_unlocks.append({
                    "id": content.id,
                    "name": content.name,
                    "type": content.unlock_type.value,
                    "xp_reward": content.xp_reward,
                })

        return new_unlocks

    def _check_requirements_met(
        self,
        profile: UserSkillProfile,
        requirements: List[SkillRequirement]
    ) -> bool:
        """Check if all requirements are met."""
        for req in requirements:
            skill = profile.skills.get(req.skill_id)
            if not skill:
                return False
            if skill.level < req.min_level:
                return False
            if skill.xp < req.min_xp:
                return False
            if skill.accuracy < req.min_accuracy:
                return False
        return True

    def _calculate_unlock_progress(
        self,
        profile: UserSkillProfile,
        content: UnlockableContent
    ) -> float:
        """Calculate progress toward unlocking content (0-1)."""
        if not content.requirements:
            return 1.0

        total_progress = 0.0
        for req in content.requirements:
            skill = profile.skills.get(req.skill_id)
            if skill:
                level_progress = min(1.0, skill.level / req.min_level)
                total_progress += level_progress
            # else: 0 progress for missing skill

        return total_progress / len(content.requirements)

    def _check_achievements(self, profile: UserSkillProfile) -> List[dict]:
        """Check for newly earned achievements."""
        new_achievements = []

        for achievement in ACHIEVEMENTS:
            if achievement.id in profile.earned_achievements:
                continue

            if self._check_achievement_criteria(profile, achievement):
                profile.earned_achievements.add(achievement.id)
                profile.total_xp += achievement.xp_reward
                new_achievements.append({
                    "id": achievement.id,
                    "name": achievement.name,
                    "icon": achievement.icon,
                    "xp_reward": achievement.xp_reward,
                    "rarity": achievement.rarity,
                })

        return new_achievements

    def _check_achievement_criteria(
        self,
        profile: UserSkillProfile,
        achievement: Achievement
    ) -> bool:
        """Check if achievement criteria are met."""
        criteria = achievement.criteria

        # Streak checks
        if "streak_days" in criteria:
            max_streak = max(
                (s.streak_days for s in profile.skills.values()),
                default=0
            )
            if max_streak < criteria["streak_days"]:
                return False

        # Overall level check
        if "overall_level" in criteria:
            if profile.overall_level < criteria["overall_level"]:
                return False

        # Any grammar skill level check
        if "any_grammar_skill_level" in criteria:
            required = criteria["any_grammar_skill_level"]
            has_skill = any(
                s.level >= required
                for s in profile.skills.values()
                if s.category == SkillCategory.GRAMMAR
            )
            if not has_skill:
                return False

        # Other criteria would be checked here based on conversation stats
        # These would typically be passed in from external tracking

        return True

    def _calculate_achievement_progress(
        self,
        profile: UserSkillProfile,
        achievement: Achievement
    ) -> float:
        """Calculate progress toward achievement (0-1)."""
        criteria = achievement.criteria

        if "streak_days" in criteria:
            max_streak = max(
                (s.streak_days for s in profile.skills.values()),
                default=0
            )
            return min(1.0, max_streak / criteria["streak_days"])

        if "overall_level" in criteria:
            return min(1.0, profile.overall_level / criteria["overall_level"])

        if "any_grammar_skill_level" in criteria:
            required = criteria["any_grammar_skill_level"]
            max_grammar = max(
                (s.level for s in profile.skills.values()
                 if s.category == SkillCategory.GRAMMAR),
                default=0
            )
            return min(1.0, max_grammar / required)

        return 0.0

    def _check_daily_reset(self, profile: UserSkillProfile):
        """Reset daily XP if it's a new day."""
        now = datetime.utcnow()
        if profile.last_daily_reset:
            if now.date() > profile.last_daily_reset.date():
                profile.daily_xp = 0
                profile.last_daily_reset = now
        else:
            profile.last_daily_reset = now

    def _save_profile(self, profile: UserSkillProfile):
        """Save profile to database."""
        if not self.db:
            return

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO skill_profiles
                        (user_id, total_xp, overall_level, skills, unlocked_content,
                         earned_achievements, daily_xp, daily_xp_cap, last_daily_reset)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            total_xp = EXCLUDED.total_xp,
                            overall_level = EXCLUDED.overall_level,
                            skills = EXCLUDED.skills,
                            unlocked_content = EXCLUDED.unlocked_content,
                            earned_achievements = EXCLUDED.earned_achievements,
                            daily_xp = EXCLUDED.daily_xp,
                            last_daily_reset = EXCLUDED.last_daily_reset,
                            updated_at = NOW()
                    """, (
                        profile.user_id,
                        profile.total_xp,
                        profile.overall_level,
                        json.dumps({k: v.to_dict() for k, v in profile.skills.items()}),
                        json.dumps(list(profile.unlocked_content)),
                        json.dumps(list(profile.earned_achievements)),
                        profile.daily_xp,
                        profile.daily_xp_cap,
                        profile.last_daily_reset,
                    ))
                    conn.commit()
        except Exception as e:
            print(f"[SkillUnlockManager] Failed to save profile: {e}")

    def _load_profile(self, user_id: str) -> Optional[UserSkillProfile]:
        """Load profile from database."""
        if not self.db:
            return None

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT user_id, total_xp, overall_level, skills,
                               unlocked_content, earned_achievements,
                               daily_xp, daily_xp_cap, last_daily_reset
                        FROM skill_profiles
                        WHERE user_id = %s
                    """, (user_id,))

                    row = cur.fetchone()
                    if not row:
                        return None

                    skills_data = row[3] if isinstance(row[3], dict) else json.loads(row[3])
                    skills = {}
                    for skill_id, sd in skills_data.items():
                        skills[skill_id] = SkillProgress(
                            skill_id=sd["skill_id"],
                            category=SkillCategory(sd["category"]),
                            level=sd["level"],
                            xp=sd["xp"],
                            xp_to_next_level=sd["xp_to_next_level"],
                            total_attempts=sd.get("total_attempts", 0),
                            successful_attempts=sd.get("successful_attempts", 0),
                            streak_days=sd.get("streak_days", 0),
                            last_practiced=datetime.fromisoformat(sd["last_practiced"])
                            if sd.get("last_practiced") else None,
                        )

                    unlocked = row[4] if isinstance(row[4], list) else json.loads(row[4])
                    earned = row[5] if isinstance(row[5], list) else json.loads(row[5])

                    return UserSkillProfile(
                        user_id=row[0],
                        total_xp=row[1],
                        overall_level=row[2],
                        skills=skills,
                        unlocked_content=set(unlocked),
                        earned_achievements=set(earned),
                        daily_xp=row[6] or 0,
                        daily_xp_cap=row[7] or 500,
                        last_daily_reset=row[8],
                    )
        except Exception as e:
            print(f"[SkillUnlockManager] Failed to load profile: {e}")
            return None


# Global instance
skill_manager = SkillUnlockManager()


def create_skill_manager_with_db(db) -> SkillUnlockManager:
    """Create a skill manager with database support."""
    return SkillUnlockManager(db=db)
