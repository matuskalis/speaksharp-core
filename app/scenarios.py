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
    ),

    "shopping_clothes": ScenarioTemplate(
        scenario_id="shopping_clothes",
        title="Shopping for Clothes",
        level_min="A2",
        level_max="B1",
        situation_description="You are in a clothing store looking for something specific to buy. A sales assistant approaches to help you.",
        user_goal="Find the right item, ask about sizes/colors/prices, try something on, and make a purchase decision.",
        task="Look for a specific item, ask the sales assistant for help, inquire about details, try it on, and decide whether to buy it.",
        success_criteria="Use shopping vocabulary correctly, ask about size/color/price, use comparatives if needed, express preferences, handle the transaction.",
        difficulty_tags=["transactional", "shopping_vocabulary", "adjectives", "comparatives", "polite_requests"],
        user_variables={
            "item_looking_for": "shirt",
            "preferred_color": "",
            "size": "",
            "budget": ""
        }
    ),

    "job_interview": ScenarioTemplate(
        scenario_id="job_interview",
        title="Job Interview",
        level_min="B1",
        level_max="C1",
        situation_description="You are at a job interview for a position you applied for. The interviewer will ask you about your background, experience, and why you want the job.",
        user_goal="Present yourself professionally, answer questions about your experience and skills, ask relevant questions about the position.",
        task="Introduce yourself professionally, describe your experience and qualifications, explain why you're interested in the role, and ask thoughtful questions about the job.",
        success_criteria="Use professional language, describe past experience using past tenses, express future plans, use formal register, demonstrate confidence and politeness.",
        difficulty_tags=["professional", "formal_register", "past_experience", "future_plans", "complex_sentences"],
        user_variables={
            "job_title": "",
            "years_experience": 0,
            "key_skills": [],
            "career_goals": ""
        }
    ),

    "hotel_checkin": ScenarioTemplate(
        scenario_id="hotel_checkin",
        title="Hotel Check-in",
        level_min="A2",
        level_max="B1",
        situation_description="You arrive at a hotel where you have a reservation. You need to check in at the front desk.",
        user_goal="Successfully check in to your hotel room, confirm your reservation details, ask about hotel amenities, and get your room key.",
        task="Check in using your reservation, confirm dates and room type, ask about breakfast/wifi/facilities, and get directions to your room.",
        success_criteria="Provide reservation details clearly, ask relevant questions about facilities, use polite language, confirm important information.",
        difficulty_tags=["transactional", "travel_vocabulary", "polite_requests", "question_formation", "confirmation"],
        user_variables={
            "reservation_name": "",
            "number_nights": 0,
            "room_type": "",
            "special_requests": []
        }
    ),

    "restaurant_complaint": ScenarioTemplate(
        scenario_id="restaurant_complaint",
        title="Handling a Restaurant Problem",
        level_min="B1",
        level_max="B2",
        situation_description="You're at a restaurant and there's a problem with your order - either it's wrong, cold, or not what you expected. You need to politely address this with the waiter.",
        user_goal="Politely explain the problem, describe what's wrong, and request a solution (replacement, discount, etc.).",
        task="Get the waiter's attention, explain the issue calmly and politely, describe what's wrong, and negotiate a resolution.",
        success_criteria="Use polite complaint language ('I'm afraid...', 'There seems to be...'), describe the problem clearly, avoid being rude, negotiate a solution professionally.",
        difficulty_tags=["transactional", "complaint_language", "polite_disagreement", "problem_solving", "negotiation"],
        user_variables={
            "problem_type": "wrong_order",
            "what_ordered": "",
            "what_received": "",
            "preferred_solution": ""
        }
    ),

    "bank_inquiry": ScenarioTemplate(
        scenario_id="bank_inquiry",
        title="Bank Account Inquiry",
        level_min="B1",
        level_max="B2",
        situation_description="You need to visit your bank to inquire about opening a new account or solving an issue with your current account.",
        user_goal="Explain your banking need, understand the options/solutions available, ask clarifying questions, and decide on next steps.",
        task="Speak with a bank representative, explain what you need, ask about fees/requirements/documents, and understand the process.",
        success_criteria="Use formal banking vocabulary, ask clear questions, understand complex information, take notes on requirements, confirm next steps.",
        difficulty_tags=["transactional", "formal_register", "financial_vocabulary", "question_formation", "comprehension"],
        user_variables={
            "inquiry_type": "new_account",
            "account_type": "",
            "concerns": [],
            "requirements": []
        }
    ),

    "making_work_friends": ScenarioTemplate(
        scenario_id="making_work_friends",
        title="Making Friends at Work",
        level_min="A2",
        level_max="B2",
        situation_description="It's your first week at a new job. You're in the break room and a friendly coworker starts a conversation with you.",
        user_goal="Build rapport with your new coworker, share information about yourself, ask about them and the workplace, and establish a friendly connection.",
        task="Introduce yourself, talk about your role and background, ask about their work, discuss workplace culture, and suggest connecting outside of work.",
        success_criteria="Use conversational English, ask follow-up questions, find common ground, express interest genuinely, use appropriate level of formality for workplace.",
        difficulty_tags=["social", "workplace_vocabulary", "small_talk", "question_formation", "rapport_building"],
        user_variables={
            "your_role": "",
            "previous_company": "",
            "interests": [],
            "questions_about_company": []
        }
    ),

    "apartment_viewing": ScenarioTemplate(
        scenario_id="apartment_viewing",
        title="Viewing an Apartment to Rent",
        level_min="B1",
        level_max="C1",
        situation_description="You're viewing an apartment that you might want to rent. The landlord or agent is showing you around and you need to ask important questions.",
        user_goal="Assess if the apartment meets your needs, ask all necessary questions about rent/utilities/rules, negotiate terms if needed.",
        task="Tour the apartment, ask about rent, utilities, deposit, lease terms, rules, and neighborhood. Express interest or concerns and discuss next steps.",
        success_criteria="Ask comprehensive questions about practical matters, use conditional language ('If I were to take it...'), negotiate politely, understand legal/financial terms.",
        difficulty_tags=["transactional", "housing_vocabulary", "negotiation", "conditionals", "formal_language"],
        user_variables={
            "budget": "",
            "move_in_date": "",
            "must_haves": [],
            "concerns": []
        }
    ),

    "flight_delay": ScenarioTemplate(
        scenario_id="flight_delay",
        title="Dealing with Flight Delay",
        level_min="B1",
        level_max="B2",
        situation_description="Your flight has been delayed and you're at the airline desk trying to understand what's happening and what options you have.",
        user_goal="Get information about the delay, understand your options (rebooking, compensation, hotel), and make a decision.",
        task="Explain your situation, ask about the delay reason and duration, inquire about compensation/rebooking/accommodation, and decide on your next steps.",
        success_criteria="Stay calm and polite despite frustration, ask clear questions about options, understand complex information about policies, make an informed decision.",
        difficulty_tags=["transactional", "travel_vocabulary", "problem_solving", "formal_complaints", "decision_making"],
        user_variables={
            "destination": "",
            "reason_for_travel": "business",
            "urgency": "moderate",
            "connecting_flights": False
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
