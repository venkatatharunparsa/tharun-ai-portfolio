'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import Sidebar from '@/components/Sidebar';
import ProjectCards from '@/components/ProjectCards';
import ChatInterface from '@/components/ChatInterface';
import VoiceButton from '@/components/VoiceButton';
import AgentStatus from '@/components/AgentStatus';
import { fetchWithTimeout } from '@/lib/fetch-utils';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const HEALTH_INTERVAL_ONLINE = 30000;
const HEALTH_INTERVAL_OFFLINE = 8000;
const HEALTH_TIMEOUT_MS = 12000;

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [sessionId] = useState(() =>
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `session-${Date.now()}`
  );
  const [agentStatus, setAgentStatus] = useState('online');
  const [backendOnline, setBackendOnline] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState('idle');
  const healthTimer = useRef(null);
  const healthFailStreak = useRef(0);

  const checkHealth = useCallback(async () => {
    try {
      const res = await fetchWithTimeout(`${BACKEND_URL}/health`, {}, HEALTH_TIMEOUT_MS);
      if (res.ok) {
        healthFailStreak.current = 0;
        setBackendOnline(true);
      } else {
        healthFailStreak.current += 1;
        if (healthFailStreak.current >= 2) setBackendOnline(false);
      }
    } catch {
      healthFailStreak.current += 1;
      if (healthFailStreak.current >= 2) setBackendOnline(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = backendOnline ? HEALTH_INTERVAL_ONLINE : HEALTH_INTERVAL_OFFLINE;
    healthTimer.current = setInterval(checkHealth, interval);
    return () => clearInterval(healthTimer.current);
  }, [checkHealth, backendOnline]);

  useEffect(() => {
    if (!backendOnline && voiceStatus === 'disconnected') {
      setAgentStatus('offline');
      return;
    }
    if (!backendOnline && ['connected', 'recording', 'processing', 'speaking', 'listening_wake'].includes(voiceStatus)) {
      const voiceMap = {
        recording: 'recording',
        processing: 'thinking',
        speaking: 'speaking',
        connected: 'online',
        listening_wake: 'online',
      };
      setAgentStatus(voiceMap[voiceStatus] || 'online');
      return;
    }
    if (!backendOnline) {
      setAgentStatus('offline');
      return;
    }
    const voiceMap = {
      recording: 'recording',
      processing: 'thinking',
      speaking: 'speaking',
      connecting: 'connecting',
      disconnected: 'connecting',
      listening_wake: 'online',
    };
    setAgentStatus(voiceMap[voiceStatus] || 'online');
  }, [backendOnline, voiceStatus]);

  const addMessage = useCallback((message) => {
    setMessages((prev) => [
      ...prev,
      { ...message, id: message.id || Date.now() },
    ]);
  }, []);

  const handleProjectClick = useCallback(
    (query) => {
      addMessage({ role: 'user', text: query, id: Date.now() });

      import('@/lib/api').then(({ sendChatMessage }) => {
        setAgentStatus('thinking');
        const history = messages.map((m) => ({ role: m.role, text: m.text }));
        sendChatMessage(query, sessionId, 'en', history)
          .then((result) => {
            addMessage({
              role: 'assistant',
              text: result.response,
              source: result.response_source,
              ragScore: result.rag_score,
              id: Date.now() + 1,
            });
          })
          .catch(() => {
            addMessage({
              role: 'assistant',
              text: 'Connection issue — please try again.',
              source: 'error',
              id: Date.now() + 1,
            });
          });
      });
    },
    [sessionId, addMessage, messages]
  );

  const handleVoiceTranscript = useCallback(
    (text) => {
      addMessage({ role: 'user', text, id: Date.now() });
    },
    [addMessage]
  );

  const handleVoiceReply = useCallback(
    (data) => {
      addMessage({
        role: 'assistant',
        text: data.text,
        source: data.source,
        agentSteps: data.agentSteps,
        toolsUsed: data.toolsUsed,
        action: data.action,
        id: Date.now() + 1,
      });
    },
    [addMessage]
  );

  const handleVoiceStatusChange = useCallback((status) => {
    setVoiceStatus(status);
  }, []);

  return (
    <div
      className="flex h-screen w-screen overflow-hidden"
      style={{ backgroundColor: 'var(--bg-primary)' }}
    >
      <Sidebar
        agentStatus={agentStatus}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <div
          className="flex items-center justify-between px-4 py-3 border-b lg:hidden"
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderColor: 'var(--border)',
          }}
        >
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-sm px-3 py-1.5 rounded-lg"
            style={{
              backgroundColor: 'var(--bg-primary)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border)',
            }}
          >
            ☰ Profile
          </button>
          <AgentStatus status={agentStatus} />
        </div>

        <div
          className="hidden lg:flex items-center justify-between px-6 py-3 border-b"
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderColor: 'var(--border)',
          }}
        >
          <div>
            <h1
              className="text-sm font-semibold"
              style={{ color: 'var(--text-primary)' }}
            >
              Tharun AI Portfolio
            </h1>
            <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              Agentic Voice Portfolio • LangGraph + Gemini + Groq
            </p>
          </div>
          <AgentStatus status={agentStatus} />
        </div>

        <ProjectCards onProjectClick={handleProjectClick} />

        <div className="flex-1 overflow-hidden">
          <ChatInterface
            messages={messages}
            onNewMessage={addMessage}
            agentStatus={agentStatus}
            sessionId={sessionId}
          />
        </div>
      </main>

      <VoiceButton
        sessionId={sessionId}
        onTranscript={handleVoiceTranscript}
        onReply={handleVoiceReply}
        onStatusChange={handleVoiceStatusChange}
      />
    </div>
  );
}
