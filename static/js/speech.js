/**
 * Speech Recognition & Microphone Visualizer Controller
 * Mobile PWA Optimized: Captures both interim & final transcripts for Android Chrome & iOS Safari!
 */
class SpeechHandler {
  constructor(onResultCallback, onStateChangeCallback) {
    this.recognition = null;
    this.isListening = false;
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
      
      // Mobile Chrome & Safari require continuous = false
      this.recognition.continuous = !this.isMobile;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US';

      this.recognition.onstart = () => {
        this.isListening = true;
        this.finalTranscript = '';
        this.lastRecognizedText = '';
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
        this.lastRecognizedText = fullTranscript;
        
        if (this.onResult && fullTranscript) {
          this.onResult(fullTranscript, false);
        }
      };

      this.recognition.onerror = (event) => {
        console.warn('[SpeechHandler] Error:', event.error);
        this.isListening = false;
        
        let errMsg = event.error;
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          errMsg = 'Quyền micro chưa được cấp. Hãy đảm bảo bạn đang dùng liên kết HTTPS hoặc cấp quyền Micro trên điện thoại!';
          alert(errMsg);
        }
        
        if (this.onStateChange) this.onStateChange('error', event.error);
      };

      this.recognition.onspeechend = () => {
        if (this.isMobile && this.recognition) {
          try {
            this.recognition.stop();
          } catch (e) {}
        }
      };

      this.recognition.onend = () => {
        this.isListening = false;
        if (this.onStateChange) this.onStateChange('stopped');
        
        // Capture last recognized text even if isFinal flag was false on mobile!
        const textToSubmit = (this.lastRecognizedText || this.finalTranscript).trim();
        if (textToSubmit && this.onResult) {
          this.onResult(textToSubmit, true); // isFinal = true
        }
      };
    } else {
      console.warn('[SpeechHandler] Web Speech API not supported on this browser.');
    }
  }

  toggleListening() {
    if (!this.recognition) {
      alert('Trình duyệt di động của bạn chưa hỗ trợ Web Speech API. Bạn có thể sử dụng ô nhập liệu bằng văn bản bên dưới!');
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
