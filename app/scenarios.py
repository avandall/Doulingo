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
    # 1. FAMILY & FRIENDS (GIA ĐÌNH & BẠN BÈ)
    # ============================================================
    "family_dinner": {
        "id": "family_dinner",
        "title": "Family Dinner Conversation",
        "category": "Family & Friends",
        "icon": "🍽️",
        "color": "#FF9933",
        "description": "Gather around the dinner table, share daily news, and talk about family traditions.",
        "open_story_guide": "A warm family dinner chat. Discuss daily highlights, family recipes, weekend plans, and supportive family advice."
    },
    "friend_catchup": {
        "id": "friend_catchup",
        "title": "Catching Up with an Old Friend",
        "category": "Family & Friends",
        "icon": "☕",
        "color": "#E91E63",
        "description": "Meet an old friend at a cozy coffee shop after years apart and share life updates.",
        "open_story_guide": "A friendly reunion at a cafe. Share recent life changes, reminisce about old memories, and plan future hangouts."
    },
    "roommate_chat": {
        "id": "roommate_chat",
        "title": "Living with Roommates",
        "category": "Family & Friends",
        "icon": "🏠",
        "color": "#795548",
        "description": "Discuss household chores, decorating the living room, and organizing movie nights.",
        "open_story_guide": "A cooperative roommate conversation. Negotiate chore schedules, apartment rules, and shared cooking."
    },

    # ============================================================
    # 2. HOBBIES & LIFESTYLE (SỞ THÍCH CÁ NHÂN & LỐI SỐNG)
    # ============================================================
    "weekend_fitness": {
        "id": "weekend_fitness",
        "title": "Weekend Sports & Fitness",
        "category": "Hobbies & Lifestyle",
        "icon": "🏃",
        "color": "#4CAF50",
        "description": "Talk about morning runs, yoga routines, gym goals, and staying healthy.",
        "open_story_guide": "An active chat about fitness and hobbies. Share workout tips, favorite outdoor sports, and healthy habits."
    },
    "book_club_chat": {
        "id": "book_club_chat",
        "title": "Book & Movie Club",
        "category": "Hobbies & Lifestyle",
        "icon": "📚",
        "color": "#9C27B0",
        "description": "Share thoughts on a recent bestseller book or inspiring movie plot and characters.",
        "open_story_guide": "A thoughtful discussion about books and cinema. Exchange recommendations and favorite character quotes."
    },
    "cooking_recipe": {
        "id": "cooking_recipe",
        "title": "Cooking & Comfort Food",
        "category": "Hobbies & Lifestyle",
        "icon": "🍳",
        "color": "#FF4B4B",
        "description": "Exchange delicious home cooking recipes, ingredient tips, and favorite dishes.",
        "open_story_guide": "A fun culinary exchange. Discuss comfort food recipes, healthy cooking shortcuts, and favorite cuisines."
    },

    # ============================================================
    # 3. STUDY & CAREER (HỌC TẬP & CÔNG VIỆC)
    # ============================================================
    "job_interview_prep": {
        "id": "job_interview_prep",
        "title": "Job Interview Practice",
        "category": "Study & Career",
        "icon": "💼",
        "color": "#1CB0F6",
        "description": "Practice presenting professional skills, career goals, and answering interview questions.",
        "open_story_guide": "A professional job interview simulation. Ask about work experience, strengths, teamwork, and career ambitions."
    },
    "study_group": {
        "id": "study_group",
        "title": "University Study Group",
        "category": "Study & Career",
        "icon": "🎓",
        "color": "#673AB7",
        "description": "Prepare for exams together, share study methods, and discuss academic subjects.",
        "open_story_guide": "An encouraging study session. Share effective note-taking tips, exam preparation strategies, and academic goals."
    },
    "workplace_colleague": {
        "id": "workplace_colleague",
        "title": "Workplace Team Project",
        "category": "Study & Career",
        "icon": "🖥️",
        "color": "#3F51B5",
        "description": "Collaborate with a colleague on a project deadline and brainstorm creative solutions.",
        "open_story_guide": "A cooperative workplace discussion. Coordinate project tasks, offer supportive feedback, and solve work challenges."
    },

    # ============================================================
    # 4. CHILDHOOD & HOMETOWN (KÝ ỨC TUỔI THƠ & QUÊ HƯƠNG)
    # ============================================================
    "hometown_memories": {
        "id": "hometown_memories",
        "title": "Hometown Memories",
        "category": "Childhood & Hometown",
        "icon": "🏡",
        "color": "#8D6E63",
        "description": "Describe what growing up in your hometown was like, favorite places, and neighbors.",
        "open_story_guide": "A nostalgic conversation about growing up. Share stories about hometown streets, local food, and childhood friends."
    },
    "memorable_teacher": {
        "id": "memorable_teacher",
        "title": "An Inspiring Teacher",
        "category": "Childhood & Hometown",
        "icon": "👨‍🏫",
        "color": "#FFB300",
        "description": "Talk about an influential teacher or mentor who encouraged you and taught life lessons.",
        "open_story_guide": "An appreciative discussion about mentors. Share how a teacher made learning enjoyable and inspired confidence."
    },

    # ============================================================
    # 5. TRAVEL & PLACES (DU LỊCH & ĐỊA ĐIỂM)
    # ============================================================
    "travel_planning": {
        "id": "travel_planning",
        "title": "Planning a Dream Trip",
        "category": "Travel & Places",
        "icon": "✈️",
        "color": "#00843D",
        "description": "Plan a relaxing vacation itinerary, compare destinations, and discuss travel tips.",
        "open_story_guide": "An exciting travel planning dialogue. Compare scenic destinations, packing essentials, and cultural sightseeing."
    },
    "hotel_checkin": {
        "id": "hotel_checkin",
        "title": "Hotel Check-In & Local Tips",
        "category": "Travel & Places",
        "icon": "🏨",
        "color": "#00BCD4",
        "description": "Check into a hotel, ask about room amenities, and get recommendations for city landmarks.",
        "open_story_guide": "A helpful hotel reception roleplay. Provide room assistance, breakfast times, and local sightseeing advice."
    },

    # ============================================================
    # 6. TECH IN DAILY LIFE (CÔNG NGHỆ TRONG ĐỜI SỐNG)
    # ============================================================
    "tech_daily_life": {
        "id": "tech_daily_life",
        "title": "Smartphones & Productivity",
        "category": "Tech & Daily Life",
        "icon": "📱",
        "color": "#E91E63",
        "description": "Discuss how mobile apps help manage time, stay connected, and learn new skills.",
        "open_story_guide": "A practical chat about everyday technology. Share useful apps, digital balance, and smartphone convenience."
    },
    "ai_learning_tools": {
        "id": "ai_learning_tools",
        "title": "AI & Language Learning",
        "category": "Tech & Daily Life",
        "icon": "🤖",
        "color": "#FF2A85",
        "description": "Talk about using artificial intelligence for studying languages, translation, and creativity.",
        "open_story_guide": "A modern discussion on AI in education. Discuss how AI tutors provide instant feedback and make learning interactive."
    },

    # ============================================================
    # 7. BASIC SOCIAL ISSUES (CÁC VẤN ĐỀ XÃ HỘI CƠ BẢN)
    # ============================================================
    "green_living_eco": {
        "id": "green_living_eco",
        "title": "Eco-Friendly Living",
        "category": "Society & Community",
        "icon": "🌱",
        "color": "#4CAF50",
        "description": "Share everyday tips for reducing plastic waste, recycling, and protecting the environment.",
        "open_story_guide": "An environmentally conscious dialogue. Discuss simple habits to save energy, recycle, and keep neighborhoods clean."
    },
    "community_volunteer": {
        "id": "community_volunteer",
        "title": "Community & Volunteering",
        "category": "Society & Community",
        "icon": "🤝",
        "color": "#3F51B5",
        "description": "Talk about helping neighbors, volunteering at charities, and community kindness.",
        "open_story_guide": "An uplifting conversation on community support. Discuss charity work, neighborhood events, and helping others."
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
