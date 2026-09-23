"""Transparent illustrative rules. No output is a regulatory or professional opinion."""

from datetime import date, datetime, timezone


def risk_score(likelihood, impact):
    return int(likelihood) * int(impact)


def band(score):
    if score >= 16:
        return "Critical"
    if score >= 10:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def active_controls(state, risk_id):
    return [c for c in state["controls"].values() if risk_id in c["risk_ids"] and c["status"] == "Active"]


def control_quality(control):
    """Completeness prompts, not a judgment that a control actually works."""
    findings = []
    for key, label in (("owner", "Named owner"), ("frequency", "Defined frequency"), ("evidence", "Evidence standard"), ("risk_ids", "Risk linkage")):
        if not control.get(key):
            findings.append(f"Missing {label.lower()}")
    description = control["description"].lower().strip()
    if len(description) < 85 or any(x in description for x in ("regularly", "is aware of", "saved to the shared folder")):
        findings.append("Activity is vague or may not be a testable control; review trigger, action and exception handling")
    # An explicit rubric makes the score inspectable. It measures documentation only.
    return max(0, 100 - 20 * len(findings)), findings


def rationalisation_candidates(state):
    controls = list(state["controls"].values())
    out = []
    for control in controls:
        _, findings = control_quality(control)
        for finding in findings:
            out.append({"controls": control["id"], "kind": "Documentation / mapping", "reason": finding})
        if control["status"] == "Active" and (date.today() - date.fromisoformat(control["last_review"])).days > 365:
            out.append({"controls": control["id"], "kind": "Overdue review", "reason": "Last inventory review was over 365 days ago; confirm whether the control is still relevant"})
    for i, first in enumerate(controls):
        if first["status"] != "Active":
            continue
        for second in controls[i + 1:]:
            if second["status"] != "Active":
                continue
            if first["process_id"] == second["process_id"] and first["description"].casefold().strip() == second["description"].casefold().strip():
                out.append({"controls": f'{first["id"]} + {second["id"]}', "kind": "Potential duplicate", "reason": "Same process and identical activity; check risk coverage and execution before consolidation"})
    for risk in state["risks"].values():
        if not active_controls(state, risk["id"]):
            out.append({"controls": risk["id"], "kind": "Coverage gap", "reason": "No active control linked to this risk; verify with the business owner"})
    return out


def assessment_checks(state, assessment):
    risk = state["risks"][assessment["risk_id"]]
    inherent = risk_score(risk["likelihood"], risk["impact"])
    residual = risk_score(assessment["residual_likelihood"], assessment["residual_impact"])
    linked = active_controls(state, risk["id"])
    flags = []
    if not linked:
        flags.append("No active control is linked to this risk. Confirm coverage and record an action.")
    if not assessment["rationale"].strip():
        flags.append("Residual rating needs a written rationale.")
    if assessment["effectiveness"] == "Effective" and not assessment["evidence"].strip():
        flags.append("Effective assessment needs an evidence reference.")
    if assessment["effectiveness"] == "Ineffective" and residual <= risk["appetite"]:
        flags.append("Low residual exposure with ineffective controls needs explicit challenge.")
    if residual < inherent and assessment["effectiveness"] == "Ineffective":
        flags.append("Reduced residual risk despite ineffective controls needs an explanation.")
    if residual > inherent:
        flags.append("Residual score exceeds inherent score; review assumptions and note any changed context.")
    if residual > risk["appetite"] and not assessment["action"].strip():
        flags.append("Outside appetite: record a proposed action and owner before approval.")
    if assessment["action"].strip() and not assessment["action_owner"].strip():
        flags.append("An action needs an owner.")
    if linked and all(not c["evidence"] for c in linked):
        flags.append("All linked controls lack documented evidence standards.")
    return flags


def record_change(state, actor, event, target, before, after, reason):
    state["audit_log"].append({
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "actor": actor.strip() or "Demo user",
        "event": event, "target": target,
        "before": before, "after": after, "reason": reason.strip(),
    })


def approve_assessment(state, assessment):
    """Approval requires completed rationale and resolved consistency prompts."""
    return bool(assessment["evidence"].strip()) and not assessment_checks(state, assessment)
