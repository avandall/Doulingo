"""
Scenario definitions for Duolingo Speak
Includes International English (IELTS / CEFR) Speaking topics and everyday roleplays.
Clean, simple UI titles with open-ended creative story seeds for AI improvisation.
"""

from typing import Dict, List, Any, Optional
from app.db import get_custom_scenarios

DEFAULT_SCENARIOS = {
    # ============================================================
    # IELTS / CEFR GROUP 1: PERSONAL & FAMILY (CÁ NHÂN & GIA ĐÌNH)
    # ============================================================
    "det_childhood_memory": {
        "id": "det_childhood_memory",
        "title": "Childhood Memories",
        "category": "Personal & Family",
        "icon": "👶",
        "color": "#FF9600",
        "description": "Share a memorable childhood story, family tradition, or talk about someone close to you.",
        "open_story_guide": "An interactive IELTS / CEFR Speaking dialogue about personal memories. Ask open-ended questions about their childhood, family traditions, lessons learned growing up, and cherished memories.",
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
        "open_story_guide": "An interactive IELTS / CEFR Speaking dialogue about friendship and character. Ask about their closest friends, ideal personality traits, shared experiences, and what friendship means to them.",
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
    # IELTS / CEFR GROUP 2: STUDIES & CAREER (HỌC TẬP & NGHỀ NGHIỆP)
    # ============================================================
    "det_career_ambition": {
        "id": "det_career_ambition",
        "title": "Career & Ambitions",
        "category": "Studies & Career",
        "icon": "💼",
        "color": "#1CB0F6",
        "description": "Talk about your current job, dream profession, workplace skills, and future career goals.",
        "open_story_guide": "An interactive IELTS / CEFR Speaking dialogue about professional life. Explore their career ambitions, work ethic, dream job challenges, and future plans.",
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
        "open_story_guide": "An interactive IELTS / CEFR Speaking dialogue about education. Ask about their favorite subjects, study methods, impactful teachers, and educational experiences.",
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
    # IELTS / CEFR GROUP 3: HOBBIES & LIFESTYLE (SỞ THÍCH & LỐI SỐNG)
    # ============================================================
    "det_book_movie": {
        "id": "det_book_movie",
        "title": "Inspiring Books & Movies",
        "category": "Hobbies & Lifestyle",
        "icon": "📚",
        "color": "#9C27B0",
        "description": "Describe a book, movie, or story that inspired you or changed your perspective.",
        "open_story_guide": "An interactive IELTS / CEFR Speaking dialogue about literature and film. Ask them to describe an inspiring story, key characters, plot twists, and why it resonated with them.",
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
        "open_story_guide": "An interactive IELTS / CEFR Speaking dialogue about wellness and lifestyle. Ask about their exercise habits, favorite recreational activities, stress relief, and healthy diet choices.",
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
    # IELTS / CEFR GROUP 4: TRAVEL & PLACES (DU LỊCH & ĐỊA ĐIỂM)
    # ============================================================
    "det_hometown_city": {
        "id": "det_hometown_city",
        "title": "Hometown & City Life",
        "category": "Travel & Places",
        "icon": "🏙️",
        "color": "#00BCD4",
        "description": "Describe your hometown, local culture, and living in a metropolis vs. the countryside.",
        "open_story_guide": "An interactive IELTS / CEFR Speaking dialogue about places and culture. Ask them to describe their hometown, local architecture, community vibes, and preferred living environment.",
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
        "open_story_guide": "An interactive IELTS / CEFR Speaking dialogue about travel experiences. Ask about memorable trips, cultural differences, dream destinations, and travel lessons.",
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
    # IELTS / CEFR GROUP 5: TECH & SOCIETY (CÔNG NGHỆ & XÃ HỘI)
    # ============================================================
    "det_social_media": {
        "id": "det_social_media",
        "title": "Social Media & Internet",
        "category": "Tech & Society",
        "icon": "📱",
        "color": "#E91E63",
        "description": "Debate the role of internet, social networks, and smartphones in modern human life.",
        "open_story_guide": "An interactive IELTS / CEFR Speaking dialogue about digital life. Discuss the pros and cons of social media, digital communication, privacy, and changing social habits.",
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
        "open_story_guide": "An interactive IELTS / CEFR Speaking dialogue about AI and the future. Ask their thoughts on artificial intelligence, future workplaces, ethical challenges, and human creativity.",
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
    # EVERYDAY & CREATIVE ROLEPLAY (HỘI THOẠI GIAO TIẾP HÀNG NGÀY)
    # ============================================================
    "everyday_chat": {
        "id": "everyday_chat",
        "title": "Everyday Social Chat",
        "category": "Everyday Roleplay",
        "icon": "☕",
        "color": "#1CB0F6",
        "description": "Chat casually with your AI partner about daily routines, coffee spots, and weekend plans.",
        "open_story_guide": "A relaxed, friendly social conversation about daily habits, hobbies, and life updates."
    },
    "cafe_dining": {
        "id": "cafe_dining",
        "title": "Café & Culinary Experiences",
        "category": "Everyday Roleplay",
        "icon": "🍕",
        "color": "#FF9600",
        "description": "Order food, discuss favorite cuisines, recipes, and dining out with friends.",
        "open_story_guide": "An engaging dining and cooking conversation covering recipes, food preferences, and restaurant ordering."
    },
    "travel_culture": {
        "id": "travel_culture",
        "title": "Travel & Cultural Exchange",
        "category": "Everyday Roleplay",
        "icon": "✈️",
        "color": "#00843D",
        "description": "Share travel stories, cultural experiences, hotel check-ins, and vacation planning.",
        "open_story_guide": "An adventurous travel dialogue about exploring new destinations, local customs, and travel tips."
    },
    "work_study_space": {
        "id": "work_study_space",
        "title": "Workplace & Academic Life",
        "category": "Everyday Roleplay",
        "icon": "💼",
        "color": "#673AB7",
        "description": "Discuss career goals, university projects, study tips, and team collaboration.",
        "open_story_guide": "A collaborative career and academic chat focusing on professional skills, study habits, and workplace teamwork."
    },
    "digital_lifestyle": {
        "id": "digital_lifestyle",
        "title": "Digital Life & Hobbies",
        "category": "Everyday Roleplay",
        "icon": "📱",
        "color": "#E91E63",
        "description": "Talk about favorite mobile apps, books, movies, fitness routines, and tech in daily life.",
        "open_story_guide": "A modern lifestyle discussion on technology, entertainment recommendations, and health."
    }
}

def list_scenarios() -> List[Dict[str, Any]]:
    scenarios_list: List[Dict[str, Any]] = []
    for sc in DEFAULT_SCENARIOS.values():
        sc_copy: Dict[str, Any] = dict(sc)
        sc_copy["is_custom"] = False
        scenarios_list.append(sc_copy)

    # 2. Material Bank Topics (parsed from 5 DB markdown files)
    try:
        from app.material_bank import get_material_bank
        mb = get_material_bank()
        for topic_id, topic in mb.topics.items():
            if topic_id not in DEFAULT_SCENARIOS:
                vocab_preview = [v.phrase for v in topic.vocabulary[:5]]
                scenarios_list.append({
                    "id": topic.topic_id,
                    "title": topic.topic_name,
                    "category": "Academic IELTS Bank",
                    "icon": "📖",
                    "color": "#1CB0F6",
                    "description": f"IELTS Topic with {len(topic.personas)} personas, {len(topic.questions)} questions, and {len(topic.vocabulary)} vocabulary items.",
                    "open_story_guide": f"Interactive IELTS Speaking discussion on {topic.topic_name}.",
                    "is_custom": False,
                    "source": "material_bank",
                    "target_levels": topic.target_levels,
                    "suggested_vocabulary": vocab_preview if vocab_preview else ["IELTS Speaking"]
                })
    except Exception as e:
        print(f"[scenarios.py] Error loading MaterialBank topics: {e}")

    # 3. Custom Scenarios from Turso DB
    custom_scenarios = get_custom_scenarios()
    for cs in custom_scenarios:
        scenarios_list.append(cs)

    return scenarios_list

def get_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    if scenario_id in DEFAULT_SCENARIOS:
        sc: Dict[str, Any] = dict(DEFAULT_SCENARIOS[scenario_id])
        sc["is_custom"] = False
        return sc

    # 2. Check Custom Scenarios from DB
    customs = get_custom_scenarios()
    for cs in customs:
        if cs["id"] == scenario_id:
            return cs

    # 3. Check Material Bank topics
    try:
        from app.material_bank import get_material_bank
        mb_topic = get_material_bank().get_topic(scenario_id)
        if mb_topic:
            vocab_preview = [v.phrase for v in mb_topic.vocabulary[:5]]
            return {
                "id": mb_topic.topic_id,
                "title": mb_topic.topic_name,
                "category": "Academic IELTS Bank",
                "icon": "📖",
                "color": "#1CB0F6",
                "description": f"IELTS Topic with {len(mb_topic.personas)} personas, {len(mb_topic.questions)} questions, and {len(mb_topic.vocabulary)} vocabulary items.",
                "open_story_guide": f"Interactive IELTS Speaking discussion on {mb_topic.topic_name}.",
                "is_custom": False,
                "source": "material_bank",
                "target_levels": mb_topic.target_levels,
                "suggested_vocabulary": vocab_preview if vocab_preview else ["IELTS Speaking"]
            }
    except Exception as e:
        print(f"[scenarios.py] Error looking up MaterialBank topic: {e}")

    return None
