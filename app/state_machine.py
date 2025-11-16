from datetime import datetime, timedelta
from typing import Optional, Callable, Dict
from uuid import UUID
from app.models import AppState, Session


class StateMachine:
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        self.current_state: AppState = AppState.ONBOARDING
        self.session: Optional[Session] = None
        self.context: Dict = {}

    def enter_state(self, state: AppState, context: Dict = None):
        print(f"\n{'='*60}")
        print(f"ENTERING STATE: {state.value}")
        print(f"{'='*60}\n")

        if context:
            self.context.update(context)

        self.current_state = state

        if state == AppState.ONBOARDING:
            self._enter_onboarding()
        elif state == AppState.DAILY_REVIEW:
            self._enter_daily_review()
        elif state == AppState.SCENARIO_SESSION:
            self._enter_scenario_session()
        elif state == AppState.FREE_CHAT:
            self._enter_free_chat()
        elif state == AppState.FEEDBACK_REPORT:
            self._enter_feedback_report()

    def exit_state(self, state: AppState):
        print(f"\n--- Exiting state: {state.value} ---\n")

        if state == AppState.ONBOARDING:
            self._exit_onboarding()
        elif state == AppState.DAILY_REVIEW:
            self._exit_daily_review()
        elif state == AppState.SCENARIO_SESSION:
            self._exit_scenario_session()
        elif state == AppState.FREE_CHAT:
            self._exit_free_chat()
        elif state == AppState.FEEDBACK_REPORT:
            self._exit_feedback_report()

    def transition_to(self, new_state: AppState, context: Dict = None):
        self.exit_state(self.current_state)
        self.enter_state(new_state, context)

    def _enter_onboarding(self):
        print("Welcome to SpeakSharp!")
        print("Let's assess your current level and set your goals.")
        self.context['onboarding_complete'] = False
        self.context['level'] = 'A1'
        self.context['goals'] = []

    def _exit_onboarding(self):
        self.context['onboarding_complete'] = True
        print(f"Onboarding complete. Level: {self.context.get('level', 'A1')}")

    def _enter_daily_review(self):
        print("Starting your daily SRS review session.")
        print("Review your vocabulary and error corrections.")
        self.session = Session(
            user_id=self.user_id,
            session_type="daily_review"
        )
        self.context['cards_reviewed'] = 0
        self.context['cards_total'] = 0

    def _exit_daily_review(self):
        if self.session:
            self.session.completed_at = datetime.now()
            self.session.state = "completed"
        reviewed = self.context.get('cards_reviewed', 0)
        total = self.context.get('cards_total', 0)
        print(f"Review session complete: {reviewed}/{total} cards reviewed")

    def _enter_scenario_session(self):
        print("Starting a conversation scenario.")
        scenario_id = self.context.get('scenario_id', 'cafe_ordering')
        print(f"Scenario: {scenario_id}")
        self.session = Session(
            user_id=self.user_id,
            session_type="scenario_session"
        )
        self.context['scenario_turns'] = 0
        self.context['scenario_complete'] = False

    def _exit_scenario_session(self):
        if self.session:
            self.session.completed_at = datetime.now()
            self.session.state = "completed"
        turns = self.context.get('scenario_turns', 0)
        print(f"Scenario complete: {turns} turns")

    def _enter_free_chat(self):
        print("Free chat mode: Talk about anything!")
        self.session = Session(
            user_id=self.user_id,
            session_type="free_chat"
        )
        self.context['chat_turns'] = 0

    def _exit_free_chat(self):
        if self.session:
            self.session.completed_at = datetime.now()
            self.session.state = "completed"
        turns = self.context.get('chat_turns', 0)
        print(f"Chat session complete: {turns} turns")

    def _enter_feedback_report(self):
        print("Generating your session feedback...")
        self.context['feedback_generated'] = False

    def _exit_feedback_report(self):
        print("Feedback delivered. Great work!")
        self.context['feedback_generated'] = True


class Router:
    """Routes user to appropriate state based on completion status."""

    def __init__(self):
        self.completion_status = {
            'today_review_done': False,
            'today_lesson_done': False,
            'today_scenario_done': False,
            'onboarding_complete': True
        }

    def route(self, state_machine: StateMachine) -> AppState:
        """Determine next state based on priority."""

        # Priority 1: Onboarding if not complete
        if not self.completion_status['onboarding_complete']:
            return AppState.ONBOARDING

        # Priority 2: Daily review if not done
        if not self.completion_status['today_review_done']:
            return AppState.DAILY_REVIEW

        # Priority 3: Scenario if not done
        if not self.completion_status['today_scenario_done']:
            return AppState.SCENARIO_SESSION

        # Default: Free chat
        return AppState.FREE_CHAT

    def mark_complete(self, state: AppState):
        """Mark state as completed for today."""
        if state == AppState.DAILY_REVIEW:
            self.completion_status['today_review_done'] = True
        elif state == AppState.SCENARIO_SESSION:
            self.completion_status['today_scenario_done'] = True
        elif state == AppState.ONBOARDING:
            self.completion_status['onboarding_complete'] = True


if __name__ == "__main__":
    from uuid import uuid4

    # Test the state machine
    user_id = uuid4()
    sm = StateMachine(user_id)
    router = Router()

    print("Testing State Machine")
    print("=" * 60)

    # Simulate daily loop
    next_state = router.route(sm)
    sm.transition_to(next_state)
    router.mark_complete(AppState.DAILY_REVIEW)

    next_state = router.route(sm)
    sm.transition_to(next_state, {'scenario_id': 'cafe_ordering'})
    router.mark_complete(AppState.SCENARIO_SESSION)

    sm.transition_to(AppState.FEEDBACK_REPORT)

    print("\nState machine test complete!")
