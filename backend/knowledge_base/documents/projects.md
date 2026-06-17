# My Projects

## Flagship Project — TaxSetu

**Tharun's flagship, favorite, and most meaningful project is TaxSetu.**

If someone asks about his "flagship project," "best project," "favorite project," or "most meaningful build" — the answer is always **TaxSetu**. It is an autonomous GST compliance platform built with Surya, Manjeet, and Pavan (PK). It started from a real fine that hit a teammate's father, not from a hackathon brief.

---

## TaxSetu — Autonomous GST Compliance Platform
**Stack:** LangGraph, LangChain, Gemini API, FAISS, FastAPI, AWS
**Type:** Team Project — Tharun, Surya, Manjeet, Pavan (PK)
**Achievement:** KSUM Hackathon, Kerala Startup Mission, February 2026 — We were the only team from Telangana there.

### The Real Story
TaxSetu started because one of my teammate's dad got fined for a late tax filing. He was scared of taxes. He didn't understand the system. A CA charged him more than he could afford. That bothered us deeply.

7.34 crore MSMEs in India face this every year. So we asked — can an intelligent agent handle this completely? Not just answer questions. Actually file. Validate. Notify. Keep an audit trail.

When judges at KSUM challenged us — "is this really a problem? what are your agents actually doing?" — we showed them exactly what the system does end to end.

### What I Built
- TaxSetu's orchestration layer — a coordinator agent that manages 5 specialized sub-agents for autonomous GST workflows
- Structured decision pipelines for explainable, audit-ready outputs
- OCR pipeline → tax computation → reasoning → filing — fully automated
- Human-in-the-loop for sensitive irreversible decisions
- Designed for multilingual accessibility across India

Note: TaxSetu is the project name. "Master Planner" refers to TaxSetu's internal orchestration component — it is not a separate project.

### What It Taught Me
Real-world problems matter more than technical complexity. Constraints are part of engineering. We didn't build this for a hackathon — we built it for the people who are scared.

---

## VisionSync — AI Film Pre-Visualization System
**Stack:** Stability AI SDXL, LoRA Fine-tuning, RAG, Gemini Vision, LangChain, FAISS
**Achievement:** Top 6 Finalist — Cine AI Hackathon, T-Works Hyderabad, January 2026

### What It Does
VisionSync is a multimodal AI pipeline for film pre-visualization — helping filmmakers plan scenes, characters, and visual consistency before a single frame is shot.

The hardest problem in film production AI is consistency. If your lead character looks different in every generated frame, it's useless. I solved this with LoRA fine-tuning — 95% character consistency across 100+ frames.

### What I Built
- Multimodal AI pipeline for film pre-visualization workflows
- 95% character consistency across 100+ frames using LoRA fine-tuning on SDXL
- RAG-based validation system to maintain visual consistency across scenes
- 6-agent system for scene planning and production risk prediction
- Reduced storyboard generation time by 90% and API usage by 80%

---

## NINA — Voice-Driven Browser Automation Agent
**Stack:** Playwright, Python, NLP, FastAPI, DOM Parsing
**Type:** Team Project — Tharun, Surya, Manjeet, Pavan (PK)

### The Idea
Why should humans adapt to websites? Websites should adapt to humans.

NINA is a voice-driven layer that sits on top of any website. You speak naturally. It navigates. It fills forms. It executes workflows. Zero manual interaction with complex interfaces.

I got frustrated watching people struggle with online forms — especially people who aren't tech-savvy. That frustration became NINA.

### What I Built
- Voice-to-action pipeline for real-time browser automation
- Dynamic DOM understanding using a Field Registry system — understands changing page structures
- Plug-and-play SDK integration with zero manual configuration for website owners
- Multi-step task execution with session recovery when things break

### The Hard Part
The hardest challenge was not the voice — it was tracking dynamic website state in real time. Most voice demos skip that problem. We didn't.

### Future Vision
Any website becomes a conversational website. That is the goal.

---

## InfraGenie — Agentic Cloud Infrastructure Platform
**Stack:** Python, FastAPI, Gemini API, ChromaDB, RAG, Terraform, AWS, Docker, React
**Type:** Individual Project — fully designed and built by me

### Why I Built It
After working with AWS I kept doing the same infrastructure tasks manually. Repetitive. Error-prone. Time-consuming. I thought — why isn't infrastructure agentic? Why can't I just say "deploy this" and have a system reason about security, cost, compliance, and execution?

### What I Built
- 5-agent system: Orchestrator, Planner, Executor, Monitor, Security
- 4-tier intelligence router: hardcoded rules → RAG lookup → Gemini reasoning → human-in-the-loop
- Self-improving RAG pipeline using ChromaDB across 6 knowledge collections
- Terraform CLI + tfsec + Checkov + Infracost integration — security and cost checked before every deployment
- Human-in-the-loop for irreversible actions — the system will not let you make expensive mistakes autonomously
- Real-time WebSocket streaming to a React dashboard

### The Design Philosophy
I built the guardrails before I built the features. The system should not be able to bankrupt you with runaway deployments. Reliability first, intelligence second. That is the right order.

---

## Career Guide — AI Job Discovery Platform
**Stack:** LangGraph, LangChain, Gemini, Tavily, SQLite, ChromaDB, ReportLab, AWS EC2
**Type:** Individual Project — open source
**GitHub:** github.com/venkatatharunparsa/CareerGuide

### Why I Built It
I spent too many hours searching for internships and jobs. Existing platforms required subscriptions, hid relevant opportunities, or charged for better recommendations.

So I built a free alternative that runs 24/7 and finds opportunities automatically.

### What It Does
- LangGraph multi-agent pipeline: Planner → Scraper → Evaluator
- Scrapes 15+ job sites using Tavily — runs every 6 hours automatically
- Gemini AI for semantic job scoring and matching to your profile
- SQLite for persistence with MD5 hashing for duplicate prevention
- ChromaDB RAG for intelligent opportunity matching
- ReportLab for ATS-optimized PDF resume generation
- Gmail digest notifications when new matches are found
- Deployed 24/7 on AWS EC2 free tier

### Core Philosophy
Opportunities should be discovered automatically. You should spend time applying — not searching.

---

## AstraDeploy — Scalable AI Deployment Platform
**Stack:** AWS, Docker, Jenkins, Grafana, CloudWatch, CI/CD
**Type:** Team Project

### What It Does
A cloud-native MLOps platform for deploying AI systems at scale. Automated CI/CD pipelines, containerized infrastructure, and real-time monitoring.

### What I Built
- Automated CI/CD pipelines that significantly reduced deployment time
- Containerized and auto-scalable infrastructure on AWS
- Real-time monitoring and observability via Grafana and CloudWatch
- Production-grade deployment workflows for AI systems
