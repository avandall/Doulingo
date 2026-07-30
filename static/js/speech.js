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
    this.isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    
    this._initSpeech();
  }

  _initSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
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
        
        if (this.onResult && fullTranscript) {
          this.onResult(fullTranscript, false); // Real-time preview update
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
          try {
            this.recognition.start();
            return;
          } catch (e) {}
        }

        this.isListening = false;
        if (this.onStateChange) this.onStateChange('stopped');

        const textToSubmit = (this.lastRecognizedText || this.finalTranscript).trim();
        if (textToSubmit && this.onResult && !this.isCancelled) {
          this.onResult(textToSubmit, true); // Submit only when user tapped stop!
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

  start() {
    if (this.recognition) {
      try {
        this.isCancelled = false;
        this.finalTranscript = '';
        this.lastRecognizedText = '';
        this.recognition.start();
      } catch (e) {
        console.error('[SpeechHandler] Start error:', e);
        try {
          this.recognition.stop();
          setTimeout(() => this.recognition.start(), 200);
        } catch (err) {}
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
      try {
        this.recognition.abort();
      } catch (e) {
        console.error('[SpeechHandler] Cancel error:', e);
      }
      if (this.onStateChange) this.onStateChange('cancelled');
    }
  }
}

window.SpeechHandler = SpeechHandler;
