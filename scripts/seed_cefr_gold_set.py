import json
from pathlib import Path

gold_set = {
    'version': '1.0',
    'description': 'CEFR Gold-Set Benchmark Transcripts for ASR Adaptive Level Detection & IRT Calibration',
    'dataset_info': {
        'total_samples': 17,
        'levels_covered': ['A1', 'A2', 'A2+', 'B1', 'B2', 'C1', 'C2'],
        'intended_use': 'Evaluation and continuous calibration of ASR Feature Extractor and IRT Rasch Model'
    },
    'transcripts': [
        {
            'id': 'gold_a1_01',
            'expected_cefr': 'A1',
            'target_level': 2,
            'expected_band': 4.0,
            'transcript': 'Hello, my name is Nam. I am twenty years old. I like coffee and football.',
            'estimated_wpm': 85.0,
            'notes': 'Present simple, basic personal intro, isolated words and short sentences.'
        },
        {
            'id': 'gold_a1_02',
            'expected_cefr': 'A1',
            'target_level': 2,
            'expected_band': 4.0,
            'transcript': 'I have a dog. It is small and white. We play in the park every morning.',
            'estimated_wpm': 90.0,
            'notes': 'Very simple syntax, high frequency elementary vocabulary.'
        },
        {
            'id': 'gold_a1_03',
            'expected_cefr': 'A1',
            'target_level': 3,
            'expected_band': 4.5,
            'transcript': 'This morning I go to school by bus. The bus is crowded but fast.',
            'estimated_wpm': 88.0,
            'notes': 'Simple daily routine description, basic conjunction.'
        },
        {
            'id': 'gold_a2_01',
            'expected_cefr': 'A2',
            'target_level': 4,
            'expected_band': 5.0,
            'transcript': 'Last weekend, I went shopping with my sister. We bought new shoes and had lunch at a noodle restaurant.',
            'estimated_wpm': 105.0,
            'notes': 'Past simple narrative, compound sentences with and.'
        },
        {
            'id': 'gold_a2_02',
            'expected_cefr': 'A2',
            'target_level': 5,
            'expected_band': 5.0,
            'transcript': 'I usually wake up early because my office is far away. If the traffic is bad, it takes one hour.',
            'estimated_wpm': 110.0,
            'notes': 'Adverb of frequency, causal connective because, first conditional.'
        },
        {
            'id': 'gold_a2_03',
            'expected_cefr': 'A2',
            'target_level': 6,
            'expected_band': 5.5,
            'transcript': 'My favorite hobby is photography. I enjoy taking photos of nature and posting them online for friends to see.',
            'estimated_wpm': 112.0,
            'notes': 'Gerunds after enjoy, basic prepositions and multi-clause structure.'
        },
        {
            'id': 'gold_a2_plus_01',
            'expected_cefr': 'A2+',
            'target_level': 7,
            'expected_band': 5.5,
            'transcript': 'I have been studying English for two years. Although it is difficult at times, I feel more confident now.',
            'estimated_wpm': 118.0,
            'notes': 'Present perfect continuous, concessive connective although, comparative adjective.'
        },
        {
            'id': 'gold_b1_01',
            'expected_cefr': 'B1',
            'target_level': 8,
            'expected_band': 6.0,
            'transcript': 'In my opinion, living in a big city provides numerous career opportunities, though the high living expenses can be challenging.',
            'estimated_wpm': 125.0,
            'notes': 'Opinion phrase, intermediate vocabulary, subordinate clauses.'
        },
        {
            'id': 'gold_b1_02',
            'expected_cefr': 'B1',
            'target_level': 9,
            'expected_band': 6.0,
            'transcript': 'When I encounter unfamiliar vocabulary while reading, I prefer deducing the meaning from context rather than checking a dictionary immediately.',
            'estimated_wpm': 128.0,
            'notes': 'Complex sentence structure, preference construction, deducing from context.'
        },
        {
            'id': 'gold_b1_03',
            'expected_cefr': 'B1',
            'target_level': 10,
            'expected_band': 6.5,
            'transcript': 'The documentary explained how renewable energy initiatives could significantly reduce greenhouse emissions over the next decade.',
            'estimated_wpm': 130.0,
            'notes': 'Reported speech, modal verbs could, domain-specific environmental vocabulary.'
        },
        {
            'id': 'gold_b2_01',
            'expected_cefr': 'B2',
            'target_level': 12,
            'expected_band': 7.0,
            'transcript': 'While remote collaboration fosters workplace flexibility, it often demands heightened self-discipline and sophisticated communication protocols.',
            'estimated_wpm': 135.0,
            'notes': 'Contrastive adverbial clause, advanced academic vocabulary.'
        },
        {
            'id': 'gold_b2_02',
            'expected_cefr': 'B2',
            'target_level': 13,
            'expected_band': 7.0,
            'transcript': 'Had the government implemented stringent macroeconomic measures earlier, the volatility in financial markets might have been mitigated.',
            'estimated_wpm': 138.0,
            'notes': 'Inversion in third conditional, sophisticated discourse register.'
        },
        {
            'id': 'gold_b2_03',
            'expected_cefr': 'B2',
            'target_level': 14,
            'expected_band': 7.5,
            'transcript': 'The empirical findings corroborate the hypothesis that regular immersion dramatically enhances phonological sensitivity and speech fluency.',
            'estimated_wpm': 140.0,
            'notes': 'Academic noun collocations, high lexical sophistication.'
        },
        {
            'id': 'gold_c1_01',
            'expected_cefr': 'C1',
            'target_level': 16,
            'expected_band': 8.0,
            'transcript': 'Navigating the intricate interplay between technological proliferation and ethical accountability requires unprecedented interdisciplinary consensus.',
            'estimated_wpm': 145.0,
            'notes': 'High-density nominalization, sophisticated abstract concepts, flawless structural complexity.'
        },
        {
            'id': 'gold_c1_02',
            'expected_cefr': 'C1',
            'target_level': 17,
            'expected_band': 8.5,
            'transcript': 'Notwithstanding the prevailing skepticism surrounding algorithmic decision-making, its judicious application yields demonstrable pedagogical dividends.',
            'estimated_wpm': 148.0,
            'notes': 'Archaic formal prepositions, nuanced philosophical stance, high lexical diversity.'
        },
        {
            'id': 'gold_c2_01',
            'expected_cefr': 'C2',
            'target_level': 19,
            'expected_band': 9.0,
            'transcript': 'The ephemeral discourse underpinning contemporary linguistics invariably oscillates between prescriptivist orthodoxy and descriptivist pluralism.',
            'estimated_wpm': 150.0,
            'notes': 'Near-native master-level rhetoric, dense domain terminology, effortless philosophical synthesis.'
        },
        {
            'id': 'gold_c2_02',
            'expected_cefr': 'C2',
            'target_level': 20,
            'expected_band': 9.0,
            'transcript': 'To dismantle such entrenched epistemic paradigms requires not merely incremental reform, but a profound epistemological reorientation.',
            'estimated_wpm': 152.0,
            'notes': 'C2 master rhetoric, correlative conjunctions with complex abstracts, scholarly nuance.'
        }
    ]
}

out_path = Path('/home/avandall/project/Doulingo/app/data/cefr_gold_set.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(gold_set, f, indent=2, ensure_ascii=False)

print('SUCCESS: Created cefr_gold_set.json')
