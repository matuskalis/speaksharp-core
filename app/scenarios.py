from typing import Dict, List
from app.models import ScenarioTemplate


SCENARIO_TEMPLATES: Dict[str, ScenarioTemplate] = {
    "cafe_ordering": ScenarioTemplate(
        scenario_id="cafe_ordering",
        title="Ordering at a Café",
        level_min="A1",
        level_max="B1",
        situation_description="You are at a café and want to order a drink and a snack. The barista will greet you and take your order.",
        user_goal="Successfully order a drink and a snack, ask about prices, and complete the transaction politely.",
        task="Order a coffee and a pastry, ask for the price, and thank the barista.",
        success_criteria="Complete the order with correct vocabulary, use polite language, ask at least one clarification question, and finish the interaction appropriately.",
        difficulty_tags=["transactional", "present_simple", "polite_requests", "food_vocabulary"],
        user_variables={
            "preferred_drink": "coffee",
            "preferred_food": "croissant",
            "budget": "flexible"
        }
    ),

    "self_introduction": ScenarioTemplate(
        scenario_id="self_introduction",
        title="Meeting Someone New",
        level_min="A1",
        level_max="B2",
        situation_description="You are at a social event and meeting someone for the first time. You will introduce yourself and learn about the other person.",
        user_goal="Exchange names, share basic information about yourself, ask questions about the other person, and maintain a friendly conversation.",
        task="Introduce yourself (name, where you're from, what you do), ask questions to learn about the other person, and find common interests.",
        success_criteria="Use correct question formation, share at least 3 pieces of information about yourself, ask at least 3 questions, and respond naturally to answers.",
        difficulty_tags=["social", "introductions", "question_formation", "present_simple", "small_talk"],
        user_variables={
            "your_name": "",
            "your_city": "",
            "your_occupation": "",
            "your_hobbies": []
        }
    ),

    "asking_directions": ScenarioTemplate(
        scenario_id="asking_directions",
        title="Asking for Directions",
        level_min="A2",
        level_max="B1",
        situation_description="You are lost in a new city and need to find your way to a specific location. You stop a friendly local to ask for help.",
        user_goal="Get clear directions to your destination and confirm you understand the route.",
        task="Ask for directions, clarify if needed, thank the person, and confirm the route back to them.",
        success_criteria="Ask politely, use question forms correctly, understand and repeat back key directions, thank appropriately.",
        difficulty_tags=["transactional", "question_formation", "prepositions_place", "imperative_understanding"],
        user_variables={
            "destination": "train station",
            "current_location": "city center",
            "urgency": "moderate"
        }
    ),

    "doctor_appointment": ScenarioTemplate(
        scenario_id="doctor_appointment",
        title="Making a Doctor's Appointment",
        level_min="A2",
        level_max="B2",
        situation_description="You need to call your doctor's office to schedule an appointment because you're not feeling well.",
        user_goal="Successfully book an appointment, explain your symptoms, and get all necessary information.",
        task="Call the doctor's office, explain why you need an appointment, agree on a time, and confirm details.",
        success_criteria="Describe symptoms clearly, negotiate appointment time, use polite phone language, confirm booking details.",
        difficulty_tags=["transactional", "health_vocabulary", "phone_language", "symptom_description", "time_negotiation"],
        user_variables={
            "symptoms": "",
            "preferred_time": "",
            "insurance_info": ""
        }
    ),

    "talk_about_your_day": ScenarioTemplate(
        scenario_id="talk_about_your_day",
        title="Tell About Your Day",
        level_min="A2",
        level_max="B2",
        situation_description="Someone asks you about your day. Share what you did today, what happened, and how you felt about it.",
        user_goal="Describe your daily activities in sequence, explain what happened, and express your feelings about the events.",
        task="Tell about your day from morning to evening. Include what you did, where you went, who you met, and how you felt.",
        success_criteria="Use past tenses correctly, sequence events logically, use time expressions (first, then, after that), include at least one interesting detail, and express emotions.",
        difficulty_tags=["narrative", "past_tenses", "sequencing", "time_expressions", "personal"],
        user_variables={
            "day": "today",
            "notable_events": [],
            "people_met": [],
            "feelings": []
        }
    )
}


