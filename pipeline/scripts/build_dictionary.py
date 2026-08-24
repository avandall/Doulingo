"""
Dictionary Builder Script for Doulingo Speak
Generates high-quality offline SQLite dictionary data/dictionary.db
covering Oxford 3000/5000, Longman 3000, IELTS, TOEIC, and Daily Life English.
"""

import os
import re
import sqlite3
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "dictionary.db")
RAW_AV_PATH = os.path.join(DATA_DIR, "anhviet109K.txt")

SOURCE_OXFORD_3000 = "/home/avandall/.gemini/antigravity-ide/brain/f0a71e13-8e11-4a72-9a1e-f2e4e924e53b/.system_generated/steps/194/content.md"
SOURCE_OXFORD_5000 = "/home/avandall/.gemini/antigravity-ide/brain/f0a71e13-8e11-4a72-9a1e-f2e4e924e53b/.system_generated/steps/198/content.md"
SOURCE_LONGMAN_3000 = "/home/avandall/.gemini/antigravity-ide/brain/f0a71e13-8e11-4a72-9a1e-f2e4e924e53b/.system_generated/steps/208/content.md"
SOURCE_IPA_UK = "/home/avandall/.gemini/antigravity-ide/brain/f0a71e13-8e11-4a72-9a1e-f2e4e924e53b/.system_generated/steps/216/content.md"
SOURCE_IPA_US = "/home/avandall/.gemini/antigravity-ide/brain/f0a71e13-8e11-4a72-9a1e-f2e4e924e53b/.system_generated/steps/218/content.md"

POS_MAP = {
    'danh từ': 'noun',
    'động từ': 'verb',
    'tính từ': 'adjective',
    'phó từ': 'adverb',
    'trạng từ': 'adverb',
    'giới từ': 'preposition',
    'liên từ': 'conjunction',
    'thán từ': 'interjection',
    'mạo từ': 'article',
    'đại từ': 'pronoun',
    'nội động từ': 'verb (intransitive)',
    'ngoại động từ': 'verb (transitive)',
    'cụm từ': 'phrase',
    'thành ngữ': 'idiom',
    'tiền tố': 'prefix',
    'hậu tố': 'suffix',
}

def load_word_list(filepath):
    words = []
    if not os.path.exists(filepath):
        return words
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line.startswith(('Title:', 'Description:', 'Source:')) or line == '---' or not line:
                continue
            w = line.strip().lower()
            w = re.sub(r'[^a-zA-Z0-9\-\s\']', '', w).strip()
            if w and len(w) >= 1:
                words.append(w)
    return list(dict.fromkeys(words))

def load_ipa_dict(filepath):
    ipa_map = {}
    if not os.path.exists(filepath):
        return ipa_map
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or '\t' not in line:
                continue
            parts = line.split('\t', 1)
            word = parts[0].strip().lower()
            ipa = parts[1].strip()
            if word and ipa and word not in ipa_map:
                ipa_map[word] = ipa
    return ipa_map

