"""
Scenario definitions for Duolingo Speak
Clean, simple UI titles with open-ended creative story seeds for AI improvisation.
No hardcoded levels, default characters, or suggested vocabulary.
"""

from app.db import get_custom_scenarios

DEFAULT_SCENARIOS = {
    "cafe_order": {
        "id": "cafe_order",
        "title": "Coffee Shop",
        "category": "Everyday",
        "icon": "☕",
        "color": "#FF9933",
        "description": "Order coffee, secret menu drinks, and gossip at a busy cafe.",
        "open_story_guide": "An unscripted cafe encounter. Improvise funny drink mixups, secret menu items, or chaotic cafe drama."
    },
    "night_market": {
        "id": "night_market",
        "title": "Night Market",
        "category": "Everyday",
        "icon": "🛒",
        "color": "#4CAF50",
        "description": "Explore bustling street food stalls and bargain for unique finds.",
        "open_story_guide": "An open night market adventure. Improvise exotic food tasting, funny price bargaining, or rare antique discoveries."
    },
    "dinner_choice": {
        "id": "dinner_choice",
        "title": "Late-Night Diner",
        "category": "Food",
        "icon": "🍕",
        "color": "#E91E63",
        "description": "Debate late-night food cravings and chef special recipes.",
        "open_story_guide": "A hilarious late-night food debate. Improvise weird food combos, midnight cravings, or chef specials."
    },
    "city_taxi": {
        "id": "city_taxi",
        "title": "City Taxi",
        "category": "Travel",
        "icon": "🚕",
        "color": "#1CB0F6",
        "description": "Navigate city streets, dodge traffic, and find secret shortcuts.",
        "open_story_guide": "A chaotic taxi ride across town. Improvise unexpected traffic jams, radio trivia, or secret detour shortcuts."
    },
    "cinema_drinks": {
        "id": "cinema_drinks",
        "title": "Cinema & Drinks",
        "category": "Fun",
        "icon": "🎬",
        "color": "#FF2A85",
        "description": "Discuss movie premieres, plot twists, and smuggled cinema snacks.",
        "open_story_guide": "A lively movie night chat. Improvise film plot debates, sold-out tickets, or secret movie spoilers."
    },
    "beach_vacation": {
        "id": "beach_vacation",
        "title": "Beach Getaway",
        "category": "Travel",
        "icon": "🏖️",
        "color": "#00843D",
        "description": "Plan a tropical beach trip, surfing sessions, and sunset barbecues.",
        "open_story_guide": "A sunny coastal getaway. Improvise sudden tropical rainstorms, beach volleyball challenges, or secret cove discoveries."
    },
    "pet_shelter": {
        "id": "pet_shelter",
        "title": "Pet Shelter",
        "category": "Life",
        "icon": "🐶",
        "color": "#9C27B0",
        "description": "Meet adorable animals, adopt pets, and share funny routine stories.",
        "open_story_guide": "A heartwarming or funny animal encounter. Improvise chaotic pet talents, adoption stories, or funny pet habits."
    },
    "cyber_repair": {
        "id": "cyber_repair",
        "title": "Cyberpunk Repair",
        "category": "Tech",
        "icon": "💻",
        "color": "#673AB7",
        "description": "Troubleshoot glitchy AI gadgets, frozen screens, and futuristic tech.",
        "open_story_guide": "A futuristic tech breakdown. Improvise rogue AI glitches, secret gadget modifications, or cyber hacker rumors."
    },
    "apartment_rent": {
        "id": "apartment_rent",
        "title": "Apartment Rental",
        "category": "Housing",
        "icon": "🏠",
        "color": "#795548",
        "description": "Negotiate rent, check balcony views, and ask about building rules.",
        "open_story_guide": "A dramatic housing inspection. Improvise eccentric landlord rules, secret balcony views, or funny room quirks."
    },
    "midnight_clinic": {
        "id": "midnight_clinic",
        "title": "Midnight Clinic",
        "category": "Health",
        "icon": "🏥",
        "color": "#00BCD4",
        "description": "Describe mysterious symptoms, get health remedies, and consult a doctor.",
        "open_story_guide": "An unusual medical checkup. Improvise strange symptoms, bizarre herbal remedies, or emergency room drama."
    },
    "secret_safehouse": {
        "id": "secret_safehouse",
        "title": "Secret Safehouse",
        "category": "Action",
        "icon": "🕶️",
        "color": "#37474F",
        "description": "Exchange secret codes, evade rival agents, and plan classified missions.",
        "open_story_guide": "A high-stakes espionage roleplay. Improvise secret agent ambushes, encrypted radio messages, or undercover escapes."
    },
    "pirate_tavern": {
        "id": "pirate_tavern",
        "title": "Pirate Ship Tavern",
        "category": "Adventure",
        "icon": "🏴‍☠️",
        "color": "#C62828",
        "description": "Hunt for lost treasure maps, toast pirate grog, and duel swashbucklers.",
        "open_story_guide": "A wild pirate adventure. Improvise treasure map clues, sea monster rumors, or tavern duel challenges."
    }
}

def list_scenarios():
    scenarios_list = []
    for sc in DEFAULT_SCENARIOS.values():
        sc_copy = sc.copy()
        sc_copy["is_custom"] = False
        scenarios_list.append(sc_copy)

    custom_scenarios = get_custom_scenarios()
    for cs in custom_scenarios:
        scenarios_list.append(cs)

    return scenarios_list

def get_scenario(scenario_id: str):
    if scenario_id in DEFAULT_SCENARIOS:
        sc = DEFAULT_SCENARIOS[scenario_id].copy()
        sc["is_custom"] = False
        return sc
    
    customs = get_custom_scenarios()
    for cs in customs:
        if cs["id"] == scenario_id:
            return cs

    return None
