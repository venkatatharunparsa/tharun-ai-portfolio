'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { getVoiceClient } from '@/lib/voice';

const CLICKABLE_STATES = [
  'connected', 'speaking', 'idle', 'ready',
  'too_short', 'no_transcript', 'error', 'connecting',
];

export default function VoiceButton({
  sessionId,
  onTranscript,
  onReply,
  onStatusChange,
}) {
  const [voiceStatus, setVoiceStatus] = useState('idle');
  const [micGranted, setMicGranted] = useState(false);

  const clientRef = useRef(null);
  const reconnectRef = useRef(null);
  const mountedRef = useRef(true);
  const voiceStatusRef = useRef('idle');
  const micGrantedRef = useRef(false);

  const onTranscriptRef = useRef(onTranscript);
  const onReplyRef = useRef(onReply);
  const onStatusChangeRef = useRef(onStatusChange);

  useEffect(() => { onTranscriptRef.current = onTranscript; }, [onTranscript]);
  useEffect(() => { onReplyRef.current = onReply; }, [onReply]);
  useEffect(() => { onStatusChangeRef.current = onStatusChange; }, [onStatusChange]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const updateStatus = useCallback((status) => {
    if (!mountedRef.current) return;
    voiceStatusRef.current = status;
    setVoiceStatus(status);
    onStatusChangeRef.current?.(status);
  }, []);

  const afterTurnIdle = useCallback((delayMs = 300) => {
    setTimeout(() => {
      if (!mountedRef.current) return;
      updateStatus('connected');
    }, delayMs);
  }, [updateStatus]);

  useEffect(() => {
    const client = getVoiceClient({
      onTranscript: (text) => onTranscriptRef.current?.(text),
      onReply: (data) => onReplyRef.current?.(data),

      onStatus: (status) => {
        if (['too_short', 'no_transcript'].includes(status)) {
          updateStatus(status);
          afterTurnIdle(2000);
          return;
        }
        if (status === 'disconnected') {
          updateStatus('disconnected');
          clearTimeout(reconnectRef.current);
          reconnectRef.current = setTimeout(async () => {
            try {
              await clientRef.current?.connect();
              updateStatus('connected');
            } catch {
              updateStatus('error');
            }
          }, 3000);
          return;
        }
        if (status === 'connected') {
          updateStatus('connected');
          return;
        }
        updateStatus(status);
      },

      onAudioStart: () => updateStatus('speaking'),
      onAudioEnd: () => afterTurnIdle(300),

      onError: () => {
        updateStatus('error');
        afterTurnIdle(2000);
      },
    });

    clientRef.current = client;
    if (sessionId) {
      client.setClientSessionId(sessionId);
    }

    updateStatus('connecting');
    client.connect()
      .then(() => updateStatus('connected'))
      .catch(() => updateStatus('error'));

    return () => {
      clearTimeout(reconnectRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    clientRef.current?.setClientSessionId(sessionId);
  }, [sessionId]);

  const handleClick = useCallback(async () => {
    const client = clientRef.current;
    if (!client) return;

    if (voiceStatus === 'recording') {
      client.stopRecording();
      return;
    }

    if (voiceStatus === 'processing') return;

    if (voiceStatus === 'speaking') {
      client.stopPlayback();
      try {
        await client.startRecording();
      } catch {
        afterTurnIdle(500);
      }
      return;
    }

    if (!CLICKABLE_STATES.includes(voiceStatus)) return;

    const ok = await client.ensureConnected();
    if (!ok) {
      updateStatus('disconnected');
      return;
    }

    try {
      await client.startRecording();
      if (!micGrantedRef.current) {
        setMicGranted(true);
        micGrantedRef.current = true;
      }
    } catch {
      afterTurnIdle(500);
    }
  }, [voiceStatus, updateStatus, afterTurnIdle]);

  const getLabel = (status) => ({
    idle: 'Click to speak',
    connecting: 'Connecting...',
    connected: 'Click to speak',
    ready: 'Click to speak',
    recording: 'Listening... click to stop',
    processing: 'Processing...',
    speaking: 'Speaking... click to interrupt',
    too_short: "Didn't catch that — try again",
    no_transcript: "Couldn't hear — try again",
    disconnected: 'Reconnecting...',
    error: 'Click to retry',
  }[status] || 'Click to speak');

  const config = {
    idle: { bg: 'var(--bg-surface)', border: 'var(--border)', icon: '🎤', pulse: false },
    connecting: { bg: 'var(--bg-surface)', border: 'var(--accent-primary)', icon: '⟳', pulse: false },
    connected: { bg: 'var(--bg-surface)', border: 'var(--accent-success)', icon: '🎤', pulse: false },
    ready: { bg: 'var(--bg-surface)', border: 'var(--accent-success)', icon: '🎤', pulse: false },
    recording: { bg: 'var(--accent-secondary)', border: 'var(--accent-secondary)', icon: '⏹', pulse: true },
    processing: { bg: 'var(--accent-primary)', border: 'var(--accent-primary)', icon: '⟳', pulse: false },
    speaking: { bg: 'var(--accent-success)', border: 'var(--accent-success)', icon: '🔊', pulse: true },
    too_short: { bg: 'var(--bg-surface)', border: '#FFB347', icon: '🎤', pulse: false },
    no_transcript: { bg: 'var(--bg-surface)', border: '#FFB347', icon: '🎤', pulse: false },
    disconnected: { bg: 'var(--bg-surface)', border: 'var(--text-secondary)', icon: '↻', pulse: false },
    error: { bg: 'var(--bg-surface)', border: '#FF6B6B', icon: '🎤', pulse: false },
  }[voiceStatus] || { bg: 'var(--bg-surface)', border: 'var(--border)', icon: '🎤', pulse: false };

  const isRecording = voiceStatus === 'recording';

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-center gap-2">
      <div
        className="px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap"
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          color: 'var(--text-secondary)',
        }}
      >
        {getLabel(voiceStatus)}
      </div>

      <div className="relative">
        {config.pulse && (
          <>
            <div
              className="absolute inset-0 rounded-full"
              style={{
                backgroundColor: config.border,
                animation: 'pulse-ring 1.2s ease-out infinite',
                opacity: 0.4,
              }}
            />
            <div
              className="absolute inset-0 rounded-full"
              style={{
                backgroundColor: config.border,
                animation: 'pulse-ring 1.2s ease-out infinite',
                animationDelay: '0.4s',
                opacity: 0.2,
              }}
            />
          </>
        )}

        <button
          type="button"
          onClick={handleClick}
          className="relative w-16 h-16 rounded-full flex items-center justify-center text-2xl transition-all duration-200 hover:scale-105 active:scale-95"
          style={{
            backgroundColor: config.bg,
            border: `2px solid ${config.border}`,
            boxShadow: isRecording
              ? '0 0 30px rgba(0, 217, 255, 0.5)'
              : '0 4px 24px rgba(0,0,0,0.4)',
          }}
        >
          {config.icon}
        </button>
      </div>

      {!micGranted && voiceStatus !== 'recording' && (
        <p
          className="text-xs text-center"
          style={{ color: 'var(--text-secondary)', maxWidth: '130px', lineHeight: '1.4' }}
        >
          Click once to enable voice
        </p>
      )}
    </div>
  );
}