class ScenarioRunner:
    def __init__(self, scenario_template: ScenarioTemplate):
        self.template = scenario_template
        self.turn_count = 0
        self.user_responses: List[str] = []
        self.completed = False

    def start(self) -> str:
        """Start the scenario and return the opening prompt."""
        print(f"\n{'='*60}")
        print(f"SCENARIO: {self.template.title}")
        print(f"{'='*60}")
        print(f"\nLevel: {self.template.level_min} - {self.template.level_max}")
        print(f"\nSituation: {self.template.situation_description}")
        print(f"\nYour goal: {self.template.user_goal}")
        print(f"\nTask: {self.template.task}")
        print(f"\n{'='*60}\n")

        return self._get_opening_prompt()

    def _get_opening_prompt(self) -> str:
        """Get the opening prompt based on scenario."""
        prompts = {
            "cafe_ordering": "Barista: Hello! Welcome to Sunrise Café. What can I get for you today?",
            "self_introduction": "Person: Hi there! I don't think we've met before. I'm Alex. Nice to meet you!",
            "talk_about_your_day": "Friend: Hey! How was your day? Tell me all about it!",
            "asking_directions": "Local: Hi there, you look a bit lost. Can I help you with something?",
            "doctor_appointment": "Receptionist: Good morning, City Medical Center. How can I help you?"
        }
        return prompts.get(self.template.scenario_id, "Let's begin!")

    def process_turn(self, user_input: str) -> Dict:
        """Process a user turn and return feedback."""
        self.turn_count += 1
        self.user_responses.append(user_input)

        # Check if scenario should end
        if self._should_end():
            self.completed = True
            return {
                "ai_response": self._get_closing_response(),
                "scenario_complete": True,
                "feedback": self._generate_feedback()
            }

        # Continue scenario
        return {
            "ai_response": self._get_next_prompt(),
            "scenario_complete": False,
            "feedback": None
        }

    def _should_end(self) -> bool:
        """Check if scenario should end."""
        # Simple heuristic: end after 5-8 turns
        min_turns = 5
        max_turns = 8

        if self.turn_count >= max_turns:
            return True

        if self.turn_count >= min_turns:
            # Check if user has met basic criteria
            if self.template.scenario_id == "cafe_ordering":
                return self._check_cafe_completion()
            elif self.template.scenario_id == "self_introduction":
                return self._check_intro_completion()
            elif self.template.scenario_id == "talk_about_your_day":
                return self._check_day_completion()
            elif self.template.scenario_id == "asking_directions":
                return self._check_directions_completion()
            elif self.template.scenario_id == "doctor_appointment":
                return self._check_doctor_completion()

        return False

    def _check_cafe_completion(self) -> bool:
        """Check if cafe ordering is complete."""
        responses_text = " ".join(self.user_responses).lower()
        has_order = any(word in responses_text for word in ["coffee", "tea", "latte", "cappuccino", "croissant", "muffin"])
        has_thanks = "thank" in responses_text
        return has_order and has_thanks

    def _check_intro_completion(self) -> bool:
        """Check if introduction is complete."""
        return len(self.user_responses) >= 3

    def _check_day_completion(self) -> bool:
        """Check if day description is complete."""
        responses_text = " ".join(self.user_responses).lower()
        has_past_tense = any(word in responses_text for word in ["went", "did", "was", "were", "had"])
        return has_past_tense and len(self.user_responses) >= 2

    def _check_directions_completion(self) -> bool:
        """Check if directions scenario is complete."""
        responses_text = " ".join(self.user_responses).lower()
        has_question = any(word in responses_text for word in ["where", "how", "which", "can you"])
        has_thanks = "thank" in responses_text
        return has_question and has_thanks and len(self.user_responses) >= 3

    def _check_doctor_completion(self) -> bool:
        """Check if doctor appointment is complete."""
        responses_text = " ".join(self.user_responses).lower()
        has_appointment_request = any(word in responses_text for word in ["appointment", "see", "doctor", "visit"])
        has_confirmation = any(word in responses_text for word in ["yes", "ok", "good", "perfect", "thank"])
        return has_appointment_request and len(self.user_responses) >= 3

    def _get_next_prompt(self) -> str:
        """Get next AI prompt based on scenario and turn count."""
        if self.template.scenario_id == "cafe_ordering":
            prompts = [
                "Barista: Great choice! What size would you like?",
                "Barista: Would you like anything else with that?",
                "Barista: Sure! That'll be $6.50. How would you like to pay?",
                "Barista: Perfect! Here's your order. Enjoy!",
            ]
        elif self.template.scenario_id == "self_introduction":
            prompts = [
                "Alex: Nice to meet you! So, where are you from?",
                "Alex: That's interesting! What do you do?",
                "Alex: Cool! What do you like to do in your free time?",
                "Alex: Oh, that's fun! We should hang out sometime.",
            ]
        elif self.template.scenario_id == "talk_about_your_day":
            prompts = [
                "Friend: Oh really? What happened?",
                "Friend: And then what did you do?",
                "Friend: How did that make you feel?",
                "Friend: That sounds like quite a day!",
            ]
        elif self.template.scenario_id == "asking_directions":
            prompts = [
                "Local: Sure! Where are you trying to get to?",
                "Local: Okay, so you need to go straight down this street, then turn left at the traffic lights.",
                "Local: After that, it's about a 5-minute walk. You'll see it on your right.",
                "Local: You're welcome! It's easy to find, don't worry.",
            ]
        elif self.template.scenario_id == "doctor_appointment":
            prompts = [
                "Receptionist: I see. What seems to be the problem?",
                "Receptionist: Okay, let me check our schedule. Would morning or afternoon work better for you?",
                "Receptionist: We have an opening on Thursday at 2 PM. Does that work?",
                "Receptionist: Perfect! I've booked you in. See you Thursday at 2 PM.",
            ]
        else:
            prompts = ["Continue...", "Tell me more.", "What else?"]

        idx = min(self.turn_count - 1, len(prompts) - 1)
        return prompts[idx]

    def _get_closing_response(self) -> str:
        """Get closing response for the scenario."""
        closings = {
            "cafe_ordering": "Barista: Thank you so much! Have a great day!",
            "self_introduction": "Alex: It was really nice meeting you! See you around!",
            "talk_about_your_day": "Friend: Thanks for sharing! I hope tomorrow is even better!",
            "asking_directions": "Local: No problem! Good luck finding it. Have a great day!",
            "doctor_appointment": "Receptionist: All set! We'll see you on Thursday. Feel better soon!"
        }
        return closings.get(self.template.scenario_id, "Thanks! That was great!")

    def _generate_feedback(self) -> Dict:
        """Generate feedback for the completed scenario."""
        return {
            "scenario_id": self.template.scenario_id,
            "turns_completed": self.turn_count,
            "success_criteria_met": self._evaluate_success(),
            "strengths": ["Good vocabulary usage", "Clear communication"],
            "areas_to_improve": ["Try using more varied expressions", "Practice natural intonation"],
            "next_steps": "Try a more advanced scenario or review challenging vocabulary."
        }

    def _evaluate_success(self) -> bool:
        """Evaluate if success criteria were met."""
        # Simplified evaluation
        if self.template.scenario_id == "cafe_ordering":
            return self._check_cafe_completion()
        elif self.template.scenario_id == "self_introduction":
            return len(self.user_responses) >= 3
        elif self.template.scenario_id == "talk_about_your_day":
            return self._check_day_completion()
        return False


def get_scenario(scenario_id: str) -> ScenarioTemplate:
    """Get scenario template by ID."""
    return SCENARIO_TEMPLATES.get(scenario_id)


def list_scenarios() -> List[str]:
    """List all available scenario IDs."""
    return list(SCENARIO_TEMPLATES.keys())


if __name__ == "__main__":
    # Test scenario runner
    print("Testing Scenario Runner")
    print("=" * 60)

    scenario = get_scenario("cafe_ordering")
    runner = ScenarioRunner(scenario)

    print(runner.start())

    # Simulate user turns
    test_turns = [
        "I'd like a large cappuccino, please.",
        "Yes, I'll have a croissant too.",
        "How much is that?",
        "I'll pay with card.",
        "Thank you!"
    ]

    for i, user_turn in enumerate(test_turns, 1):
        print(f"\nTurn {i}")
        print(f"You: {user_turn}")

        result = runner.process_turn(user_turn)

        print(f"AI: {result['ai_response']}")

        if result['scenario_complete']:
            print("\n" + "=" * 60)
            print("SCENARIO COMPLETE!")
            print("=" * 60)
            print(f"\nFeedback: {result['feedback']}")
            break

    print("\nScenario test complete!")
