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
    ),

    # JOB INTERVIEW SCENARIOS
    "job_interview_intro": ScenarioTemplate(
        scenario_id="job_interview_intro",
        title="Job Interview - Professional Introduction",
        level_min="B1",
        level_max="C1",
        situation_description="You're at the beginning of a job interview. The interviewer has just welcomed you and asked you to introduce yourself professionally.",
        user_goal="Present yourself professionally, share your background concisely, make a strong first impression, and show enthusiasm for the role.",
        task="Give a professional self-introduction covering your name, current role/background, key achievements, and why you're interested in this position.",
        success_criteria="Use formal register, speak for 1-2 minutes, highlight relevant experience, show confidence, connect your background to the role, maintain professional tone.",
        difficulty_tags=["professional", "formal_register", "self_presentation", "complex_sentences", "professional_vocabulary"],
        user_variables={
            "current_role": "",
            "years_experience": 0,
            "target_position": "",
            "key_achievement": ""
        }
    ),

    "job_interview_strengths": ScenarioTemplate(
        scenario_id="job_interview_strengths",
        title="Job Interview - Strengths & Weaknesses",
        level_min="B2",
        level_max="C1",
        situation_description="The interviewer asks you to describe your greatest strengths and areas for improvement. This is a classic interview question that requires thoughtful, balanced responses.",
        user_goal="Present your strengths with confidence and examples, discuss weaknesses honestly while showing self-awareness and growth mindset.",
        task="Describe 2-3 key strengths with specific examples, then discuss one area for improvement and what you're doing to develop it.",
        success_criteria="Use professional vocabulary, provide concrete examples, avoid clichés, show self-awareness, demonstrate growth mindset, balance honesty with positivity.",
        difficulty_tags=["professional", "self_reflection", "complex_sentences", "formal_register", "persuasion"],
        user_variables={
            "main_strength": "",
            "strength_example": "",
            "area_for_improvement": "",
            "improvement_plan": ""
        }
    ),

    "job_interview_experience": ScenarioTemplate(
        scenario_id="job_interview_experience",
        title="Job Interview - Describing Past Experience",
        level_min="B2",
        level_max="C2",
        situation_description="The interviewer asks you to describe a challenging project or situation you handled in a previous role and what you learned from it.",
        user_goal="Tell a compelling professional story using the STAR method (Situation, Task, Action, Result), demonstrating problem-solving skills and professional growth.",
        task="Describe a specific professional challenge, explain your approach, detail the actions you took, and share the results and lessons learned.",
        success_criteria="Use past tenses accurately, structure story clearly with STAR method, include specific details, show problem-solving ability, reflect on learning outcomes.",
        difficulty_tags=["professional", "narrative", "past_tenses", "complex_sentences", "storytelling", "formal_register"],
        user_variables={
            "situation": "",
            "challenge": "",
            "actions_taken": [],
            "results": "",
            "lessons_learned": ""
        }
    ),

    # TRAVEL SCENARIOS
    "airport_security": ScenarioTemplate(
        scenario_id="airport_security",
        title="Going Through Airport Security",
        level_min="A2",
        level_max="B1",
        situation_description="You're at airport security and the TSA officer is giving you instructions. You need to understand and follow their directions while having your documents ready.",
        user_goal="Understand security instructions, respond to questions about your luggage and travel, follow procedures correctly, and handle any issues politely.",
        task="Present your boarding pass and ID, answer questions about your bags and belongings, follow instructions to remove items, and go through the scanner.",
        success_criteria="Understand imperative instructions, respond clearly to yes/no questions, use polite language, stay calm under pressure, follow multi-step directions.",
        difficulty_tags=["transactional", "travel_vocabulary", "imperative_understanding", "question_answering", "formal_register"],
        user_variables={
            "destination": "",
            "items_in_bag": [],
            "electronics": [],
            "liquids": False
        }
    ),

    "taxi_ride": ScenarioTemplate(
        scenario_id="taxi_ride",
        title="Taking a Taxi",
        level_min="A2",
        level_max="B1",
        situation_description="You need to take a taxi to get to your destination. You'll need to communicate your destination, discuss the route, and handle payment.",
        user_goal="Clearly state your destination, confirm the route and price, make small talk if appropriate, and complete the transaction.",
        task="Tell the driver where you want to go, ask about the fare or route, confirm arrival, and pay for the ride.",
        success_criteria="Give clear directions, use polite requests, understand fare information, ask about time/route, thank the driver appropriately.",
        difficulty_tags=["transactional", "travel_vocabulary", "directions", "polite_requests", "negotiation"],
        user_variables={
            "destination_address": "",
            "preferred_route": "",
            "payment_method": "cash",
            "urgency": "moderate"
        }
    ),

    # SOCIAL SCENARIOS
    "meeting_neighbors": ScenarioTemplate(
        scenario_id="meeting_neighbors",
        title="Meeting New Neighbors",
        level_min="A2",
        level_max="B1",
        situation_description="You've just moved into a new apartment or house. You meet your neighbor in the hallway or at your door and they want to introduce themselves.",
        user_goal="Make a good first impression, exchange basic information, be friendly and approachable, establish a positive relationship.",
        task="Introduce yourself, share where you're from and what you do, ask about them and the neighborhood, and express interest in being good neighbors.",
        success_criteria="Use friendly informal language, ask reciprocal questions, show genuine interest, use appropriate greetings, offer basic personal information.",
        difficulty_tags=["social", "introductions", "small_talk", "question_formation", "community"],
        user_variables={
            "your_name": "",
            "where_from": "",
            "occupation": "",
            "moving_from": ""
        }
    ),

    "party_smalltalk": ScenarioTemplate(
        scenario_id="party_smalltalk",
        title="Making Small Talk at a Party",
        level_min="B1",
        level_max="B2",
        situation_description="You're at a social gathering or party and someone you don't know well starts a conversation with you. You need to keep the conversation flowing naturally.",
        user_goal="Engage in light, casual conversation, find common ground, show interest without being intrusive, and maintain a pleasant interaction.",
        task="Respond to small talk openers, ask follow-up questions, share appropriate personal information, discuss neutral topics (weather, food, event), and keep conversation balanced.",
        success_criteria="Use conversational fillers and discourse markers, ask open-ended questions, show active listening, avoid controversial topics, maintain turn-taking balance.",
        difficulty_tags=["social", "small_talk", "conversational_fluency", "question_formation", "rapport_building"],
        user_variables={
            "connection_to_host": "",
            "interests": [],
            "current_events": [],
            "conversational_style": "balanced"
        }
    ),

    "phone_call_friend": ScenarioTemplate(
        scenario_id="phone_call_friend",
        title="Casual Phone Call with a Friend",
        level_min="A2",
        level_max="B2",
        situation_description="A friend calls you to catch up. You'll have a casual conversation about recent events, make plans, and chat about everyday topics.",
        user_goal="Have a natural, friendly conversation, share updates about your life, listen to their news, and possibly make plans to meet up.",
        task="Answer the phone, exchange greetings, talk about what you've been up to, ask about their life, and arrange to meet or continue the friendship.",
        success_criteria="Use casual register, employ conversational expressions ('you know', 'I mean'), ask follow-up questions, share personal updates naturally, suggest plans.",
        difficulty_tags=["social", "phone_language", "informal_register", "conversational_fluency", "friendship"],
        user_variables={
            "friend_name": "",
            "last_contact": "",
            "recent_activities": [],
            "plan_to_suggest": ""
        }
    ),

    # PROFESSIONAL SCENARIOS
    "business_meeting": ScenarioTemplate(
        scenario_id="business_meeting",
        title="Participating in a Business Meeting",
        level_min="B2",
        level_max="C2",
        situation_description="You're attending a business meeting where team members are discussing a project. You need to participate actively, share your opinions, and contribute to the discussion.",
        user_goal="Express your ideas clearly, agree or disagree diplomatically, ask clarifying questions, and contribute meaningfully to the discussion.",
        task="Listen to others' points, express your opinion on the topic, support your ideas with reasoning, respond to questions or objections, and help reach consensus.",
        success_criteria="Use formal business language, employ diplomatic phrases for disagreement, structure arguments logically, use modal verbs for suggestions, maintain professional tone.",
        difficulty_tags=["professional", "formal_register", "opinion_expression", "negotiation", "complex_sentences", "business_vocabulary"],
        user_variables={
            "your_role": "",
            "meeting_topic": "",
            "your_position": "",
            "concerns": []
        }
    ),

    "email_followup": ScenarioTemplate(
        scenario_id="email_followup",
        title="Discussing Email Communication",
        level_min="B1",
        level_max="C1",
        situation_description="A colleague mentions they sent you an important email and wants to discuss it. You need to reference the email content and discuss next steps.",
        user_goal="Show you understand the email content, discuss the issues or proposals, ask clarifying questions, and agree on action items.",
        task="Confirm you received and read the email, discuss the main points, ask questions about unclear items, and establish what needs to be done next.",
        success_criteria="Use appropriate phrases for referring to written communication, ask for clarification professionally, summarize key points, use future forms for action items.",
        difficulty_tags=["professional", "formal_register", "business_vocabulary", "action_planning", "clarification"],
        user_variables={
            "email_topic": "",
            "sender": "",
            "main_points": [],
            "questions": []
        }
    ),

    "presentation_qa": ScenarioTemplate(
        scenario_id="presentation_qa",
        title="Q&A After a Presentation",
        level_min="B2",
        level_max="C2",
        situation_description="You've just finished giving a presentation and now it's time for questions from the audience. You need to handle questions professionally and provide clear answers.",
        user_goal="Answer questions clearly and confidently, handle difficult questions diplomatically, admit when you don't know something, and engage with the audience.",
        task="Listen to audience questions, provide thoughtful answers, clarify when needed, acknowledge good questions, and handle challenging or critical questions professionally.",
        success_criteria="Use professional language, structure answers clearly, employ phrases for buying time ('That's a great question...'), admit uncertainty gracefully, stay calm under pressure.",
        difficulty_tags=["professional", "formal_register", "public_speaking", "complex_sentences", "persuasion", "diplomacy"],
        user_variables={
            "presentation_topic": "",
            "expertise_level": "",
            "audience_type": "mixed",
            "controversial_aspects": []
        }
    ),

    # DAILY LIFE SCENARIOS
    "grocery_shopping": ScenarioTemplate(
        scenario_id="grocery_shopping",
        title="Shopping at a Grocery Store",
        level_min="A1",
        level_max="B1",
        situation_description="You're at a grocery store and need help finding items or asking about products. A store employee is available to assist you.",
        user_goal="Find the items you need, ask for help locating products, inquire about prices or alternatives, and complete your shopping.",
        task="Ask where specific items are located, inquire about product details (price, size, freshness), ask for recommendations, and thank the employee.",
        success_criteria="Use polite question forms ('Could you tell me...', 'Do you have...'), understand location directions (aisle, shelf), ask about quantities and prices clearly.",
        difficulty_tags=["transactional", "shopping_vocabulary", "question_formation", "polite_requests", "food_vocabulary"],
        user_variables={
            "shopping_list": [],
            "dietary_restrictions": [],
            "budget": "flexible",
            "unfamiliar_items": []
        }
    ),

    "doctor_symptoms": ScenarioTemplate(
        scenario_id="doctor_symptoms",
        title="Describing Symptoms to a Doctor",
        level_min="B1",
        level_max="C1",
        situation_description="You're at a doctor's appointment because you haven't been feeling well. The doctor asks you to describe your symptoms in detail.",
        user_goal="Accurately describe your symptoms, answer the doctor's questions, explain when symptoms started, and understand the diagnosis and treatment.",
        task="Describe what hurts and how it feels, explain when symptoms began, mention severity and frequency, answer medical questions, and understand the doctor's advice.",
        success_criteria="Use medical vocabulary correctly (pain, ache, sore, fever), describe duration and intensity, use present perfect for recent symptoms, understand medical instructions.",
        difficulty_tags=["transactional", "health_vocabulary", "symptom_description", "present_perfect", "formal_register"],
        user_variables={
            "main_symptom": "",
            "duration": "",
            "severity": "moderate",
            "other_symptoms": [],
            "medications": []
        }
    ),

    "bank_account": ScenarioTemplate(
        scenario_id="bank_account",
        title="Opening a Bank Account",
        level_min="B1",
        level_max="B2",
        situation_description="You want to open a new bank account. You're meeting with a bank representative who will explain the process and account options.",
        user_goal="Understand different account types, ask about fees and requirements, provide necessary information, and complete the application process.",
        task="Explain what type of account you need, ask about interest rates and fees, understand requirements and documents needed, and decide which account to open.",
        success_criteria="Use financial vocabulary (checking account, savings, interest, fees, deposit), ask comparative questions, understand complex information, provide personal details clearly.",
        difficulty_tags=["transactional", "financial_vocabulary", "formal_register", "comparatives", "decision_making"],
        user_variables={
            "account_type": "checking",
            "initial_deposit": "",
            "usage_plans": [],
            "documents_available": []
        }
    ),

    "tech_support": ScenarioTemplate(
        scenario_id="tech_support",
        title="Getting Tech Support Help",
        level_min="B1",
        level_max="B2",
        situation_description="You're having a technical problem with a device or service. You call customer support and need to explain the issue so they can help you fix it.",
        user_goal="Clearly describe the technical problem, follow troubleshooting instructions, ask for clarification when needed, and resolve the issue.",
        task="Explain what's not working, describe what you've already tried, follow the support agent's instructions step-by-step, and confirm when the issue is resolved.",
        success_criteria="Use technical vocabulary appropriately, describe problems clearly, understand imperative instructions, ask for clarification, confirm understanding of steps.",
        difficulty_tags=["transactional", "tech_vocabulary", "problem_description", "following_instructions", "formal_register"],
        user_variables={
            "device_type": "",
            "problem_description": "",
            "error_messages": [],
            "troubleshooting_done": []
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
