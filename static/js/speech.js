/**
 * Speech Recognition & Microphone Visualizer Controller
 * Features:
 * - Manual Toggle Mode: Speech recording NEVER auto-stops when hesitating!
 * - Cancel Button: Allows user to discard recording anytime without sending.
 * - Mobile PWA Compatible (Android Chrome & iOS Safari).
 */
class SpeechHandler {
  constructor(onResultCallback, onStateChangeCallback) {
    this.recognition = null;
    this.isListening = false;
    this.isCancelled = false;
    this.onResult = onResultCallback;
    this.onStateChange = onStateChangeCallback;
    this.finalTranscript = '';
    this.lastRecognizedText = '';
    this.isTranscribing = false;
    this.isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    
    // Audio Engine State Machine (TASK-004)
    // States: LEGACY_FALLBACK -> WASM_LOADING -> WASM_STAGED -> WASM_ACTIVE
    // Upgrade to WASM_ACTIVE is ONLY permitted when micState is IDLE
    this.audioEngineState = 'LEGACY_FALLBACK';
    this.micState = 'IDLE'; // 'IDLE' | 'RECORDING'
    this.accumulatedVoicedDurationMs = 0;
    this.silenceTimer = null;
    this.vadInterval = null;
    this.lastAcousticVoiceTime = null;

    this._initSpeech();
    this._stageAudioEngine();
  }

  _stageAudioEngine() {
    // Simulate/stage loading WASM module in background without blocking audio stream
    if (typeof WebAssembly !== 'undefined') {
      this.audioEngineState = 'WASM_LOADING';
      // Simulate WASM module staged once ready
      setTimeout(() => {
        this.audioEngineState = 'WASM_STAGED';
        this._tryUpgradeAudioEngine();
      }, 500);
    }
  }

  _tryUpgradeAudioEngine() {
    // Inviolable Rule: Upgrade from WASM_STAGED to WASM_ACTIVE is ONLY permitted when mic is IDLE!
    if (this.audioEngineState === 'WASM_STAGED' && this.micState === 'IDLE') {
      this.audioEngineState = 'WASM_ACTIVE';
      console.log('[SpeechHandler] Audio Engine safely upgraded to WASM_ACTIVE (mic is IDLE)');
    }
  }

  _resetAcousticVAD() {
    this.accumulatedVoicedDurationMs = 0;
    this.lastAcousticVoiceTime = Date.now();
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
    if (this.vadInterval) {
      clearInterval(this.vadInterval);
      this.vadInterval = null;
    }
  }

  _startAcousticVADMonitor() {
    this._resetAcousticVAD();
    const SILENCE_TIMEOUT_MS = 3500; // 3.5s silence threshold
    const MIN_VOICED_DURATION_MS = 1500; // 1.5s real speech threshold

    this.vadInterval = setInterval(() => {
      if (this.micState !== 'RECORDING' || !this.isListening) return;

      const now = Date.now();
      const silenceDuration = now - (this.lastAcousticVoiceTime || now);

      if (silenceDuration >= SILENCE_TIMEOUT_MS) {
        if (this.accumulatedVoicedDurationMs >= MIN_VOICED_DURATION_MS) {
          console.log(`[SpeechHandler VAD] Silence >= ${SILENCE_TIMEOUT_MS}ms with voiced ${this.accumulatedVoicedDurationMs}ms >= 1500ms. Auto-submitting.`);
          this._resetAcousticVAD();
          this.stopAndSubmit();
        } else {
          // False trigger / noise / breathing (<1.5s actual speech) -> reset silence timer, don't stop mic
          console.log(`[SpeechHandler VAD] Silence detected but voiced duration ${this.accumulatedVoicedDurationMs}ms < 1500ms (noise/cough/breath). Resetting timer.`);
          this.lastAcousticVoiceTime = now;
        }
      }
    }, 200);
  }

  _initSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      
      this.recognition.continuous = true;
      this.recognition.interimResults = false;
      this.recognition.maxAlternatives = 5;
      this.recognition.lang = 'en-US';

      this.recognition.onstart = () => {
        this.isListening = true;
        this.micState = 'RECORDING';
        this.isCancelled = false;
        this.finalTranscript = '';
        this.lastRecognizedText = '';
        this._startAcousticVADMonitor();
        if (this.onStateChange) this.onStateChange('listening');
        if (window.duoAudio) window.duoAudio.playMicStart();
        // BARGE-IN: Immediately cut off any running bot TTS or filler when user begins speaking
        if (window.duoApp && typeof window.duoApp.stopTTS === 'function') {
          window.duoApp.stopTTS();
        }
      };

      this.recognition.onresult = (event) => {
        if (this.isCancelled) return;

        const now = Date.now();
        if (this.lastSpeechTime && (now - this.lastSpeechTime > 1800)) {
          this.pauseCount = (this.pauseCount || 0) + 1;
        }
        this.lastSpeechTime = now;

        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            this.finalTranscript += event.results[i][0].transcript + ' ';
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }
        const fullTranscript = (this.finalTranscript + interimTranscript).trim();
        this.lastRecognizedText = fullTranscript;
        
