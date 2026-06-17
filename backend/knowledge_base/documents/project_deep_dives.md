# Project Deep Dives — Problem, Solution, Impact

Structured answers for detailed project questions. Each section is self-contained for retrieval.

---

## TaxSetu — Deep Dive

**Flagship project:** Yes. This is Tharun's most meaningful build.

**One-line pitch:** Autonomous GST compliance for India's 7.34 crore MSMEs.

**Origin story:** A teammate's father got fined for late tax filing. He was scared, didn't understand the system, and couldn't afford a CA. That personal moment sparked TaxSetu.

**Problem:** MSME owners fear GST compliance. Late filings mean fines. CAs are expensive. The system feels hostile to small business owners.

**Solution:** A coordinator agent managing 5 specialized sub-agents — OCR → tax computation → reasoning → filing → audit trail. Multilingual. Human-in-the-loop for irreversible actions.

**Tharun's role:** Built TaxSetu's orchestration layer (Master Planner), structured decision pipelines, and the end-to-end agent workflow.

**Stack:** LangGraph, LangChain, Gemini API, FAISS, FastAPI, AWS.

**Team:** Tharun, Surya, Manjeet, Pavan (PK).

**Achievement:** KSUM Hackathon, Kerala Startup Mission, February 2026. Only team from Telangana.

**Key differentiator:** Built for scared business owners, not for a hackathon score.

---

## InfraGenie — Deep Dive

**One-line pitch:** Say "deploy this" — agents handle security, cost, compliance, and execution.

**Origin story:** After AWS work, Tharun kept doing the same infra tasks manually. Repetitive, error-prone, time-consuming.

**Problem:** Cloud infrastructure is repetitive and risky. One wrong deploy can be expensive.

**Solution:** 5-agent system (Orchestrator, Planner, Executor, Monitor, Security) with 4-tier intelligence: hardcoded rules → RAG → Gemini reasoning → human-in-the-loop.

**Tharun's role:** Fully individual project — designed and built end to end.

**Stack:** Python, FastAPI, Gemini, ChromaDB, RAG, Terraform, AWS, Docker, React.

**Key differentiator:** Guardrails built before features. System cannot bankrupt you with runaway deployments.

**Integrations:** Terraform CLI, tfsec, Checkov, Infracost — security and cost checked before every deploy.

---

## NINA — Deep Dive

**One-line pitch:** Voice-driven browser automation — speak naturally, websites adapt to you.

**Origin story:** Watching non-tech-savvy people struggle with online forms. Frustration became NINA.

**Problem:** Humans adapt to bad website interfaces. Forms are complex. Voice demos usually skip real state tracking.

**Solution:** Voice-to-action pipeline with dynamic DOM understanding via Field Registry. Multi-step tasks with session recovery.

**Tharun's role:** Voice-to-action pipeline, Field Registry system, plug-and-play SDK design.

**Stack:** Playwright, Python, NLP, FastAPI, DOM Parsing.

**Team:** Tharun, Surya, Manjeet, Pavan (PK).

**Key differentiator:** Real-time dynamic website state tracking — not a scripted demo.

**Vision:** Any website becomes a conversational website.

---

## VisionSync — Deep Dive

**One-line pitch:** AI film pre-visualization with 95% character consistency across 100+ frames.

**Problem:** AI-generated film frames look inconsistent — useless for production if the lead character changes every shot.

**Solution:** LoRA fine-tuning on SDXL for character consistency. RAG-based validation across scenes. 6-agent system for scene planning.

**Tharun's role:** Multimodal pipeline, LoRA fine-tuning, RAG validation system.

**Stack:** Stability AI SDXL, LoRA, RAG, Gemini Vision, LangChain, FAISS.

**Achievement:** Top 6 Finalist — Cine AI Hackathon, T-Works Hyderabad, January 2026.

**Impact:** 90% reduction in storyboard generation time, 80% reduction in API usage.

---

## Career Guide — Deep Dive

**One-line pitch:** Free 24/7 AI job discovery — opportunities find you, not the other way around.

**Origin story:** Too many hours searching for internships. Existing platforms hide opportunities behind paywalls.

**Problem:** Job search is manual, repetitive, and often requires paid subscriptions.

**Solution:** LangGraph pipeline (Planner → Scraper → Evaluator). Scrapes 15+ sites every 6 hours. Gemini semantic scoring. Gmail digest notifications.

**Tharun's role:** Fully individual, open source project.

**Stack:** LangGraph, LangChain, Gemini, Tavily, SQLite, ChromaDB, ReportLab, AWS EC2.

**GitHub:** github.com/venkatatharunparsa/CareerGuide

**Philosophy:** Spend time applying, not searching.

---

## AstraDeploy — Deep Dive

**One-line pitch:** Cloud-native MLOps platform for deploying AI systems at scale.

**Problem:** Deploying AI models to production is slow, manual, and lacks observability.

**Solution:** Automated CI/CD, containerized auto-scalable AWS infrastructure, real-time Grafana + CloudWatch monitoring.

**Tharun's role:** CI/CD pipelines, containerization, production deployment workflows.

**Stack:** AWS, Docker, Jenkins, Grafana, CloudWatch.

**Team:** Tharun + team (Surya, Manjeet).

---

## Tharun AI Portfolio — Deep Dive

**One-line pitch:** This portfolio is itself an agentic AI system — not a static website.

**What it proves:** Tharun can build production multi-agent systems with voice, RAG, and real-time interaction.

**Stack:** LangGraph, FastAPI (Render), Next.js (Vercel), Supabase pgvector, Groq Whisper STT, ElevenLabs/Web Speech TTS, Upstash Redis, Gemini + Groq LLMs.

**Agents:** Verification, intent classification, RAG retrieval, tool use, contact handling — orchestrated via LangGraph.

**Why it matters:** The portfolio demonstrates the skills it describes. Meta-proof of agentic engineering.
