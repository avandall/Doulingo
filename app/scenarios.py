"""
Scenario definitions for Duolingo Speak
Includes Duolingo English Test (DET) Interactive Speaking topics and everyday roleplays.
Clean, simple UI titles with open-ended creative story seeds for AI improvisation.
"""

from typing import Dict, List, Any, Optional
from app.db import get_custom_scenarios

DEFAULT_SCENARIOS = {
    # ============================================================
    # DET GROUP 1: PERSONAL & FAMILY (CÁ NHÂN & GIA ĐÌNH)
    # ============================================================
    "det_childhood_memory": {
        "id": "det_childhood_memory",
        "title": "Childhood Memories",
        "category": "Personal & Family",
        "icon": "👶",
        "color": "#FF9600",
        "description": "Share a memorable childhood story, family tradition, or talk about someone close to you.",
        "open_story_guide": "An interactive DET Speaking dialogue about personal memories. Ask open-ended questions about their childhood, family traditions, lessons learned growing up, and cherished memories.",
        "det_mode": "exam",
        "question_card": {
            "prompt": "Describe a memorable event from your childhood that taught you an important lesson.",
            "bullet_points": [
                "What the event was and when it happened",
                "Who was with you during the event",
                "Why this memory stands out to you",
                "What life lesson you learned from the experience"
            ],
            "time_limit_seconds": 180,
            "min_time_seconds": 60
        }
    },
    "det_best_friend": {
        "id": "det_best_friend",
        "title": "Best Friends & Personality",
        "category": "Personal & Family",
        "icon": "🤝",
        "color": "#FF4B4B",
        "description": "Discuss what makes a true friend, personality traits, and unforgettable moments.",
        "open_story_guide": "An interactive DET Speaking dialogue about friendship and character. Ask about their closest friends, ideal personality traits, shared experiences, and what friendship means to them.",
        "det_mode": "exam",
        "question_card": {
            "prompt": "Describe your best friend and explain what makes your friendship special.",
            "bullet_points": [
                "Who your best friend is and how long you have known them",
                "What personality traits you admire most in this person",
                "A memorable experience you have shared together",
                "Why you believe strong friendships are important in life"
            ],
            "time_limit_seconds": 180,
            "min_time_seconds": 60
        }
    },

    # ============================================================
    # DET GROUP 2: STUDIES & CAREER (HỌC TẬP & NGHỀ NGHIỆP)
    # ============================================================
    "det_career_ambition": {
        "id": "det_career_ambition",
        "title": "Career & Ambitions",
        "category": "Studies & Career",
        "icon": "💼",
        "color": "#1CB0F6",
        "description": "Talk about your current job, dream profession, workplace skills, and future career goals.",
        "open_story_guide": "An interactive DET Speaking dialogue about professional life. Explore their career ambitions, work ethic, dream job challenges, and future plans.",
        "det_mode": "exam",
        "question_card": {
            "prompt": "Talk about a profession or career goal that you aspire to achieve in the future.",
            "bullet_points": [
                "What the profession is and what daily tasks it involves",
                "What qualifications or skills are required to succeed",
                "Why you are personally passionate about this career path",
                "How you plan to overcome potential obstacles to reach this goal"
            ],
            "time_limit_seconds": 180,
            "min_time_seconds": 60
        }
    },
    "det_school_life": {
        "id": "det_school_life",
        "title": "School & Education",
        "category": "Studies & Career",
        "icon": "🎓",
        "color": "#673AB7",
        "description": "Describe your favorite school subject, memorable teachers, or university experience.",
        "open_story_guide": "An interactive DET Speaking dialogue about education. Ask about their favorite subjects, study methods, impactful teachers, and educational experiences.",
        "det_mode": "exam",
        "question_card": {
            "prompt": "Describe a school subject or educational experience that had a significant impact on you.",
            "bullet_points": [
                "What the subject or course was and where you studied it",
                "Who taught the subject and what made their teaching method effective",
                "What specific knowledge or skill you gained",
                "How this learning experience influenced your academic or professional life"
            ],
            "time_limit_seconds": 180,
            "min_time_seconds": 60
        }
    },

    # ============================================================
    # DET GROUP 3: HOBBIES & LIFESTYLE (SỞ THÍCH & LỐI SỐNG)
    # ============================================================
    "det_book_movie": {
        "id": "det_book_movie",
        "title": "Inspiring Books & Movies",
        "category": "Hobbies & Lifestyle",
        "icon": "📚",
        "color": "#9C27B0",
        "description": "Describe a book, movie, or story that inspired you or changed your perspective.",
        "open_story_guide": "An interactive DET Speaking dialogue about literature and film. Ask them to describe an inspiring story, key characters, plot twists, and why it resonated with them.",
        "det_mode": "exam",
        "question_card": {
            "prompt": "Describe a book, film, or story that strongly inspired you or changed your perspective.",
            "bullet_points": [
                "What the title is and what the central plot is about",
                "Who the main characters are and what challenges they face",
                "What underlying theme or message resonated with you",
                "Why you would recommend this story to others"
            ],
            "time_limit_seconds": 180,
            "min_time_seconds": 60
        }
    },
    "det_sports_health": {
        "id": "det_sports_health",
        "title": "Sports & Healthy Lifestyle",
        "category": "Hobbies & Lifestyle",
        "icon": "🏃",
        "color": "#00843D",
        "description": "Discuss weekend hobbies, favorite sports, physical fitness, and healthy daily routines.",
        "open_story_guide": "An interactive DET Speaking dialogue about wellness and lifestyle. Ask about their exercise habits, favorite recreational activities, stress relief, and healthy diet choices.",
        "det_mode": "exam",
        "question_card": {
            "prompt": "Discuss the importance of maintaining a healthy lifestyle and regular physical activity.",
            "bullet_points": [
                "What physical activity or sport you enjoy doing",
                "How often you practice it and how it benefits your physical health",
                "How regular exercise impacts your mental well-being and stress levels",
                "Why many people struggle to maintain healthy routines in modern society"
            ],
            "time_limit_seconds": 180,
            "min_time_seconds": 60
        }
    },

    # ============================================================
    # DET GROUP 4: TRAVEL & PLACES (DU LỊCH & ĐỊA ĐIỂM)
    # ============================================================
    "det_hometown_city": {
        "id": "det_hometown_city",
        "title": "Hometown & City Life",
        "category": "Travel & Places",
        "icon": "🏙️",
        "color": "#00BCD4",
        "description": "Describe your hometown, local culture, and living in a metropolis vs. the countryside.",
        "open_story_guide": "An interactive DET Speaking dialogue about places and culture. Ask them to describe their hometown, local architecture, community vibes, and preferred living environment.",
        "det_mode": "exam",
        "question_card": {
            "prompt": "Describe your hometown or the city where you currently live.",
            "bullet_points": [
                "Where the city is located and what it is famous for",
                "What the local community and lifestyle are like",
                "What the major advantages and disadvantages of living there are",
                "Whether you prefer living in a bustling metropolis or a quiet rural area, and why"
            ],
            "time_limit_seconds": 180,
            "min_time_seconds": 60
        }
    },
    "det_dream_travel": {
        "id": "det_dream_travel",
        "title": "Dream Travel Destination",
        "category": "Travel & Places",
        "icon": "✈️",
        "color": "#3F51B5",
        "description": "Share stories about a place you visited or describe your dream vacation destination.",
        "open_story_guide": "An interactive DET Speaking dialogue about travel experiences. Ask about memorable trips, cultural differences, dream destinations, and travel lessons.",
        "det_mode": "exam",
        "question_card": {
            "prompt": "Describe a place you have visited or a dream travel destination you wish to explore.",
            "bullet_points": [
                "Where the destination is and what makes it unique",
                "Who you traveled with or would like to travel with",
                "What specific cultural landmarks or activities interest you there",
                "Why traveling to new places is valuable for personal development"
            ],
            "time_limit_seconds": 180,
            "min_time_seconds": 60
        }
    },

    # ============================================================
    # DET GROUP 5: TECH & SOCIETY (CÔNG NGHỆ & XÃ HỘI)
    # ============================================================
    "det_social_media": {
        "id": "det_social_media",
        "title": "Social Media & Internet",
        "category": "Tech & Society",
        "icon": "📱",
        "color": "#E91E63",
        "description": "Debate the role of internet, social networks, and smartphones in modern human life.",
        "open_story_guide": "An interactive DET Speaking dialogue about digital life. Discuss the pros and cons of social media, digital communication, privacy, and changing social habits.",
        "det_mode": "exam",
        "question_card": {
            "prompt": "Discuss the influence of social media and smartphone communication on modern relationships.",
            "bullet_points": [
                "How social media has transformed daily communication",
                "What the positive benefits of global connectivity are",
                "What negative impacts excessive internet use can have on social skills",
                "How individuals can balance digital technology with real-life interactions"
            ],
            "time_limit_seconds": 180,
            "min_time_seconds": 60
        }
    },
    "det_ai_future": {
        "id": "det_ai_future",
        "title": "AI & Future Society",
        "category": "Tech & Society",
        "icon": "🤖",
        "color": "#FF2A85",
        "description": "Discuss how artificial intelligence, automation, and innovation are shaping the future.",
        "open_story_guide": "An interactive DET Speaking dialogue about AI and the future. Ask their thoughts on artificial intelligence, future workplaces, ethical challenges, and human creativity.",
        "det_mode": "exam",
        "question_card": {
            "prompt": "Discuss how artificial intelligence and automation will affect the future workforce and society.",
            "bullet_points": [
                "What industries or professions are most likely to change due to AI",
                "What the major benefits of artificial intelligence are in productivity",
                "What ethical challenges or concerns society must address regarding AI",
                "What uniquely human skills will remain essential in an automated future"
            ],
            "time_limit_seconds": 180,
            "min_time_seconds": 60
        }
    },

    # ============================================================
    # EVERYDAY LIFE ROLEPLAYS (TÌNH HUỐNG GIAO TIẾP HẰNG NGÀY)
    # ============================================================
    "cafe_order": {
        "id": "cafe_order",
        "title": "Coffee Shop Order",
        "category": "Everyday Roleplay",
        "icon": "☕",
        "color": "#FF9933",
        "description": "Order coffee, secret menu drinks, and gossip at a busy cafe.",
        "open_story_guide": "An unscripted cafe encounter. Improvise funny drink mixups, secret menu items, or chaotic cafe drama."
    },
    "night_market": {
        "id": "night_market",
        "title": "Street Night Market",
        "category": "Everyday Roleplay",
        "icon": "🛒",
        "color": "#4CAF50",
        "description": "Explore bustling street food stalls and bargain for unique finds.",
        "open_story_guide": "An open night market adventure. Improvise exotic food tasting, funny price bargaining, or rare antique discoveries."
    },
    "dinner_choice": {
        "id": "dinner_choice",
        "title": "Late-Night Diner",
        "category": "Everyday Roleplay",
        "icon": "🍕",
        "color": "#E91E63",
        "description": "Debate late-night food cravings and chef special recipes.",
        "open_story_guide": "A hilarious late-night food debate. Improvise weird food combos, midnight cravings, or chef specials."
    },
    "city_taxi": {
        "id": "city_taxi",
        "title": "City Taxi Ride",
        "category": "Everyday Roleplay",
        "icon": "🚕",
        "color": "#1CB0F6",
        "description": "Navigate city streets, dodge traffic, and find secret shortcuts.",
        "open_story_guide": "A chaotic taxi ride across town. Improvise unexpected traffic jams, radio trivia, or secret detour shortcuts."
    },
    "cinema_drinks": {
        "id": "cinema_drinks",
        "title": "Cinema & Movie Night",
        "category": "Everyday Roleplay",
        "icon": "🎬",
        "color": "#FF2A85",
        "description": "Discuss movie premieres, plot twists, and smuggled cinema snacks.",
        "open_story_guide": "A lively movie night chat. Improvise film plot debates, sold-out tickets, or secret movie spoilers."
    },
    "apartment_rent": {
        "id": "apartment_rent",
        "title": "Apartment Rental Hunt",
        "category": "Everyday Roleplay",
        "icon": "🏠",
        "color": "#795548",
        "description": "Negotiate rent, check balcony views, and ask about building rules.",
        "open_story_guide": "A dramatic housing inspection. Improvise eccentric landlord rules, secret balcony views, or funny room quirks."
    },
    "midnight_clinic": {
        "id": "midnight_clinic",
        "title": "Midnight Medical Clinic",
        "category": "Everyday Roleplay",
        "icon": "🏥",
        "color": "#00BCD4",
        "description": "Describe mysterious symptoms, get health remedies, and consult a doctor.",
        "open_story_guide": "An unusual medical checkup. Improvise strange symptoms, bizarre herbal remedies, or emergency room drama."
    },

    # ============================================================
    # SPECIAL / CREATIVE ROLEPLAYS
    # ============================================================
    "beach_vacation": {
        "id": "beach_vacation",
        "title": "Beach Getaway Trip",
        "category": "Travel & Places",
        "icon": "🏖️",
        "color": "#00843D",
        "description": "Plan a tropical beach trip, surfing sessions, and sunset barbecues.",
        "open_story_guide": "A sunny coastal getaway. Improvise sudden tropical rainstorms, beach volleyball challenges, or secret cove discoveries."
    },
    "pet_shelter": {
        "id": "pet_shelter",
        "title": "Pet Shelter Adoption",
        "category": "Hobbies & Lifestyle",
        "icon": "🐶",
        "color": "#9C27B0",
        "description": "Meet adorable animals, adopt pets, and share funny routine stories.",
        "open_story_guide": "A heartwarming or funny animal encounter. Improvise chaotic pet talents, adoption stories, or funny pet habits."
    },
    "cyber_repair": {
        "id": "cyber_repair",
        "title": "Cyberpunk Tech Repair",
        "category": "Tech & Society",
        "icon": "💻",
        "color": "#673AB7",
        "description": "Troubleshoot glitchy AI gadgets, frozen screens, and futuristic tech.",
        "open_story_guide": "A futuristic tech breakdown. Improvise rogue AI glitches, secret gadget modifications, or cyber hacker rumors."
    },
    "secret_safehouse": {
        "id": "secret_safehouse",
        "title": "Secret Agent Safehouse",
        "category": "Creative Roleplay",
        "icon": "🕶️",
        "color": "#37474F",
        "description": "Exchange secret codes, evade rival agents, and plan classified missions.",
        "open_story_guide": "A high-stakes espionage roleplay. Improvise secret agent ambushes, encrypted radio messages, or undercover escapes."
    },
    "pirate_tavern": {
        "id": "pirate_tavern",
        "title": "Pirate Ship Tavern",
        "category": "Creative Roleplay",
        "icon": "🏴‍☠️",
        "color": "#C62828",
        "description": "Hunt for lost treasure maps, toast pirate grog, and duel swashbucklers.",
        "open_story_guide": "A wild pirate adventure. Improvise treasure map clues, sea monster rumors, or tavern duel challenges."
    }
}

def list_scenarios() -> List[Dict[str, Any]]:
    scenarios_list: List[Dict[str, Any]] = []
    for sc in DEFAULT_SCENARIOS.values():
        sc_copy: Dict[str, Any] = dict(sc)
        sc_copy["is_custom"] = False
        scenarios_list.append(sc_copy)

    custom_scenarios = get_custom_scenarios()
    for cs in custom_scenarios:
        scenarios_list.append(cs)

    return scenarios_list

def get_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    if scenario_id in DEFAULT_SCENARIOS:
        sc: Dict[str, Any] = dict(DEFAULT_SCENARIOS[scenario_id])
        sc["is_custom"] = False
        return sc
    
    customs = get_custom_scenarios()
    for cs in customs:
        if cs["id"] == scenario_id:
            return cs

    return None
