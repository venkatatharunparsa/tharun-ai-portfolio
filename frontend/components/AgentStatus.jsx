/**
 * AgentStatus — shows online/thinking/speaking/offline indicator
 * Appears in sidebar and near mic button
 */
"use client";

export default function AgentStatus({ status = "online" }) {
  const configs = {
    online: {
      color: "var(--accent-success)",
      label: "Tharun AI • Online",
      pulse: true,
    },
    thinking: {
      color: "var(--accent-primary)",
      label: "Thinking...",
      pulse: false,
    },
    connecting: {
      color: "var(--accent-primary)",
      label: "Connecting voice...",
      pulse: false,
    },
    speaking: {
      color: "var(--accent-secondary)",
      label: "Speaking...",
      pulse: true,
    },
    recording: {
      color: "#FF6B6B",
      label: "Listening...",
      pulse: true,
    },
    offline: {
      color: "var(--text-secondary)",
      label: "Offline",
      pulse: false,
    },
  };

  const config = configs[status] || configs.online;

  return (
    <div className="flex items-center gap-2">
      <div className="relative flex items-center justify-center w-3 h-3">
        {config.pulse && (
          <div
            className="absolute w-3 h-3 rounded-full opacity-0"
            style={{
              backgroundColor: config.color,
              animation: "pulse-ring 1.5s ease-out infinite",
            }}
          />
        )}
        <div
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: config.color }}
        />
      </div>
      <span className="text-xs font-medium" style={{ color: config.color }}>
        {config.label}
      </span>
    </div>
  );
}
