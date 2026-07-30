/**
 * Speech Recognition & Microphone Visualizer Controller
 * Uses Web Speech API for real-time continuous Speech-to-Text (STT)
 */
class SpeechHandler {
  constructor(onResultCallback, onStateChangeCallback) {
    this.recognition = null;
    this.isListening = false;
    this.onResult = onResultCallback;
    this.onStateChange = onStateChangeCallback;
    this.finalTranscript = '';
    
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
        this.finalTranscript = '';
        if (this.onStateChange) this.onStateChange('listening');
        if (window.duoAudio) window.duoAudio.playMicStart();
      };

      this.recognition.onresult = (event) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            this.finalTranscript += event.results[i][0].transcript + ' ';
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }
        const fullTranscript = (this.finalTranscript + interimTranscript).trim();
        if (this.onResult) this.onResult(fullTranscript, false);
      };

      this.recognition.onerror = (event) => {
        console.warn('[SpeechHandler] Error:', event.error);
        if (this.onStateChange) this.onStateChange('error', event.error);
      };

      this.recognition.onend = () => {
        this.isListening = false;
        if (this.onStateChange) this.onStateChange('stopped');
        if (this.finalTranscript.trim() && this.onResult) {
          this.onResult(this.finalTranscript.trim(), true); // isFinal = true
        }
      };
    } else {
      console.warn('[SpeechHandler] Web Speech API not supported on this browser.');
    }
  }

  toggleListening() {
    if (!this.recognition) {
      alert('Trình duyệt của bạn chưa hỗ trợ Web Speech API. Bạn có thể sử dụng ô nhập liệu bằng văn bản bên dưới!');
      return;
    }

    if (this.isListening) {
      this.stop();
    } else {
      this.start();
    }
  }

  start() {
    if (this.recognition && !this.isListening) {
      try {
        this.finalTranscript = '';
        this.recognition.start();
      } catch (e) {
        console.error('[SpeechHandler] Start error:', e);
      }
    }
  }

  stop() {
    if (this.recognition && this.isListening) {
      try {
        this.recognition.stop();
      } catch (e) {
        console.error('[SpeechHandler] Stop error:', e);
      }
    }
  }
}

window.SpeechHandler = SpeechHandler;
