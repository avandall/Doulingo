"""
Scenario definitions for Duolingo Speak
10 Relatable, Everyday Life Topics (Bình dân cuộc sống).
Merged with SQLite database custom topics.
"""

from app.characters import get_character
from app.db import get_custom_scenarios

DEFAULT_SCENARIOS = {
    "cafe_order": {
        "id": "cafe_order",
        "title": "Ordering Coffee & Bakery Snacks",
        "category": "Everyday Life ☕",
        "icon": "☕",
        "color": "#FF9933",
        "level": "Beginner",
        "level_code": "A2",
        "default_character": "rajesh",
        "description": "Order coffee, ask for milk choices, customize sugar levels, and pick a freshly baked pastry.",
        "objective": "Practice polite ordering, food vocabulary, and asking simple questions.",
        "suggested_vocabulary": ["I'd like an iced latte", "Less sugar please", "With oat milk", "To go / For here", "Fresh pastry"]
    },
    "grocery_market": {
        "id": "grocery_market",
        "title": "Grocery Shopping & Market Bargaining",
        "category": "Everyday Life 🛒",
        "icon": "🛒",
        "color": "#4CAF50",
        "level": "Beginner-Intermediate",
        "level_code": "A2-B1",
        "default_character": "priya",
        "description": "Buy fresh fruits, vegetables, and negotiate prices with dramatic Bollywood diva Priya.",
        "objective": "Practice asking for prices, quantity, and bargaining politely.",
        "suggested_vocabulary": ["How much is this?", "Is it fresh?", "Can you give a discount?", "Half a kilo", "Ripe mangoes"]
    },
    "dinner_choice": {
        "id": "dinner_choice",
        "title": "Deciding What to Eat for Dinner",
        "category": "Food & Dining 🍕",
        "icon": "🍕",
        "color": "#E91E63",
        "level": "Beginner",
        "level_code": "A2",
        "default_character": "marco",
        "description": "Argue passionately with Italian Chef Marco about whether to eat pizza, sushi, or homecooked pasta.",
        "objective": "Practice expressing food cravings, agreeing/disagreeing, and making plans.",
        "suggested_vocabulary": ["I'm craving...", "What are you in the mood for?", "Homemade pasta", "Spicy food", "Let's order delivery"]
    },
    "taxi_directions": {
        "id": "taxi_directions",
        "title": "Asking for Directions & Taking a Taxi",
        "category": "Travel & Transportation 🚕",
        "icon": "🚕",
        "color": "#1CB0F6",
        "level": "Beginner",
        "level_code": "A2",
        "default_character": "brody",
        "description": "Tell your taxi driver where to go, ask about the fastest route, and avoid traffic jams.",
        "objective": "Practice giving directions, location prepositions, and asking about time.",
        "suggested_vocabulary": ["Turn left at the light", "Take the highway", "How long will it take?", "Drop me off here", "Traffic is heavy"]
    },
    "weekend_movies": {
        "id": "weekend_movies",
        "title": "Talking About Movies & Weekend Plans",
        "category": "Entertainment 🎬",
        "icon": "🎬",
        "color": "#FF2A85",
        "level": "Intermediate",
        "level_code": "B1",
        "default_character": "chloe",
        "description": "Chat about the latest cinema releases, streaming series, and weekend hangout plans with Chloe.",
        "objective": "Practice talking about entertainment, recommending movies, and weekend activities.",
        "suggested_vocabulary": ["Binge-watch", "Have you seen...", "Popcorn movie", "Hang out", "Worth watching"]
    },
    "beach_vacation": {
        "id": "beach_vacation",
        "title": "Planning a Weekend Beach Trip",
        "category": "Travel & Fun 🏖️",
        "icon": "🏖️",
        "color": "#00843D",
        "level": "Intermediate",
        "level_code": "B1",
        "default_character": "brody",
        "description": "Plan a sunny beach trip, discuss packing sunscreen, surfing, and outdoor barbecues with Captain Brody.",
        "objective": "Practice future intentions, packing lists, and outdoor activities.",
        "suggested_vocabulary": ["Sunscreen", "Beach resort", "Rent a surfboard", "Seafood barbecue", "Soak up the sun"]
    },
    "pets_routine": {
        "id": "pets_routine",
        "title": "Pets, Cute Animals & Daily Habits",
        "category": "Daily Life 🐶",
        "icon": "🐶",
        "color": "#9C27B0",
        "level": "Beginner",
        "level_code": "A2",
        "default_character": "evelyn",
        "description": "Share stories about your pets, daily morning routines, and relaxing evening habits with Dr. Evelyn.",
        "objective": "Practice simple present tense, daily routine verbs, and talking about pets.",
        "suggested_vocabulary": ["Walk the dog", "Morning coffee", "Adoption", "Cute kitten", "Unwind after work"]
    },
    "apartment_chores": {
        "id": "apartment_chores",
        "title": "Apartment Life & House Chores",
        "category": "Home & Life 🏠",
        "icon": "🏠",
        "color": "#DD0000",
        "level": "Intermediate",
        "level_code": "B1",
        "default_character": "hans",
        "description": "Complain or organize room cleaning, laundry schedules, and apartment maintenance with strict Hans Gruber.",
        "objective": "Practice household vocabulary, schedules, and chore distribution.",
        "suggested_vocabulary": ["Do the laundry", "Vacuum the carpet", "Fix the sink", "Noisy neighbors", "Rent payment"]
    },
    "apps_socialmedia": {
        "id": "apps_socialmedia",
        "title": "Chatting About Apps & Social Media",
        "category": "Technology 📱",
        "icon": "📱",
        "color": "#CE82FF",
        "level": "Intermediate",
        "level_code": "B1",
        "default_character": "chloe",
        "description": "Discuss viral trends, useful smartphone apps, screen time, and funny videos with Gen-Z Chloe.",
        "objective": "Practice tech vocabulary, describing trends, and opinion expressions.",
        "suggested_vocabulary": ["Viral video", "Notification", "Scroll through feed", "Useful app", "Screen time limit"]
    },
    "traffic_weather": {
        "id": "traffic_weather",
        "title": "Complaining About Traffic & Rain",
        "category": "Daily Life 🌧️",
        "icon": "🌧️",
        "color": "#00247D",
        "level": "Beginner-Intermediate",
        "level_code": "A2-B1",
        "default_character": "william",
        "description": "Complain about unexpected heavy rain, traffic gridlocks, and cancelled plans with Sir William.",
        "objective": "Practice weather descriptors, expressing frustration politely, and small talk.",
        "suggested_vocabulary": ["Pouring rain", "Gridlock traffic", "Stuck in traffic", "Soaked", "Weather forecast"]
    }
}

def get_scenario(scenario_id: str):
    if scenario_id in DEFAULT_SCENARIOS:
        sc = DEFAULT_SCENARIOS[scenario_id].copy()
        sc["character_info"] = get_character(sc["default_character"])
        return sc
    
    customs = get_custom_scenarios()
    for sc in customs:
        if sc["id"] == scenario_id:
            sc_copy = sc.copy()
            sc_copy["character_info"] = get_character(sc["default_character"])
            return sc_copy
            
    return None

def list_scenarios():
    res = []
    for s in DEFAULT_SCENARIOS.values():
        item = s.copy()
        item["character_info"] = get_character(s["default_character"])
        res.append(item)
    
    customs = get_custom_scenarios()
    for c in customs:
        item = c.copy()
        item["character_info"] = get_character(c["default_character"])
        res.append(item)
        
    return res