        // Emit interim results so user sees they are being heard
        if (this.onResult) {
          this.onResult(fullTranscript, false);
        }

        // BARGE-IN: If speech detected and bot audio is somehow still playing, cut it off immediately
        if (fullTranscript && window.duoApp && typeof window.duoApp.stopTTS === 'function' && window.duoApp.currentAudio) {
          window.duoApp.stopTTS();
        }
      };

      this.recognition.onerror = (event) => {
        console.warn('[SpeechHandler] Error:', event.error);
        if (event.error === 'aborted' || this.isCancelled) {
          this.isListening = false;
          this.micState = 'IDLE';
          this._resetAcousticVAD();
          this._tryUpgradeAudioEngine();
          if (this.onStateChange) this.onStateChange('stopped');
          return;
        }

        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          alert('Quyền micro chưa được cấp. Hãy cấp quyền Micro trên trình duyệt điện thoại!');
        }
        
        this.isListening = false;
        this.micState = 'IDLE';
        this._resetAcousticVAD();
        this._tryUpgradeAudioEngine();
        if (this.onStateChange) this.onStateChange('error', event.error);
      };

      // PREVENT AUTO-STOPPING WHEN HESITATING: Auto-restart if browser pauses on its own!
      this.recognition.onend = () => {
        if (this.isCancelled) {
          this.isListening = false;
          this.micState = 'IDLE';
          this._resetAcousticVAD();
          this._tryUpgradeAudioEngine();
          this.finalTranscript = '';
          this.lastRecognizedText = '';
          if (this.onStateChange) this.onStateChange('cancelled');
          return;
        }

        // If user is still supposed to be listening (did not tap stop), keep recording!
        if (this.isListening) {
          this.pauseCount = (this.pauseCount || 0) + 1;
          setTimeout(() => {
            if (this.isListening) {
              try {
                this.recognition.start();
              } catch (e) {}
            }
          }, 150);
          return;
        }

        this.isListening = false;
        this.micState = 'IDLE';
        this._resetAcousticVAD();
        this._tryUpgradeAudioEngine();
        if (this.onStateChange) this.onStateChange('stopped');

        const textToSubmit = (this.lastRecognizedText || this.finalTranscript).trim();
        if (this.isCancelled) {
          this._cleanupStream();
          return;
        }

        // Dual-Track STT (Phase 4 Task-010: Optimistic Client-Side STT & Asynchronous Acoustic Extraction):
        // Track 1: Optimistic - If browser Web Speech captured text, emit immediately (0ms delay)
        if (textToSubmit && this.onResult) {
          this.onResult(textToSubmit, true, null);
        }

        // Process audio blob from MediaRecorder
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
          this.mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            this._cleanupStream();

            if (textToSubmit) {
              // Extract acoustic metrics in background without blocking conversation
              this._extractAcousticMetricsAsync(audioBlob, textToSubmit);
            } else {
              // Track 2: Robust Fallback - Web Speech API was empty (mobile browser/fast stop)
              // Transcribe recorded audio blob via server Whisper ASR and trigger turn!
              if (this.onStateChange) this.onStateChange('transcribing');
              await this._submitTranscribeAudio(audioBlob, '');
            }
          };
          try {
            this.mediaRecorder.stop();
          } catch (e) {
            console.warn('[SpeechHandler] Stop mediaRecorder error:', e);
          }
        } else {
          this._cleanupStream();
          if (!textToSubmit && this.onStateChange) {
            this.onStateChange('empty');
          }
        }
      };
    } else {
      console.warn('[SpeechHandler] Web Speech API not supported on this browser.');
    }
  }

  toggleListening() {
    if (!this.recognition) {
      alert('Trình duyệt của bạn chưa hỗ trợ Web Speech API. Bạn có thể sử dụng ô nhập liệu văn bản!');
      return;
    }

    if (this.isListening) {
      this.stopAndSubmit();
    } else {
      this.start();
    }
  }

  startListening() {
    if (!this.isListening) {
      this.start();
    }
  }

  stopListening() {
    if (this.isListening) {
      this.stopAndSubmit();
    }
  }

  start() {
    // BARGE-IN: Instantly stop bot speech the exact moment the mic is triggered (0ms latency)
    if (window.duoApp && typeof window.duoApp.stopTTS === 'function') {
      window.duoApp.stopTTS();
    }
    if (window.duoAudio && typeof window.duoAudio.stopFiller === 'function') {
      window.duoAudio.stopFiller();
    }

    if (this.recognition) {
      try {
        this.isListening = true;
        this.micState = 'RECORDING';
        this.isCancelled = false;
        this.finalTranscript = '';
        this.lastRecognizedText = '';
        this.pauseCount = 0;
        this.lastSpeechTime = Date.now();
        this.audioChunks = [];
        this._startAcousticVADMonitor();
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
            this.audioStream = stream;
            
            // Set up audio visualizer for dynamic waveform & acoustic energy tracking
            try {
              this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
              this.analyser = this.audioContext.createAnalyser();
              this.microphone = this.audioContext.createMediaStreamSource(stream);
              this.microphone.connect(this.analyser);
              this.analyser.fftSize = 256;
              const bufferLength = this.analyser.frequencyBinCount;
              this.dataArray = new Uint8Array(bufferLength);
              
              let lastFrameTime = Date.now();
              const updateWaveform = () => {
                if (!this.isListening) return;
                this.analyser.getByteFrequencyData(this.dataArray);
                let sum = 0;
                for (let i = 0; i < bufferLength; i++) {
                  sum += this.dataArray[i];
                }
                const average = sum / bufferLength;
                const now = Date.now();
                const deltaMs = now - lastFrameTime;
                lastFrameTime = now;

                // Acoustic VAD accumulation: average volume threshold > 12 corresponds to voiced speech
                if (average > 12) {
                  this.accumulatedVoicedDurationMs += deltaMs;
                  this.lastAcousticVoiceTime = now;
                }

                if (this.onVolumeChange) this.onVolumeChange(average);
                requestAnimationFrame(updateWaveform);
              };
              updateWaveform();
            } catch (err) {
              console.warn("AudioContext setup failed:", err);
            }

            this.mediaRecorder = new MediaRecorder(stream);
            this.mediaRecorder.ondataavailable = e => {
              if (e.data && e.data.size > 0) this.audioChunks.push(e.data);
            };
            this.mediaRecorder.start();
          }).catch(e => {
            console.warn('[SpeechHandler] Audio stream record fallback:', e);
          });
        }
        this.recognition.start();
      } catch (e) {
        console.error('[SpeechHandler] Start error:', e);
        try {
          this.recognition.stop();
          setTimeout(() => {
            this.isListening = true;
            this.micState = 'RECORDING';
            this.recognition.start();
          }, 200);
        } catch (err) {
          this.isListening = false;
          this.micState = 'IDLE';
          this._tryUpgradeAudioEngine();
        }
      }
    }
  }

  stopAndSubmit() {
    this._resetAcousticVAD();
    if (this.recognition && this.isListening) {
      this.isListening = false; // Mark that user explicitly tapped stop button!
      this.micState = 'IDLE';
      this._tryUpgradeAudioEngine();
      try {
        this.recognition.stop();
      } catch (e) {
        console.error('[SpeechHandler] Stop error:', e);
      }
    }
  }

  cancel() {
    this._resetAcousticVAD();
    if (window.duoApp && typeof window.duoApp.stopTTS === 'function') {
      window.duoApp.stopTTS();
    }
    if (this.recognition) {
      this.isCancelled = true;
      this.isListening = false;
      this.micState = 'IDLE';
      this._tryUpgradeAudioEngine();
      this.finalTranscript = '';
      this.lastRecognizedText = '';
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        try { this.mediaRecorder.stop(); } catch(e) {}
      }
      this._cleanupStream();
      try {
        this.recognition.abort();
      } catch (e) {
        console.error('[SpeechHandler] Cancel error:', e);
      }
      if (this.onStateChange) this.onStateChange('cancelled');
    }
  }

  async _extractAcousticMetricsAsync(audioBlob, transcript) {
    this.isTranscribing = true;
    try {
      const formData = new FormData();
      if (audioBlob) {
        formData.append('file', audioBlob, 'user_speech.webm');
      }
      formData.append('transcript', transcript || '');
      const res = await fetch('/api/audio/extract_acoustic_metrics', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        const speechMetrics = data.speech_metrics || null;
        if (speechMetrics && this.onAcousticMetrics) {
          this.onAcousticMetrics(speechMetrics);
        }
        return data;
      }
    } catch (e) {
      console.warn('[SpeechHandler] Async acoustic extraction failed:', e);
    } finally {
      this.isTranscribing = false;
    }
    return null;
  }

  async _submitTranscribeAudio(audioBlob, fallbackText) {
    this.isTranscribing = true;
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'user_speech.webm');
      formData.append('fallback_text', fallbackText || '');
      const res = await fetch('/api/transcribe_audio', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        const finalTx = (data.transcript || fallbackText).trim();
        const speechMetrics = data.speech_metrics || null;
        if (finalTx && this.onResult) {
          this.onResult(finalTx, true, speechMetrics);
          return;
        }
      }
    } catch (e) {
      console.warn('[SpeechHandler] Audio transcribe API fallback to local STT:', e);
    } finally {
      this.isTranscribing = false;
    }
    if (fallbackText && this.onResult) {
      this.onResult(fallbackText, true, null);
    }
  }

  _cleanupStream() {
    if (this.audioStream) {
      try {
        this.audioStream.getTracks().forEach(t => t.stop());
      } catch(e) {}
      this.audioStream = null;
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      try {
        this.audioContext.close();
      } catch(e) {}
    }
  }
}

window.SpeechHandler = SpeechHandler;
