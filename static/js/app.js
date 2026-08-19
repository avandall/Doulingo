/**
 * DuoSpeak Application Controller v3.0
 * - Complete rebuild with proper event delegation
 * - Fix: Start Roleplay button works
 * - Fix: IELTS/CEFR Exam modal shows correctly
 * - Fix: TTS + Audio player integrated
 * - Fix: DOM nesting issues resolved
 * - Features: Lazy translation, vocabulary book, flashcards,
 *             history drawer, weekly report, error journal
 */

class DuoSpeakApp {
  constructor() {
    // State
    this.scenarios = [];
    this.characters = [];
    this.savedWords = [];
    this.selectedCharacter = null;
    this.currentScenario = null;
    this.conversationHistory = [];
    this.turnCount = 0;
    this.totalXP = 150;
    this.turnScores = [];
    this.currentLevel = 1;
    this.targetLang = localStorage.getItem('duo_target_lang') || 'vi';
    this.isDetInteractiveMode = false;
    this.currentDetScenario = null;

    // Audio/Speech State
    this.speechHandler = null;
    this.currentAudio = null;
    this.isSeekDragging = false;
    this.currentAIText = '';
    this.currentAITextVi = '';

    // Caches
    this.wordCache = new Map();
    this.ttsCache = new Map();
    this.sentenceTranslationCache = new Map();

    // History
    this.historyLog = [];
    this.currentHistoryAIIdx = 0;

    // DET Exam State
    this.isDetRecording = false;
    this.detElapsedSeconds = 0;
    this.detTimerInterval = null;
    this.detSpeechAccumulated = '';

    // IELTS category filter
    this.activeIeltsCategory = 'all';

    this.init();
  }

  // ============================================================
  // API URL HELPER
  // ============================================================
  apiUrl(path) {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    const origin = (window.location && window.location.origin !== 'null' && window.location.origin !== 'file://')
      ? window.location.origin : 'http://localhost:8000';
    return `${origin}${path.startsWith('/') ? '' : '/'}${path}`;
  }

  // ============================================================
  // INIT
  // ============================================================
  async init() {
    // Render mascot in brand
    if (window.DuoMascot) {
      DuoMascot.renderInto('brand-mascot', 'happy');
    }

    // Setup speech handler
    this.speechHandler = new SpeechHandler(
      (transcript, isFinal) => this.handleSpeechResult(transcript, isFinal),
      (state, detail) => this.handleSpeechStateChange(state, detail)
    );
    this.speechHandler.onVolumeChange = (vol) => this.handleVolumeChange(vol);

    this.bindEvents();
    this.updateLangDisplay();
    await Promise.all([this.loadCharacters(), this.loadScenarios()]);
    await this.updateVocabBadgeCount();
    this.loadUserStats();
  }

  // ============================================================
  // DATA LOADING
  // ============================================================
  async loadCharacters() {
    try {
      const res = await fetch(this.apiUrl('/api/characters'));
      if (!res.ok) throw new Error('Characters API failed');
      const data = await res.json();
      this.characters = data.characters || [];
      this.renderCharacters();
      // Auto-select first character
      if (this.characters.length > 0 && !this.selectedCharacter) {
        this.selectCharacter(this.characters[0]);
      }
    } catch (e) {
      console.error('[DuoSpeak] Failed to load characters:', e);
      this.renderCharactersFallback();
    }
  }

  async loadScenarios() {
    try {
      const res = await fetch(this.apiUrl('/api/scenarios'));
      if (!res.ok) throw new Error('Scenarios API failed');
      const data = await res.json();
      this.scenarios = data.scenarios || [];
      this.renderAllScenarios();
    } catch (e) {
      console.error('[DuoSpeak] Failed to load scenarios:', e);
    }
  }

  async loadUserStats() {
    try {
      const res = await fetch(this.apiUrl('/api/user_stats'));
      if (!res.ok) return;
      const data = await res.json();
      const streakEl = document.getElementById('stat-streak-count');
      const xpEl = document.getElementById('stat-xp-count');
      if (streakEl) streakEl.textContent = data.streak_days || 5;
      if (xpEl) xpEl.textContent = data.total_xp || 150;
      this.totalXP = data.total_xp || 150;
    } catch (e) {
      // Silently fail
    }
  }

  // ============================================================
  // RENDER CHARACTERS
  // ============================================================
  renderCharacters() {
    const container = document.getElementById('characters-scroll-row');
    if (!container) return;
    container.innerHTML = '';

    this.characters.forEach(char => {
      const card = document.createElement('div');
      card.className = 'character-card';
      card.dataset.charId = char.id;
      card.innerHTML = `
        <div class="character-selected-dot"></div>
        <div class="character-avatar">${char.avatar_icon || '🤖'}</div>
        <div class="character-name">${char.name || char.id}</div>
        <div class="character-accent">${char.accent || ''}</div>
      `;
      card.addEventListener('click', () => {
        if (window.duoAudio) window.duoAudio.playClick();
        this.selectCharacter(char);
      });
      container.appendChild(card);
    });
  }

  renderCharactersFallback() {
    const fallbackChars = [
      { id: 'lily', name: 'Lily', accent: 'US English', avatar_icon: '👩' },
      { id: 'rajesh', name: 'Rajesh', accent: 'Indian English', avatar_icon: '👨‍💼' },
      { id: 'beatrice', name: 'Beatrice', accent: 'British', avatar_icon: '👩‍🎓' },
      { id: 'oscar', name: 'Oscar', accent: 'Australian', avatar_icon: '🧑' },
    ];
    this.characters = fallbackChars;
    this.renderCharacters();
    this.selectCharacter(fallbackChars[0]);
  }

  selectCharacter(char) {
    this.selectedCharacter = char;
    // Update UI
    document.querySelectorAll('.character-card').forEach(card => {
      card.classList.toggle('selected', card.dataset.charId === char.id);
    });
    // Update practice screen avatar
    const avatarEl = document.getElementById('ai-avatar-icon');
    if (avatarEl) avatarEl.textContent = char.avatar_icon || '🤖';
  }

  // ============================================================
  // RENDER SCENARIOS
  // ============================================================
  renderAllScenarios() {
    const ieltsScenarios = this.scenarios.filter(s => s.mode === 'ielts_exam');
    const roleplayScenarios = this.scenarios.filter(s => s.mode !== 'ielts_exam');

    this.renderIeltsGrid(ieltsScenarios);
    this.renderRoleplayGrid(roleplayScenarios);
  }

