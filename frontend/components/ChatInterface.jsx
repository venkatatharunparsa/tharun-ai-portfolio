"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { sendChatMessage } from "@/lib/api";

const WELCOME_MESSAGE = {
  id: "welcome",
  role: "assistant",
  text: "Hey — I'm Tharun. Ask me anything; I'll search my knowledge base, compare projects, or summarize our chat. You can type or use the mic.",
  source: "system",
};

export function executeAction(action) {
  if (!action || typeof window === "undefined") return;
  if (action.type === "open_url") {
    window.open(action.url, "_blank", "noopener,noreferrer");
  } else if (action.type === "open_email") {
    window.location.href = action.url;
  }
}

export default function ChatInterface({
  messages,
  onNewMessage,
  agentStatus,
  sessionId,
}) {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef(null);
  const loadingTimer = useRef(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      clearTimeout(loadingTimer.current);
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = useCallback(async (queryOverride = null) => {
    const query = queryOverride || input.trim();
    if (!query || isLoading) return;

    setInput("");
    setIsLoading(true);
    clearTimeout(loadingTimer.current);

    onNewMessage({ role: "user", text: query, id: Date.now() });

    loadingTimer.current = setTimeout(() => {
      if (mountedRef.current) setIsLoading(false);
    }, 30000);

    try {
      const history = messages.map((m) => ({ role: m.role, text: m.text }));
      const result = await sendChatMessage(query, sessionId, "en", history);
      clearTimeout(loadingTimer.current);
      if (!mountedRef.current) return;

      onNewMessage({
        role: "assistant",
        text: result.response,
        source: result.response_source,
        ragScore: result.rag_score,
        agentSteps: result.agent_steps,
        toolsUsed: result.tools_used,
        action: result.action,
        followups: result.followup_suggestions || [],
        id: Date.now() + 1,
      });
    } catch {
      clearTimeout(loadingTimer.current);
      if (!mountedRef.current) return;
      onNewMessage({
        role: "assistant",
        text: "Something went wrong — please try again.",
        source: "error",
        id: Date.now() + 1,
      });
    } finally {
      if (mountedRef.current) setIsLoading(false);
    }
  }, [input, isLoading, messages, onNewMessage, sessionId]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <Message message={WELCOME_MESSAGE} />
        {messages.map((msg, index) => (
          <div key={msg.id}>
            <Message message={msg} />
            {msg.role === "assistant" &&
              msg.followups?.length > 0 &&
              index === messages.length - 1 && (
                <FollowupSuggestions
                  suggestions={msg.followups}
                  onSelect={(q) => handleSend(q)}
                />
              )}
          </div>
        ))}
        {isLoading && <ThinkingIndicator />}
        <div ref={bottomRef} />
      </div>

      <div
        className="p-4 pb-24 border-t"
        style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-surface)" }}
      >
        <div
          className="flex items-center gap-3 rounded-xl px-4 py-3"
          style={{
            backgroundColor: "var(--bg-primary)",
            border: "1px solid var(--border)",
          }}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Tharun's projects, skills, or experience..."
            className="flex-1 bg-transparent outline-none text-sm"
            style={{ color: "var(--text-primary)" }}
            disabled={isLoading}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-all"
            style={{
              backgroundColor: input.trim() ? "var(--accent-primary)" : "var(--border)",
              color: "white",
              cursor: input.trim() ? "pointer" : "not-allowed",
            }}
          >
            ↑
          </button>
        </div>
        <p className="text-center text-xs mt-2" style={{ color: "var(--text-secondary)" }}>
          Tharun AI • Powered by LangGraph + Gemini + Groq
        </p>
      </div>
    </div>
  );
}

