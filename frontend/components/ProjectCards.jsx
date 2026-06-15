/**
 * ProjectCards — top section showing Tharun's projects.
 * Clicking a card triggers Tharun AI to explain that project.
 */
"use client";

const projects = [
  {
    id: "taxsetu",
    name: "TaxSetu",
    tagline: "Autonomous GST Compliance Platform",
    type: "MULTI-AGENT",
    typeColor: "var(--accent-primary)",
    stack: ["LangGraph", "Gemini", "FastAPI", "AWS"],
    achievement: "🏆 KSUM Hackathon • Kerala 2026",
    query: "Tell me about TaxSetu project",
    github: "https://github.com/venkatatharunparsa",
  },
  {
    id: "infragenie",
    name: "InfraGenie",
    tagline: "Agentic Cloud Infrastructure Platform",
    type: "AGENTIC",
    typeColor: "var(--accent-secondary)",
    stack: ["LangGraph", "Terraform", "AWS", "RAG"],
    achievement: "⚡ Individual Project",
    query: "Tell me about InfraGenie",
    github: "https://github.com/venkatatharunparsa",
  },
  {
    id: "visionsync",
    name: "VisionSync",
    tagline: "AI Film Pre-Visualization System",
    type: "MULTIMODAL",
    typeColor: "#FF6B6B",
    stack: ["LoRA", "SDXL", "Gemini Vision", "RAG"],
    achievement: "🎬 Top 6 • Cine AI Hackathon 2026",
    query: "Tell me about VisionSync",
    github: "https://github.com/venkatatharunparsa",
  },
  {
    id: "nina",
    name: "NINA",
    tagline: "Voice-Driven Browser Automation Agent",
    type: "VOICE AI",
    typeColor: "var(--accent-success)",
    stack: ["Playwright", "NLP", "FastAPI", "DOM"],
    achievement: "🎤 Team Project",
    query: "Tell me about NINA",
    github: "https://github.com/venkatatharunparsa",
  },
  {
    id: "astradeploy",
    name: "AstraDeploy",
    tagline: "Scalable AI Deployment Platform",
    type: "MLOps",
    typeColor: "#FFB347",
    stack: ["AWS", "Docker", "Jenkins", "Grafana"],
    achievement: "☁️ Team Project",
    query: "Tell me about AstraDeploy",
    github: "https://github.com/venkatatharunparsa",
  },
  {
    id: "careerguide",
    name: "Career Guide",
    tagline: "AI Job Discovery Platform",
    type: "AUTOMATION",
    typeColor: "#A78BFA",
    stack: ["AWS", "Python", "GitHub Actions", "Scraping"],
    achievement: "🔍 Open Source • Individual Project",
    query: "Tell me about Career Guide",
    github: "https://github.com/venkatatharunparsa/CareerGuide",
  },
];

export default function ProjectCards({ onProjectClick }) {
  return (
    <div className="p-4 border-b" style={{ borderColor: "var(--border)" }}>
      <div className="flex items-center justify-between mb-3">
        <h2
          className="text-xs font-semibold uppercase tracking-wider"
          style={{ color: "var(--text-secondary)" }}
        >
          Projects — Click to ask Tharun AI
        </h2>
        <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
          {projects.length} projects
        </span>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
        {projects.map((project) => (
          <ProjectCard
            key={project.id}
            project={project}
            onClick={() => onProjectClick(project.query)}
          />
        ))}
      </div>
    </div>
  );
}

function ProjectCard({ project, onClick }) {
  return (
    <div
      className="flex-shrink-0 w-52 p-3 rounded-xl cursor-pointer transition-all duration-200 hover:scale-[1.02] group"
      style={{
        backgroundColor: "var(--bg-surface-2)",
        border: "1px solid var(--border)",
      }}
      onClick={onClick}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = project.typeColor;
        e.currentTarget.style.boxShadow = `0 0 15px ${project.typeColor}22`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--border)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <span
          className="text-xs font-bold px-2 py-0.5 rounded-full"
          style={{
            color: project.typeColor,
            backgroundColor: `${project.typeColor}18`,
            border: `1px solid ${project.typeColor}44`,
          }}
        >
          {project.type}
        </span>
        <a
          href={project.github}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs opacity-40 hover:opacity-100 transition-opacity"
          style={{ color: "var(--text-secondary)" }}
          onClick={(e) => e.stopPropagation()}
        >
          ↗
        </a>
      </div>

      <h3 className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
        {project.name}
      </h3>

      <p className="text-xs mb-2 leading-relaxed" style={{ color: "var(--text-secondary)" }}>
        {project.tagline}
      </p>

      <div className="flex flex-wrap gap-1 mb-2">
        {project.stack.slice(0, 3).map((tech) => (
          <span
            key={tech}
            className="text-xs px-1.5 py-0.5 rounded"
            style={{
              backgroundColor: "var(--bg-primary)",
              color: "var(--text-secondary)",
            }}
          >
            {tech}
          </span>
        ))}
      </div>

      <p className="text-xs font-medium" style={{ color: project.typeColor }}>
        {project.achievement}
      </p>

      <div
        className="mt-2 pt-2 border-t opacity-0 group-hover:opacity-100 transition-opacity"
        style={{ borderColor: "var(--border)" }}
      >
        <p className="text-xs" style={{ color: "var(--accent-primary)" }}>
          💬 Ask Tharun AI about this →
        </p>
      </div>
    </div>
  );
}