  renderIeltsGrid(scenarios) {
    const grid = document.getElementById('ielts-scenarios-grid');
    if (!grid) return;
    grid.innerHTML = '';

    const filtered = this.activeIeltsCategory === 'all'
      ? scenarios
      : scenarios.filter(s => s.category === this.activeIeltsCategory);

    filtered.forEach(sc => {
      grid.appendChild(this.createScenarioCard(sc, 'ielts'));
    });

    // Add custom IELTS card
    const addCard = document.createElement('div');
    addCard.className = 'scenario-card add-custom-card ielts-card';
    addCard.innerHTML = `
      <div class="add-custom-icon">➕</div>
      <div class="add-custom-label">Add Custom IELTS Topic</div>
    `;
    addCard.addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.openCustomTopicModal('ielts_exam');
    });
    grid.appendChild(addCard);
  }

  renderRoleplayGrid(scenarios) {
    const grid = document.getElementById('roleplay-scenarios-grid');
    if (!grid) return;
    grid.innerHTML = '';

    scenarios.forEach(sc => {
      grid.appendChild(this.createScenarioCard(sc, 'roleplay'));
    });

    // Add custom roleplay card
    const addCard = document.createElement('div');
    addCard.className = 'scenario-card add-custom-card';
    addCard.innerHTML = `
      <div class="add-custom-icon">➕</div>
      <div class="add-custom-label">Add Custom Topic</div>
    `;
    addCard.addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.openCustomTopicModal('roleplay');
    });
    grid.appendChild(addCard);
  }

  createScenarioCard(sc, type) {
    const card = document.createElement('div');
    card.className = `scenario-card${type === 'ielts' ? ' ielts-card' : ''}`;
    card.dataset.scenarioId = sc.id;
    card.dataset.scenarioMode = sc.mode || 'roleplay';

    card.innerHTML = `
      <div class="scenario-card-icon">${sc.icon || '💬'}</div>
      <div class="scenario-card-title">${sc.title || 'Untitled'}</div>
      <div class="scenario-card-desc">${sc.description || ''}</div>
      <div class="scenario-card-footer">
        <span class="scenario-level-badge">${sc.level_code || sc.level || 'B1'}</span>
        <span class="scenario-start-arrow">→</span>
      </div>
    `;

    card.addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      if (sc.mode === 'ielts_exam') {
        this.openDetExamModal(sc);
      } else {
        this.startScenario(sc.id);
      }
    });

    return card;
  }

  // ============================================================
  // SCREEN NAVIGATION
  // ============================================================
  showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) target.classList.add('active');
  }

  // ============================================================
  // START SCENARIO (ROLEPLAY)
  // ============================================================
  async startScenario(scenarioId) {
    const scenario = this.scenarios.find(s => s.id === scenarioId);
    if (!scenario) {
      console.error('[DuoSpeak] Scenario not found:', scenarioId);
      return;
    }

    this.currentScenario = scenario;
    this.conversationHistory = [];
    this.turnCount = 0;
    this.turnScores = [];
    this.historyLog = [];
    this.currentHistoryAIIdx = 0;
    this.currentAIText = '';
    this.currentAITextVi = '';
    this._clearTTSCache();

    const charId = this.selectedCharacter ? this.selectedCharacter.id : 'lily';
    const charData = this.selectedCharacter || { id: charId, name: 'AI', avatar_icon: '🤖' };

    // Update practice screen UI
    const titleEl = document.getElementById('scenario-stage-title');
    if (titleEl) titleEl.textContent = scenario.title || 'Practice';

    const progressFill = document.getElementById('lesson-progress-fill');
    if (progressFill) progressFill.style.width = '0%';

    const avatarEl = document.getElementById('ai-avatar-icon');
    if (avatarEl) avatarEl.textContent = charData.avatar_icon || '🤖';

    const nameEl = document.getElementById('ai-persona-name-text');
    if (nameEl) nameEl.textContent = `${charData.name || charId} ${charData.accent ? '·' : ''} ${charData.accent || ''}`.trim();

    const aiTextEl = document.getElementById('ai-speech-text');
    if (aiTextEl) aiTextEl.innerHTML = '<div class="loading-spinner"><div class="spinner-ring"></div> Generating opening...</div>';

    const transcriptEl = document.getElementById('transcript-display');
    if (transcriptEl) transcriptEl.textContent = 'Tap the mic to start speaking...';

    // Hide review box
    const reviewBox = document.getElementById('transcript-review-box');
    if (reviewBox) reviewBox.style.display = 'none';

    // Reset turn counter
    const turnsEl = document.getElementById('current-turns-count');
    if (turnsEl) turnsEl.textContent = '0 Turns';

    this.showScreen('practice-screen');
    this._setPlayerLoading();

    try {
      const res = await fetch(this.apiUrl('/api/start_scenario'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: scenarioId,
          character_id: charId,
          level: this.currentLevel
        })
      });

      if (!res.ok) throw new Error(`Start scenario failed: ${res.status}`);
      const data = await res.json();

      const aiResponse = data.ai_response || data.response || data.ai_utterance || "Hello! Let's practice together!";
      const aiResponseVi = data.ai_response_vi || '';

      this.displayAITurn(aiResponse, aiResponseVi);

      // Push to conversation history for next turn
      this.conversationHistory.push({ role: 'assistant', content: aiResponse });

      // Play TTS
      await this.playTTS(aiResponse, charId);

    } catch (e) {
      console.error('[DuoSpeak] Start scenario error:', e);
      const fallback = "Hello! I'm ready to practice with you. What would you like to talk about?";
      this.displayAITurn(fallback, '');
      await this.playTTS(fallback, charId);
    }
  }

  // ============================================================
  // PROCESS TURN (USER SPEAKS → AI REPLIES)
  // ============================================================
  async submitSpokenTurn(userTranscript) {
    if (!userTranscript.trim()) return;
    if (!this.currentScenario) return;

    const charId = this.selectedCharacter ? this.selectedCharacter.id : 'lily';

    // Add user message to history log
    this.historyLog.push({
      role: 'user',
      textEn: userTranscript,
      turnNum: this.turnCount
    });
    this.conversationHistory.push({ role: 'user', content: userTranscript });

    // Update UI - show thinking state
    const aiTextEl = document.getElementById('ai-speech-text');
    if (aiTextEl) aiTextEl.innerHTML = '<div class="loading-spinner"><div class="spinner-ring"></div> AI is thinking...</div>';
    this._setPlayerLoading();

    // Hide translation
    const transEl = document.getElementById('ai-translation-text');
    if (transEl) { transEl.style.display = 'none'; transEl.textContent = ''; }
    this.currentAITextVi = '';

    // Disable mic during processing
    const micBtn = document.getElementById('btn-mic-toggle');
    if (micBtn) micBtn.disabled = true;

    try {
      const res = await fetch(this.apiUrl('/api/process_turn'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: this.currentScenario.id,
          character_id: charId,
          user_transcript: userTranscript,
          conversation_history: this.conversationHistory.slice(-10), // last 10 msgs
          level: this.currentLevel
        })
      });

      if (!res.ok) throw new Error(`Process turn failed: ${res.status}`);
      const data = await res.json();

      const aiResponse = data.ai_response || data.response || data.ai_utterance || "Interesting! Please continue.";
      const aiResponseVi = data.ai_response_vi || '';
      const feedback = data.user_feedback || {};
      const fluencyScore = feedback.fluency_score || data.fluency_score || 80;
      const nativeSuggestion = feedback.native_phrasing || data.native_suggestion || userTranscript;
      const xpGained = data.xp_gained || 10;
      const isCompleted = data.is_completed || false;

      this.turnCount++;
      this.totalXP += xpGained;
      this.turnScores.push({ user: userTranscript, ai: aiResponse, score: fluencyScore });

      // Update conversation history
      this.conversationHistory.push({ role: 'assistant', content: aiResponse });

      // Update progress bar
      const progressFill = document.getElementById('lesson-progress-fill');
      if (progressFill) {
        const progress = Math.min(100, this.turnCount * 10);
        progressFill.style.width = `${progress}%`;
      }

      // Update turns counter
      const turnsEl = document.getElementById('current-turns-count');
      if (turnsEl) turnsEl.textContent = `${this.turnCount} Turn${this.turnCount !== 1 ? 's' : ''}`;

      // Display AI turn
      this.displayAITurn(aiResponse, aiResponseVi);

      // Play TTS
      await this.playTTS(aiResponse, charId);

      // Show feedback sheet
      this.showFeedbackSheet(fluencyScore, nativeSuggestion, xpGained);

      // Update XP display
      const xpEl = document.getElementById('stat-xp-count');
      if (xpEl) xpEl.textContent = this.totalXP;

      // Add XP to backend
      fetch(this.apiUrl(`/api/user_stats/add_xp?xp=${xpGained}`), { method: 'POST' }).catch(() => {});

      if (isCompleted) {
        setTimeout(() => this.finishAndScoreRoleplay(), 2000);
      }

    } catch (e) {
      console.error('[DuoSpeak] Process turn error:', e);
      const fallback = "That's great! Could you tell me more about that?";
      this.displayAITurn(fallback, '');
      await this.playTTS(fallback, charId);
    } finally {
      if (micBtn) micBtn.disabled = false;
    }
  }

  // ============================================================
  // DISPLAY AI TURN
  // ============================================================
  displayAITurn(text, textVi = '') {
    this.currentAIText = text;
    this.currentAITextVi = textVi;

    // Add to history log
    const idx = this.historyLog.length;
    this.historyLog.push({
      role: 'ai',
      textEn: text,
      textVi: textVi,
      turnNum: this.turnCount,
      blobUrl: null
    });
    this.currentHistoryAIIdx = idx;

    // Render interactive word tokens
    this.renderInteractiveAIText(text);

    // Show/hide translation
    const transEl = document.getElementById('ai-translation-text');
    if (transEl) {
      if (textVi) {
        transEl.textContent = textVi;
        transEl.style.display = 'block';
      } else {
        transEl.style.display = 'none';
        transEl.textContent = '';
      }
    }

    // Reset translate button
    const translateBtn = document.getElementById('btn-lazy-translate');
    if (translateBtn) translateBtn.classList.remove('active');
    const fullTransBtn = document.getElementById('btn-toggle-translate');
    if (fullTransBtn) fullTransBtn.classList.remove('active');

    // Scroll to bottom
    const dialogueArea = document.getElementById('dialogue-area');
    if (dialogueArea) {
      setTimeout(() => { dialogueArea.scrollTop = dialogueArea.scrollHeight; }, 100);
    }
  }

  renderInteractiveAIText(text) {
    const container = document.getElementById('ai-speech-text');
    if (!container) return;
    container.innerHTML = '';

    const words = text.split(/(\s+)/);
    words.forEach(chunk => {
      if (/^\s+$/.test(chunk)) {
        container.appendChild(document.createTextNode(chunk));
      } else {
        const span = document.createElement('span');
        span.className = 'word-token';
        span.textContent = chunk;
        const cleanWord = chunk.replace(/[^a-zA-Z'-]/g, '').toLowerCase();
        if (cleanWord.length > 1) {
          span.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showWordLookup(cleanWord, chunk);
          });
        }
        container.appendChild(span);
      }
    });
  }

  // ============================================================
  // SPEECH HANDLERS
  // ============================================================
  handleSpeechResult(transcript, isFinal) {
    const transcriptEl = document.getElementById('transcript-display');
    if (transcriptEl) {
      transcriptEl.textContent = transcript || 'Listening...';
      transcriptEl.classList.toggle('active', !!transcript);
    }

    if (isFinal && transcript.trim()) {
      // Show review box for editing before sending
      const reviewBox = document.getElementById('transcript-review-box');
      const reviewInput = document.getElementById('review-speech-input');
      if (reviewBox && reviewInput) {
        reviewInput.value = transcript.trim();
        reviewBox.style.display = 'block';
      }

      // DET mode: accumulate speech instead of submitting
      if (this.isDetRecording && document.getElementById('modal-det-exam')?.classList.contains('active')) {
        this.detSpeechAccumulated += ' ' + transcript.trim();
        // Update word count display if element exists
        const wcEl = document.getElementById('det-speech-word-count');
        if (wcEl) {
          const words = this.detSpeechAccumulated.trim().split(/\s+/).filter(Boolean).length;
          wcEl.textContent = `${words} words`;
        }
      }
    }
  }

  handleSpeechStateChange(state, detail) {
    const micBtn = document.getElementById('btn-mic-toggle');
    const cancelBtn = document.getElementById('btn-cancel-mic');
    const waveform = document.getElementById('waveform-anim');
    const transcriptEl = document.getElementById('transcript-display');

    if (state === 'listening') {
      if (micBtn) {
        micBtn.textContent = '⏹️';
        micBtn.classList.add('listening');
        micBtn.title = 'Press to stop recording';
      }
      if (cancelBtn) cancelBtn.style.display = 'flex';
      if (waveform) waveform.classList.add('active');
      if (transcriptEl) transcriptEl.textContent = 'Listening... Speak clearly!';
    } else if (state === 'stopped' || state === 'error' || state === 'cancelled') {
      if (micBtn) {
        micBtn.textContent = '🎙️';
        micBtn.classList.remove('listening');
        micBtn.title = 'Press to speak';
      }
      if (cancelBtn) cancelBtn.style.display = 'none';
      if (waveform) {
        waveform.classList.remove('active');
        // Reset inline heights so CSS idle animation resumes
        waveform.querySelectorAll('.wave-bar').forEach(bar => { bar.style.height = ''; });
      }
      if (state === 'cancelled') {
        if (transcriptEl) transcriptEl.textContent = 'Recording cancelled.';
        const reviewBox = document.getElementById('transcript-review-box');
        if (reviewBox) reviewBox.style.display = 'none';
      } else if (state === 'stopped') {
        if (transcriptEl) transcriptEl.textContent = 'Processing your speech...';
      }
    }
  }

  handleVolumeChange(volume) {
    const animateWaveform = (id) => {
      const el = document.getElementById(id);
      if (!el || !el.classList.contains('active')) return;

      const bars = el.querySelectorAll('.wave-bar');
      const numBars = bars.length;
      if (numBars === 0) return;

      // Use frequency data if available for realistic bars
      if (this.speechHandler && this.speechHandler.analyser && this.speechHandler.dataArray) {
        const data = this.speechHandler.dataArray;
        const bucketSize = Math.floor(data.length / numBars);
        bars.forEach((bar, i) => {
          const start = i * bucketSize;
          let sum = 0;
          for (let j = start; j < start + bucketSize && j < data.length; j++) {
            sum += data[j];
          }
          const avg = sum / bucketSize;
          // Map 0-255 to 4-36px height with slight spatial randomness
          const h = 4 + (avg / 255) * 32 + (Math.random() * 2 - 1);
          bar.style.height = `${Math.max(4, Math.min(36, h))}px`;
        });
      } else {
        // Fallback: use average volume with random spatial variation
        const scale = Math.min(volume / 128, 1.0);
        bars.forEach(bar => {
          const h = 4 + scale * 32 * (Math.random() * 0.6 + 0.4);
          bar.style.height = `${Math.max(4, Math.min(36, h))}px`;
        });
      }
    };

    animateWaveform('waveform-anim');
    animateWaveform('det-waveform-anim');
  }


  // ============================================================
  // TTS
  // ============================================================
  async playTTS(text, charId) {
    if (!text) return;
    this._setPlayerLoading();

    const cacheKey = `${charId}::${text.slice(0, 100)}`;
    if (this.ttsCache.has(cacheKey)) {
      this._playAudioBlob(this.ttsCache.get(cacheKey), cacheKey);
      return;
    }

    try {
      const url = this.apiUrl(`/api/tts?text=${encodeURIComponent(text.slice(0, 500))}&character_id=${charId}`);
      const res = await fetch(url);
      if (!res.ok) throw new Error('TTS fetch failed');
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      this.ttsCache.set(cacheKey, blobUrl);

      // Store in history log
      if (this.historyLog.length > 0) {
        const last = this.historyLog[this.historyLog.length - 1];
        if (last.role === 'ai') last.blobUrl = blobUrl;
      }

      this._playAudioBlob(blobUrl, cacheKey);
    } catch (e) {
      console.warn('[DuoSpeak] TTS error:', e);
      this._setPlayerReady(); // Show controls even if TTS failed
    }
  }

  _playAudioBlob(blobUrl, cacheKey) {
    this.stopTTS();
    const audio = new Audio(blobUrl);
    this.currentAudio = audio;

    audio.addEventListener('canplaythrough', () => {
      this._setPlayerReady();
    });

    audio.addEventListener('timeupdate', () => {
      if (!this.isSeekDragging) this._updateSeekbar();
    });

    audio.addEventListener('ended', () => {
      const btnPlay = document.getElementById('audio-btn-playpause');
      if (btnPlay) btnPlay.textContent = '▶️';
    });

    audio.play().catch(e => {
      console.warn('[DuoSpeak] Audio play error:', e);
      this._setPlayerReady();
    });
  }

  stopTTS() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  }

  _clearTTSCache() {
    this.ttsCache.forEach(url => { try { URL.revokeObjectURL(url); } catch(e) {} });
    this.ttsCache.clear();
  }

  _setPlayerLoading() {
    const loading = document.getElementById('audio-player-loading');
    const controls = document.getElementById('audio-player-controls');
    if (loading) loading.style.display = 'flex';
    if (controls) controls.style.display = 'none';
  }

  _setPlayerReady() {
    const loading = document.getElementById('audio-player-loading');
    const controls = document.getElementById('audio-player-controls');
    if (loading) loading.style.display = 'none';
    if (controls) controls.style.display = 'flex';
    const btnPlay = document.getElementById('audio-btn-playpause');
    if (btnPlay) btnPlay.textContent = '⏸️';
  }

  _updateSeekbar() {
    if (!this.currentAudio) return;
    const seekbar = document.getElementById('audio-seekbar');
    const timeEl = document.getElementById('audio-time-display');
    const dur = this.currentAudio.duration || 0;
    const cur = this.currentAudio.currentTime || 0;
    if (seekbar && dur > 0) seekbar.value = (cur / dur) * 100;
    if (timeEl) timeEl.textContent = `${this._fmtTime(cur)} / ${this._fmtTime(dur)}`;
  }

  _fmtTime(s) {
    const sec = Math.floor(s % 60);
    const min = Math.floor(s / 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
  }

  // ============================================================
  // FEEDBACK SHEET
  // ============================================================
  showFeedbackSheet(score, nativeSuggestion, xp) {
    const sheet = document.getElementById('feedback-sheet');
    const emojiEl = document.getElementById('feedback-emoji');
    const titleEl = document.getElementById('feedback-title-text');
    const scoreBadge = document.getElementById('feedback-score-badge');
    const nativeEl = document.getElementById('native-phrasing-text');
    const xpEl = document.getElementById('feedback-xp-earned');

    if (score >= 90) {
      if (emojiEl) emojiEl.textContent = '🏆';
      if (titleEl) titleEl.textContent = 'Excellent Speaking!';
    } else if (score >= 75) {
      if (emojiEl) emojiEl.textContent = '🎉';
      if (titleEl) titleEl.textContent = 'Great Job!';
    } else {
      if (emojiEl) emojiEl.textContent = '💪';
      if (titleEl) titleEl.textContent = 'Keep Practicing!';
    }

    if (scoreBadge) scoreBadge.textContent = `Score: ${score}/100`;
    if (nativeEl) nativeEl.textContent = `"${nativeSuggestion}"`;
    if (xpEl) xpEl.textContent = `⚡ +${xp} XP`;

    if (sheet) {
      sheet.classList.add('active');
      // Auto-close after 4 seconds
      setTimeout(() => sheet.classList.remove('active'), 4000);
    }
  }

  closeFeedbackSheet() {
    const sheet = document.getElementById('feedback-sheet');
    if (sheet) sheet.classList.remove('active');
  }

  // ============================================================
  // FINISH ROLEPLAY → VICTORY SCREEN
  // ============================================================
  finishAndScoreRoleplay() {
    this.stopTTS();
    if (this.speechHandler) this.speechHandler.cancel();

    const avgScore = this.turnScores.length > 0
      ? Math.round(this.turnScores.reduce((a, t) => a + t.score, 0) / this.turnScores.length)
      : 80;

    // Update victory stats
    const overallEl = document.getElementById('victory-overall-score');
    const fluencyEl = document.getElementById('victory-fluency-score');
    const grammarEl = document.getElementById('victory-grammar-score');
    const turnsEl = document.getElementById('victory-turns-completed');

    if (overallEl) overallEl.textContent = `${avgScore}/100`;
    if (fluencyEl) fluencyEl.textContent = `${Math.min(100, avgScore + 2)}/100`;
    if (grammarEl) grammarEl.textContent = `${Math.max(60, avgScore - 3)}/100`;
    if (turnsEl) turnsEl.textContent = `${this.turnCount} Turns`;

    // Render transcript
    const breakdown = document.getElementById('victory-scores-breakdown');
    if (breakdown) {
      breakdown.innerHTML = '';
      this.historyLog.forEach(entry => {
        const item = document.createElement('div');
        item.className = 'score-turn-item';
        const isAI = entry.role === 'ai';
        item.innerHTML = `
          <div class="score-turn-speaker ${isAI ? 'ai' : 'user'}">
            ${isAI ? '🤖 AI Partner' : '🎙️ You'}
          </div>
          <div class="score-turn-text">${entry.textEn || ''}</div>
        `;
        breakdown.appendChild(item);
      });
    }

    // Confetti!
    if (window.confetti) {
      confetti({ particleCount: 80, spread: 70, origin: { y: 0.6 } });
    }

    this.showScreen('victory-screen');
  }

  finishAndScoreDetInteractive() {
    this.submitDetSpeech('interactive_speaking',
      this.conversationHistory.filter(m => m.role === 'user').map(m => m.content).join('. ')
    );
  }

  // ============================================================
  // HISTORY NAVIGATION (for Audio Player ⏮ ⏭)
  // ============================================================
  navPrevHistoryTurn() {
    let prevIdx = -1;
    for (let i = this.currentHistoryAIIdx - 1; i >= 0; i--) {
      if (this.historyLog[i] && this.historyLog[i].role === 'ai') { prevIdx = i; break; }
    }
    if (prevIdx < 0) { this.showToast('🕒 This is the first turn.'); return; }
    this._navToAITurn(prevIdx);
  }

  navNextHistoryTurn() {
    let nextIdx = -1;
    for (let i = this.currentHistoryAIIdx + 1; i < this.historyLog.length; i++) {
      if (this.historyLog[i] && this.historyLog[i].role === 'ai') { nextIdx = i; break; }
    }
    if (nextIdx < 0) { this.showToast('🕒 This is the latest turn.'); return; }
    this._navToAITurn(nextIdx);
  }

  _navToAITurn(idx) {
    const entry = this.historyLog[idx];
    if (!entry || entry.role !== 'ai') return;
    this.currentHistoryAIIdx = idx;
    this.currentAIText = entry.textEn;
    this.currentAITextVi = entry.textVi || '';
    this.renderInteractiveAIText(entry.textEn);

    if (entry.blobUrl) {
      this._playAudioBlob(entry.blobUrl);
    } else {
      const charId = this.selectedCharacter ? this.selectedCharacter.id : 'lily';
      this.playTTS(entry.textEn, charId);
    }
  }

  // ============================================================
  // HISTORY DRAWER
  // ============================================================
  openHistoryDrawer() {
    this._renderHistoryDrawer();
    document.getElementById('history-drawer-overlay').classList.add('active');
  }

  _renderHistoryDrawer() {
    const body = document.getElementById('history-drawer-body');
    if (!body) return;
    body.innerHTML = '';

    if (this.historyLog.length === 0) {
      body.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-weight:700;padding:30px;font-size:14px;">No conversation yet!</div>';
      return;
    }

    this.historyLog.forEach((entry, idx) => {
      const card = document.createElement('div');
      card.className = `history-turn-card${idx === this.currentHistoryAIIdx ? ' current' : ''}`;
      const isAI = entry.role === 'ai';
      card.innerHTML = `
        <div class="history-turn-label ${isAI ? 'ai-label' : 'user-label'}">
          ${isAI ? `🤖 ${this.selectedCharacter ? this.selectedCharacter.name : 'AI'}` : '🎙️ You'}
          ${entry.turnNum !== undefined ? `· Turn ${entry.turnNum}` : ''}
        </div>
        <div class="history-turn-text">${entry.textEn || ''}</div>
      `;
      if (isAI) {
        card.addEventListener('click', () => {
          this._navToAITurn(idx);
          document.getElementById('history-drawer-overlay').classList.remove('active');
        });
      }
      body.appendChild(card);
    });

    // Scroll to bottom
    setTimeout(() => { body.scrollTop = body.scrollHeight; }, 50);
  }

  // ============================================================
  // LAZY TRANSLATION
  // ============================================================
  async handleLazyTranslateTurn() {
    const transEl = document.getElementById('ai-translation-text');
    const btn = document.getElementById('btn-lazy-translate');
    if (!transEl) return;

    const isVisible = transEl.style.display !== 'none' && transEl.textContent;
    if (isVisible) {
      transEl.style.display = 'none';
      if (btn) btn.classList.remove('active');
      return;
    }

    if (this.currentAITextVi) {
      transEl.textContent = this.currentAITextVi;
      transEl.style.display = 'block';
      if (btn) btn.classList.add('active');
      return;
    }

    if (!this.currentAIText) return;
    const cacheKey = `${this.targetLang}::${this.currentAIText}`;
    if (this.sentenceTranslationCache.has(cacheKey)) {
      const cached = this.sentenceTranslationCache.get(cacheKey);
      this.currentAITextVi = cached;
      transEl.textContent = cached;
      transEl.style.display = 'block';
      if (btn) btn.classList.add('active');
      return;
    }

    transEl.innerHTML = '<span style="color:var(--text-muted);font-style:italic;">⏳ Translating...</span>';
    transEl.style.display = 'block';

    try {
      const res = await fetch(this.apiUrl('/api/translate_sentence'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: this.currentAIText, target_lang: this.targetLang })
      });
      const data = await res.json();
      const translation = data.translation || this.currentAIText;
      this.currentAITextVi = translation;
      this.sentenceTranslationCache.set(cacheKey, translation);
      transEl.textContent = translation;
      if (btn) btn.classList.add('active');
    } catch (e) {
      transEl.textContent = this.currentAIText;
    }
  }

  async toggleLazyTranslate() {
    await this.handleLazyTranslateTurn();
  }

  // ============================================================
  // WORD LOOKUP
  // ============================================================
  async showWordLookup(word, originalToken) {
    const modal = document.getElementById('modal-word-lookup');
    const titleEl = document.getElementById('word-title');
    const phoneticEl = document.getElementById('word-phonetic');
    const labelEl = document.getElementById('word-translation-label');
    const transEl = document.getElementById('word-translation-text');

    if (!modal) return;
    if (titleEl) titleEl.textContent = word;
    if (phoneticEl) phoneticEl.textContent = `/${word}/`;
    if (transEl) transEl.textContent = 'Loading...';
    if (labelEl) {
      const labels = { vi: 'Vietnamese', 'en-def': 'English Definition', es: 'Spanish', fr: 'French' };
      labelEl.textContent = labels[this.targetLang] || 'Translation';
    }
    modal.classList.add('active');

    const cacheKey = `${word.toLowerCase()}_${this.targetLang}`;
    if (this.wordCache.has(cacheKey)) {
      const cached = this.wordCache.get(cacheKey);
      if (phoneticEl) phoneticEl.textContent = cached.phonetic || `/${word}/`;
      if (transEl) transEl.textContent = cached.translation;
      return;
    }

    try {
      const res = await fetch(this.apiUrl(`/api/translate_word?word=${encodeURIComponent(word)}&target_lang=${this.targetLang}`));
      const data = await res.json();
      if (phoneticEl) phoneticEl.textContent = data.phonetic || `/${word}/`;
      if (transEl) transEl.textContent = data.translation || word;
      this.wordCache.set(cacheKey, data);
      // Update vocab count
      await this.updateVocabBadgeCount();
    } catch (e) {
      if (transEl) transEl.textContent = 'Lookup failed. Try again.';
    }
  }

  // ============================================================
  // VOCABULARY BOOK
  // ============================================================
  async openVocabBookModal() {
    document.getElementById('modal-vocab-book').classList.add('active');
    try {
      const res = await fetch(this.apiUrl(`/api/saved_words?target_lang=${this.targetLang}`));
      const data = await res.json();
      this.savedWords = data.words || [];
      this.renderVocabWordsList('');
    } catch (e) {
      console.error('[DuoSpeak] Vocab load error:', e);
    }
  }

  renderVocabWordsList(filter) {
    const list = document.getElementById('vocab-words-list');
    if (!list) return;
    list.innerHTML = '';

    const words = filter
      ? this.savedWords.filter(w => w.word && w.word.toLowerCase().includes(filter))
      : this.savedWords;

    if (words.length === 0) {
      list.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;font-size:14px;">No words saved yet. Tap a word in conversation to look it up!</div>';
      return;
    }

    words.forEach(w => {
      const card = document.createElement('div');
      card.className = 'vocab-word-card';
      card.innerHTML = `
        <div>
          <div class="vocab-word-main">${w.word || ''}</div>
          <div class="vocab-phonetic">${w.phonetic || ''}</div>
        </div>
        <div class="vocab-translation">${w.translation || ''}</div>
      `;
      list.appendChild(card);
    });
  }

  async updateVocabBadgeCount() {
    try {
      const res = await fetch(this.apiUrl('/api/saved_words'));
      const data = await res.json();
      const count = data.count || 0;
      const badge = document.getElementById('vocab-count-badge');
      if (badge) badge.textContent = count;
    } catch (e) {}
  }

  // ============================================================
  // FLASHCARDS
  // ============================================================
  openFlashcards() {
    if (!this.savedWords || this.savedWords.length === 0) {
      this.showToast('📖 Vocab book is empty! Look up some words first.');
      return;
    }
    this.fcIndex = 0;
    document.getElementById('modal-vocab-book').classList.remove('active');
    document.getElementById('modal-flashcard-practice').classList.add('active');
    this.renderFlashcard();
  }

  renderFlashcard() {
    const inner = document.getElementById('flashcard-inner');
    if (inner) inner.classList.remove('flipped');

    if (this.fcIndex >= this.savedWords.length) {
      document.getElementById('modal-flashcard-practice').classList.remove('active');
      this.showToast('🎉 You finished all flashcards!');
      return;
    }

    const w = this.savedWords[this.fcIndex];
    const wordEl = document.getElementById('fc-word');
    const phoneticEl = document.getElementById('fc-phonetic');
    const transEl = document.getElementById('fc-translation');
    const curEl = document.getElementById('fc-current');
    const totalEl = document.getElementById('fc-total');

    if (wordEl) wordEl.textContent = w.word || '';
    if (phoneticEl) phoneticEl.textContent = w.phonetic || '';
    if (transEl) transEl.textContent = w.translation || 'Translation';
    if (curEl) curEl.textContent = this.fcIndex + 1;
    if (totalEl) totalEl.textContent = this.savedWords.length;
  }

  // ============================================================
  // CUSTOM TOPIC
  // ============================================================
  openCustomTopicModal(mode) {
    const modal = document.getElementById('modal-custom-topic');
    if (!modal) return;
    modal.dataset.topicMode = mode || 'roleplay';
    document.getElementById('custom-topic-title').value = '';
    document.getElementById('custom-topic-desc').value = '';
    document.getElementById('custom-topic-icon').value = '💬';
    document.querySelectorAll('.emoji-item').forEach(el => el.classList.remove('active'));
    const firstEmoji = document.querySelector('.emoji-item');
    if (firstEmoji) firstEmoji.classList.add('active');
    modal.classList.add('active');
  }

  async saveCustomTopic() {
    const modal = document.getElementById('modal-custom-topic');
    const title = document.getElementById('custom-topic-title').value.trim();
    const desc = document.getElementById('custom-topic-desc').value.trim();
    const icon = document.getElementById('custom-topic-icon').value || '💬';
    const mode = modal ? (modal.dataset.topicMode || 'roleplay') : 'roleplay';

    if (!title) { this.showToast('⚠️ Please enter a topic title.'); return; }

    try {
      const res = await fetch(this.apiUrl('/api/custom_scenarios'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description: desc || title, icon, mode })
      });
      if (!res.ok) throw new Error('Save failed');
      const data = await res.json();
      this.scenarios.push(data.scenario);
      this.renderAllScenarios();
      modal.classList.remove('active');
      this.showToast('✅ Custom topic saved!');
    } catch (e) {
      this.showToast('❌ Failed to save topic.');
    }
  }

  // ============================================================
  // RANDOM ROLEPLAY
  // ============================================================
  startRandomRoleplay() {
    const roleplayScenarios = this.scenarios.filter(s => s.mode !== 'ielts_exam');
    if (roleplayScenarios.length === 0) return;
    const random = roleplayScenarios[Math.floor(Math.random() * roleplayScenarios.length)];
    this.startScenario(random.id);
  }

  // ============================================================
  // IELTS / DET EXAM
  // ============================================================
  openDetExamModal(sc) {
    if (!sc) return;
    this.currentDetScenario = sc;
    this.isDetInteractiveMode = false;
    this.detSpeechAccumulated = '';
    this.stopDetMonologueTimer();

    const titleEl = document.getElementById('det-exam-title');
    const catEl = document.getElementById('det-exam-category-badge');
    if (titleEl) titleEl.textContent = sc.title || 'IELTS Speaking Topic';
    if (catEl) catEl.textContent = `🎓 ${sc.category || 'IELTS / CEFR Speaking'}`;

    const qCard = sc.question_card || {};
    const promptEl = document.getElementById('det-card-prompt-text');
    const bulletsEl = document.getElementById('det-card-bullet-points');

    if (promptEl) promptEl.textContent = qCard.prompt || sc.description || 'Describe this topic in detail.';
    if (bulletsEl) {
      const bullets = qCard.bullet_points || [
        'What the main topic is about',
        'When and where it occurred',
        'Who was involved',
        'Why it matters to you'
      ];
      bulletsEl.innerHTML = bullets.map(b => `<li>${b}</li>`).join('');
    }

    // Reset timer
    const timerEl = document.getElementById('det-monologue-timer');
    const statusEl = document.getElementById('det-timer-status-badge');
    const btnRecord = document.getElementById('btn-det-start-record');
    const micStatusEl = document.getElementById('det-mic-status');

    if (timerEl) timerEl.textContent = '00:00 / 03:00';
    if (statusEl) { statusEl.textContent = '⏳ Speak at least 1 minute'; statusEl.classList.remove('met'); }
    if (btnRecord) btnRecord.innerHTML = '🎙️ Start Recording';
    if (micStatusEl) { micStatusEl.textContent = 'Press "Start Recording" below to begin speaking...'; micStatusEl.classList.remove('active'); }

    // Reset tabs
    document.getElementById('btn-tab-read-speak').classList.add('active');
    document.getElementById('btn-tab-interactive').classList.remove('active');
    document.getElementById('det-view-read-speak').style.display = 'block';
    document.getElementById('det-view-interactive').style.display = 'none';

    document.getElementById('modal-det-exam').classList.add('active');
  }

  startDetMonologueTimer() {
    this.isDetRecording = true;
    this.detElapsedSeconds = 0;
    this.detSpeechAccumulated = '';

    const btnRecord = document.getElementById('btn-det-start-record');
    const micStatusEl = document.getElementById('det-mic-status');
    const waveform = document.getElementById('det-waveform-anim');

    if (btnRecord) { btnRecord.innerHTML = '⏹️ Stop Recording'; }
    if (micStatusEl) { micStatusEl.textContent = '🎙️ Recording... Speak confidently!'; micStatusEl.classList.add('active'); }
    if (waveform) waveform.classList.add('active');

    // Start speech recognition
    if (this.speechHandler) this.speechHandler.startListening();

    this.detTimerInterval = setInterval(() => {
      this.detElapsedSeconds++;
      const timerEl = document.getElementById('det-monologue-timer');
      const statusEl = document.getElementById('det-timer-status-badge');
      if (timerEl) timerEl.textContent = `${this._fmtTime(this.detElapsedSeconds)} / 03:00`;
      if (this.detElapsedSeconds >= 60 && statusEl) {
        statusEl.textContent = '✅ Time requirement met!';
        statusEl.classList.add('met');
      }
      if (this.detElapsedSeconds >= 180) this.stopDetMonologueTimer();
    }, 1000);
  }

  stopDetMonologueTimer() {
    this.isDetRecording = false;
    if (this.detTimerInterval) {
      clearInterval(this.detTimerInterval);
      this.detTimerInterval = null;
    }

    const btnRecord = document.getElementById('btn-det-start-record');
    const micStatusEl = document.getElementById('det-mic-status');
    const waveform = document.getElementById('det-waveform-anim');

    if (btnRecord) btnRecord.innerHTML = '🎙️ Start Recording';
    if (micStatusEl) { micStatusEl.textContent = '✅ Recording stopped. Press Submit to evaluate.'; micStatusEl.classList.remove('active'); }
    if (waveform) waveform.classList.remove('active');

    if (this.speechHandler) this.speechHandler.stopListening();
  }

  async submitDetSpeech(mode, overrideText) {
    this.stopDetMonologueTimer();

    // Gather speech text: from speech recognition accumulation or override
    const speechText = (overrideText || this.detSpeechAccumulated || '').trim();

    if (!speechText) {
      this.showToast('⚠️ Please record your speech before submitting!');
      return;
    }

    const btnSubmit = document.getElementById('btn-det-submit-speech');
    if (btnSubmit) { btnSubmit.disabled = true; btnSubmit.innerHTML = '⏳ AI Examiner Evaluating...'; }

    try {
      const wordCount = speechText.split(/\s+/).filter(Boolean).length;
      const durationSecs = this.detElapsedSeconds || Math.max(60, Math.round(wordCount / 2));
      const wpm = Math.round((wordCount / Math.max(1, durationSecs)) * 60);
      const fillerMatches = speechText.toLowerCase().match(/\b(uh|um|er|ah|like|you know|actually|basically|literally)\b/g);
      const fillerCount = fillerMatches ? fillerMatches.length : 0;

      const res = await fetch(this.apiUrl('/api/det/evaluate_speech'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: this.currentDetScenario ? this.currentDetScenario.id : 'det_childhood_memory',
          user_speech: speechText,
          duration_seconds: durationSecs,
          mode: mode || 'read_then_speak',
          wpm, pause_count: 0, filler_count: fillerCount
        })
      });

      if (!res.ok) throw new Error(`Eval failed: ${res.status}`);
      const data = await res.json();
      document.getElementById('modal-det-exam').classList.remove('active');
      this.renderDetScoreReport(data);
    } catch (e) {
      console.error('[DuoSpeak] DET eval error:', e);
      this.showToast('❌ Evaluation failed. Please try again.');
    } finally {
      if (btnSubmit) { btnSubmit.disabled = false; btnSubmit.innerHTML = '📤 Submit Speaking Test'; }
    }
  }

  renderDetScoreReport(data) {
    const scoreEl = document.getElementById('det-report-score');
    const cefrEl = document.getElementById('det-report-cefr');
    if (scoreEl) scoreEl.textContent = data.det_score || data.ielts_band || 6.0;
    if (cefrEl) cefrEl.textContent = data.cefr_level || 'B2 Upper-Intermediate';

    const setBar = (barId, valId, val, suffix = '/100') => {
      const bar = document.getElementById(barId);
      const valEl = document.getElementById(valId);
      if (bar) bar.style.width = `${val}%`;
      if (valEl) valEl.textContent = `${val}${suffix}`;
    };

    setBar('det-bar-fluency',   'det-val-fluency',   data.fluency_score || 80);
    setBar('det-bar-grammar',   'det-val-grammar',   data.grammar_score || 78);
    setBar('det-bar-vocab',     'det-val-vocab',     data.vocabulary_score || 82);
    setBar('det-bar-coherence', 'det-val-coherence', data.coherence_score || 85);

    const ac = data.acoustic_metrics || {};
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('det-ac-wpm', `${ac.wpm || 110} WPM`);
    setEl('det-ac-pauses', `${ac.pause_count || 0} pauses`);
    setEl('det-ac-fillers', `${ac.filler_count || 0} fillers`);
    setEl('det-ac-diagnosis', ac.rhythm_diagnosis || 'Natural, flowing speech.');
    setEl('det-report-critique', data.examiner_critique || 'Good overall performance. Keep practicing!');
    setEl('det-report-sample', data.sample_native_response || 'Sample response coming soon.');

    const upgradesEl = document.getElementById('det-report-upgrades');
    if (upgradesEl) {
      const upgrades = data.sentence_upgrades || [];
      upgradesEl.innerHTML = upgrades.map(u => `
        <div class="upgrade-card">
          <div class="upgrade-orig">❌ "${u.original || ''}"</div>
          <div class="upgrade-improved">✨ "${u.upgraded || ''}"</div>
          <div class="upgrade-explain">💡 ${u.explanation || ''}</div>
        </div>
      `).join('') || '<div style="color:var(--text-muted);font-size:13px;font-style:italic;">No sentence upgrades for this response.</div>';
    }

    document.getElementById('modal-det-score-report').classList.add('active');
  }

  // ============================================================
  // WEEKLY REPORT
  // ============================================================
  async openWeeklyReport() {
    if (window.duoAudio) window.duoAudio.playClick();
    document.getElementById('modal-weekly-report').classList.add('active');

    try {
      const res = await fetch(this.apiUrl('/api/reports/weekly?user_id=user_demo&days=7'));
      if (!res.ok) throw new Error('Weekly report API failed');
      const data = await res.json();

      const band = parseFloat(data.overall_band || 6.0).toFixed(1);
      const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

      setEl('weekly-overall-band', band);

      const b = parseFloat(band);
      let cefr = 'B2 Upper-Intermediate';
      if (b >= 8.5) cefr = 'C2 Expert';
      else if (b >= 7.5) cefr = 'C1 Advanced';
      else if (b >= 6.0) cefr = 'B2 Upper-Intermediate';
      else if (b >= 5.0) cefr = 'B1 Intermediate';
      else cefr = 'A2 Elementary';
      setEl('weekly-cefr-badge', cefr);

      setEl('weekly-summary-text', data.summary || `${data.evaluations_count || 0} evaluations completed. Overall band: ${band}.`);
      setEl('weekly-strongest-badge', `💪 ${(data.strongest_axis || 'fluency').toUpperCase()}`);
      setEl('weekly-weakest-badge', `🎯 ${(data.weakest_axis || 'grammar').toUpperCase()}`);

      const axes = data.axes_scores || {};
      const setBar = (barId, valId, val) => {
        const score = parseFloat(val || 6.0);
        const pct = Math.min(100, Math.max(10, (score / 9.0) * 100));
        const barEl = document.getElementById(barId);
        const valEl = document.getElementById(valId);
        if (barEl) barEl.style.width = `${pct}%`;
        if (valEl) valEl.textContent = `Band ${score.toFixed(1)}`;
      };
      setBar('weekly-bar-fluency',       'weekly-val-fluency',       axes.fluency);
      setBar('weekly-bar-lexical',       'weekly-val-lexical',       axes.lexical);
      setBar('weekly-bar-grammar',       'weekly-val-grammar',       axes.grammar);
      setBar('weekly-bar-pronunciation', 'weekly-val-pronunciation', axes.pronunciation);

      const recList = document.getElementById('weekly-recommendations-list');
      if (recList) {
        recList.innerHTML = '';
        (data.recommendations || ['Focus on varied sentence structures and continuous speech flow.']).forEach(r => {
          const li = document.createElement('li');
          li.textContent = r;
          recList.appendChild(li);
        });
      }

      const errList = document.getElementById('weekly-recurring-errors-list');
      if (errList) {
        errList.innerHTML = '';
        const errs = data.recurring_errors || [];
        if (errs.length === 0) {
          errList.innerHTML = '<span style="color:var(--text-muted);font-style:italic;font-size:13px;">No recurring errors. Great work!</span>';
        } else {
          errs.forEach(e => {
            const detail = typeof e === 'object' ? (e.error_detail || JSON.stringify(e)) : String(e);
            const div = document.createElement('div');
            div.className = 'error-journal-card';
            div.innerHTML = `<div class="error-journal-detail">⚠️ ${detail}</div>`;
            errList.appendChild(div);
          });
        }
      }
    } catch (e) {
      console.error('[DuoSpeak] Weekly report error:', e);
    }
  }

  // ============================================================
  // ERROR JOURNAL
  // ============================================================
  async openErrorJournal() {
    if (window.duoAudio) window.duoAudio.playClick();
    document.getElementById('modal-error-journal').classList.add('active');
    const container = document.getElementById('error-journal-list');
    if (!container) return;
    container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;">Loading...</div>';

    try {
      const res = await fetch(this.apiUrl('/api/reports/weekly?user_id=user_demo&days=30'));
      if (!res.ok) throw new Error('Error journal API failed');
      const data = await res.json();
      const errs = data.recurring_errors || [];
      container.innerHTML = '';

      if (errs.length === 0) {
        container.innerHTML = `
          <div style="text-align:center;padding:30px;background:rgba(16,185,129,0.06);border-radius:14px;border:2px dashed var(--emerald);">
            <div style="font-size:32px;margin-bottom:8px;">🎉</div>
            <div style="font-size:15px;font-weight:800;color:var(--emerald);">No Critical Errors Logged!</div>
            <div style="font-size:13px;color:var(--text-muted);margin-top:4px;">Keep practicing to improve!</div>
          </div>
        `;
      } else {
        errs.forEach(item => {
          const detail = typeof item === 'object' ? (item.error_detail || JSON.stringify(item)) : String(item);
          const cat = typeof item === 'object' ? (item.category || 'Grammar / Vocabulary') : 'Error';
          const card = document.createElement('div');
          card.className = 'error-journal-card';
          card.innerHTML = `
            <div class="error-journal-category">📌 ${cat}</div>
            <div class="error-journal-detail">${detail}</div>
            <div class="error-journal-suggestion">💡 AI will weave this into your next practice session.</div>
          `;
          container.appendChild(card);
        });
      }
    } catch (e) {
      container.innerHTML = '<div style="color:var(--rose);font-weight:700;padding:20px;">Failed to load Error Journal.</div>';
    }
  }

  // ============================================================
  // COPY TRANSCRIPT
  // ============================================================
  copyTranscriptToClipboard() {
    const text = this.historyLog.map(e =>
      `${e.role === 'ai' ? 'AI' : 'You'}: ${e.textEn}`
    ).join('\n\n');
    navigator.clipboard.writeText(text).then(() => {
      this.showToast('📋 Transcript copied!');
    });
  }

  // ============================================================
  // LEVEL / DISPLAY UPDATES
  // ============================================================
  updateLevelDisplay() {
    const levelNames = [
      '', 'Elementary', 'Elementary+', 'Pre-Intermediate', 'Pre-Intermediate+',
      'Intermediate', 'Intermediate+', 'Upper-Intermediate', 'Upper-Intermediate+',
      'Advanced', 'Advanced+', 'Advanced++', 'C1', 'C1+', 'Near-Native',
      'Near-Native+', 'Native-Like', 'Native-Like+', 'Expert', 'Expert+', 'Native Expert'
    ];
    const name = levelNames[this.currentLevel] || `Level ${this.currentLevel}`;
    const badge = document.getElementById('level-badge-display');
    if (badge) badge.textContent = `Level ${this.currentLevel} · ${name}`;

    const slider = document.getElementById('level-slider-input');
    if (slider) {
      const pct = ((this.currentLevel - 1) / 19) * 100;
      slider.style.setProperty('--fill', `${pct}%`);
    }
  }

  updateLangDisplay() {
    const flags = { vi: '🇻🇳', 'en-def': '🇬🇧', es: '🇪🇸', fr: '🇫🇷' };
    const langEl = document.getElementById('lang-display');
    if (langEl) langEl.textContent = flags[this.targetLang] || '🌐';

    const select = document.getElementById('select-target-lang');
    if (select) select.value = this.targetLang;
  }

  // ============================================================
  // TOAST / NOTIFICATIONS
  // ============================================================
  showToast(message, duration = 3000) {
    const toast = document.getElementById('fork-toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), duration);
  }

  // ============================================================
  // BIND ALL EVENTS
  // ============================================================
  bindEvents() {

    // === NAVBAR ===
    const btnWeekly = document.getElementById('btn-open-weekly-report');
    if (btnWeekly) btnWeekly.addEventListener('click', () => this.openWeeklyReport());

    const btnCloseWeekly = document.getElementById('btn-close-weekly-report');
    if (btnCloseWeekly) btnCloseWeekly.addEventListener('click', () => document.getElementById('modal-weekly-report').classList.remove('active'));
    const btnCloseWeeklyBtm = document.getElementById('btn-close-weekly-report-bottom');
    if (btnCloseWeeklyBtm) btnCloseWeeklyBtm.addEventListener('click', () => document.getElementById('modal-weekly-report').classList.remove('active'));

    const btnErr = document.getElementById('btn-open-error-journal');
    if (btnErr) btnErr.addEventListener('click', () => this.openErrorJournal());
    const btnCloseErr = document.getElementById('btn-close-error-journal');
    if (btnCloseErr) btnCloseErr.addEventListener('click', () => document.getElementById('modal-error-journal').classList.remove('active'));
    const btnCloseErrBtm = document.getElementById('btn-close-error-journal-bottom');
    if (btnCloseErrBtm) btnCloseErrBtm.addEventListener('click', () => document.getElementById('modal-error-journal').classList.remove('active'));

    const btnVocab = document.getElementById('btn-open-vocab-modal');
    if (btnVocab) btnVocab.addEventListener('click', () => { if (window.duoAudio) window.duoAudio.playClick(); this.openVocabBookModal(); });
    const btnCloseVocab = document.getElementById('btn-close-vocab-modal');
    if (btnCloseVocab) btnCloseVocab.addEventListener('click', () => document.getElementById('modal-vocab-book').classList.remove('active'));
    const btnCloseVocabBtm = document.getElementById('btn-close-vocab-bottom');
    if (btnCloseVocabBtm) btnCloseVocabBtm.addEventListener('click', () => document.getElementById('modal-vocab-book').classList.remove('active'));

    const searchVocab = document.getElementById('input-search-vocab');
    if (searchVocab) searchVocab.addEventListener('input', e => this.renderVocabWordsList(e.target.value.trim().toLowerCase()));

    const btnFlashcards = document.getElementById('btn-open-flashcards');
    if (btnFlashcards) btnFlashcards.addEventListener('click', () => { if (window.duoAudio) window.duoAudio.playClick(); this.openFlashcards(); });
    const btnCloseFlash = document.getElementById('btn-close-flashcard-modal');
    if (btnCloseFlash) btnCloseFlash.addEventListener('click', () => document.getElementById('modal-flashcard-practice').classList.remove('active'));

    const flashcardContainer = document.getElementById('flashcard-container');
    if (flashcardContainer) {
      flashcardContainer.addEventListener('click', () => {
        const inner = document.getElementById('flashcard-inner');
        if (inner) inner.classList.toggle('flipped');
      });
    }
    const btnFcHard = document.getElementById('btn-fc-hard');
    if (btnFcHard) btnFcHard.addEventListener('click', () => { this.fcIndex++; this.renderFlashcard(); });
    const btnFcEasy = document.getElementById('btn-fc-easy');
    if (btnFcEasy) btnFcEasy.addEventListener('click', () => { this.fcIndex++; this.renderFlashcard(); });

    // === LANG MODAL ===
    const btnLang = document.getElementById('btn-open-lang-modal');
    if (btnLang) btnLang.addEventListener('click', () => { if (window.duoAudio) window.duoAudio.playClick(); document.getElementById('modal-lang-setting').classList.add('active'); });
    const btnCloseLang = document.getElementById('btn-close-lang-modal');
    if (btnCloseLang) btnCloseLang.addEventListener('click', () => document.getElementById('modal-lang-setting').classList.remove('active'));
    const btnCloseLang2 = document.getElementById('btn-close-lang-modal-2');
    if (btnCloseLang2) btnCloseLang2.addEventListener('click', () => document.getElementById('modal-lang-setting').classList.remove('active'));
    const btnSaveLang = document.getElementById('btn-save-lang-setting');
    if (btnSaveLang) btnSaveLang.addEventListener('click', () => {
      const select = document.getElementById('select-target-lang');
      this.targetLang = select.value;
      localStorage.setItem('duo_target_lang', this.targetLang);
      this.wordCache.clear();
      this.updateLangDisplay();
      this.updateVocabBadgeCount();
      document.getElementById('modal-lang-setting').classList.remove('active');
      this.showToast('✅ Language setting saved!');
    });

    // === WORD LOOKUP MODAL ===
    const btnCloseWord = document.getElementById('btn-close-word-modal');
    if (btnCloseWord) btnCloseWord.addEventListener('click', () => document.getElementById('modal-word-lookup').classList.remove('active'));
    const btnCloseWord2 = document.getElementById('btn-close-word-modal-2');
    if (btnCloseWord2) btnCloseWord2.addEventListener('click', () => document.getElementById('modal-word-lookup').classList.remove('active'));
    const wordModal = document.getElementById('modal-word-lookup');
    if (wordModal) wordModal.addEventListener('click', e => { if (e.target === wordModal) wordModal.classList.remove('active'); });

    // === CUSTOM TOPIC ===
    const btnCloseCust = document.getElementById('btn-close-custom-modal');
    if (btnCloseCust) btnCloseCust.addEventListener('click', () => document.getElementById('modal-custom-topic').classList.remove('active'));
    const btnCancelCust = document.getElementById('btn-cancel-custom-modal');
    if (btnCancelCust) btnCancelCust.addEventListener('click', () => document.getElementById('modal-custom-topic').classList.remove('active'));
    const btnSaveCust = document.getElementById('btn-save-custom-topic');
    if (btnSaveCust) btnSaveCust.addEventListener('click', () => this.saveCustomTopic());
    const btnRandom = document.getElementById('btn-random-roleplay');
    if (btnRandom) btnRandom.addEventListener('click', () => { if (window.duoAudio) window.duoAudio.playClick(); this.startRandomRoleplay(); });
    const btnOpenCust = document.getElementById('btn-open-custom-modal');
    if (btnOpenCust) btnOpenCust.addEventListener('click', () => { if (window.duoAudio) window.duoAudio.playClick(); this.openCustomTopicModal('roleplay'); });

    // Emoji grid
    const emojiGrid = document.getElementById('emoji-picker-grid');
    if (emojiGrid) {
      emojiGrid.querySelectorAll('.emoji-item').forEach(item => {
        item.addEventListener('click', () => {
          emojiGrid.querySelectorAll('.emoji-item').forEach(el => el.classList.remove('active'));
          item.classList.add('active');
          const hiddenInput = document.getElementById('custom-topic-icon');
          if (hiddenInput) hiddenInput.value = item.dataset.emoji || '💬';
        });
      });
    }

    // === LEVEL SLIDER ===
    const slider = document.getElementById('level-slider-input');
    if (slider) {
      slider.addEventListener('input', e => {
        this.currentLevel = parseInt(e.target.value, 10);
        this.updateLevelDisplay();
      });
      this.updateLevelDisplay();
    }

    // === IELTS CATEGORY FILTER ===
    const ieltsFilter = document.getElementById('ielts-category-filter');
    if (ieltsFilter) {
      ieltsFilter.querySelectorAll('.cat-pill').forEach(pill => {
        pill.addEventListener('click', () => {
          ieltsFilter.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
          pill.classList.add('active');
          this.activeIeltsCategory = pill.dataset.ieltsCat || 'all';
          const ieltsScenarios = this.scenarios.filter(s => s.mode === 'ielts_exam');
          this.renderIeltsGrid(ieltsScenarios);
        });
      });
    }

    // === PRACTICE SCREEN ===
    const btnClosePractice = document.getElementById('btn-close-practice');
    if (btnClosePractice) btnClosePractice.addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.stopTTS();
      if (this.speechHandler) this.speechHandler.cancel();
      this.showScreen('home-screen');
    });

    const btnFinish = document.getElementById('btn-finish-roleplay');
    if (btnFinish) btnFinish.addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.stopTTS();
      if (this.isDetInteractiveMode) this.finishAndScoreDetInteractive();
      else this.finishAndScoreRoleplay();
    });

    // === MIC ===
    const btnMic = document.getElementById('btn-mic-toggle');
    if (btnMic) btnMic.addEventListener('click', () => this.speechHandler.toggleListening());
    const btnCancelMic = document.getElementById('btn-cancel-mic');
    if (btnCancelMic) btnCancelMic.addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      if (this.speechHandler) this.speechHandler.cancel();
      const reviewBox = document.getElementById('transcript-review-box');
      if (reviewBox) reviewBox.style.display = 'none';
    });

    // === TRANSCRIPT REVIEW ===
    const btnReviewSend = document.getElementById('btn-review-send');
    if (btnReviewSend) btnReviewSend.addEventListener('click', () => {
      const input = document.getElementById('review-speech-input');
      const val = input ? input.value.trim() : '';
      if (val) {
        const reviewBox = document.getElementById('transcript-review-box');
        if (reviewBox) reviewBox.style.display = 'none';
        if (input) input.value = '';
        this.submitSpokenTurn(val);
      }
    });

    const btnReviewRetry = document.getElementById('btn-review-retry');
    if (btnReviewRetry) btnReviewRetry.addEventListener('click', () => {
      const reviewBox = document.getElementById('transcript-review-box');
      if (reviewBox) reviewBox.style.display = 'none';
      const input = document.getElementById('review-speech-input');
      if (input) input.value = '';
      if (this.speechHandler) this.speechHandler.startListening();
    });

    const reviewInput = document.getElementById('review-speech-input');
    if (reviewInput) {
      reviewInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          document.getElementById('btn-review-send').click();
        }
      });
    }

    // === BUBBLE ACTIONS ===
    const btnLazyTrans = document.getElementById('btn-lazy-translate');
    if (btnLazyTrans) btnLazyTrans.addEventListener('click', () => this.handleLazyTranslateTurn());
    const btnToggleTrans = document.getElementById('btn-toggle-translate');
    if (btnToggleTrans) btnToggleTrans.addEventListener('click', () => this.toggleLazyTranslate());
    const btnCopyAI = document.getElementById('btn-copy-ai-speech');
    if (btnCopyAI) btnCopyAI.addEventListener('click', () => {
      if (this.currentAIText) {
        navigator.clipboard.writeText(this.currentAIText);
        this.showToast('📋 Copied!');
      }
    });

    // === AUDIO PLAYER ===
    this._bindAudioPlayer();

    // === HISTORY DRAWER ===
    const btnOpenHistory = document.getElementById('btn-open-history');
    if (btnOpenHistory) btnOpenHistory.addEventListener('click', () => this.openHistoryDrawer());
    const btnCloseHistory = document.getElementById('btn-close-history');
    if (btnCloseHistory) btnCloseHistory.addEventListener('click', () => document.getElementById('history-drawer-overlay').classList.remove('active'));
    const historyOverlay = document.getElementById('history-drawer-overlay');
    if (historyOverlay) historyOverlay.addEventListener('click', e => {
      if (e.target === historyOverlay || !e.target.closest('.drawer-panel')) {
        historyOverlay.classList.remove('active');
      }
    });

    // === FEEDBACK SHEET ===
    const btnContinueFeedback = document.getElementById('btn-continue-feedback');
    if (btnContinueFeedback) btnContinueFeedback.addEventListener('click', () => this.closeFeedbackSheet());

    // === VICTORY SCREEN ===
    const btnVictoryCont = document.getElementById('btn-victory-continue');
    if (btnVictoryCont) btnVictoryCont.addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.showScreen('home-screen');
    });
    const btnCopyTranscript = document.getElementById('btn-copy-transcript');
    if (btnCopyTranscript) btnCopyTranscript.addEventListener('click', () => this.copyTranscriptToClipboard());

    // === DET EXAM MODAL ===
    const btnCloseDet = document.getElementById('btn-close-det-exam');
    if (btnCloseDet) btnCloseDet.addEventListener('click', () => {
      this.stopDetMonologueTimer();
      if (this.speechHandler) this.speechHandler.cancel();
      document.getElementById('modal-det-exam').classList.remove('active');
    });

    const btnTabReadSpeak = document.getElementById('btn-tab-read-speak');
    const btnTabInteractive = document.getElementById('btn-tab-interactive');
    if (btnTabReadSpeak && btnTabInteractive) {
      btnTabReadSpeak.addEventListener('click', () => {
        btnTabReadSpeak.classList.add('active');
        btnTabInteractive.classList.remove('active');
        document.getElementById('det-view-read-speak').style.display = 'block';
        document.getElementById('det-view-interactive').style.display = 'none';
      });
      btnTabInteractive.addEventListener('click', () => {
        btnTabInteractive.classList.add('active');
        btnTabReadSpeak.classList.remove('active');
        document.getElementById('det-view-read-speak').style.display = 'none';
        document.getElementById('det-view-interactive').style.display = 'block';
      });
    }

    const btnStartRecord = document.getElementById('btn-det-start-record');
    if (btnStartRecord) {
      btnStartRecord.addEventListener('click', () => {
        if (this.isDetRecording) this.stopDetMonologueTimer();
        else this.startDetMonologueTimer();
      });
    }

    const btnSubmitDet = document.getElementById('btn-det-submit-speech');
    if (btnSubmitDet) btnSubmitDet.addEventListener('click', () => this.submitDetSpeech('read_then_speak'));

    const btnStartInteractive = document.getElementById('btn-start-det-interactive-room');
    if (btnStartInteractive) {
      btnStartInteractive.addEventListener('click', () => {
        document.getElementById('modal-det-exam').classList.remove('active');
        if (this.currentDetScenario) {
          this.isDetInteractiveMode = true;
          this.startScenario(this.currentDetScenario.id);
        }
      });
    }

    // === DET SCORE REPORT ===
    const btnDetClose = document.getElementById('btn-det-close-report');
    if (btnDetClose) btnDetClose.addEventListener('click', () => {
      document.getElementById('modal-det-score-report').classList.remove('active');
      document.getElementById('modal-det-exam').classList.remove('active');
      this.stopDetMonologueTimer();
      if (this.speechHandler) this.speechHandler.cancel();
      this.isDetInteractiveMode = false;
      this.showScreen('home-screen');
    });

    const btnDetTryAgain = document.getElementById('btn-det-try-again');
    if (btnDetTryAgain) btnDetTryAgain.addEventListener('click', () => {
      document.getElementById('modal-det-score-report').classList.remove('active');
      this.stopDetMonologueTimer();
      if (this.currentDetScenario) this.openDetExamModal(this.currentDetScenario);
    });

    // === CLOSE MODALS ON OVERLAY CLICK ===
    ['modal-lang-setting', 'modal-custom-topic', 'modal-vocab-book', 'modal-flashcard-practice',
     'modal-weekly-report', 'modal-error-journal', 'modal-det-exam', 'modal-det-score-report'].forEach(id => {
      const overlay = document.getElementById(id);
      if (overlay) {
        overlay.addEventListener('click', e => {
          if (e.target === overlay) overlay.classList.remove('active');
        });
      }
    });
  }

  // ============================================================
  // AUDIO PLAYER BINDING
  // ============================================================
  _bindAudioPlayer() {
    const btnPlay = document.getElementById('audio-btn-playpause');
    const btnRewind = document.getElementById('audio-btn-rewind');
    const btnNext = document.getElementById('audio-btn-next');
    const seekbar = document.getElementById('audio-seekbar');

    if (btnPlay) {
      btnPlay.addEventListener('click', () => {
        if (!this.currentAudio) return;
        if (this.currentAudio.paused) {
          if (this.currentAudio.currentTime >= this.currentAudio.duration - 0.1) {
            this.currentAudio.currentTime = 0;
          }
          this.currentAudio.play();
          btnPlay.textContent = '⏸️';
        } else {
          this.currentAudio.pause();
          btnPlay.textContent = '▶️';
        }
      });
    }

    if (btnRewind) btnRewind.addEventListener('click', () => this.navPrevHistoryTurn());
    if (btnNext)   btnNext.addEventListener('click',   () => this.navNextHistoryTurn());

    if (seekbar) {
      seekbar.addEventListener('pointerdown', () => { this.isSeekDragging = true; });
      seekbar.addEventListener('pointerup', () => {
        this.isSeekDragging = false;
        if (this.currentAudio && this.currentAudio.duration) {
          this.currentAudio.currentTime = (parseFloat(seekbar.value) / 100) * this.currentAudio.duration;
        }
      });
      seekbar.addEventListener('input', () => {
        if (this.currentAudio && this.currentAudio.duration) {
          const t = (parseFloat(seekbar.value) / 100) * this.currentAudio.duration;
          const timeEl = document.getElementById('audio-time-display');
          if (timeEl) timeEl.textContent = `${this._fmtTime(t)} / ${this._fmtTime(this.currentAudio.duration)}`;
        }
      });
    }
  }
}

// Bootstrap application
window.addEventListener('DOMContentLoaded', () => {
  window.app = new DuoSpeakApp();
});
