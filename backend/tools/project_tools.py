"""Project comparison and listing tools."""
from tools.knowledge_tools import search_knowledge_base

PROJECT_NAMES = [
    "TaxSetu", "NINA", "VisionSync", "InfraGenie", "AstraDeploy", "Career Guide",
]


def list_projects() -> dict:
    result = search_knowledge_base("Tharun Parsa projects TaxSetu NINA InfraGenie VisionSync")
    return {
        "known_projects": PROJECT_NAMES,
        "kb_excerpt": result.get("chunks", [])[:3],
    }


def compare_projects(project_a: str, project_b: str) -> dict:
    search_a = search_knowledge_base(f"{project_a} project Tharun built tech stack purpose")
    search_b = search_knowledge_base(f"{project_b} project Tharun built tech stack purpose")
    return {
        "project_a": project_a,
        "project_b": project_b,
        "facts_a": search_a.get("chunks", [])[:3],
        "facts_b": search_b.get("chunks", [])[:3],
    }
