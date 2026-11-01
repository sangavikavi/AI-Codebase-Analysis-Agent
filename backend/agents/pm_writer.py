from backend.graph.state import AnalysisState
from backend.services.event_bus import event_bus


async def pm_writer_node(state: AnalysisState) -> dict:
    """
    PM Business Documentation Writer Agent:
    Produces business-focused, non-technical documentation including:
    - Executive Feature Inventory
    - End-to-end User Journeys and workflows
    - Feature priorities and business impact
    - External vendor and platform integrations
    - Business governance and policy rules
    - Analytics and reporting capabilities
    - Current functional limitations and roadmap horizons
    - User context directive reflection
    - Strictly non-technical, executive tone (reads completely different from SDE report!)
    """
    project_id = state["project_id"]
    stack = state.get("detected_stack", "Cloud Business System")
    endpoints = state.get("api_endpoints", [])
    injections = state.get("user_context_injections", [])
    config = state.get("config", {})

    await event_bus.emit_event(
        project_id=project_id,
        event_type="info",
        stage="PM Documentation",
        message="PM Writer: Synthesizing business value, user flows, and roadmap implications.",
        percentage=80.0,
    )

    # Convert endpoints into business capabilities
    feature_items = []
    for ep in endpoints[:10]:
        path = ep.get("path", "")
        method = ep.get("method", "GET")
        if "auth" in path or "login" in path:
            feature_items.append("User Onboarding & Identity Governance: Secure credential access and session authentication.")
        elif "user" in path:
            feature_items.append("Customer Profile Management: Viewing, updating, and administering customer directory accounts.")
        elif "health" in path or "metric" in path:
            feature_items.append("Operational Reliability & Health Oversight: Continuous service availability tracking.")
        elif "project" in path:
            feature_items.append("Project Portfolio Workspace: Multi-project creation, repository loading, and lifecycle tracking.")
        else:
            feature_items.append(f"Business Operation ({path.strip('/')}): Core automated workflow for enterprise transactions.")

    # Deduplicate while preserving order
    unique_features = list(dict.fromkeys(feature_items))
    if not unique_features:
        unique_features = [
            "Core Automated Business Workflows: Processing transactions and managing records.",
            "Identity & Security Governance: Guarding customer data with enterprise encryption.",
            "Interactive Operational Workspace: Empowering teams with unified management tooling."
        ]

    feature_inventory_md = "\n".join(f"{i+1}. **{feat.split(':')[0]}**:{feat.split(':')[1]}" for i, feat in enumerate(unique_features))

    # User context reflection in business terms
    pm_injections_text = ""
    if injections:
        inj_lines = "\n".join(f"- **Strategic Priority**: {inj}" for inj in injections)
        pm_injections_text = f"""## 8. Stakeholder Context & Strategic Directives
The product strategy incorporates the following direct stakeholder inputs:
{inj_lines}
"""

    report_markdown = f"""# Product Management & Business Architecture Report

## Executive Summary
This platform delivers a high-impact digital solution built upon modern {stack} foundations. Designed to accelerate operational velocity, it provides robust identity safeguards, streamlined customer workflows, and automated process execution.

---

## 1. Feature Inventory & Business Capabilities
{feature_inventory_md}

---

## 2. Customer Journeys & Business Workflows
### Journey A: Customer Onboarding & Verification
1. **Access Initiation**: The end-user lands on the secure portal and enters required registration credentials.
2. **Identity Verification**: The platform verifies credentials against policy rules and issues a secure session token.
3. **Workspace Entry**: The user transitions directly to the tailored dashboard with immediate visibility into their designated assets.

### Journey B: Operational Execution & Value Realization
1. **Initiation**: The user creates a new project record and links external data sources.
2. **Automated Analysis**: Real-time progress indicators keep the user informed without exposing technical complexity.
3. **Decision Support**: The platform delivers synthesized findings and exportable deliverables for stakeholder presentations.

---

## 3. Feature Dependencies & Business Priority Matrix
| Capability | Business Priority | Target Persona | Key Value Driver |
|:---|:---|:---|:---|
| Identity & Access Security | **P0 (Critical)** | All Users | Trust, regulatory compliance, data protection |
| Core Process Automation | **P0 (Critical)** | Operations / Analysts | Eliminates manual workflows, saves hours of effort |
| Real-time Tracking & Visibility | **P1 (High)** | Team Managers | Transparency, immediate status awareness |
| Document Exporting & Sharing | **P1 (High)** | Executives / Stakeholders | Cross-functional alignment and reporting |

---

## 4. External Integrations & Partner Ecosystem
- **Cloud Infrastructure**: Scalable containerized deployment across multi-cloud infrastructure.
- **Identity & Directory Services**: Extensible integration with corporate single sign-on (SSO) systems.
- **External Intelligence Feeds**: Integrated industry technical benchmarking and security research sources.

---

## 5. Enterprise Business Rules & Policy Governance
- **Role-Based Isolation**: Regular users can only access records created within their own workspace boundary.
- **Zero-Trust Administrative Controls**: Privileged administrative functions require explicit admin authentication.
- **Data Integrity & Validation**: Corrupted, malformed, or unauthorized incoming inputs are rejected with clear user guidance.

---

## 6. Functional Boundaries & Current Platform Limitations
- **File Ingestion Scope**: Configured for single archive packages under 100MB to preserve responsiveness.
- **Historical Reporting**: Real-time status reporting covers active cycles; longitudinal trends require external export.

---

## 7. Product Roadmap & Strategic Evolution
- **Phase 1 (Current)**: Multi-persona documentation, interactive live steering, and RAG question answering.
- **Phase 2 (Upcoming)**: Automated PR review bot, Slack/Teams workflow notifications, and enterprise team sharing.
- **Phase 3 (Vision)**: Continuous code analysis synced with GitHub Webhooks on every production commit.

---

{pm_injections_text}
"""

    await event_bus.emit_event(
        project_id=project_id,
        event_type="milestone",
        stage="PM Documentation",
        message="PM Writer: Non-technical business architecture report created successfully.",
        percentage=85.0,
    )

    return {
        "pm_report": report_markdown,
        "current_step": "pm_writer",
        "progress_percentage": 85.0,
    }
