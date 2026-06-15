/**
 * Sidebar — left panel with Tharun's profile, skills, and resume link.
 * Collapsible on mobile via isOpen prop.
 */
"use client";

import AgentStatus from "./AgentStatus";

const skills = [
  { category: "Agentic AI", items: ["LangGraph", "LangChain", "CrewAI", "RAG Pipelines"] },
  { category: "LLMs", items: ["Gemini", "Groq", "GPT-4", "Prompt Engineering"] },
  { category: "Cloud & MLOps", items: ["AWS", "Azure", "Docker", "CI/CD"] },
  { category: "Backend", items: ["FastAPI", "Python", "WebSockets", "Redis"] },
];

export default function Sidebar({ agentStatus = "online", isOpen = true, onClose }) {
  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed lg:relative inset-y-0 left-0 z-30
          w-72 h-full flex flex-col
          border-r transition-transform duration-300
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
        style={{
          backgroundColor: "var(--bg-surface)",
          borderColor: "var(--border)",
        }}
      >
        <div className="p-6 border-b" style={{ borderColor: "var(--border)" }}>
          <div className="relative w-16 h-16 mb-4">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold glow-indigo"
              style={{
                background: "linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))",
              }}
            >
              T
            </div>
            <div
              className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2"
              style={{
                backgroundColor: "var(--accent-success)",
                borderColor: "var(--bg-surface)",
              }}
            />
          </div>

          <h1 className="text-lg font-bold mb-1" style={{ color: "var(--text-primary)" }}>
            Venkata Tharun Parsa
          </h1>
          <p className="text-sm mb-3" style={{ color: "var(--accent-primary)" }}>
            Agentic AI Engineer
          </p>
          <AgentStatus status={agentStatus} />
        </div>

        <div className="p-6 border-b space-y-3" style={{ borderColor: "var(--border)" }}>
          <DetailItem icon="🎓" text="RGUKT Basar • 2027" />
          <DetailItem icon="📍" text="Hyderabad, India" />
          <DetailItem icon="💼" text="Open to Opportunities" />
          <DetailItem icon="🌐" text="Remote / Hybrid / On-site" />
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <h2
            className="text-xs font-semibold uppercase tracking-wider"
            style={{ color: "var(--text-secondary)" }}
          >
            Technical Skills
          </h2>
          {skills.map((group) => (
            <div key={group.category}>
              <p className="text-xs font-medium mb-2" style={{ color: "var(--accent-primary)" }}>
                {group.category}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {group.items.map((skill) => (
                  <span
                    key={skill}
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{
                      backgroundColor: "var(--bg-primary)",
                      color: "var(--text-secondary)",
                      border: "1px solid var(--border)",
                    }}
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="p-6 border-t space-y-2" style={{ borderColor: "var(--border)" }}>
          <LinkButton href="https://github.com/venkatatharunparsa" icon="⚡" label="GitHub" />
          <LinkButton
            href="https://www.linkedin.com/in/venkata-tharun-parsa-98850632a/"
            icon="💼"
            label="LinkedIn"
          />
          <LinkButton
            href="mailto:parsavenkatatharun@gmail.com"
            icon="📧"
            label="Email Tharun"
            accent
          />
          <a
            href="/Venkata_Tharun_Parsa_Resume.pdf"
            download="Venkata_Tharun_Parsa_Resume.pdf"
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-medium transition-all hover:scale-[1.02] active:scale-95"
            style={{
              backgroundColor: "var(--bg-primary)",
              color: "var(--accent-secondary)",
              border: "1px solid var(--accent-secondary)",
            }}
          >
            <span>📄</span>
            <span>Download Resume</span>
            <span className="ml-auto text-xs opacity-60">PDF</span>
          </a>
        </div>
      </aside>
    </>
  );
}

function DetailItem({ icon, text }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm">{icon}</span>
      <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
        {text}
      </span>
    </div>
  );
}

function LinkButton({ href, icon, label, accent = false }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-medium transition-all hover:scale-[1.02]"
      style={{
        backgroundColor: accent ? "var(--accent-primary)" : "var(--bg-primary)",
        color: accent ? "white" : "var(--text-secondary)",
        border: accent ? "none" : "1px solid var(--border)",
      }}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </a>
  );
}
