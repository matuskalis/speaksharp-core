from datetime import datetime, timedelta
from typing import List, Dict, Optional
from uuid import UUID, uuid4
import math
from app.models import SRSCard, SRSReview, CardType, Error


class SRSSystem:
    """Spaced Repetition System with SM-2 algorithm."""

    def __init__(self):
        # Mock in-memory database
        self.cards: Dict[UUID, SRSCard] = {}
        self.reviews: List[SRSReview] = []

    def add_item(
        self,
        user_id: UUID,
        card_type: CardType,
        front: str,
        back: str,
        level: str = "A1",
        source: str = "lesson",
        difficulty: float = 0.5
    ) -> UUID:
        """Add a new SRS card."""
        card = SRSCard(
            card_id=uuid4(),
            user_id=user_id,
            card_type=card_type,
            front=front,
            back=back,
            level=level,
            source=source,
            difficulty=difficulty,
            next_review_date=datetime.now() + timedelta(days=1),
            interval_days=1,
            ease_factor=2.5,
            review_count=0
        )

        self.cards[card.card_id] = card
        print(f"✓ Added card: {card.card_type.value} - {front[:50]}...")
        return card.card_id

    def get_due_items(self, user_id: UUID, limit: int = 20) -> List[SRSCard]:
        """Get cards due for review."""
        now = datetime.now()
        due_cards = [
            card for card in self.cards.values()
            if card.user_id == user_id and card.next_review_date <= now
        ]

        # Sort by next_review_date (oldest first)
        due_cards.sort(key=lambda c: c.next_review_date)

        return due_cards[:limit]

    def update_item(
        self,
        card_id: UUID,
        quality: int,
        response_time_ms: int,
        user_response: str,
        correct: bool
    ) -> SRSCard:
        """Update card after review using SM-2 algorithm."""
        if card_id not in self.cards:
            raise ValueError(f"Card {card_id} not found")

        card = self.cards[card_id]

        # Calculate new values using SM-2
        new_interval, new_ease = self._calculate_sm2(
            quality=quality,
            current_interval=card.interval_days,
            current_ease=card.ease_factor
        )

        # Update card
        card.interval_days = new_interval
        card.ease_factor = new_ease
        card.next_review_date = self.schedule_next_review(new_interval)
        card.review_count += 1

        # Log review
        review = SRSReview(
            review_id=uuid4(),
            card_id=card_id,
            user_id=card.user_id,
            quality=quality,
            response_time_ms=response_time_ms,
            user_response=user_response,
            correct=correct,
            new_interval_days=new_interval,
            new_ease_factor=new_ease
        )
        self.reviews.append(review)

        print(f"✓ Updated card: quality={quality}, new_interval={new_interval} days, ease={new_ease:.2f}")

        return card

    def schedule_next_review(self, interval_days: int) -> datetime:
        """Calculate next review date."""
        return datetime.now() + timedelta(days=interval_days)

    def _calculate_sm2(self, quality: int, current_interval: int, current_ease: float) -> tuple[int, float]:
        """
        SM-2 Algorithm for spaced repetition.

        Quality scale:
        5 - perfect response
        4 - correct response after a hesitation
        3 - correct response recalled with serious difficulty
        2 - incorrect response; where the correct one seemed easy to recall
        1 - incorrect response; the correct one remembered
        0 - complete blackout

        Returns: (new_interval_days, new_ease_factor)
        """

        # Update ease factor
        new_ease = current_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

        # Ensure ease factor doesn't go below 1.3
        new_ease = max(1.3, new_ease)

        # Calculate new interval
        if quality < 3:
            # Failed recall - reset to 1 day
            new_interval = 1
        else:
            # Successful recall
            if current_interval == 1:
                new_interval = 1
            elif current_interval == 2:
                new_interval = 6
            else:
                new_interval = math.ceil(current_interval * new_ease)

        return new_interval, new_ease

    def create_card_from_error(self, error: Error, user_id: UUID) -> UUID:
        """Create an SRS card from a corrected error."""
        front = f"Fix this sentence:\n{error.user_sentence}"
        back = f"Corrected: {error.corrected_sentence}\n\nExplanation: {error.explanation}"

        return self.add_item(
            user_id=user_id,
            card_type=CardType.ERROR_REPAIR,
            front=front,
            back=back,
            source="error",
            difficulty=0.7
        )

    def get_stats(self, user_id: UUID) -> Dict:
        """Get user SRS statistics."""
        user_cards = [c for c in self.cards.values() if c.user_id == user_id]

        now = datetime.now()
        due_cards = [c for c in user_cards if c.next_review_date <= now]
        upcoming_cards = [c for c in user_cards if c.next_review_date > now]

        user_reviews = [r for r in self.reviews if r.user_id == user_id]
        recent_reviews = [r for r in user_reviews if r.reviewed_at > now - timedelta(days=7)]

        if recent_reviews:
            avg_quality = sum(r.quality for r in recent_reviews) / len(recent_reviews)
            accuracy = sum(1 for r in recent_reviews if r.correct) / len(recent_reviews) * 100
        else:
            avg_quality = 0
            accuracy = 0

        return {
            "total_cards": len(user_cards),
            "due_now": len(due_cards),
            "upcoming": len(upcoming_cards),
            "total_reviews": len(user_reviews),
            "reviews_last_7_days": len(recent_reviews),
            "avg_quality": round(avg_quality, 2),
            "accuracy_percent": round(accuracy, 1)
        }


