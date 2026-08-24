#!/usr/bin/env python3
"""
Seed Demo Data Script for Duolingo Speak (Capstone M4 Deliverable)
Ensures a clean-machine clone can be run immediately with pre-populated demo data.
"""

import logging
import os
import sys

# Ensure project root is in python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.storage.db import (
    add_custom_scenario,
    add_user_xp,
    get_db_connection,
    init_db,
    save_translated_word,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_demo_data")


def main():
    logger.info("Initializing database schema...")
    init_db()

    logger.info("Seeding demo custom IELTS Speaking scenarios...")
    demo_scenarios = [
        {
            "id": "det_seed_ielts_job_interview",
            "title": "IELTS Speaking Part 3: Technology in Careers",
            "category": "IELTS Exam Practice",
            "icon": "🎓",
            "color": "#FFC800",
            "level": "Advanced",
            "level_code": "C1",
            "default_character": "vikram",
            "description": "Discuss the impact of artificial intelligence and automation on modern career paths.",
            "objective": "Use advanced academic vocabulary and complex conditional structures.",
            "suggested_vocabulary": ["automation", "unprecedented", "adaptability", "paradigm shift"],
        },
        {
            "id": "seed_cafe_smalltalk",
            "title": "Coffee Shop Conversation in London",
            "category": "Daily Conversation",
            "icon": "☕",
            "color": "#1CB0F6",
            "level": "Intermediate",
            "level_code": "B1",
            "default_character": "chanel",
            "description": "Order coffee and engage in polite small talk with a local barista.",
            "objective": "Practice polite requests, natural fillers, and casual intonation.",
            "suggested_vocabulary": ["cappuccino", "recommendation", "cozy", "frequent"],
        },
    ]

    for sc in demo_scenarios:
        add_custom_scenario(sc)

    logger.info("Seeding dictionary cache & saved vocabulary...")
    demo_words = [
        ("perseverance", "vi", "Tiếng Việt", "Sự kiên trì, bền bỉ", "/ˌpɜː.sɪˈvɪə.rəns/"),
        ("articulate", "vi", "Tiếng Việt", "Diễn đạt lưu loát, rõ ràng", "/ɑːˈtɪk.jə.lət/"),
        ("meticulous", "vi", "Tiếng Việt", "Tỉ mỉ, cẩn thận từng chi tiết", "/məˈtɪk.jə.ləs/"),
        ("ubiquitous", "vi", "Tiếng Việt", "Phổ biến, có mặt ở khắp mọi nơi", "/juːˈbɪk.wɪ.təs/"),
    ]

    for word, target_lang, label, translation, phonetic in demo_words:
        save_translated_word(word, target_lang, label, translation, phonetic)

    logger.info("Setting initial user gamification stats (XP & Streak)...")
    add_user_xp(50)  # Boost XP to ensure positive feedback loop on first run

    logger.info("Checking database integrity...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM custom_scenarios")
    sc_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM word_dictionary")
    word_count = cursor.fetchone()[0]
    conn.close()

    logger.info(f"✅ [SEED SUCCESS] Database ready! {sc_count} scenarios, {word_count} vocabulary entries seeded.")


if __name__ == "__main__":
    main()
