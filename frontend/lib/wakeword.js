/**
 * Wake Word Detector — Phase 1
 *
 * Uses Web Speech API continuous recognition.
 * Auto-enables after mic is granted (no toggle needed).
 * Pauses during active recording to prevent mic conflict.
 * Fuzzy matches common mishears of "Tharun".
 */

const WAKE_PATTERNS = [
  "hey tharun",
  "hi tharun",
  "hello tharun",
  "ok tharun",
  "okay tharun",
  "tharun",
  "hey taron",
  "hey thrown",
  "hey the run",
  "hey sharon",
  "hey siren",
  "hey taroon",
  "hey tarun",
  "hey theron",
  "hay tharun",
  "hey ai",
  "hey a i",
];

export class WakeWordDetector {
  constructor(onWakeWord) {
    this.onWakeWord = onWakeWord;
    this.recognition = null;
    this.isListening = false;
    this.isSupported = false;
    this.enabled = false;
    this.paused = false;
    this.restartTimer = null;
    this._init();
  }

  _init() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;

    this.isSupported = true;
    this.recognition = new SR();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = "en-IN";
    this.recognition.maxAlternatives = 5;

    this.recognition.onresult = (event) => {
      if (this.paused) return;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        for (let j = 0; j < event.results[i].length; j++) {
          const text = event.results[i][j].transcript.toLowerCase().trim();
          if (this._matches(text)) {
            this.onWakeWord(text);
            return;
          }
        }
      }
    };

    this.recognition.onerror = (e) => {
      if (e.error === "not-allowed") {
        this.isSupported = false;
        return;
      }
      if (this.enabled && !this.paused) {
        this._scheduleRestart(1500);
      }
    };

    this.recognition.onend = () => {
      this.isListening = false;
      if (this.enabled && !this.paused) {
        this._scheduleRestart(300);
      }
    };
  }

  _matches(text) {
    return WAKE_PATTERNS.some((p) => text.includes(p));
  }

  _scheduleRestart(ms) {
    clearTimeout(this.restartTimer);
    this.restartTimer = setTimeout(() => this._start(), ms);
  }

  _start() {
    if (!this.isSupported || this.isListening || this.paused) return;
    try {
      this.recognition.start();
      this.isListening = true;
    } catch {
      // Already started — ignore
    }
  }

  _stop() {
    clearTimeout(this.restartTimer);
    try {
      this.recognition?.stop();
    } catch {
      // ignore
    }
    this.isListening = false;
  }

  pause() {
    this.paused = true;
    this._stop();
  }

  resume() {
    this.paused = false;
    if (this.enabled) {
      this._scheduleRestart(500);
    }
  }

  autoEnable() {
    if (!this.isSupported || this.enabled) return;
    this.enabled = true;
    this.paused = false;
    this._scheduleRestart(100);
  }

  enable() {
    if (!this.isSupported) return false;
    this.enabled = true;
    this._start();
    return true;
  }

  disable() {
    this.enabled = false;
    this.paused = false;
    this._stop();
  }

  get supported() {
    return this.isSupported;
  }

  get active() {
    return this.enabled && !this.paused;
  }
}