def clean_vietnamese_text(text):
    if not text:
        return ""
    text = text.replace("_", " ")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_full_anhviet_dictionary(filepath):
    print(f"Parsing full Anh-Viet dictionary file ({filepath})...", flush=True)
    t0 = time.time()
    dict_data = {}
    
    current_word = None
    current_phonetic = ""
    current_pos_list = []
    current_meanings = []
    current_examples = []
    
    def save_current():
        nonlocal current_word, current_phonetic, current_pos_list, current_meanings, current_examples
        if not current_word:
            return
        
        clean_w = current_word.strip().lower()
        if not clean_w:
            return
        
        meanings_clean = []
        for m in current_meanings:
            m = clean_vietnamese_text(m)
            m = re.sub(r'^\([^\)]+\)\s*', '', m).strip()
            if m and m not in meanings_clean:
                meanings_clean.append(m)
                
        clean_ex = []
        for ex_en, ex_vi in current_examples:
            ex_en = clean_vietnamese_text(ex_en)
            ex_vi = clean_vietnamese_text(ex_vi)
            if ex_en:
                clean_ex.append((ex_en, ex_vi))
                
        pos_standard = []
        for p in current_pos_list:
            p_clean = p.lower().strip()
            mapped = POS_MAP.get(p_clean, p_clean)
            if mapped not in pos_standard:
                pos_standard.append(mapped)
                
        if clean_w not in dict_data:
            dict_data[clean_w] = {
                'word': clean_w,
                'phonetic': current_phonetic,
                'pos': pos_standard,
                'meanings': meanings_clean,
                'examples': clean_ex
            }
        else:
            existing = dict_data[clean_w]
            if not existing['phonetic'] and current_phonetic:
                existing['phonetic'] = current_phonetic
            for p in pos_standard:
                if p not in existing['pos']:
                    existing['pos'].append(p)
            for m in meanings_clean:
                if m not in existing['meanings']:
                    existing['meanings'].append(m)
            for ex in clean_ex:
                if ex not in existing['examples']:
                    existing['examples'].append(ex)

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.rstrip('\r\n')
            if not line:
                continue
            if line.startswith(('Title:', 'Description:', 'Source:')) or line == '---':
                continue
                
            if line.startswith('@'):
                save_current()
                entry_line = line[1:].strip()
                m_phone = re.search(r'/(.*?)/', entry_line)
                if m_phone:
                    current_phonetic = f"/{m_phone.group(1).strip()}/"
                    w_raw = entry_line[:m_phone.start()].strip()
                else:
                    current_phonetic = ""
                    w_raw = entry_line.strip()
                    
                current_word = w_raw
                current_pos_list = []
                current_meanings = []
                current_examples = []
                
            elif line.startswith('*'):
                pos_str = line[1:].strip()
                pos_main = pos_str.split(',')[0].strip()
                if pos_main:
                    current_pos_list.append(pos_main)
                    
            elif line.startswith('-'):
                m_str = line[1:].strip()
                if m_str:
                    current_meanings.append(m_str)
                    
            elif line.startswith('='):
                ex_str = line[1:].strip()
                if '+' in ex_str:
                    parts = ex_str.split('+', 1)
                    current_examples.append((parts[0].strip(), parts[1].strip()))
                else:
                    current_examples.append((ex_str, ''))
                    
    save_current()
    print(f"Parsed {len(dict_data)} total entries from Anh-Viet in {time.time()-t0:.2f}s", flush=True)
    return dict_data

