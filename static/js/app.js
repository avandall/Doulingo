/**
 * Duolingo Speak Application Controller
 * Features:
 * - Custom Audio Player with seekbar, play/pause, stop, rewind.
 * - Conversation History Drawer with replay + fork-from-turn.
 * - Lazy On-Demand Translation (user clicks Translate → LLM called once, cached).
 * - TTS Blob URL RAM cache (ElevenLabs called once per sentence, then 0ms replay).
 * - ElevenLabs & Edge-TTS Expressive Voice Actor Integration.
 * - Instant 0ms Word Lookup (Frontend Map + Backend RAM Cache).
 * - Copyable Conversation Transcript Log.
 */

class DuolingoSpeakApp {
  constructor() {
    this.scenarios = [];
    this.characters = [];
    this.savedWords = [];
    this.selectedCharacter = null;
    this.isUserSelectedCharacter = false;
    this.currentScenario = null;
    this.conversationHistory = [];
    this.turnCount = 0;
    this.totalXP = 150;
    this.turnScores = [];
    this.currentLevel = 1;
    this.targetLang = localStorage.getItem('duo_target_lang') || 'vi';

    this.speechHandler = null;
    this.currentAudio = null;
    this.wordCache = new Map();           // Word translation cache
    this.ttsCache = new Map();            // TTS Blob URL RAM cache
    this.sentenceTranslationCache = new Map(); // Lazy sentence translation cache
    this.historyLog = [];                 // Full conversation history with audio
    this.currentHistoryAIIdx = 0;         // Currently viewed AI turn index
    this.isSeekDragging = false;          // Seekbar drag state
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
    document.getElementById('modal-word-lookup').addEventListener('click', (e) => {
      if (e.target.id === 'modal-word-lookup') {
        document.getElementById('modal-word-lookup').classList.remove('active');
      }
    });

    // Custom Topic Modal
    document.getElementById('btn-open-custom-modal').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.openCustomTopicModal('roleplay');
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

    // QUIT PRACTICE
    document.getElementById('btn-close-practice').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.stopTTS();
      if (this.speechHandler) this.speechHandler.cancel();
      this.showScreen('scenario-screen');
    });

    // Copy AI Speech Button
    const copySpeechBtn = document.getElementById('btn-copy-ai-speech');
    if (copySpeechBtn) {
      copySpeechBtn.addEventListener('click', () => {
        const textToCopy = this.currentAIText || '';
        if (textToCopy) {
          navigator.clipboard.writeText(textToCopy);
          const oldText = copySpeechBtn.textContent;
          copySpeechBtn.textContent = '✅ Copied!';
          setTimeout(() => { copySpeechBtn.textContent = oldText; }, 1500);
        }
      });
    }

    // Lazy Translate Button
    const lazyTranslateBtn = document.getElementById('btn-lazy-translate');
    if (lazyTranslateBtn) {
      lazyTranslateBtn.addEventListener('click', () => {
        this.handleLazyTranslateTurn();
      });
    }

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

    const reviewSendBtn = document.getElementById('btn-review-send');
    if (reviewSendBtn) {
      reviewSendBtn.addEventListener('click', () => {
        const reviewInput = document.getElementById('review-speech-input');
        const val = reviewInput ? reviewInput.value.trim() : '';
        if (val) {
          if (window.duoAudio) window.duoAudio.playClick();
          const reviewBox = document.getElementById('transcript-review-box');
          if (reviewBox) reviewBox.style.display = 'none';
          if (reviewInput) reviewInput.value = '';
          this.submitSpokenTurn(val);
        }
      });
    }
    const reviewRetryBtn = document.getElementById('btn-review-retry');
    if (reviewRetryBtn) {
      reviewRetryBtn.addEventListener('click', () => {
        if (window.duoAudio) window.duoAudio.playClick();
        const reviewBox = document.getElementById('transcript-review-box');
        if (reviewBox) reviewBox.style.display = 'none';
        const reviewInput = document.getElementById('review-speech-input');
        if (reviewInput) reviewInput.value = '';
        if (this.speechHandler) {
          this.speechHandler.startListening();
        }
      });
    }
    const reviewInputEl = document.getElementById('review-speech-input');
    if (reviewInputEl) {
      reviewInputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          if (reviewSendBtn) reviewSendBtn.click();
        }
      });
    }

    // ===== AUDIO PLAYER CONTROLS =====
    this._bindAudioPlayerControls();

    // ===== HISTORY DRAWER =====
    document.getElementById('btn-open-history').addEventListener('click', () => {
      this.openHistoryDrawer();
    });
    document.getElementById('btn-close-history').addEventListener('click', () => {
      document.getElementById('history-drawer-overlay').classList.remove('active');
    });
    document.getElementById('history-drawer-overlay').addEventListener('click', (e) => {
      if (e.target === document.getElementById('history-drawer-overlay')) {
        document.getElementById('history-drawer-overlay').classList.remove('active');
      }
    });

    // Translation Toggle Button — Lazy LLM translate on demand
    document.getElementById('btn-toggle-translate').addEventListener('click', () => {
      this.toggleLazyTranslate();
    });

    // Finish & Score
    document.getElementById('btn-finish-roleplay').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.stopTTS();
      if (this.isDetInteractiveMode) {
        this.finishAndScoreDetInteractive();
      } else {
        this.finishAndScoreRoleplay();
      }
    });
    document.getElementById('btn-continue-feedback').addEventListener('click', () => {
      this.closeFeedbackSheet();
    });
    document.getElementById('btn-victory-continue').addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.showScreen('scenario-screen');
    });

    // Copy transcript
    const copyBtn = document.getElementById('btn-copy-transcript');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => this.copyTranscriptToClipboard());
    }
  }

  // =============================================
  // AUDIO PLAYER BINDING
  // =============================================
  _bindAudioPlayerControls() {
    const seekbar = document.getElementById('audio-seekbar');
    const btnPlay = document.getElementById('audio-btn-playpause');
    const btnRewind = document.getElementById('audio-btn-rewind');
    const btnNext = document.getElementById('audio-btn-next');

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

    if (btnRewind) {
      btnRewind.addEventListener('click', () => {
        this.navPrevHistoryTurn();
      });
    }

    if (btnNext) {
      btnNext.addEventListener('click', () => {
        this.navNextHistoryTurn();
      });
    }

    // Seekbar drag
    if (seekbar) {
      seekbar.addEventListener('pointerdown', () => { this.isSeekDragging = true; });
      seekbar.addEventListener('pointerup', () => {
        this.isSeekDragging = false;
        if (this.currentAudio && this.currentAudio.duration) {
          this.currentAudio.currentTime = (parseFloat(seekbar.value) / 100) * this.currentAudio.duration;
        }
      });
      seekbar.addEventListener('input', () => {
        // Preview time while dragging
        if (this.currentAudio && this.currentAudio.duration) {
          const t = (parseFloat(seekbar.value) / 100) * this.currentAudio.duration;
          document.getElementById('audio-time-display').textContent =
            `${this._fmtTime(t)} / ${this._fmtTime(this.currentAudio.duration)}`;
        }
      });
    }
    this.bindDetExamEvents();
  }

  bindDetExamEvents() {
    const btnCloseExam = document.getElementById('btn-close-det-exam');
    if (btnCloseExam) {
      btnCloseExam.addEventListener('click', () => {
        this.stopDetMonologueTimer();
        document.getElementById('modal-det-exam').classList.remove('active');
      });
    }

    const tabReadSpeak = document.getElementById('btn-tab-read-speak');
    const tabInteractive = document.getElementById('btn-tab-interactive');
    if (tabReadSpeak && tabInteractive) {
      tabReadSpeak.addEventListener('click', () => {
        tabReadSpeak.classList.add('active');
        tabInteractive.classList.remove('active');
        document.getElementById('det-view-read-speak').style.display = 'block';
        document.getElementById('det-view-interactive').style.display = 'none';
      });
      tabInteractive.addEventListener('click', () => {
        tabInteractive.classList.add('active');
        tabReadSpeak.classList.remove('active');
        document.getElementById('det-view-read-speak').style.display = 'none';
        document.getElementById('det-view-interactive').style.display = 'block';
      });
    }

    const textarea = document.getElementById('det-speech-textarea');
    if (textarea) {
      textarea.addEventListener('input', () => {
        const words = textarea.value.trim().split(/\s+/).filter(w => w.length > 0).length;
        const wcEl = document.getElementById('det-speech-word-count');
        if (wcEl) wcEl.textContent = `${words} words`;
      });
    }

    const btnStartRecord = document.getElementById('btn-det-start-record');
    if (btnStartRecord) {
      btnStartRecord.addEventListener('click', () => {
        if (this.isDetRecording) {
          this.stopDetMonologueTimer();
        } else {
          this.startDetMonologueTimer();
        }
      });
    }

    const btnSubmitSpeech = document.getElementById('btn-det-submit-speech');
    if (btnSubmitSpeech) {
      btnSubmitSpeech.addEventListener('click', () => {
        this.submitDetSpeech('read_then_speak');
      });
    }

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

    const btnCloseReport = document.getElementById('btn-det-close-report');
    if (btnCloseReport) {
      btnCloseReport.addEventListener('click', () => {
        document.getElementById('modal-det-score-report').classList.remove('active');
        document.getElementById('modal-det-exam').classList.remove('active');
        this.stopDetMonologueTimer();
        if (this.speechHandler) this.speechHandler.cancel();
        this.isDetInteractiveMode = false;
        this.showScreen('scenario-screen');
      });
    }

    const btnTryAgain = document.getElementById('btn-det-try-again');
    if (btnTryAgain) {
      btnTryAgain.addEventListener('click', () => {
        document.getElementById('modal-det-score-report').classList.remove('active');
        this.stopDetMonologueTimer();
        if (this.currentDetScenario) {
          this.openDetExamModal(this.currentDetScenario);
        }
      });
    }
  }

  openDetExamModal(sc) {
    this.currentDetScenario = sc;
    this.isDetInteractiveMode = false;
    this.stopDetMonologueTimer();

    const titleEl = document.getElementById('det-exam-title');
    const catBadgeEl = document.getElementById('det-exam-category-badge');
    if (titleEl) titleEl.textContent = sc.title || 'IELTS & CEFR Speaking Topic';
    if (catBadgeEl) catBadgeEl.textContent = `🎓 ${sc.category || 'IELTS / CEFR SPEAKING'}`;

    const cardPrompt = document.getElementById('det-card-prompt-text');
    const bulletList = document.getElementById('det-card-bullet-points');
    const qCard = sc.question_card || {};
    if (cardPrompt) cardPrompt.textContent = qCard.prompt || sc.description || 'Describe this topic in detail.';
    if (bulletList) {
      const bps = qCard.bullet_points || [
        'What the main topic or event is',
        'When and where it occurred',
        'Who was involved',
        'Why it is significant to you'
      ];
      bulletList.innerHTML = bps.map(p => `<li>${p}</li>`).join('');
    }

    const textarea = document.getElementById('det-speech-textarea');
    if (textarea) {
      textarea.value = '';
      textarea.placeholder = 'Bấm nút màu cam bên dưới để ghi âm bài nói liên tục trong 1 - 3 phút, hoặc nhập trực tiếp bài nói của bạn vào đây...';
    }
    const wcEl = document.getElementById('det-speech-word-count');
    if (wcEl) wcEl.textContent = '0 words';

    const timerEl = document.getElementById('det-monologue-timer');
    if (timerEl) timerEl.textContent = '00:00 / 03:00';
    const statusEl = document.getElementById('det-timer-status-badge');
    if (statusEl) {
      statusEl.textContent = '⏳ Speak at least 1 minute';
      statusEl.style.color = '#666';
    }
    const btnRecord = document.getElementById('btn-det-start-record');
    if (btnRecord) btnRecord.innerHTML = '🎙️ START RECORDING (GHI ÂM)';

    const tabReadSpeak = document.getElementById('btn-tab-read-speak');
    const tabInteractive = document.getElementById('btn-tab-interactive');
    if (tabReadSpeak && tabInteractive) {
      tabReadSpeak.classList.add('active');
      tabInteractive.classList.remove('active');
      document.getElementById('det-view-read-speak').style.display = 'block';
      document.getElementById('det-view-interactive').style.display = 'none';
    }

    document.getElementById('modal-det-exam').classList.add('active');
  }

  startDetMonologueTimer() {
    this.isDetRecording = true;
    this.detElapsedSeconds = 0;
    const btnRecord = document.getElementById('btn-det-start-record');
    if (btnRecord) {
      btnRecord.innerHTML = '⏹️ STOP RECORDING (DỪNG GHI ÂM)';
      btnRecord.classList.remove('btn-red');
      btnRecord.classList.add('btn-blue');
    }

    if (this.speechHandler) {
      this.speechHandler.startListening();
    }

    this.detTimerInterval = setInterval(() => {
      this.detElapsedSeconds++;
      const timerEl = document.getElementById('det-monologue-timer');
      const statusEl = document.getElementById('det-timer-status-badge');
      if (timerEl) {
        timerEl.textContent = `${this._fmtTime(this.detElapsedSeconds)} / 03:00`;
      }
      if (this.detElapsedSeconds >= 60) {
        if (statusEl) {
          statusEl.textContent = '✅ Time requirement met (1 - 3 mins)';
          statusEl.style.color = '#00843D';
        }
      }
      if (this.detElapsedSeconds >= 180) {
        this.stopDetMonologueTimer();
      }
    }, 1000);
  }

  stopDetMonologueTimer() {
    this.isDetRecording = false;
    if (this.detTimerInterval) {
      clearInterval(this.detTimerInterval);
      this.detTimerInterval = null;
    }
    const btnRecord = document.getElementById('btn-det-start-record');
    if (btnRecord) {
      btnRecord.innerHTML = '🎙️ START RECORDING (GHI ÂM)';
      btnRecord.classList.remove('btn-blue');
      btnRecord.classList.add('btn-red');
    }
    if (this.speechHandler) {
      this.speechHandler.stopListening();
    }
  }

  async submitDetSpeech(mode, overrideText) {
    this.stopDetMonologueTimer();
    const textarea = document.getElementById('det-speech-textarea');
    const speechText = overrideText || (textarea ? textarea.value.trim() : '');
    if (!speechText) {
      alert('Vui lòng ghi âm hoặc nhập nội dung bài nói trước khi nộp bài!');
      return;
    }

    const btnSubmit = document.getElementById('btn-det-submit-speech');
    const originalBtnText = btnSubmit ? btnSubmit.innerHTML : '📤 SUBMIT SPEAKING TEST';
    if (btnSubmit) {
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '⏳ AI Examiner is evaluating...';
    }

    try {
      const wordCount = speechText.trim().split(/\s+/).filter(Boolean).length;
      const durationSecs = this.detElapsedSeconds || 95;
      const wpm = Math.round((wordCount / Math.max(1, durationSecs)) * 60);
      const pauseCount = (window.duoSpeech && typeof window.duoSpeech.pauseCount === 'number') ? window.duoSpeech.pauseCount : 0;
      const fillerMatches = speechText.toLowerCase().match(/\b(uh|um|er|ah|like|you know|actually|basically|literally)\b/g);
      const fillerCount = fillerMatches ? fillerMatches.length : 0;

      const resp = await fetch('/api/det/evaluate_speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: this.currentDetScenario ? this.currentDetScenario.id : 'det_childhood_memory',
          user_speech: speechText,
          duration_seconds: durationSecs,
          mode: mode || 'read_then_speak',
          wpm: wpm,
          pause_count: pauseCount,
          filler_count: fillerCount
        })
      });
      const data = await resp.json();
      document.getElementById('modal-det-exam').classList.remove('active');
      this.renderDetScoreReport(data);
    } catch (e) {
      console.error('Error submitting DET speech:', e);
      alert('Đã xảy ra lỗi khi chấm điểm bài nói. Vui lòng thử lại!');
    } finally {
      if (btnSubmit) {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = originalBtnText;
      }
    }
  }

  renderDetScoreReport(data) {
    const scoreEl = document.getElementById('det-report-score');
    const cefrEl = document.getElementById('det-report-cefr');
    if (scoreEl) scoreEl.textContent = data.det_score || 120;
    if (cefrEl) cefrEl.textContent = data.cefr_level || 'B2 Upper-Intermediate';

    const fluencyVal = document.getElementById('det-val-fluency');
    const grammarVal = document.getElementById('det-val-grammar');
    const vocabVal = document.getElementById('det-val-vocab');
    const coherenceVal = document.getElementById('det-val-coherence');

    const fScore = data.fluency_score || 85;
    const gScore = data.grammar_score || 80;
    const vScore = data.vocabulary_score || 85;
    const cScore = data.coherence_score || 88;

    if (fluencyVal) fluencyVal.textContent = `${fScore}/100`;
    if (grammarVal) grammarVal.textContent = `${gScore}/100`;
    if (vocabVal) vocabVal.textContent = `${vScore}/100`;
    if (coherenceVal) coherenceVal.textContent = `${cScore}/100`;

    const barF = document.getElementById('det-bar-fluency');
    const barG = document.getElementById('det-bar-grammar');
    const barV = document.getElementById('det-bar-vocab');
    const barC = document.getElementById('det-bar-coherence');
    if (barF) barF.style.width = `${fScore}%`;
    if (barG) barG.style.width = `${gScore}%`;
    if (barV) barV.style.width = `${vScore}%`;
    if (barC) barC.style.width = `${cScore}%`;

    const critiqueEl = document.getElementById('det-report-critique');
    if (critiqueEl) critiqueEl.textContent = data.examiner_critique || 'Bài làm đạt yêu cầu đề bài.';

    const ac = data.acoustic_metrics || {};
    const wpmEl = document.getElementById('det-ac-wpm');
    const pausesEl = document.getElementById('det-ac-pauses');
    const fillersEl = document.getElementById('det-ac-fillers');
    const diagEl = document.getElementById('det-ac-diagnosis');
    if (wpmEl) wpmEl.textContent = `${ac.wpm || 115} WPM (${ac.pace_label || 'Tự nhiên'})`;
    if (pausesEl) pausesEl.textContent = `${ac.pause_count || 0} lần`;
    if (fillersEl) fillersEl.textContent = `${ac.filler_count || 0} từ`;
    if (diagEl) diagEl.textContent = ac.rhythm_diagnosis || 'Trôi chảy, nhịp điệu tự nhiên.';

    const upgradesContainer = document.getElementById('det-report-upgrades');
    if (upgradesContainer) {
      const ups = data.sentence_upgrades || [];
      upgradesContainer.innerHTML = ups.map(u => `
        <div class="det-upgrade-card">
          <div class="orig">❌ "${u.original || ''}"</div>
          <div class="upgr">✨ "${u.upgraded || ''}"</div>
          <div class="expl">💡 ${u.explanation || 'Nâng cấp từ vựng học thuật C1/C2.'}</div>
        </div>
      `).join('');
    }

    const sampleEl = document.getElementById('det-report-sample');
    if (sampleEl) sampleEl.textContent = data.sample_native_response || 'Sample band 160 response available soon.';

    document.getElementById('modal-det-score-report').classList.add('active');
  }

  _fmtTime(seconds) {
    const s = Math.floor(seconds % 60);
    const m = Math.floor(seconds / 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
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
    if (btnPlay) btnPlay.textContent = '⏸️'; // Show pause icon (audio plays automatically)
  }

  _updateSeekbar() {
    if (!this.currentAudio || this.isSeekDragging) return;
    const seekbar = document.getElementById('audio-seekbar');
    const timeEl = document.getElementById('audio-time-display');
    const dur = this.currentAudio.duration || 0;
    const cur = this.currentAudio.currentTime || 0;
    if (seekbar && dur > 0) {
      seekbar.value = (cur / dur) * 100;
    }
    if (timeEl) {
      timeEl.textContent = `${this._fmtTime(cur)} / ${this._fmtTime(dur)}`;
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

  _clearTTSCache() {
    // Revoke all cached Blob URLs to free RAM, then clear the cache map
    this.ttsCache.forEach((blobUrl) => {
      URL.revokeObjectURL(blobUrl);
    });
    this.ttsCache.clear();
  }

  // =============================================
  // LAZY TRANSLATION (on-demand, cached in RAM)
  // =============================================
  async toggleLazyTranslate() {
    const transEl = document.getElementById('ai-translation-text');
    const btn = document.getElementById('btn-toggle-translate');
    if (!transEl) return;

    const isVisible = transEl.style.display !== 'none' && getComputedStyle(transEl).display !== 'none';
    if (isVisible) {
      transEl.style.display = 'none';
      if (btn) btn.classList.remove('active');
      return;
    }

    // If AI already provided translation, show immediately (0 extra API calls)
    if (this.currentAITextVi) {
      transEl.textContent = this.currentAITextVi;
      transEl.style.display = 'block';
      if (btn) btn.classList.add('active');
      return;
    }

    const textToTranslate = this.currentAIText;
    if (!textToTranslate) return;

    const cacheKey = `${this.targetLang}::${textToTranslate}`;
    if (this.sentenceTranslationCache.has(cacheKey)) {
      this.currentAITextVi = this.sentenceTranslationCache.get(cacheKey);
      transEl.textContent = this.currentAITextVi;
      transEl.style.display = 'block';
      if (btn) btn.classList.add('active');
      return;
    }

    // First time user clicks Translate — call LLM once, cache result
    transEl.innerHTML = '<span class="translate-loading">\u23f3 \u0110ang d\u1ecbch...</span>';
    transEl.style.display = 'block';

    try {
      const res = await fetch('/api/translate_sentence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textToTranslate, target_lang: this.targetLang })
      });
      const data = await res.json();
      const translation = data.translation || textToTranslate;

      this.currentAITextVi = translation;
      this.sentenceTranslationCache.set(cacheKey, translation);

      // Update historyLog for current turn
      if (this.historyLog.length > 0) {
        const last = this.historyLog[this.historyLog.length - 1];
        if (last.role === 'ai' && last.textEn === textToTranslate) {
          last.textVi = translation;
        }
      }

      transEl.textContent = translation;
      if (btn) btn.classList.add('active');

    } catch (e) {
      transEl.textContent = textToTranslate;
      console.warn('Lazy translate failed:', e);
    }
  }

  // =============================================
  // CONVERSATION HISTORY TURN NAVIGATION (RAM CACHE)
  // =============================================
  _getLatestAITurnIndex() {
    for (let i = this.historyLog.length - 1; i >= 0; i--) {
      if (this.historyLog[i] && this.historyLog[i].role === 'ai') return i;
    }
    return -1;
  }

  navPrevHistoryTurn() {
    let prevIdx = -1;
    for (let i = this.currentHistoryAIIdx - 1; i >= 0; i--) {
      if (this.historyLog[i] && this.historyLog[i].role === 'ai') {
        prevIdx = i;
        break;
      }
    }
    if (prevIdx === -1) {
      this._showForkToast('🕒 Đây là lượt đầu tiên của hội thoại!');
      return;
    }
    this._navToHistoryAITurn(prevIdx);
  }

  navNextHistoryTurn() {
    let nextIdx = -1;
    for (let i = this.currentHistoryAIIdx + 1; i < this.historyLog.length; i++) {
      if (this.historyLog[i] && this.historyLog[i].role === 'ai') {
        nextIdx = i;
        break;
      }
    }
    if (nextIdx === -1) {
      this._showForkToast('🕒 Đây là lượt mới nhất của hội thoại!');
      return;
    }
    this._navToHistoryAITurn(nextIdx);
  }

  _navToHistoryAITurn(idx) {
    const entry = this.historyLog[idx];
    if (!entry || entry.role !== 'ai') return;
    this.currentHistoryAIIdx = idx;

    const isLatest = (idx === this._getLatestAITurnIndex());

    this.currentAIText = entry.textEn;
    this.currentAITextVi = entry.textVi || '';
    this.renderInteractiveAIText(entry.textEn);

    const transEl = document.getElementById('ai-translation-text');
    const btnTranslate = document.getElementById('btn-toggle-translate');
    if (transEl) {
      transEl.textContent = entry.textVi || '';
      transEl.style.display = 'none';
      if (btnTranslate) btnTranslate.classList.remove('active');
    }

    if (isLatest) {
      document.getElementById('current-turns-count').textContent = `Turns: ${this.turnCount} (Unlimited)`;
      document.getElementById('transcript-display').textContent = 'Tap mic to respond!';
    } else {
      document.getElementById('current-turns-count').textContent = `Turn ${entry.turnNum} (Past — speak to fork from here)`;
      document.getElementById('transcript-display').textContent = `Tap mic to respond from Turn ${entry.turnNum}...`;
      this._showForkToast(`↩️ Đang xem Turn ${entry.turnNum} (lưu trong cache RAM)`);
    }

    const charId = this.selectedCharacter ? this.selectedCharacter.id : 'lily';
    this.playTTS(entry.textEn, charId);
  }

  // =============================================
  // CONVERSATION HISTORY DRAWER
  // =============================================
  openHistoryDrawer() {
    this._renderHistoryDrawer();
    document.getElementById('history-drawer-overlay').classList.add('active');
  }

  _renderHistoryDrawer() {
    const body = document.getElementById('history-drawer-body');
    if (!body) return;
    body.innerHTML = '';

    if (this.historyLog.length === 0) {
      body.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-weight:700;padding:30px 0;font-size:14px;">No conversation yet!</div>';
      return;
    }

    this.historyLog.forEach((entry, idx) => {
      const card = document.createElement('div');
      const isCurrentTurn = idx === this.historyLog.length - 1;
      card.className = `history-turn-card${isCurrentTurn ? ' current-turn' : ''}`;
      const isAI = entry.role === 'ai';
      const charName = this.selectedCharacter ? this.selectedCharacter.name : 'AI';
      const charIcon = this.selectedCharacter ? (this.selectedCharacter.avatar_icon || '🤖') : '🤖';

      card.style.textAlign = 'left';

      card.innerHTML = `
        <div class="history-turn-label" style="justify-content: flex-start;">
          <span class="turn-badge ${isAI ? '' : 'user-badge'}">${isAI ? `${charIcon} ${charName}` : '👤 You'}</span>
          <span>Turn ${entry.turnNum}</span>
          ${isCurrentTurn ? '<span class="turn-badge current-badge">NOW</span>' : ''}
        </div>
        <div class="${isAI ? 'history-turn-text-en' : 'history-turn-text-user'}" style="text-align: left;">"${entry.textEn}"</div>
        ${isAI && entry.textVi ? `<div class="history-turn-text-vi" style="text-align: left;">🇻🇳 "${entry.textVi}"</div>` : ''}
        ${isAI ? `<div class="history-turn-actions" style="justify-content: flex-start;">
          <button class="btn-history-action" data-idx="${idx}" data-action="replay">🔊 Nghe lại</button>
          <button class="btn-history-action fork-btn" data-idx="${idx}" data-action="fork">↩️ Nói lại từ đây</button>
        </div>` : ''}
      `;
      body.appendChild(card);
    });

    body.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const idx = parseInt(e.currentTarget.getAttribute('data-idx'));
        const action = e.currentTarget.getAttribute('data-action');
        if (action === 'replay') this.replayFromHistory(idx);
        if (action === 'fork') this.forkFromHistory(idx);
      });
    });

    setTimeout(() => { body.scrollTop = body.scrollHeight; }, 50);
  }

  replayFromHistory(idx) {
    document.getElementById('history-drawer-overlay').classList.remove('active');
    this._navToHistoryAITurn(idx);
  }

  forkFromHistory(idx) {
    const entry = this.historyLog[idx];
    if (!entry || entry.role !== 'ai') return;

    if (!confirm(`↩️ Quay lại Turn ${entry.turnNum} và nói lại?\n\nCác lượt sau đó sẽ bị xóa.`)) return;

    document.getElementById('history-drawer-overlay').classList.remove('active');

    this.conversationHistory = this.conversationHistory.slice(0, idx + 1);
    this.historyLog = this.historyLog.slice(0, idx + 1);
    this.turnCount = Math.floor(idx / 2) + 1;
    this.currentHistoryAIIdx = idx;

    this.currentAIText = entry.textEn;
    this.currentAITextVi = entry.textVi || '';
    this.renderInteractiveAIText(entry.textEn);

    const transEl = document.getElementById('ai-translation-text');
    if (transEl) {
      transEl.textContent = entry.textVi || '';
      transEl.style.display = entry.textVi ? 'block' : 'none';
    }

    document.getElementById('current-turns-count').textContent = `Turns: ${this.turnCount} (Unlimited)`;
    this.updateProgressBar();
    this.playTTS(entry.textEn, this.selectedCharacter ? this.selectedCharacter.id : 'lily');
    this._showForkToast(`↩️ Đã quay lại Turn ${entry.turnNum} — hãy nói lại!`);
    document.getElementById('btn-mic-toggle').disabled = false;
    document.getElementById('transcript-display').textContent = 'Tap mic to respond again from this point!';
  }

  updateProgressBar() {
    const fillEl = document.getElementById('lesson-progress-fill');
    const textEl = document.getElementById('lesson-progress-text');
    if (!fillEl || !textEl) return;

    const targetTurns = this.isDetInteractiveMode ? (this.detMaxTurns || 5) : 5;
    const pct = Math.min(100, Math.round((this.turnCount / targetTurns) * 100));

    fillEl.style.width = `${pct}%`;
    textEl.textContent = `${pct}%`;
  }

  _showForkToast(msg) {
    const toast = document.getElementById('fork-toast');
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2800);
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
      this.initCategoryFilterBar();
      this.renderScenarios(this.currentIeltsCategory || 'all', this.currentRoleplayCategory || 'all');
    } catch (e) {
      console.error('Failed to load scenarios:', e);
    }
  }

  initCategoryFilterBar() {
    const ieltsBar = document.getElementById('ielts-category-filter-bar');
    if (ieltsBar) {
      const buttons = ieltsBar.querySelectorAll('.cat-pill');
      buttons.forEach(btn => {
        btn.addEventListener('click', () => {
          if (window.duoAudio) window.duoAudio.playClick();
          buttons.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          this.currentIeltsCategory = btn.dataset.ieltsCat || 'all';
          this.renderScenarios(this.currentIeltsCategory, this.currentRoleplayCategory || 'all');
        });
      });
    }

    const roleplayBar = document.getElementById('roleplay-category-filter-bar');
    if (roleplayBar) {
      const buttons = roleplayBar.querySelectorAll('.cat-pill');
      buttons.forEach(btn => {
        btn.addEventListener('click', () => {
          if (window.duoAudio) window.duoAudio.playClick();
          buttons.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          this.currentRoleplayCategory = btn.dataset.roleplayCat || 'all';
          this.renderScenarios(this.currentIeltsCategory || 'all', this.currentRoleplayCategory);
        });
      });
    }
  }

  openCustomTopicModal(targetSection = 'roleplay') {
    this.customTopicTargetSection = targetSection;
    const modal = document.getElementById('modal-custom-topic');
    if (!modal) return;

    const titleEl = modal.querySelector('h2');
    const descEl = modal.querySelector('p');
    const inputTitle = document.getElementById('custom-topic-title');
    const inputDesc = document.getElementById('custom-topic-desc');

    if (targetSection === 'ielts') {
      if (titleEl) titleEl.textContent = '➕ Tạo Đề Thi IELTS Speaking Mới';
      if (descEl) descEl.textContent = 'Thêm chủ đề thi IELTS với chấm điểm tự động 4 tiêu chí & đề xuất nâng cấp C1/C2';
      if (inputTitle) inputTitle.placeholder = 'e.g. Discussing Artificial Intelligence in Education...';
      if (inputDesc) inputDesc.placeholder = 'e.g. Describe how AI affects students and teachers...';
    } else {
      if (titleEl) titleEl.textContent = '➕ Tạo Chủ Đề Roleplay Giao Tiếp Mới';
      if (descEl) descEl.textContent = 'Thêm tình huống hội thoại thực tế hàng ngày cùng nhân vật AI';
      if (inputTitle) inputTitle.placeholder = 'e.g. Ordering Coffee at a Busy Café...';
      if (inputDesc) inputDesc.placeholder = 'e.g. Chatting with barista about specials & pastry choices...';
    }

    if (inputTitle) inputTitle.value = '';
    if (inputDesc) inputDesc.value = '';
    modal.classList.add('active');
  }

  createAddTopicCard(targetSection, label, sublabel) {
    const card = document.createElement('div');
    card.className = 'scenario-card add-topic-card';
    card.style.cssText = 'border: 2px dashed rgba(160, 160, 160, 0.45); background: rgba(160, 160, 160, 0.04); display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; cursor: pointer; min-height: 200px; transition: all 0.25s ease; padding: 20px; border-radius: 20px;';
    card.innerHTML = `
      <div style="font-size: 52px; color: rgba(160, 160, 160, 0.55); font-weight: 300; line-height: 1; margin-bottom: 8px;">+</div>
      <div style="font-weight: 800; font-size: 15px; color: var(--text-color); opacity: 0.85;">${label}</div>
      <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px; font-weight: 600;">${sublabel}</div>
    `;
    card.addEventListener('mouseover', () => {
      card.style.borderColor = targetSection === 'ielts' ? '#FF4B4B' : '#1CB0F6';
      card.style.background = targetSection === 'ielts' ? 'rgba(255, 75, 75, 0.06)' : 'rgba(28, 176, 246, 0.06)';
    });
    card.addEventListener('mouseout', () => {
      card.style.borderColor = 'rgba(160, 160, 160, 0.45)';
      card.style.background = 'rgba(160, 160, 160, 0.04)';
    });
    card.addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      this.openCustomTopicModal(targetSection);
    });
    return card;
  }

  createScenarioCardElement(sc) {
    const card = document.createElement('div');
    card.className = 'scenario-card';
    const isDet = (sc.id || '').startsWith('det_') || sc.mode === 'ielts_exam';
    const badgeColor = isDet ? '#FF4B4B' : '#1CB0F6';
    card.innerHTML = `
      <div class="scenario-card-header">
        <div class="scenario-icon">${sc.icon || '💬'}</div>
        <span class="scenario-cat-badge" style="background-color: ${badgeColor}18; color: ${badgeColor}; font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 99px; text-transform: uppercase;">${sc.category || 'Everyday'}</span>
      </div>
      <div class="scenario-title">${sc.title} ${sc.is_custom ? '✨' : ''}</div>
      <div class="scenario-desc">${sc.description}</div>
      <button class="btn-duo ${isDet ? 'btn-red' : 'btn-blue'}" style="width:100%; margin-top: auto;">${isDet ? 'IELTS / CEFR EXAM' : 'START ROLEPLAY'}</button>
    `;

    card.addEventListener('click', () => {
      if (window.duoAudio) window.duoAudio.playClick();
      if (isDet) {
        this.openDetExamModal(sc);
      } else {
        this.startScenario(sc.id);
      }
    });

    return card;
  }

  renderScenarios(ieltsCat = 'all', roleplayCat = 'all') {
    const ieltsGrid = document.getElementById('ielts-scenarios-grid');
    const roleplayGrid = document.getElementById('roleplay-scenarios-grid');
    if (!ieltsGrid || !roleplayGrid) return;

    ieltsGrid.innerHTML = '';
    roleplayGrid.innerHTML = '';

    const isIeltsScenario = (sc) => (sc.id || '').startsWith('det_') || sc.mode === 'ielts_exam';

    const ieltsScenarios = this.scenarios.filter(sc => {
      if (!isIeltsScenario(sc)) return false;
      if (ieltsCat === 'all') return true;
      return sc.category === ieltsCat;
    });

    const roleplayScenarios = this.scenarios.filter(sc => {
      if (isIeltsScenario(sc)) return false;
      if (roleplayCat === 'all') return true;
      return sc.category === roleplayCat;
    });

    // Render IELTS cards with plus card at the end of section
    const ieltsCardElements = ieltsScenarios.map(sc => this.createScenarioCardElement(sc));
    const addIeltsCard = this.createAddTopicCard('ielts', '➕ Thêm chủ đề thi IELTS', 'Bấm vào để tạo đề thi IELTS tự do');
    ieltsCardElements.push(addIeltsCard);
    ieltsCardElements.forEach(cardEl => ieltsGrid.appendChild(cardEl));

    // Render Roleplay cards with plus card at the end of section
    const roleplayCardElements = roleplayScenarios.map(sc => this.createScenarioCardElement(sc));
    const addRoleplayCard = this.createAddTopicCard('roleplay', '➕ Thêm chủ đề Roleplay', 'Bấm vào để tạo tình huống tự do');
    roleplayCardElements.push(addRoleplayCard);
    roleplayCardElements.forEach(cardEl => roleplayGrid.appendChild(cardEl));
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

    const isIelts = this.customTopicTargetSection === 'ielts';

    const payload = {
      title: title,
      category: isIelts ? 'Personal & Family' : 'Everyday Roleplay',
      icon: iconInput.value.trim() || (isIelts ? '🎓' : '💬'),
      color: isIelts ? '#FF4B4B' : '#1CB0F6',
      level: isIelts ? 'Upper Intermediate' : 'Beginner',
      level_code: isIelts ? 'B2' : 'A2',
      default_character: 'lily',
      description: descInput.value.trim() || (isIelts ? 'Custom IELTS Speaking topic.' : 'Custom everyday roleplay topic.'),
      objective: isIelts ? 'Demonstrate fluency, lexical resource, and accuracy.' : 'Practice speaking freely.',
      suggested_vocabulary: isIelts ? ['Fluency', 'Lexical resource', 'Coherence'] : ['Everyday conversation', 'Free chat'],
      mode: isIelts ? 'ielts_exam' : 'roleplay'
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
      payload.id = isIelts ? `det_custom_${Date.now()}` : `custom_${Date.now()}`;
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
      this.historyLog = [];
      this.sentenceTranslationCache.clear();

      this.stopTTS();
      // Clear TTS cache from previous session to free RAM
      this._clearTTSCache();

      // Calculate maxTurns for IELTS Exam Interactive mode (level dependent: L1-5: 4 turns, L6-10: 6 turns, L11-15: 8 turns, L16-20: 10 turns)
      const maxTurns = this.isDetInteractiveMode
        ? (this.currentLevel <= 5 ? 4 : this.currentLevel <= 10 ? 6 : this.currentLevel <= 15 ? 8 : 10)
        : null;
      this.detMaxTurns = maxTurns;

      // Update Header
      const titlePrefix = this.isDetInteractiveMode ? '🎓 IELTS Interactive Speaking' : this.currentScenario.title;
      document.getElementById('scenario-stage-title').textContent = `${titlePrefix} (${this.selectedCharacter.name}) - Lvl ${this.currentLevel}`;
      document.getElementById('current-turns-count').textContent = this.isDetInteractiveMode
        ? `Turns: 0 / ${maxTurns} (IELTS Exam)`
        : 'Turns: 0 (Unlimited)';
      this.updateProgressBar();

      const btnFinish = document.getElementById('btn-finish-roleplay');
      if (btnFinish) {
        btnFinish.innerHTML = this.isDetInteractiveMode ? '🏁 KẾT THÚC & CHẤM ĐIỂM' : '🏁 FINISH';
      }

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
      this.initialAIText = startData.ai_response;
      this.initialAITextVi = startData.ai_response_vi || '';

      this.renderInteractiveAIText(this.currentAIText);
      document.getElementById('ai-translation-text').textContent = this.currentAITextVi;
      document.getElementById('ai-translation-text').style.display = 'none';
      const labelEl = document.getElementById('btn-lazy-translate-label');
      if (labelEl) labelEl.textContent = 'Gợi ý / Dịch';

      this.conversationHistory.push({ role: 'assistant', content: this.currentAIText });
      this.historyLog.push({
        turnNum: 1,
        role: 'ai',
        textEn: this.currentAIText,
        textVi: this.currentAITextVi
      });
      this.currentHistoryAIIdx = 0;

      // Play Neural Voice TTS
      this.playTTS(this.currentAIText, this.selectedCharacter.id);

    } catch (e) {
      console.error('Failed to start scenario:', e);
    }
  }

  async handleLazyTranslateTurn() {
    const transEl = document.getElementById('ai-translation-text');
    const labelEl = document.getElementById('btn-lazy-translate-label');
    if (!transEl) return;

    if (transEl.style.display !== 'none' && transEl.textContent.trim() !== '' && transEl.textContent !== '⏳ Đang dịch câu thoại...') {
      transEl.style.display = 'none';
      if (labelEl) labelEl.textContent = 'Gợi ý / Dịch';
      return;
    }

    if (this.currentAITextVi && this.currentAITextVi.trim() !== '') {
      transEl.textContent = this.currentAITextVi;
      transEl.style.display = 'block';
      if (labelEl) labelEl.textContent = 'Ẩn bản dịch';
      return;
    }

    transEl.textContent = '⏳ Đang dịch câu thoại...';
    transEl.style.display = 'block';
    if (labelEl) labelEl.textContent = 'Đang dịch...';

    try {
      const recentContext = this.historyLog.slice(-3).map(item => item.textEn).filter(Boolean);
      const res = await fetch('/api/translate_sentence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: this.currentAIText,
          target_lang: 'vi',
          character_name: this.selectedCharacter ? this.selectedCharacter.name : '',
          scenario_title: this.currentScenario ? this.currentScenario.title : '',
          context_history: recentContext
        })
      });
      const data = await res.json();
      if (data && data.translation) {
        this.currentAITextVi = data.translation;
        transEl.textContent = data.translation;
        transEl.style.display = 'block';
        if (labelEl) labelEl.textContent = 'Ẩn bản dịch';

        if (this.historyLog.length > 0 && this.historyLog[this.historyLog.length - 1].role === 'ai') {
          this.historyLog[this.historyLog.length - 1].textVi = data.translation;
        }
        if (this.turnScores.length > 0) {
          this.turnScores[this.turnScores.length - 1].aiResponseVi = data.translation;
        }
      } else {
        transEl.textContent = 'Không thể dịch câu này.';
        if (labelEl) labelEl.textContent = 'Gợi ý / Dịch';
      }
    } catch (e) {
      console.error('Lazy translation failed:', e);
      transEl.textContent = 'Lỗi kết nối khi dịch.';
      if (labelEl) labelEl.textContent = 'Gợi ý / Dịch';
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
        let touched = false;
        tokenSpan.addEventListener('touchend', (e) => {
          e.stopPropagation();
          e.preventDefault();
          touched = true;
          this.lookupWord(cleanWord);
        }, { passive: false });
        tokenSpan.addEventListener('click', (e) => {
          if (touched) {
            touched = false;
            return;
          }
          e.stopPropagation();
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
    if (this.isDetRecording) {
      const textarea = document.getElementById('det-speech-textarea');
      if (textarea && transcript && transcript.trim()) {
        textarea.value = transcript.trim();
        const words = textarea.value.trim().split(/\s+/).filter(w => w.length > 0).length;
        const wcEl = document.getElementById('det-speech-word-count');
        if (wcEl) wcEl.textContent = `${words} words`;
      }
      return;
    }
    document.getElementById('transcript-display').textContent = `"${transcript}"` || 'Listening...';
    if (isFinal && transcript.trim()) {
      const reviewBox = document.getElementById('transcript-review-box');
      const reviewInput = document.getElementById('review-speech-input');
      if (reviewBox && reviewInput) {
        reviewInput.value = transcript.trim();
        reviewBox.style.display = 'block';
        reviewInput.focus();
        document.getElementById('transcript-display').textContent = '👀 Kiểm tra câu bạn vừa nói bên dưới trước khi bấm "GỬI CÂU NÀY" (hoặc chạm vào để sửa nếu máy nghe sai):';
      } else {
        this.submitSpokenTurn(transcript.trim());
      }
    }
  }

  handleSpeechStateChange(state, detail) {
    const micBtn = document.getElementById('btn-mic-toggle');
    const cancelBtn = document.getElementById('btn-cancel-mic');
    const waveform = document.getElementById('waveform-anim');
    const reviewBox = document.getElementById('transcript-review-box');

    if (state === 'listening') {
      if (reviewBox) reviewBox.style.display = 'none';
      micBtn.classList.add('recording');
      waveform.classList.add('active');
      if (cancelBtn) cancelBtn.style.display = 'inline-flex';
      DuoMascot.renderInto('practice-mascot', 'listening');
      document.getElementById('transcript-display').textContent = '🎙️ Recording... Tap mic again when done to review!';
    } else if (state === 'cancelled') {
      if (reviewBox) reviewBox.style.display = 'none';
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

    const latestIdx = this._getLatestAITurnIndex();
    if (this.currentHistoryAIIdx >= 0 && this.currentHistoryAIIdx < latestIdx) {
      const idx = this.currentHistoryAIIdx;
      this.conversationHistory = this.conversationHistory.slice(0, idx + 1);
      this.historyLog = this.historyLog.slice(0, idx + 1);
      this.turnCount = Math.floor(idx / 2) + 1;
    }

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

      const nextTurnNum = this.turnCount + 1;
      this.historyLog.push({
        turnNum: nextTurnNum,
        role: 'user',
        textEn: userText,
        textVi: ''
      });
      this.historyLog.push({
        turnNum: nextTurnNum + 1,
        role: 'ai',
        textEn: data.ai_response,
        textVi: data.ai_response_vi || ''
      });
      this.currentHistoryAIIdx = this.historyLog.length - 1;

      this.turnCount++;
      if (this.isDetInteractiveMode) {
        document.getElementById('current-turns-count').textContent = `Turns: ${this.turnCount} / ${this.detMaxTurns} (IELTS Exam)`;
        if (this.turnCount >= this.detMaxTurns) {
          setTimeout(() => {
            alert(`🏆 Bạn đã hoàn thành đủ ${this.detMaxTurns} lượt trả lời của bài thi IELTS Interactive Speaking! Hệ thống đang tổng hợp và chấm điểm chính thức...`);
            this.finishAndScoreDetInteractive();
          }, 600);
        }
      } else {
        document.getElementById('current-turns-count').textContent = `Turns: ${this.turnCount} (Unlimited)`;
      }
      this.updateProgressBar();

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
    let sheetClass = '';
    let titleText = 'GREAT CONTINUOUS SPEAKING!';

    if (score >= 90) {
      sheetClass = '';
      titleText = 'GREAT CONTINUOUS SPEAKING!';
    } else if (score >= 80) {
      sheetClass = 'suggestion';
      titleText = 'LIGHT GRAMMAR SUGGESTION 💡';
    } else {
      sheetClass = 'needs-work';
      titleText = 'GOOD EFFORT! KEEP PRACTICING!';
    }

    sheet.className = `feedback-sheet active ${sheetClass}`;

    document.getElementById('feedback-title-text').textContent = titleText;
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
    const labelEl = document.getElementById('btn-lazy-translate-label');
    if (labelEl) labelEl.textContent = 'Gợi ý / Dịch';

    // Play Neural Voice TTS
    this.playTTS(this.currentAIText, this.selectedCharacter ? this.selectedCharacter.id : 'lily');
  }

  finishAndScoreDetInteractive() {
    this.stopTTS();
    if (this.turnScores.length === 0 && this.conversationHistory.length === 0) {
      alert('Bạn cần trả lời ít nhất 1 câu hỏi trước khi nộp bài thi IELTS Interactive Speaking!');
      return;
    }
    const userSpeech = this.conversationHistory
      .filter(t => t.role === 'user' || t.speaker === 'User')
      .map(t => t.content || t.text)
      .join(' . ');
    const speechToEval = userSpeech.trim() || (this.turnScores.map(ts => ts.userText).join(' . '));
    this.submitDetSpeech('interactive_speaking', speechToEval || 'Candidate completed interactive speaking turns.');
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

    // Render Opening Question (Turn 0 - Start of Conversation)
    if (this.initialAIText) {
      const charName = this.selectedCharacter ? this.selectedCharacter.name : 'AI';
      const charIcon = this.selectedCharacter ? (this.selectedCharacter.avatar_icon || '🤖') : '🤖';

      const openItem = document.createElement('div');
      openItem.className = 'score-turn-item';
      openItem.style.display = 'flex';
      openItem.style.flexDirection = 'column';
      openItem.style.alignItems = 'stretch';
      openItem.style.gap = '8px';
      openItem.style.padding = '14px 18px';
      openItem.style.width = '100%';

      openItem.innerHTML = `
        <div style="width: 100%; display:flex; justify-content:center; align-items:center; gap: 20px; border-bottom: 1px dashed rgba(0,0,0,0.1); padding-bottom: 8px; margin-bottom: 4px; text-align: center;">
          <span style="color: var(--duo-blue); font-weight:800; font-size: 15px;">Turn 0 — Start</span>
          <span style="color: var(--duo-green); font-weight:800; font-size: 15px;">AI Opening Question</span>
        </div>
        <div style="width: 100%; font-size: 15px; color: var(--duo-green-dark); text-align: left; line-height: 1.5; align-self: flex-start;">
          <strong>${charIcon} ${charName}:</strong> "${this.initialAIText}"
        </div>
        ${this.initialAITextVi ? `<div style="width: 100%; font-size: 14px; color: var(--text-muted); font-style: italic; text-align: left; line-height: 1.4; align-self: flex-start;">🇻🇳 Dịch: "${this.initialAITextVi}"</div>` : ''}
      `;
      scoresContainer.appendChild(openItem);
    }

    this.turnScores.forEach(ts => {
      const item = document.createElement('div');
      item.className = 'score-turn-item';
      item.style.display = 'flex';
      item.style.flexDirection = 'column';
      item.style.alignItems = 'stretch';
      item.style.gap = '8px';
      item.style.padding = '14px 18px';
      item.style.width = '100%';

      const charName = this.selectedCharacter ? this.selectedCharacter.name : 'AI';
      const charIcon = this.selectedCharacter ? (this.selectedCharacter.avatar_icon || '🤖') : '🤖';

      item.innerHTML = `
        <div style="width: 100%; display:flex; justify-content:center; align-items:center; gap: 20px; border-bottom: 1px dashed rgba(0,0,0,0.1); padding-bottom: 8px; margin-bottom: 4px; text-align: center;">
          <span style="color: var(--duo-blue); font-weight:800; font-size: 15px;">Turn ${ts.turn}</span>
          <span style="color: ${ts.overall >= 85 ? 'var(--duo-green)' : 'var(--duo-orange)'}; font-weight:800; font-size: 15px;">Score: ${ts.overall}/100</span>
        </div>
        <div style="width: 100%; font-size: 15px; text-align: left; line-height: 1.5; color: var(--text-dark); align-self: flex-start;">
          <strong>👤 You:</strong> "${ts.userText}"
        </div>
        <div style="width: 100%; font-size: 15px; color: var(--duo-green-dark); text-align: left; line-height: 1.5; align-self: flex-start;">
          <strong>${charIcon} ${charName}:</strong> "${ts.aiResponse}"
        </div>
        ${ts.aiResponseVi ? `<div style="width: 100%; font-size: 14px; color: var(--text-muted); font-style: italic; text-align: left; line-height: 1.4; align-self: flex-start;">🇻🇳 Dịch: "${ts.aiResponseVi}"</div>` : ''}
        ${ts.nativePhrasing ? `<div style="width: 100%; font-size: 14px; color: var(--duo-purple); font-weight:700; text-align: left; line-height: 1.4; align-self: flex-start;">💡 Native Tip: "${ts.nativePhrasing}"</div>` : ''}
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

  _setupAudioPlayback(audioUrl) {
    this.currentAudio = new Audio(audioUrl);
    this.currentAudio.addEventListener('loadedmetadata', () => {
      this._setPlayerReady();
      this._updateSeekbar();
    });
    this.currentAudio.addEventListener('timeupdate', () => {
      this._updateSeekbar();
    });
    this.currentAudio.addEventListener('ended', () => {
      const btnPlay = document.getElementById('audio-btn-playpause');
      if (btnPlay) btnPlay.textContent = '▶️';
    });
    this.currentAudio.play().then(() => {
      this._setPlayerReady();
    }).catch(err => {
      console.warn('TTS playback error:', err);
      this._setPlayerReady();
    });
  }

  async playTTS(text, charId = 'lily') {
    this.stopTTS();
    this._setPlayerLoading();

    const cacheKey = `${charId}::${text}`;

    // If we already fetched this audio blob, play from RAM (zero API call)
    if (this.ttsCache.has(cacheKey)) {
      this._setupAudioPlayback(this.ttsCache.get(cacheKey));
      return;
    }

    // First time: fetch from API, convert to Blob URL, cache it in RAM
    try {
      const url = `/api/tts?text=${encodeURIComponent(text)}&char_id=${encodeURIComponent(charId)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`TTS HTTP ${res.status}`);

      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);

      // Cache the blob URL — next time Voice button is pressed, plays instantly
      this.ttsCache.set(cacheKey, blobUrl);

      this._setupAudioPlayback(blobUrl);
    } catch (err) {
      console.warn('TTS fetch failed, falling back to direct src:', err);
      // Fallback: use src directly (old behavior) if fetch itself fails
      const url = `/api/tts?text=${encodeURIComponent(text)}&char_id=${encodeURIComponent(charId)}`;
      this._setupAudioPlayback(url);
    }
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
