/**
 * Duolingo Speak Application Controller
 * Features:
 * - ElevenLabs & Edge-TTS Expressive Voice Actor Integration.
 * - Dynamic Partner Randomizer: Users freely choose character or get a RANDOM partner on every start.
 * - Cancel Speech Recording Button (Discard recording without sending).
 * - Saved Vocabulary Book Modal (Fetches /api/saved_words from SQLite DB).
 * - Instant 0ms Word Lookup (Frontend Map + Backend RAM Cache).
 * - Reliable Full AI Sentence Translation Toggle across all turns.
 * - Copyable Conversation Transcript Log (RAM Stored).
 * - Deterministic Consistent Scoring & Evaluation.
 * - Text Sanitized TTS (No Stuttering / No Mid-sentence Pauses).
 */

class DuolingoSpeakApp {
  constructor() {
    this.scenarios = [];
    this.characters = [];
    this.savedWords = [];
    this.selectedCharacter = null;
    this.isUserSelectedCharacter = false; // Flag if user manually tapped a character card
    this.currentScenario = null;
    this.conversationHistory = [];
    this.turnCount = 0;
    this.totalXP = 150;
    this.turnScores = [];
    this.currentLevel = 1;
    this.targetLang = localStorage.getItem('duo_target_lang') || 'vi';

    this.speechHandler = null;
    this.currentAudio = null;
    this.wordCache = new Map(); // Instant 0ms frontend word cache
    this.init();
  }

  async init() {
    DuoMascot.renderInto('brand-mascot', 'happy');
    DuoMascot.renderInto('practice-mascot', 'happy');
    DuoMascot.renderInto('victory-mascot', 'celebrate');

    this.speechHandler = new SpeechHandler(
      (transcript, isFinal) => this.handleSpeechResult(transcript, isFinal),
      (state, detail) => this.handleSpeechStateChange(state, detail)
    );

    this.bindEvents();
    this.updateLangDisplay();
    await this.loadCharacters();
    await this.loadScenarios();
    await this.updateVocabBadgeCount();
  }