def build_curated_database():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    ox3k = load_word_list(SOURCE_OXFORD_3000)
    ox5k = load_word_list(SOURCE_OXFORD_5000)
    lm3k = load_word_list(SOURCE_LONGMAN_3000)
    
    ipa_uk = load_ipa_dict(SOURCE_IPA_UK)
    ipa_us = load_ipa_dict(SOURCE_IPA_US)
    
    av_dict = parse_full_anhviet_dictionary(RAW_AV_PATH)
    
    ielts_academic_topics = [
        "academic", "accommodate", "accumulate", "acknowledge", "acquire", "adapt", "adequate", "adjacent",
        "advocate", "aggregate", "allocate", "ambiguous", "amend", "analogy", "anticipate", "appendix",
        "appreciate", "arbitrary", "automate", "bias", "bulk", "capable", "category", "cease", "channel",
        "clause", "coherent", "coincide", "collapse", "commence", "compatible", "compensate", "compile",
        "complement", "comprehensive", "comprise", "compute", "conceive", "conclude", "concurrent", "conduct",
        "conform", "consent", "consequent", "consist", "constant", "constitute", "constrain", "construct",
        "consume", "contemporary", "context", "contract", "contradict", "contrary", "contrast", "contribute",
        "controversy", "convene", "converse", "convert", "convince", "corporate", "correspond", "criteria",
        "crucial", "currency", "decade", "decline", "deduce", "demonstrate", "denote", "deny", "depress",
        "derive", "design", "deviate", "differentiate", "dimension", "diminish", "discrete", "discriminate",
        "displace", "display", "dispose", "distinct", "distort", "distribute", "diverse", "document",
        "domain", "domestic", "dominate", "draft", "drama", "duration", "dynamic", "eliminate", "emerge",
        "emphasis", "empirical", "enable", "encounter", "enhance", "enormous", "ensure", "entity",
        "environment", "equate", "equip", "equivalent", "erode", "error", "establish", "estate",
        "estimate", "ethic", "ethnic", "evaluate", "eventual", "evident", "evolve", "exceed", "exclude",
        "exhibit", "expand", "expert", "explicit", "exploit", "export", "expose", "external", "extract",
        "facilitate", "factor", "feature", "federal", "fee", "file", "final", "finance", "finite",
        "flexible", "fluctuate", "focus", "format", "formula", "forthcoming", "foundation", "framework",
        "function", "fund", "fundamental", "furthermore", "gender", "generate", "generation", "globe",
        "goal", "grade", "grant", "guarantee", "guideline", "hence", "hierarchy", "highlight", "hypothesis",
        "identical", "identify", "ideology", "ignorance", "illustrate", "image", "immigrate", "impact",
        "implement", "implicate", "implicit", "imply", "impose", "incentive", "incidence", "incline",
        "income", "incorporate", "index", "indicate", "individual", "induce", "inevitable", "infer",
        "infrastructure", "inherent", "inhibit", "initial", "initiative", "injure", "innovate", "input",
        "insert", "insight", "inspect", "instance", "institute", "instruct", "integral", "integrate",
        "integrity", "intelligence", "intense", "interact", "intermediate", "internal", "interpret",
        "interval", "intervene", "intrinsic", "invest", "investigate", "invoke", "involve", "isolate",
        "issue", "item", "job", "journal", "justify", "label", "labor", "layer", "lecture", "legal",
        "legislate", "levy", "liberal", "license", "likewise", "link", "locate", "logic", "maintain",
        "major", "manipulate", "manual", "margin", "mature", "maximize", "mechanism", "media", "mediate",
        "medical", "medium", "mental", "method", "migrate", "military", "minimize", "minimum", "ministry",
        "minor", "mode", "modify", "monitor", "motive", "mutual", "negate", "network", "neutral",
        "nevertheless", "nonetheless", "norm", "notion", "notwithstanding", "nuclear", "objective", "obtain",
        "obvious", "occupy", "occur", "odd", "offset", "ongoing", "option", "orient", "outcome", "output",
        "overall", "overlap", "overseas", "panel", "paradigm", "paragraph", "parallel", "parameter",
        "participate", "partner", "passive", "perceive", "percent", "period", "persist", "perspective",
        "phase", "phenomenon", "philosophy", "physical", "plus", "policy", "portion", "pose", "positive",
        "potential", "practitioner", "precede", "precise", "predict", "predominant", "preliminary", "presume",
        "previous", "primary", "prime", "principal", "principle", "prior", "priority", "proceed", "process",
        "professional", "prohibit", "project", "promote", "proportion", "prospect", "protocol", "psychology",
        "publication", "publish", "purchase", "pursue", "qualitative", "quote", "radical", "random",
        "range", "ratio", "rational", "react", "recover", "refine", "regime", "region", "register",
        "regulate", "reinforce", "reject", "relax", "release", "relevant", "reluctance", "rely", "remove",
        "require", "research", "reside", "resolve", "resource", "respond", "restore", "restrain", "restrict",
        "retain", "reveal", "revenue", "reverse", "revise", "revolution", "rigid", "role", "route",
        "scenario", "schedule", "scheme", "scope", "section", "sector", "secure", "seek", "select",
        "sequence", "series", "sex", "shift", "significant", "similar", "simulate", "site", "so-called",
        "sole", "somewhat", "source", "specific", "specify", "sphere", "stable", "statistic", "status",
        "straightforward", "strategy", "stress", "structure", "style", "submit", "subordinate", "subsequent",
        "subsidy", "substitute", "successor", "sufficient", "sum", "summary", "supplement", "survey",
        "survive", "suspend", "sustain", "sustainable", "symbol", "tape", "target", "task", "team", "technical",
        "technique", "technology", "temporary", "tense", "terminate", "text", "theme", "theory", "thereby",
        "thesis", "topic", "trace", "tradition", "transfer", "transform", "transit", "transmit", "transport",
        "trend", "trigger", "ultimate", "undergo", "underlie", "undertake", "uniform", "unify", "unique",
        "utilize", "valid", "vary", "vehicle", "version", "via", "violate", "virtual", "visible", "vision",
        "visual", "volume", "voluntary", "welfare", "whereas", "whereby", "widespread",
        "ubiquitous", "ameliorate", "paradigm", "profound", "meticulous", "ephemeral", "pragmatic",
        "resilience", "mitigate", "deteriorate", "exacerbate", "plausible", "indispensable", "unprecedented"
    ]
    
    toeic_business_topics = [
        "agenda", "announcement", "applicant", "application", "appraisal", "audit", "authorization",
        "bankrupt", "bargain", "beneficiary", "boardroom", "brand", "briefcase", "brochure", "budget",
        "candidate", "capacity", "career", "catering", "certificate", "client", "collaboration",
        "colleague", "commercial", "commitment", "commute", "compensation", "competitor", "compliance",
        "compromise", "conference", "confidential", "confirmation", "conglomerate", "consensus", "consignment",
        "consultant", "consumer", "contractor", "convention", "conveyance", "correspondence", "courier",
        "credentials", "criterion", "curriculum", "deadline", "dealership", "debt", "dedication", "deficit",
        "delegate", "delegation", "delivery", "demographics", "department", "deposit", "depreciation",
        "designate", "destination", "directory", "disability", "disbursement", "discharge", "disclaimer",
        "discount", "dispatch", "distribution", "dividend", "downsize", "earnings", "efficiency", "embargo",
        "endorsement", "enterprise", "entrepreneur", "equipment", "escalate", "estimate", "etiquette",
        "evaluation", "executive", "expenditure", "expense", "expertise", "expiration", "feasibility",
        "feedback", "finance", "firm", "fiscal", "fluctuation", "forecast", "formality", "franchise",
        "freight", "grievance", "headquarters", "hospitality", "incentive", "indemnity", "inflation",
        "infringement", "initiative", "innovation", "installment", "insurance", "inventory", "investment",
        "invoice", "itinerary", "joint venture", "jurisdiction", "lease", "ledger", "liability", "liaison",
        "logistics", "maintenance", "management", "manpower", "manufacturing", "marketing", "merchandise",
        "merger", "milestone", "monopoly", "mortgage", "negotiate", "negotiation", "networking", "notice",
        "occupancy", "operation", "organization", "orientation", "outsource", "overhaul", "overseas",
        "overtime", "overview", "package", "partnership", "patent", "payroll", "penalty", "pension",
        "performance", "perk", "personnel", "petition", "portfolio", "postage", "prerequisite", "presentation",
        "prestige", "procedure", "procurement", "productivity", "profitability", "promotion", "proposal",
        "proprietor", "prospective", "protocol", "provision", "punctuality", "qualification", "quota",
        "quotation", "rationale", "real estate", "rebate", "receipt", "reception", "recession", "recipient",
        "recommendation", "reconciliation", "recruitment", "redundancy", "referee", "refund", "reimbursement",
        "relocation", "remittance", "renovation", "reorganization", "representative", "requisition", "resignation",
        "resolution", "restructure", "resume", "retail", "retention", "retirement", "revenue", "sanction",
        "satisfaction", "scrutiny", "security", "seminar", "seniority", "settlement", "shareholder", "shipment",
        "shortage", "solicitation", "specification", "spokesperson", "sponsorship", "stakeholder",
        "standardization", "stationery", "statutory", "stipulation", "stockholder", "subcontractor", "subsidiary",
        "supervision", "supervisor", "surplus", "tariff", "taxation", "telecommuting", "tenant", "tenure",
        "termination", "testimonial", "threshold", "timetable", "toll-free", "trademark", "transaction",
        "transcript", "transferable", "treasury", "turnover", "underwrite", "unemployment", "union", "upgrade",
        "urgency", "vacancy", "valuation", "vandalism", "vendor", "venture", "venue", "verification",
        "viability", "voucher", "warehouse", "warranty", "wholesale", "withdrawal", "workforce", "workload",
        "workplace", "workshop", "yield"
    ]
    
    ordered_words = []
    seen = set()
    
    def add_word(w):
        w = w.strip().lower()
        if w and w not in seen and len(w) >= 1:
            seen.add(w)
            ordered_words.append(w)
            
    for w in ox3k:
        add_word(w)
    for w in ox5k:
        add_word(w)
    for w in lm3k:
        add_word(w)
    for w in ielts_academic_topics:
        add_word(w)
    for w in toeic_business_topics:
        add_word(w)
        
    av_sorted_candidates = []
    for w, data in av_dict.items():
        if w in seen:
            continue
        if not re.match(r'^[a-z]+(-[a-z]+)?$', w):
            continue
        if len(w) < 2 or len(w) > 22:
            continue
        richness = len(data['meanings']) * 3 + len(data['examples']) * 4 + (2 if data['phonetic'] else 0)
        av_sorted_candidates.append((richness, w))
        
    av_sorted_candidates.sort(key=lambda x: x[0], reverse=True)
    
    for _, w in av_sorted_candidates:
        add_word(w)
        if len(ordered_words) >= 8600:
            break
            
    final_records = []
    for w in ordered_words:
        av_entry = av_dict.get(w, {})
        phonetic = ipa_uk.get(w) or ipa_us.get(w) or av_entry.get('phonetic', '')
        if not phonetic:
            phonetic = f"/{w}/"
        elif not phonetic.startswith('/'):
            phonetic = f"/{phonetic}/"
            
        pos_list = av_entry.get('pos', [])
        pos_str = ", ".join(pos_list) if pos_list else "noun/verb"
        
        meanings = av_entry.get('meanings', [])
        if meanings:
            top_meanings = meanings[:3]
            translation_str = "; ".join(top_meanings)
        else:
            translation_str = w.capitalize()
            
        examples = av_entry.get('examples', [])
        def_parts = []
        if examples:
            ex_snippets = []
            for ex_en, ex_vi in examples[:2]:
                if ex_vi:
                    ex_snippets.append(f"{ex_en} ({ex_vi})")
                else:
                    ex_snippets.append(ex_en)
            def_parts.append("; ".join(ex_snippets))
            
        if not def_parts and len(meanings) > 3:
            def_parts.append("Nghĩa mở rộng: " + "; ".join(meanings[3:6]))
            
        definition_str = " | ".join(def_parts) if def_parts else f"Common English term: {w}"
        
        final_records.append((
            w,
            phonetic,
            pos_str,
            translation_str,
            definition_str
        ))
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dictionary (
            word TEXT PRIMARY KEY,
            phonetic TEXT,
            pos TEXT,
            translation TEXT NOT NULL,
            definition TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dict_word ON dictionary(word)")
    cursor.executemany("""
        INSERT OR REPLACE INTO dictionary (word, phonetic, pos, translation, definition)
        VALUES (?, ?, ?, ?, ?)
    """, final_records)
    conn.commit()
    
    cursor.execute("SELECT count(*) FROM dictionary")
    total_count = cursor.fetchone()[0]
    conn.close()
    return total_count

if __name__ == "__main__":
    count = build_curated_database()
    print(f"Dictionary generation complete. Total entries: {count}")
