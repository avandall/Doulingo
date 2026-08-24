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
    
    this._initSpeech();
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
        this.isCancelled = false;
        this.finalTranscript = '';
        this.lastRecognizedText = '';
        if (this.onStateChange) this.onStateChange('listening');
        if (window.duoAudio) window.duoAudio.playMicStart();
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
      };

      this.recognition.onerror = (event) => {
        console.warn('[SpeechHandler] Error:', event.error);
        if (event.error === 'aborted' || this.isCancelled) {
          this.isListening = false;
          if (this.onStateChange) this.onStateChange('stopped');
          return;
        }

        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          alert('Quyền micro chưa được cấp. Hãy cấp quyền Micro trên trình duyệt điện thoại!');
        }
        
        this.isListening = false;
        if (this.onStateChange) this.onStateChange('error', event.error);
      };

      // PREVENT AUTO-STOPPING WHEN HESITATING: Auto-restart if browser pauses on its own!
      this.recognition.onend = () => {
        if (this.isCancelled) {
          this.isListening = false;
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
        if (this.onStateChange) this.onStateChange('stopped');

        const textToSubmit = (this.lastRecognizedText || this.finalTranscript).trim();
        if (this.isCancelled) {
          this._cleanupStream();
          return;
        }

        // Authentic Duolingo: Send recorded audio blob to Backend AI Whisper / Gemini Audio ASR for true studio-grade English recognition
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
          this.mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            this._cleanupStream();
            await this._submitTranscribeAudio(audioBlob, textToSubmit);
          };
          this.mediaRecorder.stop();
        } else {
          this._cleanupStream();
          if (textToSubmit && this.onResult) {
            this.onResult(textToSubmit, true);
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
    if (this.recognition) {
      try {
        this.isListening = true;
        this.isCancelled = false;
        this.finalTranscript = '';
        this.lastRecognizedText = '';
        this.pauseCount = 0;
        this.lastSpeechTime = Date.now();
        this.audioChunks = [];
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
            this.audioStream = stream;
            
            // Set up audio visualizer for dynamic waveform
            try {
              this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
              this.analyser = this.audioContext.createAnalyser();
              this.microphone = this.audioContext.createMediaStreamSource(stream);
              this.microphone.connect(this.analyser);
              this.analyser.fftSize = 256;
              const bufferLength = this.analyser.frequencyBinCount;
              this.dataArray = new Uint8Array(bufferLength);
              
              const updateWaveform = () => {
                if (!this.isListening) return;
                this.analyser.getByteFrequencyData(this.dataArray);
                let sum = 0;
                for (let i = 0; i < bufferLength; i++) {
                  sum += this.dataArray[i];
                }
                const average = sum / bufferLength;
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
            this.recognition.start();
          }, 200);
        } catch (err) {
          this.isListening = false;
        }
      }
    }
  }

  stopAndSubmit() {
    if (this.recognition && this.isListening) {
      this.isListening = false; // Mark that user explicitly tapped stop button!
      try {
        this.recognition.stop();
      } catch (e) {
        console.error('[SpeechHandler] Stop error:', e);
      }
    }
  }

  cancel() {
    if (this.recognition) {
      this.isCancelled = true;
      this.isListening = false;
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
