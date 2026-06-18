/**
 * VoiceClient — Tharun AI Portfolio
 *
 * Single mic stream during active recording; released between turns so
 * wake-word SpeechRecognition can use the mic.
 */

const BACKEND_WS_URL =
  process.env.NEXT_PUBLIC_BACKEND_WS_URL || "ws://localhost:8000";
const SILENCE_DELAY_MS = 900;
const WS_PING_INTERVAL = 30000;

/** @type {VoiceClient | null} */
let sharedClient = null;

export function getVoiceClient(callbacks = {}) {
  if (!sharedClient) {
    sharedClient = new VoiceClient(callbacks);
  } else {
    sharedClient.setCallbacks(callbacks);
  }
  return sharedClient;
}

export function destroyVoiceClient() {
  sharedClient?.disconnect();
  sharedClient = null;
}

export class VoiceClient {
  constructor(callbacks = {}) {
    this.ws = null;
    this.mediaRecorder = null;
    this.micStream = null;
    this.audioContext = null;
    this.currentAudioSource = null;
    this.sessionId = null;
    this.clientSessionId = null;
    this.isRecording = false;
    this.silenceTimer = null;
    this.pingTimer = null;
    this._connectPromise = null;
    this._intentionalClose = false;
    this._levelAudioContext = null;
    this._levelAnalyser = null;
    this._levelRaf = null;
    this._totalBytesSent = 0;

    this.setCallbacks(callbacks);
  }

  setCallbacks(callbacks = {}) {
    this.onTranscript = callbacks.onTranscript || (() => {});
    this.onReply = callbacks.onReply || (() => {});
    this.onStatus = callbacks.onStatus || (() => {});
    this.onError = callbacks.onError || (() => {});
    this.onAudioStart = callbacks.onAudioStart || (() => {});
    this.onAudioEnd = callbacks.onAudioEnd || (() => {});
  }

