"""
Scenario definitions for Duolingo Speak
10 Open-Topic Roleplay Scenarios featuring assigned AI Characters.
"""

from app.characters import get_character

SCENARIOS = {
    "travel_world": {
        "id": "travel_world",
        "title": "Planning a Dream World Tour",
        "category": "Travel & Culture",
        "icon": "✈️",
        "color": "#138808",
        "level": "Intermediate",
        "level_code": "B1",
        "default_character": "ananya",
        "target_turns": 6,
        "description": "Discuss dream destinations, backpacker tips, street foods, and unforgettable travel memories with Ananya from Mumbai.",
        "objective": "Practice descriptive language, expressing travel preferences, and sharing personal stories.",
        "suggested_vocabulary": ["Bucket list", "Off the beaten path", "Local delicacies", "Breathtaking view", "Cultural immersion"]
    },
    "tech_startup": {
        "id": "tech_startup",
        "title": "Pitching a Crazy Startup Idea",
        "category": "Business & Tech",
        "icon": "💡",
        "color": "#FF9933",
        "level": "Advanced",
        "level_code": "B2",
        "default_character": "rajesh",
        "target_turns": 7,
        "description": "Pitch an innovative app or business idea to Raj, an energetic tech mentor from Bangalore.",
        "objective": "Practice persuasive speech, explaining value propositions, and answering investor questions.",
        "suggested_vocabulary": ["Game-changer", "Target audience", "Scalability", "Revenue model", "Solve a real pain point"]
    },
    "movie_popculture": {
        "id": "movie_popculture",
        "title": "Movie & Pop Culture Debate",
        "category": "Entertainment",
        "icon": "🍿",
        "color": "#FF2A85",
        "level": "Beginner",
        "level_code": "A2-B1",
        "default_character": "chloe",
        "target_turns": 5,
        "description": "Debate your favorite cinema blockbusters, binge-worthy series, and hot pop culture trends with Chloe.",
        "objective": "Practice expressing opinions, agreeing/disagreeing casually, and talking about entertainment.",
        "suggested_vocabulary": ["Plot twist", "Binge-watch", "Overrated", "Masterpiece", "Cinematography"]
    },
    "mars_space": {
        "id": "mars_space",
        "title": "Living on Mars & Space Exploration",
        "category": "Science & Future",
        "icon": "🚀",
        "color": "#DD0000",
        "level": "Advanced",
        "level_code": "B2-C1",
        "default_character": "hans",
        "target_turns": 6,
        "description": "Explore the physics, engineering, and human challenges of colonizing Mars with Hans Gruber.",
        "objective": "Practice technical vocabulary, discussing hypothetical scenarios, and logical reasoning.",
        "suggested_vocabulary": ["Terraforming", "Space colonization", "Atmospheric pressure", "Sustainable habitat", "Interplanetary travel"]
    },
    "culinary_secrets": {
        "id": "culinary_secrets",
        "title": "World Culinary Showdown",
        "category": "Food & Cooking",
        "icon": "🍳",
        "color": "#58CC02",
        "default_character": "ananya",
        "target_turns": 6,
        "description": "Discuss secret spice recipes, street food markets vs fine dining, and cooking misadventures.",
        "objective": "Practice sensory descriptors, recipe instructions, and food vocabulary.",
        "suggested_vocabulary": ["Aromatic spices", "Crispy texture", "Savory flavor", "Comfort food", "Secret ingredient"]
    },
    "history_time_travel": {
        "id": "history_time_travel",
        "title": "Time Travel & Historical Mysteries",
        "category": "History & Philosophy",
        "icon": "⏳",
        "color": "#00247D",
        "level": "Advanced",
        "level_code": "C1",
        "default_character": "william",
        "target_turns": 7,
        "description": "Travel back in time with Sir William to witness historic events or solve ancient mysteries.",
        "objective": "Practice past modal verbs (would have, could have), formal vocabulary, and storytelling.",
        "suggested_vocabulary": ["Historical turning point", "If I were to visit...", "Ancient civilization", "Unsolved mystery", "Monumental era"]
    },
    "ai_robot_ethics": {
        "id": "ai_robot_ethics",
        "title": "AI Ethics: Should Robots Have Rights?",
        "category": "Technology & Ethics",
        "icon": "🤖",
        "color": "#CE82FF",
        "level": "Master",
        "level_code": "C1",
        "default_character": "hans",
        "target_turns": 8,
        "description": "Engage in an ethical discussion about artificial consciousness, robot rights, and human safety.",
        "objective": "Practice structured debate, ethical terms, and counter-arguments.",
        "suggested_vocabulary": ["Sentience", "Moral obligation", "Artificial general intelligence", "Automated decisions", "Ethical framework"]
    },
    "life_coaching": {
        "id": "life_coaching",
        "title": "Work-Life Balance & Finding Purpose",
        "category": "Lifestyle & Wellness",
        "icon": "🧘",
        "color": "#D80621",
        "level": "Intermediate",
        "level_code": "B1-B2",
        "default_character": "evelyn",
        "target_turns": 6,
        "description": "Have a soothing, deep conversation with Dr. Evelyn about career goals, stress management, and happiness.",
        "objective": "Practice expressing emotions, personal reflections, and future aspirations.",
        "suggested_vocabulary": ["Mindfulness", "Preventing burnout", "Inner peace", "Work-life harmony", "Core values"]
    },
    "wildlife_adventure": {
        "id": "wildlife_adventure",
        "title": "Wildest Outdoor Misadventures",
        "category": "Sports & Adventure",
        "icon": "🦈",
        "color": "#00843D",
        "level": "Beginner-Intermediate",
        "level_code": "A2-B1",
        "default_character": "brody",
        "target_turns": 6,
        "description": "Share crazy camping, surfing, or animal encounter stories with Captain Brody from Australia.",
        "objective": "Practice casual narrative tenses, exclamation phrases, and outdoor vocabulary.",
        "suggested_vocabulary": ["Close call", "In the wild", "Surfing the waves", "Unforgettable adrenaline", "Out in the bush"]
    },
    "gaming_future": {
        "id": "gaming_future",
        "title": "VR, Metaverse & The Future of Gaming",
        "category": "Gaming & Art",
        "icon": "🎮",
        "color": "#BC002D",
        "level": "Intermediate",
        "level_code": "B1",
        "default_character": "yuki",
        "target_turns": 6,
        "description": "Discuss immersive virtual reality worlds, anime art styles, and game design with Yuki from Tokyo.",
        "objective": "Practice expressing creative ideas, discussing virtual worlds, and technical gaming terms.",
        "suggested_vocabulary": ["Immersive experience", "Virtual reality", "Game mechanics", "Artistic vision", "Player engagement"]
    }
}

def get_scenario(scenario_id: str):
    sc = SCENARIOS.get(scenario_id)
    if sc:
        sc_copy = sc.copy()
        sc_copy["character_info"] = get_character(sc_copy["default_character"])
        return sc_copy
    return None

def list_scenarios():
    res = []
    for s in SCENARIOS.values():
        item = s.copy()
        item["character_info"] = get_character(s["default_character"])
        res.append(item)
    return res