if __name__ == "__main__":
    # Test SRS system
    print("Testing SRS System")
    print("=" * 60)

    user_id = uuid4()
    srs = SRSSystem()

    # Add some cards
    print("\n1. Adding cards...")
    print("-" * 60)

    card1 = srs.add_item(
        user_id=user_id,
        card_type=CardType.DEFINITION,
        front="What does 'ubiquitous' mean?",
        back="Present, appearing, or found everywhere",
        level="B2"
    )

    card2 = srs.add_item(
        user_id=user_id,
        card_type=CardType.CLOZE,
        front="I ___ to the store yesterday. (go)",
        back="I went to the store yesterday.",
        level="A2"
    )

    card3 = srs.add_item(
        user_id=user_id,
        card_type=CardType.PRODUCTION,
        front="Translate: Me gusta leer libros.",
        back="I like to read books.",
        level="A1"
    )

    # Add card from error
    print("\n2. Creating card from error...")
    print("-" * 60)

    from app.models import Error, ErrorType

    error = Error(
        type=ErrorType.GRAMMAR,
        user_sentence="She don't like coffee.",
        corrected_sentence="She doesn't like coffee.",
        explanation="Use 'doesn't' with he/she/it in present tense negative."
    )

    error_card = srs.create_card_from_error(error, user_id)

    # Get due items
    print("\n3. Getting due items...")
    print("-" * 60)

    due_cards = srs.get_due_items(user_id)
    print(f"Found {len(due_cards)} cards due for review")

    # Review cards
    print("\n4. Reviewing cards...")
    print("-" * 60)

    for i, card in enumerate(due_cards[:3], 1):
        print(f"\nCard {i}:")
        print(f"Front: {card.front}")
        print(f"Back: {card.back}")

        # Simulate different quality scores
        quality = 5 if i == 1 else (3 if i == 2 else 4)
        response_time = 2000 + (i * 500)
        correct = quality >= 3

        print(f"Review: quality={quality}, time={response_time}ms, correct={correct}")

        updated_card = srs.update_item(
            card_id=card.card_id,
            quality=quality,
            response_time_ms=response_time,
            user_response="User's answer",
            correct=correct
        )

        print(f"Next review: {updated_card.next_review_date.strftime('%Y-%m-%d %H:%M')}")

    # Get stats
    print("\n5. User statistics...")
    print("-" * 60)

    stats = srs.get_stats(user_id)
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n" + "=" * 60)
    print("SRS system test complete!")