function Message({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex animate-fade-in-up ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold mr-2 mt-1 flex-shrink-0"
          style={{
            background: "linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))",
          }}
        >
          T
        </div>
      )}

      <div className="max-w-[80%] space-y-1">
        <div
          className="px-4 py-3 rounded-2xl text-sm leading-relaxed"
          style={{
            backgroundColor: isUser ? "var(--accent-primary)" : "var(--bg-surface-2)",
            color: "var(--text-primary)",
            borderBottomRightRadius: isUser ? "4px" : "16px",
            borderBottomLeftRadius: isUser ? "16px" : "4px",
          }}
        >
          {message.text}
          {message.toolsUsed?.length > 0 || message.agentSteps?.length > 0 ? (
            <AgentTrace toolsUsed={message.toolsUsed || []} steps={message.agentSteps} />
          ) : null}
          {message.ragScore ? (
            <div className="mt-1 text-xs opacity-40">
              confidence: {Math.round(message.ragScore * 100)}%
            </div>
          ) : null}
        </div>

        {message.action && (
          <button
            type="button"
            onClick={() => executeAction(message.action)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:scale-105 active:scale-95 cursor-pointer"
            style={{
              backgroundColor: "var(--bg-primary)",
              border: "1px solid var(--accent-primary)",
              color: "var(--accent-primary)",
              width: "fit-content",
            }}
          >
            <span>↗</span>
            <span>{message.action.label}</span>
          </button>
        )}

        {!isUser &&
          (message.source === "contact_redirect" ||
            message.text?.toLowerCase().includes("resume") ||
            message.text?.toLowerCase().includes("download")) && (
            <a
              href="/Venkata_Tharun_Parsa_Resume.pdf"
              download="Venkata_Tharun_Parsa_Resume.pdf"
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:scale-105"
              style={{
                backgroundColor: "var(--bg-primary)",
                border: "1px solid var(--accent-secondary)",
                color: "var(--accent-secondary)",
                width: "fit-content",
              }}
            >
              <span>📄</span>
              <span>Download Resume</span>
            </a>
          )}
      </div>
    </div>
  );
}

function FollowupSuggestions({ suggestions, onSelect }) {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 ml-9 mt-1 mb-2">
      {suggestions.map((s, i) => (
        <button
          key={i}
          type="button"
          onClick={() => onSelect(s)}
          className="text-xs px-3 py-1.5 rounded-full transition-all hover:scale-105 active:scale-95 text-left"
          style={{
            backgroundColor: "var(--bg-primary)",
            border: "1px solid var(--accent-primary)",
            color: "var(--accent-primary)",
          }}
        >
          {s}
        </button>
      ))}
    </div>
  );
}

function AgentTrace({ toolsUsed, steps }) {
  return (
    <div
      className="mt-2 pt-2 border-t text-xs space-y-1"
      style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
    >
      <div className="font-medium" style={{ color: "var(--accent-primary)" }}>
        Agent ran: {toolsUsed.join(" → ")}
      </div>
      {(steps || []).slice(-4).map((s, i) => (
        <div key={i} className="opacity-80">
          • {s.detail || s.type}
          {s.tool ? ` (${s.tool})` : ""}
        </div>
      ))}
    </div>
  );
}

function ThinkingIndicator() {
  return (
    <div className="flex justify-start animate-fade-in-up">
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold mr-2 flex-shrink-0"
        style={{
          background: "linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))",
        }}
      >
        T
      </div>
      <div
        className="px-4 py-3 rounded-2xl flex items-center gap-1"
        style={{ backgroundColor: "var(--bg-surface-2)", borderBottomLeftRadius: "4px" }}
      >
        <div className="w-1.5 h-1.5 rounded-full thinking-dot" style={{ backgroundColor: "var(--accent-primary)" }} />
        <div className="w-1.5 h-1.5 rounded-full thinking-dot" style={{ backgroundColor: "var(--accent-primary)" }} />
        <div className="w-1.5 h-1.5 rounded-full thinking-dot" style={{ backgroundColor: "var(--accent-primary)" }} />
      </div>
    </div>
  );
}