  bindEvents() {
    // Level Slider
    const levelSlider = document.getElementById('level-slider-input');
    if (levelSlider) {
      levelSlider.addEventListener('input', (e) => {
        this.currentLevel = parseInt(e.target.value, 10);
        this.updateLevelDisplay();
      });
    }

    // Vocabulary Book Modal Events
    document.getElementById('btn-open-vocab-modal').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.openVocabBookModal();
    });

    document.getElementById('btn-close-vocab-modal').addEventListener('click', () => {
      document.getElementById('modal-vocab-book').classList.remove('active');
    });

    document.getElementById('btn-close-vocab-bottom').addEventListener('click', () => {
      document.getElementById('modal-vocab-book').classList.remove('active');
    });

    document.getElementById('input-search-vocab').addEventListener('input', (e) => {
      this.renderVocabWordsList(e.target.value.trim().toLowerCase());
    });

    // Language Setting Modal
    document.getElementById('btn-open-lang-modal').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      document.getElementById('modal-lang-setting').classList.add('active');
    });

    document.getElementById('btn-close-lang-modal').addEventListener('click', () => {
      document.getElementById('modal-lang-setting').classList.remove('active');
    });

    document.getElementById('btn-save-lang-setting').addEventListener('click', () => {
      const select = document.getElementById('select-target-lang');
      this.targetLang = select.value;
      localStorage.setItem('duo_target_lang', this.targetLang);
      this.wordCache.clear();
      this.updateLangDisplay();
      this.updateVocabBadgeCount();
      document.getElementById('modal-lang-setting').classList.remove('active');
    });

    // Word Lookup Modal Close
    document.getElementById('btn-close-word-modal').addEventListener('click', () => {
      document.getElementById('modal-word-lookup').classList.remove('active');
    });

    // Custom Topic Modal
    document.getElementById('btn-open-custom-modal').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      document.getElementById('modal-custom-topic').classList.add('active');
    });

    document.getElementById('btn-close-modal').addEventListener('click', () => {
      document.getElementById('modal-custom-topic').classList.remove('active');
    });

    document.getElementById('btn-save-custom-topic').addEventListener('click', () => {
      this.saveCustomTopic();
    });

    // 5x5 Emoji Grid Picker selection
    const emojiGrid = document.getElementById('emoji-picker-grid');
    if (emojiGrid) {
      emojiGrid.querySelectorAll('.emoji-grid-item').forEach(item => {
        item.addEventListener('click', () => {
          if (window.duoAudio) window.duoAudio.playClick();
          emojiGrid.querySelectorAll('.emoji-grid-item').forEach(el => el.classList.remove('active'));
          item.classList.add('active');
          const emojiVal = item.getAttribute('data-emoji') || '💬';
          const hiddenInput = document.getElementById('custom-topic-icon');
          if (hiddenInput) hiddenInput.value = emojiVal;
        });
      });
    }

    // Random Roleplay
    document.getElementById('btn-random-roleplay').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.startRandomRoleplay();
    });

    // QUIT PRACTICE: Immediately stop Audio & Microphone!
    document.getElementById('btn-close-practice').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.stopTTS();
      if (this.speechHandler) this.speechHandler.cancel();
      this.showScreen('scenario-screen');
    });

    // Mic Toggle & CANCEL Button
    document.getElementById('btn-mic-toggle').addEventListener('click', () => {
      this.speechHandler.toggleListening();
    });

    const cancelBtn = document.getElementById('btn-cancel-mic');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        if (window.duoAudio) window.duoAudio.playClick();
        if (this.speechHandler) this.speechHandler.cancel();
      });
    }

    document.getElementById('btn-submit-text').addEventListener('click', () => {
      const input = document.getElementById('input-manual-text');
      const val = input.value.trim();
      if (val) {
        this.submitSpokenTurn(val);
        input.value = '';
      }
    });

    document.getElementById('input-manual-text').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        document.getElementById('btn-submit-text').click();
      }
    });

    // TTS Play Button
    document.getElementById('btn-tts-play').addEventListener('click', () => {
      if (this.currentAIText) {
        this.playTTS(this.currentAIText, this.selectedCharacter ? this.selectedCharacter.id : 'lily');
      }
    });

    // Translation Toggle Button (Full AI Sentence Translation)
    document.getElementById('btn-toggle-translate').addEventListener('click', () => {
      const transEl = document.getElementById('ai-translation-text');
      if (!transEl) return;

      if (!transEl.textContent.trim() && this.currentAITextVi) {
        transEl.textContent = this.currentAITextVi;
      }

      const isHidden = transEl.style.display === 'none' || getComputedStyle(transEl).display === 'none';
      transEl.style.display = isHidden ? 'block' : 'none';
    });

    // Finish & Score
    document.getElementById('btn-finish-roleplay').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.stopTTS();
      this.finishAndScoreRoleplay();
    });

    document.getElementById('btn-continue-feedback').addEventListener('click', () => {
      this.closeFeedbackSheet();
    });

    document.getElementById('btn-victory-continue').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.showScreen('scenario-screen');
    });

    // COPY FULL CONVERSATION TRANSCRIPT TO CLIPBOARD
    const copyBtn = document.getElementById('btn-copy-transcript');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        this.copyTranscriptToClipboard();
      });
    }
  }

  stopTTS() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  async updateVocabBadgeCount() {
    try {
      const res = await fetch(`/api/saved_words?target_lang=${encodeURIComponent(this.targetLang)}`);
      const data = await res.json();
      const badge = document.getElementById('vocab-count-badge');
      if (badge) badge.textContent = data.count || 0;
    } catch (e) {
      console.error('Failed to update vocab count:', e);
    }
  }

  async openVocabBookModal() {
    try {
      const res = await fetch(`/api/saved_words?target_lang=${encodeURIComponent(this.targetLang)}`);
      const data = await res.json();
      this.savedWords = data.words || [];

      const badge = document.getElementById('vocab-count-badge');
      if (badge) badge.textContent = data.count || 0;

      document.getElementById('input-search-vocab').value = '';
      this.renderVocabWordsList();
      document.getElementById('modal-vocab-book').classList.add('active');

    } catch (e) {
      console.error('Failed to open vocab book modal:', e);
    }
  }

  renderVocabWordsList(filterQuery = '') {
    const listContainer = document.getElementById('vocab-words-list');
    if (!listContainer) return;
    listContainer.innerHTML = '';

    const filtered = this.savedWords.filter(w =>
      w.word.toLowerCase().includes(filterQuery) ||
      w.translation.toLowerCase().includes(filterQuery)
    );

    if (filtered.length === 0) {
      listContainer.innerHTML = `
        <div style="text-align:center; padding: 20px; color: var(--text-muted); font-weight: 700;">
          ${filterQuery ? 'No matching words found.' : 'Chưa có từ vựng nào được lưu. Bấm vào từ vựng bất kỳ trong khi trò chuyện để lưu vào Sổ Từ Vựng!'}
        </div>
      `;
      return;
    }

    filtered.forEach(w => {
      const card = document.createElement('div');
      card.className = 'vocab-item-card';
      card.style.display = 'flex';
      card.style.justifyContent = 'space-between';
      card.style.alignItems = 'center';
      card.style.padding = '10px 14px';
      card.style.background = 'rgba(0,0,0,0.03)';
      card.style.borderRadius = '12px';
      card.style.border = '1px solid rgba(0,0,0,0.06)';

      card.innerHTML = `
        <div>
          <div style="font-weight: 900; font-size: 16px; color: var(--duo-blue);">${w.word} <span style="font-size:12px; color: var(--text-muted); font-weight:700;">${w.phonetic || ''}</span></div>
          <div style="font-weight: 800; font-size: 14px; color: var(--text-dark); margin-top: 2px;">${w.translation}</div>
        </div>
        <button class="btn-icon-sm play-word-sound" title="Listen pronunciation">🔊</button>
      `;

      card.querySelector('.play-word-sound').addEventListener('click', () => {
        this.playTTS(w.word, 'chloe');
      });

      listContainer.appendChild(card);
    });
  }

  updateLevelDisplay() {
    const badge = document.getElementById('level-badge-display');
    if (!badge) return;
    let label = 'Elementary';
    if (this.currentLevel > 4 && this.currentLevel <= 9) label = 'Intermediate';
    else if (this.currentLevel > 9 && this.currentLevel <= 15) label = 'Advanced';
    else if (this.currentLevel > 15) label = 'Native Expert';

    badge.textContent = `Level ${this.currentLevel}: ${label}`;
  }

  updateLangDisplay() {
    const btn = document.getElementById('btn-open-lang-modal');
    if (!btn) return;
    const labels = {
      'vi': 'English ➔ Vietnamese 🇻🇳',
      'en-def': 'English Definition 🇬🇧',
      'es': 'English ➔ Spanish 🇪🇸',
      'fr': 'English ➔ French 🇫🇷'
    };
    btn.textContent = `🌐 ${labels[this.targetLang] || 'English ➔ Vietnamese 🇻🇳'}`;
  }

  async loadCharacters() {
    try {
      const res = await fetch('/api/characters');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.characters = data.characters || [];
      this.renderCharactersRow();
    } catch (e) {
      console.error('Failed to load characters:', e);
    }
  }

  renderCharactersRow() {
    const row = document.getElementById('characters-scroll-row');
    if (!row) return;
    row.innerHTML = '';

    if (!this.selectedCharacter && this.characters.length > 0) {
      this.selectedCharacter = this.characters[0];
      this.isUserSelectedCharacter = true;
    }

    this.characters.forEach((c) => {
      const isSelected = this.selectedCharacter && this.selectedCharacter.id === c.id;
      const card = document.createElement('div');
      card.className = `character-card-mini ${isSelected ? 'selected' : ''}`;
      card.innerHTML = `
        <div class="character-avatar">${c.avatar_icon}</div>
        <div class="character-name">${c.name}</div>
        <span class="character-trait-badge">${c.trait || c.role}</span>
      `;

      card.addEventListener('click', () => {
        if (window.duoAudio) window.duoAudio.playClick();
        document.querySelectorAll('.character-card-mini').forEach(el => el.classList.remove('selected'));
        card.classList.add('selected');
        this.selectedCharacter = c;
        this.isUserSelectedCharacter = true;
      });

      row.appendChild(card);
    });
  }

  async loadScenarios() {
    try {
      const res = await fetch('/api/scenarios');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      let apiScenarios = data.scenarios || [];

      const localCustoms = JSON.parse(localStorage.getItem('duo_custom_topics') || '[]');
      const existingIds = new Set(apiScenarios.map(s => s.id));
      localCustoms.forEach(lc => {
        if (!existingIds.has(lc.id)) {
          apiScenarios.push(lc);
        }
      });

      this.scenarios = apiScenarios;
      this.renderScenarios();
    } catch (e) {
      console.error('Failed to load scenarios:', e);
    }
  }

  renderScenarios() {
    const grid = document.getElementById('scenarios-grid');
    if (!grid) return;
    grid.innerHTML = '';

    this.scenarios.forEach(sc => {
      const card = document.createElement('div');
      card.className = 'scenario-card';
      card.innerHTML = `
        <div class="scenario-card-header">
          <div class="scenario-icon">${sc.icon || '💬'}</div>
        </div>
        <div class="scenario-title">${sc.title} ${sc.is_custom ? '✨' : ''}</div>
        <div class="scenario-desc">${sc.description}</div>
        <button class="btn-duo btn-blue" style="width:100%; margin-top: auto;">START ROLEPLAY</button>
      `;

      card.addEventListener('click', () => {
        if (window.duoAudio) window.duoAudio.playClick();
        this.startScenario(sc.id);
      });

      grid.appendChild(card);
    });
  }

  async saveCustomTopic() {
    const titleInput = document.getElementById('custom-topic-title');
    const descInput = document.getElementById('custom-topic-desc');
    const iconInput = document.getElementById('custom-topic-icon');

    const title = titleInput.value.trim();
    if (!title) {
      alert('Vui lòng nhập tên chủ đề!');
      return;
    }

    const payload = {
      title: title,
      category: 'Everyday Life ☕',
      icon: iconInput.value.trim() || '💬',
      color: '#1CB0F6',
      level: 'Beginner',
      level_code: 'A2',
      default_character: 'lily',
      description: descInput.value.trim() || 'Custom everyday life topic.',
      objective: 'Practice speaking freely.',
      suggested_vocabulary: ['Everyday conversation', 'Free chat']
    };

    try {
      const res = await fetch('/api/custom_scenarios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      const savedScenario = data.scenario || payload;

      const localCustoms = JSON.parse(localStorage.getItem('duo_custom_topics') || '[]');
      localCustoms.unshift(savedScenario);
      localStorage.setItem('duo_custom_topics', JSON.stringify(localCustoms));

      titleInput.value = '';
      descInput.value = '';
      document.getElementById('modal-custom-topic').classList.remove('active');

      await this.loadScenarios();

    } catch (e) {
      console.error('Failed to save custom topic to server, saving locally:', e);
      const localCustoms = JSON.parse(localStorage.getItem('duo_custom_topics') || '[]');
      payload.id = `custom_${Date.now()}`;
      payload.is_custom = true;
      localCustoms.unshift(payload);
      localStorage.setItem('duo_custom_topics', JSON.stringify(localCustoms));

      titleInput.value = '';
      descInput.value = '';
      document.getElementById('modal-custom-topic').classList.remove('active');
      await this.loadScenarios();
    }
  }

  async startRandomRoleplay() {
    if (this.scenarios.length === 0 || this.characters.length === 0) return;
    const randScenario = this.scenarios[Math.floor(Math.random() * this.scenarios.length)];
    this.isUserSelectedCharacter = false; // Reset to random
    await this.startScenario(randScenario.id);
  }

  async startScenario(scenarioId) {
    try {
      const resSc = await fetch(`/api/scenarios/${scenarioId}`);
      this.currentScenario = await resSc.json();

      // If user did not manually pick a character card, pick a RANDOM partner automatically!
      if (!this.isUserSelectedCharacter || !this.selectedCharacter) {
        if (this.characters.length > 0) {
          this.selectedCharacter = this.characters[Math.floor(Math.random() * this.characters.length)];
        }
      }

      const resChar = await fetch(`/api/characters/${this.selectedCharacter.id}`);
      this.selectedCharacter = await resChar.json();

      this.conversationHistory = [];
      this.turnCount = 0;
      this.turnScores = [];

      this.stopTTS();

      // Update Header
      document.getElementById('scenario-stage-title').textContent = `${this.currentScenario.title} (${this.selectedCharacter.name}) - Lvl ${this.currentLevel}`;
      document.getElementById('current-turns-count').textContent = 'Turns: 0 (Unlimited)';

      document.getElementById('ai-persona-name').textContent = `${this.selectedCharacter.name} (${this.selectedCharacter.country})`;
      this.renderInteractiveAIText('Generating AI opening question...');
      document.getElementById('ai-translation-text').textContent = '';
      document.getElementById('ai-translation-text').style.display = 'none';

      DuoMascot.renderInto('practice-mascot', 'happy');
      this.showScreen('practice-screen');

      // AI Character PROACTIVELY Initiates Conversation
      const resStart = await fetch('/api/start_scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: this.currentScenario.id,
          character_id: this.selectedCharacter.id,
          level: this.currentLevel
        })
      });

      const startData = await resStart.json();
      this.currentAIText = startData.ai_response;
      this.currentAITextVi = startData.ai_response_vi || '';

      this.renderInteractiveAIText(this.currentAIText);
      document.getElementById('ai-translation-text').textContent = this.currentAITextVi;
      document.getElementById('ai-translation-text').style.display = 'none';

      this.conversationHistory.push({ role: 'assistant', content: this.currentAIText });

      // Play Neural Voice TTS
      this.playTTS(this.currentAIText, this.selectedCharacter.id);

    } catch (e) {
      console.error('Failed to start scenario:', e);
    }
  }

  renderInteractiveAIText(text) {
    const container = document.getElementById('ai-speech-text');
    if (!container) return;
    container.innerHTML = '';

    const parts = text.split(/(\s+)/);
    parts.forEach(part => {
      if (part.trim().length === 0) {
        container.appendChild(document.createTextNode(part));
        return;
      }

      const match = part.match(/^([^a-zA-Z0-9'-]*)([a-zA-Z0-9'-]+)([^a-zA-Z0-9'-]*)$/);
      if (match) {
        const [_, prefix, cleanWord, suffix] = match;
        if (prefix) container.appendChild(document.createTextNode(prefix));

        const tokenSpan = document.createElement('span');
        tokenSpan.className = 'word-token';
        tokenSpan.textContent = cleanWord;
        tokenSpan.title = `Click to translate '${cleanWord}'`;
        tokenSpan.addEventListener('click', () => {
          this.lookupWord(cleanWord);
        });
        container.appendChild(tokenSpan);

        if (suffix) container.appendChild(document.createTextNode(suffix));
      } else {
        container.appendChild(document.createTextNode(part));
      }
    });
  }

  /**
   * High-Performance Instant 0ms Word Lookup using Frontend + Backend RAM Caching!
   */
  async lookupWord(word) {
    const cleanWord = word.trim().toLowerCase();
    if (!cleanWord) return;

    const cacheKey = `${cleanWord}_${this.targetLang}`;

    // Instant 0ms Frontend RAM Lookup!
    if (this.wordCache.has(cacheKey)) {
      const cached = this.wordCache.get(cacheKey);
      this.showWordModal(cached);
      return;
    }

    try {
      if (window.duoAudio) window.duoAudio.playClick();
      const res = await fetch(`/api/translate_word?word=${encodeURIComponent(cleanWord)}&target_lang=${encodeURIComponent(this.targetLang)}`);
      const data = await res.json();

      this.wordCache.set(cacheKey, data);
      this.showWordModal(data);
      this.updateVocabBadgeCount();

    } catch (e) {
      console.error('Word lookup failed:', e);
    }
  }

  showWordModal(data) {
    document.getElementById('word-title').textContent = data.word;
    document.getElementById('word-phonetic').textContent = data.phonetic;
    document.getElementById('word-translation-label').textContent = data.target_label;
    document.getElementById('word-translation-text').textContent = data.translation;
    document.getElementById('modal-word-lookup').classList.add('active');
  }

  handleSpeechResult(transcript, isFinal) {
    document.getElementById('transcript-display').textContent = `"${transcript}"` || 'Listening...';
    if (isFinal && transcript.trim()) {
      this.submitSpokenTurn(transcript.trim());
    }
  }

  handleSpeechStateChange(state, detail) {
    const micBtn = document.getElementById('btn-mic-toggle');
    const cancelBtn = document.getElementById('btn-cancel-mic');
    const waveform = document.getElementById('waveform-anim');

    if (state === 'listening') {
      micBtn.classList.add('recording');
      waveform.classList.add('active');
      if (cancelBtn) cancelBtn.style.display = 'inline-flex';
      DuoMascot.renderInto('practice-mascot', 'listening');
      document.getElementById('transcript-display').textContent = '🎙️ Recording... Tap mic again to SEND, or tap Cancel to discard!';
    } else if (state === 'cancelled') {
      micBtn.classList.remove('recording');
      waveform.classList.remove('active');
      if (cancelBtn) cancelBtn.style.display = 'none';
      DuoMascot.renderInto('practice-mascot', 'happy');
      document.getElementById('transcript-display').textContent = '❌ Recording cancelled. Tap mic to try again!';
    } else {
      micBtn.classList.remove('recording');
      waveform.classList.remove('active');
      if (cancelBtn) cancelBtn.style.display = 'none';
      if (state === 'stopped') DuoMascot.renderInto('practice-mascot', 'happy');
    }
  }

  async submitSpokenTurn(userText) {
    this.stopTTS();
    document.getElementById('transcript-display').textContent = `"${userText}"`;
    document.getElementById('btn-mic-toggle').disabled = true;

    try {
      const res = await fetch('/api/process_turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: this.currentScenario.id,
          character_id: this.selectedCharacter ? this.selectedCharacter.id : null,
          user_transcript: userText,
          conversation_history: this.conversationHistory,
          level: this.currentLevel
        })
      });

      const data = await res.json();
      document.getElementById('btn-mic-toggle').disabled = false;

      this.conversationHistory.push({ role: 'user', content: userText });
      this.conversationHistory.push({ role: 'assistant', content: data.ai_response });

      this.turnCount++;
      document.getElementById('current-turns-count').textContent = `Turns: ${this.turnCount} (Unlimited)`;

      const fb = data.user_feedback || {};
      const turnScoreObj = {
        turn: this.turnCount,
        userText: userText,
        aiResponse: data.ai_response,
        aiResponseVi: data.ai_response_vi,
        fluency: fb.fluency_score || 90,
        grammar: fb.grammar_score || 92,
        overall: fb.overall_score || 91,
        nativePhrasing: fb.native_phrasing || ''
      };
      this.turnScores.push(turnScoreObj);

      this.showFeedbackSheet(data);

      if (fb.overall_score >= 85 && window.duoAudio) {
        window.duoAudio.playSuccess();
      }

      this.nextTurnData = data;

    } catch (e) {
      console.error('Turn submission error:', e);
      document.getElementById('btn-mic-toggle').disabled = false;
    }
  }

  showFeedbackSheet(data) {
    const fb = data.user_feedback || {};
    const sheet = document.getElementById('feedback-sheet');

    const score = fb.overall_score || 90;
    const isGood = score >= 85;
    sheet.className = `feedback-sheet active ${isGood ? '' : 'needs-work'}`;

    document.getElementById('feedback-title-text').textContent = isGood ? 'GREAT CONTINUOUS SPEAKING!' : 'GOOD EFFORT!';
    document.getElementById('feedback-score-badge').textContent = `Turn Score: ${score}/100 🔥`;

    document.getElementById('native-phrasing-text').textContent = fb.native_phrasing || 'Keep expressing yourself freely!';
    document.getElementById('feedback-xp-earned').textContent = `+${fb.xp_earned || 10} XP`;

    DuoMascot.renderInto('practice-mascot', fb.duo_reaction || 'happy');
  }

  closeFeedbackSheet() {
    const sheet = document.getElementById('feedback-sheet');
    sheet.classList.remove('active');

    if (!this.nextTurnData) return;

    const data = this.nextTurnData;
    this.totalXP += data.user_feedback.xp_earned || 10;
    document.getElementById('stat-xp-count').textContent = this.totalXP;

    this.currentAIText = data.ai_response;
    this.currentAITextVi = data.ai_response_vi || '';

    this.renderInteractiveAIText(this.currentAIText);
    document.getElementById('ai-translation-text').textContent = this.currentAITextVi;
    document.getElementById('ai-translation-text').style.display = 'none';

    // Play Neural Voice TTS
    this.playTTS(this.currentAIText, this.selectedCharacter ? this.selectedCharacter.id : 'lily');
  }

  finishAndScoreRoleplay() {
    this.stopTTS();
    if (this.turnScores.length === 0) {
      alert('Hãy nói ít nhất 1 câu trước khi kết thúc bài luyện!');
      return;
    }

    let sumFluency = 0;
    let sumGrammar = 0;
    let sumOverall = 0;

    this.turnScores.forEach(ts => {
      sumFluency += ts.fluency;
      sumGrammar += ts.grammar;
      sumOverall += ts.overall;
    });

    const totalTurns = this.turnScores.length;
    const avgFluency = Math.round(sumFluency / totalTurns);
    const avgGrammar = Math.round(sumGrammar / totalTurns);
    const avgOverall = Math.round(sumOverall / totalTurns);

    document.getElementById('victory-overall-score').textContent = `${avgOverall}/100`;
    document.getElementById('victory-fluency-score').textContent = `${avgFluency}/100`;
    document.getElementById('victory-grammar-score').textContent = `${avgGrammar}/100`;
    document.getElementById('victory-turns-completed').textContent = `${totalTurns} Turns`;

    // Render Full Turn-by-Turn Dialogue Script Review
    const scoresContainer = document.getElementById('victory-scores-breakdown');
    scoresContainer.innerHTML = '';
    this.turnScores.forEach(ts => {
      const item = document.createElement('div');
      item.className = 'score-turn-item';
      item.style.display = 'flex';
      item.style.flexDirection = 'column';
      item.style.gap = '6px';
      item.style.padding = '12px 16px';

      item.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px dashed rgba(0,0,0,0.1); padding-bottom: 6px;">
          <span style="color: var(--duo-blue); font-weight:800;">Turn ${ts.turn}</span>
          <span style="color: ${ts.overall >= 85 ? 'var(--duo-green)' : 'var(--duo-orange)'}; font-weight:800;">Score: ${ts.overall}/100</span>
        </div>
        <div style="font-size: 14px;"><strong>👤 You Spoke:</strong> "${ts.userText}"</div>
        <div style="font-size: 14px; color: var(--duo-green-dark);"><strong>🦉 AI Reply:</strong> "${ts.aiResponse}"</div>
        ${ts.aiResponseVi ? `<div style="font-size: 13px; color: var(--text-muted); font-style: italic;">🇻🇳 Dịch: "${ts.aiResponseVi}"</div>` : ''}
        ${ts.nativePhrasing ? `<div style="font-size: 13px; color: var(--duo-purple); font-weight:700;">💡 Native Tip: "${ts.nativePhrasing}"</div>` : ''}
      `;
      scoresContainer.appendChild(item);
    });

    if (window.duoAudio) window.duoAudio.playVictory();
    this.showScreen('victory-screen');
  }

  copyTranscriptToClipboard() {
    if (!this.turnScores || this.turnScores.length === 0) {
      alert('Chưa có lịch sử hội thoại để sao chép!');
      return;
    }

    let textBuffer = `=======================================\n`;
    textBuffer += `DUOLINGO SPEAK - ROLEPLAY CONVERSATION LOG\n`;
    textBuffer += `Topic: ${this.currentScenario ? this.currentScenario.title : 'Everyday Life'}\n`;
    textBuffer += `Partner: ${this.selectedCharacter ? this.selectedCharacter.name : 'AI'}\n`;
    textBuffer += `Level: ${this.currentLevel}/20\n`;
    textBuffer += `=======================================\n\n`;

    this.turnScores.forEach(ts => {
      textBuffer += `Turn ${ts.turn} (Score: ${ts.overall}/100):\n`;
      textBuffer += `User: "${ts.userText}"\n`;
      textBuffer += `AI:   "${ts.aiResponse}"\n`;
      if (ts.aiResponseVi) textBuffer += `Dịch: "${ts.aiResponseVi}"\n`;
      if (ts.nativePhrasing) textBuffer += `Native Tip: "${ts.nativePhrasing}"\n`;
      textBuffer += `---------------------------------------\n`;
    });

    navigator.clipboard.writeText(textBuffer).then(() => {
      if (window.duoAudio) window.duoAudio.playSuccess();
      alert('📋 Đã sao chép toàn bộ lịch sử trò chuyện vào Clipboard!');
    }).catch(err => {
      console.error('Clipboard copy failed:', err);
      alert('Không thể tự động sao chép, bạn có thể bôi đen đoạn văn bản để copy thủ công!');
    });
  }

  playTTS(text, charId = 'lily') {
    this.stopTTS();

    const url = `/api/tts?text=${encodeURIComponent(text)}&char_id=${encodeURIComponent(charId)}`;
    this.currentAudio = new Audio(url);
    this.currentAudio.play().catch(err => {
      console.warn('HTML5 Audio play error:', err);
    });
  }

  showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) target.classList.add('active');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new DuolingoSpeakApp();
});
