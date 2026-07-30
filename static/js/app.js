/**
 * Duolingo Speak Main Application Controller
 * Handles 8 AI Characters & 10 Dynamic Topic Scenarios
 */

class DuolingoSpeakApp {
  constructor() {
    this.scenarios = [];
    this.characters = [];
    this.selectedCharacter = null;
    this.currentScenario = null;
    this.conversationHistory = [];
    this.turnCount = 0;
    this.totalXP = 150;

    this.speechHandler = null;
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
    await this.loadCharacters();
    await this.loadScenarios();
  }

  bindEvents() {
    document.getElementById('btn-close-practice').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.showScreen('scenario-screen');
    });

    document.getElementById('btn-mic-toggle').addEventListener('click', () => {
      this.speechHandler.toggleListening();
    });

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

    document.getElementById('btn-tts-play').addEventListener('click', () => {
      if (this.currentAIText) {
        this.playTTS(this.currentAIText, this.selectedCharacter ? this.selectedCharacter.tts_tld : 'com');
      }
    });

    document.getElementById('btn-toggle-translate').addEventListener('click', () => {
      const transEl = document.getElementById('ai-translation-text');
      transEl.style.display = transEl.style.display === 'block' ? 'none' : 'block';
    });

    document.getElementById('btn-continue-feedback').addEventListener('click', () => {
      this.closeFeedbackSheet();
    });

    document.getElementById('btn-victory-continue').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.showScreen('scenario-screen');
    });
  }

  async loadCharacters() {
    try {
      const res = await fetch('/api/characters');
      const data = await res.json();
      this.characters = data.characters;
      this.renderCharactersRow();
    } catch (e) {
      console.error('Failed to load characters:', e);
    }
  }

  renderCharactersRow() {
    const row = document.getElementById('characters-scroll-row');
    if (!row) return;
    row.innerHTML = '';

    this.characters.forEach((c, idx) => {
      const card = document.createElement('div');
      card.className = `character-card-mini ${idx === 0 ? 'selected' : ''}`;
      card.innerHTML = `
        <div class="character-avatar">${c.avatar_icon}</div>
        <div class="character-name">${c.name}</div>
        <span class="character-accent-badge">${c.country} • ${c.accent.split('(')[0]}</span>
      `;

      card.addEventListener('click', () => {
        if (window.duoAudio) window.duoAudio.playClick();
        document.querySelectorAll('.character-card-mini').forEach(el => el.classList.remove('selected'));
        card.classList.add('selected');
        this.selectedCharacter = c;
      });

      row.appendChild(card);
    });

    if (this.characters.length > 0) {
      this.selectedCharacter = this.characters[0];
    }
  }

  async loadScenarios() {
    try {
      const res = await fetch('/api/scenarios');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.scenarios = data.scenarios || [];
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
      const charInfo = sc.character_info || {};
      const card = document.createElement('div');
      card.className = 'scenario-card';
      card.innerHTML = `
        <div class="scenario-card-header">
          <div class="scenario-icon">${sc.icon}</div>
          <span class="badge-level" style="background:${sc.color}">${sc.level_code || 'B1'}</span>
        </div>
        <div class="scenario-title">${sc.title}</div>
        <div class="scenario-desc">${sc.description}</div>
        <div class="vocab-pills">
          <span class="vocab-pill" style="background: rgba(0,0,0,0.08); font-weight:800;">
            ${charInfo.avatar_icon || '🦉'} ${charInfo.name || 'AI Persona'} (${charInfo.country || ''})
          </span>
          ${sc.suggested_vocabulary.map(v => `<span class="vocab-pill">${v}</span>`).join('')}
        </div>
        <button class="btn-duo btn-blue" style="width:100%; margin-top: auto;">START ROLEPLAY (${sc.target_turns} TURNS)</button>
      `;

      card.addEventListener('click', () => {
        if (window.duoAudio) window.duoAudio.playClick();
        this.startScenario(sc.id, charInfo.id);
      });

      grid.appendChild(card);
    });
  }

  async startScenario(scenarioId, defaultCharId) {
    try {
      const resSc = await fetch(`/api/scenarios/${scenarioId}`);
      this.currentScenario = await resSc.json();

      // Use explicitly selected character or scenario default
      const charIdToUse = this.selectedCharacter ? this.selectedCharacter.id : defaultCharId;
      const resChar = await fetch(`/api/characters/${charIdToUse}`);
      this.selectedCharacter = await resChar.json();

      this.conversationHistory = [];
      this.turnCount = 0;

      // Update UI Header
      document.getElementById('scenario-stage-title').textContent = `${this.currentScenario.title} (${this.selectedCharacter.name})`;
      this.updateProgressBar(0);

      // Initial AI Greeting from character
      this.currentAIText = `Hello there! I'm ${this.selectedCharacter.name} from ${this.selectedCharacter.country}. Welcome to our discussion on '${this.currentScenario.title}'! How would you like to start?`;
      document.getElementById('ai-persona-name').textContent = `${this.selectedCharacter.name} (${this.selectedCharacter.accent})`;
      document.getElementById('ai-speech-text').textContent = this.currentAIText;
      document.getElementById('ai-translation-text').textContent = `Xin chào! Tôi là ${this.selectedCharacter.name}. Chào mừng bạn đến với buổi trò chuyện!`;
      document.getElementById('ai-translation-text').style.display = 'none';

      DuoMascot.renderInto('practice-mascot', 'happy');
      this.showScreen('practice-screen');

      // Auto TTS with character's accent TLD
      this.playTTS(this.currentAIText, this.selectedCharacter.tts_tld);

    } catch (e) {
      console.error('Failed to start scenario:', e);
    }
  }

  handleSpeechResult(transcript, isFinal) {
    document.getElementById('transcript-display').textContent = transcript || 'Listening...';
    if (isFinal && transcript.trim()) {
      this.submitSpokenTurn(transcript.trim());
    }
  }

  handleSpeechStateChange(state, detail) {
    const micBtn = document.getElementById('btn-mic-toggle');
    const waveform = document.getElementById('waveform-anim');
    if (state === 'listening') {
      micBtn.classList.add('recording');
      waveform.classList.add('active');
      DuoMascot.renderInto('practice-mascot', 'listening');
      document.getElementById('transcript-display').textContent = 'Listening... Speak now!';
    } else {
      micBtn.classList.remove('recording');
      waveform.classList.remove('active');
      if (state === 'stopped') DuoMascot.renderInto('practice-mascot', 'happy');
    }
  }

  async submitSpokenTurn(userText) {
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
          conversation_history: this.conversationHistory
        })
      });

      const data = await res.json();
      document.getElementById('btn-mic-toggle').disabled = false;

      // Update History
      this.conversationHistory.push({ role: 'user', content: userText });
      this.conversationHistory.push({ role: 'assistant', content: data.ai_response });

      this.turnCount++;

      // Show Feedback Sheet
      this.showFeedbackSheet(data);

      if (data.user_feedback.fluency_score >= 85 && window.duoAudio) {
        window.duoAudio.playSuccess();
      }

      this.nextTurnData = data;

    } catch (e) {
      console.error('Turn submission error:', e);
      document.getElementById('btn-mic-toggle').disabled = false;
    }
  }

  showFeedbackSheet(data) {
    const fb = data.user_feedback;
    const sheet = document.getElementById('feedback-sheet');

    const isGood = fb.fluency_score >= 85;
    sheet.className = `feedback-sheet active ${isGood ? '' : 'needs-work'}`;

    document.getElementById('feedback-title-text').textContent = isGood ? 'EXCELLENT CONTINUOUS SPEAKING!' : 'GOOD EFFORT!';
    document.getElementById('feedback-score-badge').textContent = `Fluency: ${fb.fluency_score}/100 🔥`;
    document.getElementById('native-phrasing-text').textContent = fb.native_phrasing;
    document.getElementById('feedback-xp-earned').textContent = `+${fb.xp_earned} XP`;

    DuoMascot.renderInto('practice-mascot', fb.duo_reaction || 'happy');
  }

  closeFeedbackSheet() {
    const sheet = document.getElementById('feedback-sheet');
    sheet.classList.remove('active');

    if (!this.nextTurnData) return;

    const data = this.nextTurnData;
    this.totalXP += data.user_feedback.xp_earned;
    document.getElementById('stat-xp-count').textContent = this.totalXP;

    const progressPct = Math.min(100, (this.turnCount / this.currentScenario.target_turns) * 100);
    this.updateProgressBar(progressPct);

    if (this.turnCount >= this.currentScenario.target_turns || data.is_completed) {
      if (window.duoAudio) window.duoAudio.playVictory();
      this.showVictoryScreen();
    } else {
      this.currentAIText = data.ai_response;
      document.getElementById('ai-speech-text').textContent = this.currentAIText;
      document.getElementById('ai-translation-text').textContent = data.ai_response_vi;
      document.getElementById('ai-translation-text').style.display = 'none';

      // Play TTS with character accent
      this.playTTS(this.currentAIText, this.selectedCharacter ? this.selectedCharacter.tts_tld : 'com');
    }
  }

  showVictoryScreen() {
    document.getElementById('victory-xp-earned').textContent = `+${this.turnCount * 10} XP`;
    document.getElementById('victory-turns-completed').textContent = `${this.turnCount} / ${this.currentScenario.target_turns}`;
    this.showScreen('victory-screen');
  }

  updateProgressBar(pct) {
    document.getElementById('progress-bar-fill').style.width = `${pct}%`;
  }

  playTTS(text, tld = 'com') {
    if (this.currentAudio) {
      this.currentAudio.pause();
    }
    const url = `/api/tts?text=${encodeURIComponent(text)}&tld=${encodeURIComponent(tld)}`;
    this.currentAudio = new Audio(url);
    this.currentAudio.play().catch(err => console.warn('TTS auto-play warning:', err));
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