  setClientSessionId(sessionId) {
    this.clientSessionId = sessionId || null;
    if (sessionId && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ event: "init", session_id: sessionId }));
    }
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    if (this._connectPromise) {
      return this._connectPromise;
    }

    this._intentionalClose = false;

    this._connectPromise = new Promise((resolve, reject) => {
      const ws = new WebSocket(`${BACKEND_WS_URL}/voice`);
      ws.binaryType = "arraybuffer";
      this.ws = ws;

      const finish = (fn, value) => {
        if (this._connectPromise) {
          this._connectPromise = null;
          fn(value);
        }
      };

      ws.onopen = () => {
        if (this.ws !== ws) return;

        try {
          if (this.clientSessionId) {
            ws.send(
              JSON.stringify({ event: "init", session_id: this.clientSessionId }),
            );
          }
          this._startPing();
          this.onStatus("connected");
          finish(resolve);
        } catch (err) {
          finish(reject, err);
        }
      };

      ws.onmessage = (event) => {
        if (this.ws !== ws) return;
        if (event.data instanceof ArrayBuffer) {
          this._playAudioBytes(event.data);
          return;
        }
        try {
          const msg = JSON.parse(event.data);
          this._handleMessage(msg);
        } catch (e) {
          console.error("WS parse error:", e);
        }
      };

      ws.onerror = () => {
        if (this.ws !== ws) return;
        this.onError("Connection error");
        finish(reject, new Error("WebSocket error"));
      };

      ws.onclose = () => {
        if (this.ws === ws) {
          this.ws = null;
        }
        this._stopPing();
        this.isRecording = false;
        this._connectPromise = null;

        if (!this._intentionalClose) {
          this.onStatus("disconnected");
        }
      };
    });

    return this._connectPromise;
  }

  async ensureConnected() {
    if (this.ws?.readyState === WebSocket.OPEN) return true;
    try {
      await this.connect();
      return this.ws?.readyState === WebSocket.OPEN;
    } catch {
      return false;
    }
  }

  _startPing() {
    this._stopPing();
    this.pingTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ event: "ping" }));
      }
    }, WS_PING_INTERVAL);
  }

  _stopPing() {
    clearInterval(this.pingTimer);
    this.pingTimer = null;
  }

  _handleMessage(msg) {
    switch (msg.type) {
      case "status":
        this.onStatus(msg.status);
        if (msg.session_id) this.sessionId = msg.session_id;
        break;
      case "transcript":
        this.onTranscript(msg.text);
        break;
      case "reply_text":
        this.onReply({
          text: msg.text,
          intent: msg.intent,
          source: msg.response_source,
          processingTime: msg.processing_time_ms,
          agentSteps: msg.agent_steps,
          toolsUsed: msg.tools_used,
          action: msg.action,
        });
        break;
      case "use_webspeech":
        this._speakWithWebSpeech(msg.text);
        break;
      case "error":
        this.onError(msg.message);
        break;
      default:
        break;
    }
  }

  /**
   * Release mic so SpeechRecognition wake-word can access it.
   * Permission stays granted — next startRecording() is fast.
   */
  releaseMicStream() {
    if (this.mediaRecorder?.state === "recording") {
      try {
        this.mediaRecorder.stop();
      } catch {
        // ignore
      }
    }
    this.mediaRecorder = null;
    this.isRecording = false;
    clearTimeout(this.silenceTimer);
    this._stopAudioLevelMonitor();

    this.micStream?.getTracks().forEach((t) => t.stop());
    this.micStream = null;
  }

  async _ensureMicStream() {
    if (this.micStream?.active) return this.micStream;

    this.micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: false,
        autoGainControl: true,
      },
    });
    return this.micStream;
  }

  _stopAudioLevelMonitor() {
    if (this._levelRaf) {
      cancelAnimationFrame(this._levelRaf);
      this._levelRaf = null;
    }
    this._levelAnalyser = null;
    if (this._levelAudioContext) {
      this._levelAudioContext.close().catch(() => {});
      this._levelAudioContext = null;
    }
  }

  _startAudioLevelMonitor(stream) {
    this._stopAudioLevelMonitor();
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      analyser.fftSize = 256;
      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      this._levelAudioContext = audioContext;
      this._levelAnalyser = analyser;

      const checkAudioLevel = () => {
        if (!this.isRecording || !this._levelAnalyser) return;
        this._levelAnalyser.getByteFrequencyData(dataArray);
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        console.log("[audio-level]", avg.toFixed(1));
        this._levelRaf = requestAnimationFrame(checkAudioLevel);
      };
      checkAudioLevel();
    } catch (err) {
      console.warn("[audio-level] monitor unavailable:", err);
    }
  }

  async startRecording() {
    if (this.isRecording) return;

    try {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        await this.connect();
      }

      const stream = await this._ensureMicStream();
      this._startAudioLevelMonitor(stream);
      this._totalBytesSent = 0;

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      this.mediaRecorder = new MediaRecorder(stream, { mimeType });

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && this.ws?.readyState === WebSocket.OPEN) {
          this._totalBytesSent += event.data.size;
          console.log(
            "[audio-chunk]",
            event.data.size,
            "total:",
            this._totalBytesSent,
          );
          this.ws.send(event.data);
          this._resetSilenceTimer();
        }
      };

      this.mediaRecorder.onstop = () => {
        console.log("[audio-total-sent]", this._totalBytesSent, "bytes");
        this._stopAudioLevelMonitor();
        this.isRecording = false;
      };

      this.mediaRecorder.start(200);
      this.isRecording = true;
      this.onStatus("recording");
    } catch (err) {
      if (err.name === "NotAllowedError") {
        this.onError("Microphone access denied");
      } else {
        this.onError("Could not start recording");
      }
      throw err;
    }
  }

  stopRecording() {
    if (!this.isRecording) return;
    clearTimeout(this.silenceTimer);

    const sendEndOfSpeech = () => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ event: "end_of_speech" }));
      }
      this.isRecording = false;
      this.onStatus("processing");
    };

    const recorder = this.mediaRecorder;
    if (recorder?.state === "recording") {
      const onStop = () => {
        // Let the final binary chunk flush over the socket before STT runs.
        setTimeout(sendEndOfSpeech, 150);
      };
      recorder.addEventListener("stop", onStop, { once: true });
      try {
        recorder.requestData();
      } catch {
        // ignore — not all browsers support requestData
      }
      recorder.stop();
      return;
    }

    sendEndOfSpeech();
  }

  stopPlayback() {
    if (this.currentAudioSource) {
      try {
        this.currentAudioSource.stop();
      } catch {
        // already stopped
      }
      this.currentAudioSource = null;
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    this.onAudioEnd();
  }

  _resetSilenceTimer() {
    clearTimeout(this.silenceTimer);
    this.silenceTimer = setTimeout(() => {
      if (this.isRecording) this.stopRecording();
    }, SILENCE_DELAY_MS);
  }

  async _playAudioBytes(arrayBuffer) {
    try {
      this.onAudioStart();
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (this.audioContext.state === "suspended") {
        await this.audioContext.resume();
      }
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer.slice(0));
      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(this.audioContext.destination);
      this.currentAudioSource = source;
      source.onended = () => {
        this.currentAudioSource = null;
        this.onAudioEnd();
      };
      source.start();
    } catch (err) {
      console.error("Audio playback error:", err);
      this.onAudioEnd();
    }
  }

  _speakWithWebSpeech(text) {
    if (!("speechSynthesis" in window)) {
      this.onAudioEnd();
      return;
    }
    this.onAudioStart();
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    utterance.onend = () => this.onAudioEnd();
    utterance.onerror = () => this.onAudioEnd();
    window.speechSynthesis.speak(utterance);
  }

  disconnect() {
    this._intentionalClose = true;
    clearTimeout(this.silenceTimer);
    this._stopPing();
    this.releaseMicStream();

    const ws = this.ws;
    this.ws = null;
    this._connectPromise = null;

    if (ws) {
      ws.onopen = null;
      ws.onmessage = null;
      ws.onerror = null;
      ws.onclose = null;
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        try {
          ws.close();
        } catch {
          // ignore
        }
      }
    }
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("beforeunload", () => {
    destroyVoiceClient();
  });
}
