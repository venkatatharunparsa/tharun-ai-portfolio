/**
 * API client for Tharun AI backend.
 * Used for text chat (REST) and health checks.
 * Voice uses WebSocket via voice.js
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const CHAT_TIMEOUT_MS = 90000;

export async function sendChatMessage(
  query,
  sessionId = null,
  language = "en",
  conversationHistory = []
) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), CHAT_TIMEOUT_MS);

  try {
    const response = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        session_id: sessionId,
        language,
        conversation_history: conversationHistory.slice(-6),
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    return response.json();
  } finally {
    clearTimeout(timeout);
  }
}

export async function checkHealth() {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    const response = await fetch(`${BACKEND_URL}/health`, {
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeout);
    return response.ok;
  } catch {
    return false;
  }
}

// Backward-compatible alias
export const sendMessage = sendChatMessage;
