"""ControlSphere: fictional first-line controls and RCSA workbench."""

import pandas as pd
import streamlit as st

from domain import (
    active_controls, approve_assessment, assessment_checks, band,
    control_quality, rationalisation_candidates, record_change, risk_score,
)
from sample_data import initial_state

st.set_page_config(page_title="ControlSphere", page_icon="◉", layout="wide")
if "workbench" not in st.session_state:
    st.session_state.workbench = initial_state()
state = st.session_state.workbench

st.markdown("""<style>
.block-container {max-width: 1300px; padding-top: 2rem}
[data-testid="stMetricValue"] {font-size: 1.75rem}
.smallnote {color: #57677a; font-size: .9rem}
[data-testid="stBaseButton-primary"] {background-color: #245a84 !important; border-color: #245a84 !important}
[data-testid="stBaseButton-primary"]:hover {background-color: #174663 !important; border-color: #174663 !important}
</style>""", unsafe_allow_html=True)
st.title("◉ ControlSphere")
st.caption("A fictional benchmark operations workbench · control framework · rationalisation · RCSA")
st.info("Synthetic portfolio demonstration. The rules are illustrative.")

page = st.sidebar.radio("Explore", ["Overview", "Process → Risk → Control", "Control Library", "Rationalisation", "RCSA Workshop", "Governance & Audit Trail"], key="nav_page")
actor = st.sidebar.text_input("Demo reviewer", "Portfolio reviewer", help="A label in the local audit trail, not authenticated identity.")
st.sidebar.caption("Edits live in this browser session. Refreshing or restarting the app resets the sample; export before leaving.")
if st.sidebar.button("Reset demonstration", type="secondary"):
    st.session_state.workbench = initial_state()
    st.rerun()


def risk_label(risk_id):
    risk = state["risks"][risk_id]
    return f'{risk_id} · {risk["name"]}'


def control_label(control_id):
    return f'{control_id} · {state["controls"][control_id]["name"]}'


def metrics():
    controls = list(state["controls"].values())
    missing_owner = sum(not c["owner"] for c in controls if c["status"] == "Active")
    poor_docs = sum(control_quality(c)[0] < 100 for c in controls if c["status"] == "Active")
    uncovered = sum(not active_controls(state, r) for r in state["risks"])
    outside = sum(risk_score(a["residual_likelihood"], a["residual_impact"]) > state["risks"][a["risk_id"]]["appetite"] for a in state["assessments"].values())
    return controls, missing_owner, poor_docs, uncovered, outside


def navigate_to(destination, **selection):
    """A widget callback runs before the sidebar navigation widget is rendered."""
    for key, value in selection.items():
        st.session_state[key] = value
    st.session_state.nav_page = destination


if page == "Overview":
    st.header("Controls framework overview")
    st.caption("Select a measure to see what is driving it, then follow the relevant record into the workbench.")
    controls, missing_owner, poor_docs, uncovered, outside = metrics()
    active = [c for c in controls if c["status"] == "Active"]
    quality_flags = [(c, control_quality(c)[1]) for c in active if control_quality(c)[1]]
    gaps = [r for r in state["risks"].values() if not active_controls(state, r["id"])]
    rationalisation = [x for x in rationalisation_candidates(state) if x["kind"] in ("Potential duplicate", "Overdue review")]
    assessments = state["assessments"]
    lenses = [
        ("inventory", "Active controls", str(len(active)), "Active controls in the inventory; choose a process to inspect their distribution."),
        ("quality", "Documentation", str(len(quality_flags)), "Active control records with documentation or mapping prompts."),
        ("rationalise", "Rationalisation", str(len(rationalisation)), "Potential duplicate controls and overdue inventory reviews needing a human decision."),
        ("coverage", "Coverage gaps", str(len(gaps)), "Risks without an active mapped control; coverage must be verified by an owner."),
        ("rcsa", "RCSA progress", f'{len(assessments)}/{len(state["risks"])}', "Risks with an RCSA submission out of all risks in the sample."),
    ]
    if "overview_focus" not in st.session_state:
        st.session_state.overview_focus = "inventory"
    for col, (lens, title, value, explanation) in zip(st.columns(5), lenses):
        with col:
            if st.button(f"{value} · {title}", key=f"focus_{lens}", type="primary" if st.session_state.overview_focus == lens else "secondary", width="stretch", help=explanation):
                st.session_state.overview_focus = lens
                st.rerun()
    st.caption(f'{len(assessments)} of {len(state["risks"])} risks have an RCSA submission. {outside} submitted assessment(s) are outside appetite; unassessed risks are not counted as within appetite.')

    st.subheader("Process posture")
    posture = []
    for process in state["processes"].values():
        pid = process["id"]
        scoped_controls = [c for c in active if c["process_id"] == pid]
        scoped_risks = [r for r in state["risks"].values() if r["process_id"] == pid]
        covered = sum(bool(active_controls(state, r["id"])) for r in scoped_risks)
        posture.append({
            "Process": process["name"], "Active controls": len(scoped_controls),
            "Risks covered": f"{covered}/{len(scoped_risks)}",
            "Records to improve": sum(bool(control_quality(c)[1]) for c in scoped_controls),
            "RCSA submissions": f'{sum(r["id"] in assessments for r in scoped_risks)}/{len(scoped_risks)}',
        })
    st.dataframe(pd.DataFrame(posture), hide_index=True, width="stretch")
    scope = st.selectbox("Focus on a process", ["All processes", *state["processes"]],
                         format_func=lambda p: "All processes" if p == "All processes" else state["processes"][p]["name"],
                         key="overview_process")
    in_scope = lambda p: scope == "All processes" or p == scope
    focus = st.session_state.overview_focus

    with st.container(border=True):
        if focus == "inventory":
            selected = [c for c in active if in_scope(c["process_id"])]
            st.subheader("Where the active controls sit")
            if scope == "All processes":
                counts = pd.DataFrame({"Process": [p["Process"] for p in posture], "Active controls": [p["Active controls"] for p in posture]}).set_index("Process")
                st.bar_chart(counts, horizontal=True)
            st.write(f'**{len(selected)} active controls** in this view · {sum(c["key"] for c in selected)} classified as key · {sum(c["mode"] == "Automated" for c in selected)} automated.')
            if selected:
                selected_id = st.selectbox("Choose a control to review", [c["id"] for c in selected], format_func=control_label, key="overview_control")
                item = state["controls"][selected_id]
                st.caption(f'{item["type"]} · {item["mode"]} · {len(item["risk_ids"])} linked risk(s) · owner: {item["owner"] or "Unassigned"}')
                st.button("Open this control in the library", key="open_control", on_click=navigate_to,
                          args=("Control Library",), kwargs={"selected_control": selected_id})
        elif focus == "quality":
            selected = [(c, reasons) for c, reasons in quality_flags if in_scope(c["process_id"])]
            st.subheader("Documentation that needs attention")
            if selected:
                st.dataframe(pd.DataFrame([{"Control": c["id"], "Owner": c["owner"] or "Unassigned", "Prompts": len(reasons), "First prompt": reasons[0]} for c, reasons in selected]), hide_index=True, width="stretch")
                selected_id = st.selectbox("Review a flagged record", [c["id"] for c, _ in selected], format_func=control_label, key="overview_quality")
                for reason in next(reasons for c, reasons in selected if c["id"] == selected_id):
                    st.caption(f"• {reason}")
                st.button("Improve this control record", key="open_quality", on_click=navigate_to,
                          args=("Control Library",), kwargs={"selected_control": selected_id})
            else:
                st.success("No automatic documentation prompts in this process. This does not establish operating effectiveness.")
        elif focus == "rationalise":
            selected = [x for x in rationalisation if in_scope(state["controls"][x["controls"].split(" + ")[0]]["process_id"])]
            st.subheader("Candidates for human review")
            if selected:
                st.dataframe(pd.DataFrame([{"Candidate": x["controls"], "Signal": x["kind"], "Review question": x["reason"]} for x in selected]), hide_index=True, width="stretch")
                st.caption("Identical descriptions can hide different risk coverage. A flag is a question for the owner, not a consolidation decision.")
                st.button("Open rationalisation queue", key="open_rationalise", on_click=navigate_to,
                          args=("Rationalisation",))
            else:
                st.success("No duplicate-text or overdue-review signals in this process.")
        elif focus == "coverage":
            selected = [r for r in gaps if in_scope(r["process_id"])]
            st.subheader("Risks awaiting coverage confirmation")
            if selected:
                for risk in selected:
                    process = state["processes"][risk["process_id"]]
                    st.warning(f'{risk["id"]} · {risk["name"]} — {process["name"]}. No active control is mapped; verify actual coverage with the process owner.')
                st.button("Explore process and risk links", key="open_mapping", on_click=navigate_to,
                          args=("Process → Risk → Control",), kwargs={"selected_process": selected[0]["process_id"]})
            else:
                st.success("Every risk in this process has at least one active mapped control. Mapping does not prove that the control works.")
        else:
            scoped_risks = [r for r in state["risks"].values() if in_scope(r["process_id"])]
            submitted = [r for r in scoped_risks if r["id"] in assessments]
            st.subheader("RCSA cycle progress")
            st.progress(len(submitted) / len(scoped_risks), text=f'{len(submitted)} of {len(scoped_risks)} risks assessed in this view')
            outside_here = [r for r in submitted if risk_score(assessments[r["id"]]["residual_likelihood"], assessments[r["id"]]["residual_impact"]) > r["appetite"]]
            st.write(f'**{len(outside_here)} outside appetite** among submitted assessments · **{len(scoped_risks) - len(submitted)} awaiting assessment**.')
            if outside_here:
                st.dataframe(pd.DataFrame([{"Risk": r["id"], "Residual": risk_score(assessments[r["id"]]["residual_likelihood"], assessments[r["id"]]["residual_impact"]), "Appetite": r["appetite"], "Status": assessments[r["id"]]["status"]} for r in outside_here]), hide_index=True, width="stretch")
            pending = [r for r in scoped_risks if r["id"] not in assessments]
            next_risk = (outside_here or pending or submitted)
            if next_risk:
                st.button("Open the next RCSA review", key="open_rcsa", on_click=navigate_to,
                          args=("RCSA Workshop",), kwargs={"selected_risk": next_risk[0]["id"]})

    st.subheader("Management attention")
    priorities = []
    if gaps:
        priorities.append(f'**Confirm coverage:** {", ".join(r["id"] for r in gaps)} has no active mapped control. Ask the process owner whether the gap is real.')
    if outside:
        priorities.append(f'**Act on residual exposure:** {outside} submitted assessment(s) exceed illustrative appetite; review the proposed actions and owners.')
    if quality_flags:
        priorities.append(f'**Improve documentation:** {len(quality_flags)} active records have completeness prompts; {missing_owner} lack a named owner.')
    if rationalisation:
        priorities.append(f'**Challenge inventory quality:** {len(rationalisation)} duplicate-text or overdue-review signals need a documented disposition.')
    if len(assessments) < len(state["risks"]):
        priorities.append(f'**Complete assessments:** {len(state["risks"]) - len(assessments)} risks have no RCSA submission; the outside-appetite count is therefore incomplete.')
    for item in priorities[:5]:
        st.markdown(f"- {item}")
    st.caption("This view derives from the current session's records and links. It does not infer incidents, test results or a production control opinion.")

elif page == "Process → Risk → Control":
    st.header("Process → Risk → Control")
    pid = st.selectbox("Business process", list(state["processes"]), format_func=lambda i: f'{i} · {state["processes"][i]["name"]}', key="selected_process")
    process = state["processes"][pid]
    st.caption(f'Owner area: {process["unit"]} · Fictional benchmark data workflow')
    for risk in (r for r in state["risks"].values() if r["process_id"] == pid):
        with st.expander(risk_label(risk["id"]), expanded=True):
            score = risk_score(risk["likelihood"], risk["impact"])
            st.write(f'Inherent: **{score} · {band(score)}** (L {risk["likelihood"]} × I {risk["impact"]}); illustrative appetite **≤ {risk["appetite"]}**')
            linked = active_controls(state, risk["id"])
            if not linked:
                st.error("Coverage prompt: no active linked control. A business owner must verify the actual position.")
            for control in linked:
                quality, _ = control_quality(control)
                st.write(f'**{control["id"]} · {control["name"]}** — {control["type"]}; owner: {control["owner"] or "Unassigned"}; documentation score: {quality}/100')
                st.caption(control["description"])

elif page == "Control Library":
    st.header("Control Library & Documentation Review")
    rows = []
    for c in state["controls"].values():
        score, findings = control_quality(c)
        rows.append({"ID": c["id"], "Name": c["name"], "Process": state["processes"][c["process_id"]]["name"], "Risks": ", ".join(c["risk_ids"]) or "—", "Owner": c["owner"] or "—", "Frequency": c["frequency"] or "—", "Score*": score, "Status": c["status"]})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption("* Documentation completeness prompt only. The score does not establish design or operating effectiveness.")
    cid = st.selectbox("Inspect or improve a control", list(state["controls"]), format_func=control_label, key="selected_control")
    control = state["controls"][cid]
    score, findings = control_quality(control)
    st.subheader(f"{cid} · {control['name']}")
    st.write("**Current description:**", control["description"])
    st.write("**Objective:**", control["objective"])
    st.write("**Control type:**", control["type"], "· **Execution:**", control["mode"], "· **Key:**", "Yes" if control["key"] else "No", "· **Status:**", control["status"])
    st.write("**Last inventory review:**", control["last_review"])
    st.write("**Evidence:**", control["evidence"] or "Not documented")
    if findings:
        for finding in findings:
            st.warning(finding)
    else:
        st.success("No automatic documentation prompts. A reviewer still needs to assess real design and execution.")
    with st.form(f"edit_{cid}"):
        description = st.text_area("Activity: who, action, trigger, exception handling", control["description"])
        col1, col2 = st.columns(2)
        owner = col1.text_input("Named owner", control["owner"])
        frequency = col2.text_input("Frequency / trigger", control["frequency"])
        evidence = st.text_input("Evidence retained", control["evidence"])
        available = [r for r in state["risks"] if state["risks"][r]["process_id"] == control["process_id"]]
        linked = st.multiselect("Risks addressed", available, default=control["risk_ids"], format_func=risk_label)
        reason = st.text_input("Reason for change (required)")
        save = st.form_submit_button("Save reviewed record")
        if save:
            if not reason.strip():
                st.error("Record a reason for the audit trail.")
            else:
                before = {k: control[k] for k in ("description", "owner", "frequency", "evidence", "risk_ids")}
                after = {"description": description.strip(), "owner": owner.strip(), "frequency": frequency.strip(), "evidence": evidence.strip(), "risk_ids": linked}
                if before == after:
                    st.info("No fields changed.")
                else:
                    control.update(after)
                    control["last_review"] = __import__("datetime").date.today().isoformat()
                    record_change(state, actor, "Control record revised", cid, before, after, reason)
                    st.rerun()
    with st.expander("Lifecycle decision — separate from a proposal"):
        st.caption("Changing status affects coverage and future RCSA checks. Confirm risk impact with the owner; this demo records your decision but cannot enforce a real approval chain.")
        with st.form(f"lifecycle_{cid}"):
            status = st.selectbox("Control status", ["Active", "Under review", "Retired"], index=["Active", "Under review", "Retired"].index(control["status"]))
            status_reason = st.text_area("Owner decision and coverage rationale")
            change_status = st.form_submit_button("Record lifecycle change")
            if change_status:
                if status == control["status"]:
                    st.info("Status is unchanged.")
                elif len(status_reason.strip()) < 20:
                    st.error("Explain the decision and impact on linked risks (at least 20 characters).")
                else:
                    before = control["status"]
                    control["status"] = status
                    record_change(state, actor, "Lifecycle status changed", cid, before, status, status_reason)
                    st.rerun()

elif page == "Rationalisation":
    st.header("Rationalisation Review Queue")
    st.caption("Rule-generated candidates start a review. Duplicate wording can conceal different objectives or risk coverage; no control is merged or retired automatically.")
    candidates = rationalisation_candidates(state)
    st.dataframe(pd.DataFrame(candidates), hide_index=True, width="stretch")
    choices = list(dict.fromkeys(item["controls"] for item in candidates))
    if choices:
        target = st.selectbox("Candidate to decide", choices)
        with st.form("decision"):
            decision = st.selectbox("Reviewer disposition", ["Retain", "Enhance", "Consolidate", "Retire", "Investigate"])
            rationale = st.text_area("Evidence and rationale", placeholder="What did you check? Why is this disposition appropriate?")
            submit = st.form_submit_button("Record proposed disposition")
            if submit:
                if len(rationale.strip()) < 20:
                    st.error("Add a specific rationale (at least 20 characters).")
                else:
                    before = state["decisions"].get(target)
                    after = {"disposition": decision, "rationale": rationale.strip(), "reviewer": actor.strip() or "Demo user"}
                    state["decisions"][target] = after
                    record_change(state, actor, "Rationalisation proposal", target, before, after, rationale)
                    st.success("Proposal recorded. The control remains active pending owner approval and a separately documented change.")
    if state["decisions"]:
        st.subheader("Recorded proposals")
        st.dataframe(pd.DataFrame([{"Target": k, **v} for k, v in state["decisions"].items()]), hide_index=True, width="stretch")

elif page == "RCSA Workshop":
    st.header("Illustrative RCSA Workshop")
    st.caption("Choose a risk, review inherent exposure and linked controls, then propose a residual rating. The residual score is a documented human assessment, never a direct arithmetic deduction from control quality.")
    rid = st.selectbox("Risk in scope", list(state["risks"]), format_func=risk_label, key="selected_risk")
    risk = state["risks"][rid]
    linked = active_controls(state, rid)
    st.write(f'**Scope:** {state["processes"][risk["process_id"]]["name"]} · Sample period: 2026 Q3')
    st.write(f'**Inherent risk:** {risk["likelihood"]} × {risk["impact"]} = **{risk_score(risk["likelihood"], risk["impact"])} ({band(risk_score(risk["likelihood"], risk["impact"]))})** · illustrative appetite ≤ {risk["appetite"]}')
    if linked:
        for control in linked:
            st.write(f'**{control["id"]}** {control["name"]} · {control["owner"] or "Owner missing"} · evidence standard: {control["evidence"] or "missing"}')
    else:
        st.error("No active mapped control. Confirm with the process owner before rating effectiveness.")
    old = state["assessments"].get(rid, {})
    options = ["Not assessed", "Effective", "Partially effective", "Ineffective"]
    with st.form(f"rcsa_{rid}"):
        effectiveness = st.selectbox("Overall linked-control effectiveness (reviewer judgment)", options, index=options.index(old.get("effectiveness", "Not assessed")))
        left, right = st.columns(2)
        rl = left.slider("Residual likelihood", 1, 5, old.get("residual_likelihood", risk["likelihood"]))
        ri = right.slider("Residual impact", 1, 5, old.get("residual_impact", risk["impact"]))
        evidence = st.text_input("Evidence reference (synthetic demo text only)", old.get("evidence", ""))
        rationale = st.text_area("Assessment rationale", old.get("rationale", ""))
        action = st.text_input("Proposed action (if needed)", old.get("action", ""))
        action_owner = st.text_input("Action owner (if needed)", old.get("action_owner", ""))
        notes = st.text_area("Reviewer challenge / comments", old.get("notes", ""))
        col1, col2 = st.columns(2)
        draft = col1.form_submit_button("Save draft")
        approve = col2.form_submit_button("Approve assessment")
        if draft or approve:
            assessment = {"risk_id": rid, "effectiveness": effectiveness, "residual_likelihood": rl, "residual_impact": ri, "evidence": evidence, "rationale": rationale, "action": action, "action_owner": action_owner, "notes": notes, "status": "Draft"}
            flags = assessment_checks(state, assessment)
            if effectiveness == "Not assessed":
                flags.append("Record an effectiveness conclusion before approval.")
            if approve and (not approve_assessment(state, assessment) or flags):
                st.error("Approval is blocked. Resolve the quality prompts below, including an evidence reference.")
            else:
                if approve:
                    assessment["status"] = "Approved in demo"
                state["assessments"][rid] = assessment
                record_change(state, actor, f'RCSA {assessment["status"]}', rid, old or None, assessment.copy(), rationale or "Draft saved for review")
                st.success(f'{assessment["status"]} saved for {rid}.')
            for flag in flags:
                st.warning(flag)
    saved = state["assessments"].get(rid)
    if saved:
        residual = risk_score(saved["residual_likelihood"], saved["residual_impact"])
        st.subheader("Saved assessment & quality review")
        st.write(f'**{saved["status"]}** · Residual {residual} ({band(residual)}) · {"Outside" if residual > risk["appetite"] else "Within"} illustrative appetite')
        for flag in assessment_checks(state, saved):
            st.warning(flag)

else:
    st.header("Governance & Audit Trail")
    controls, missing_owner, poor_docs, uncovered, outside = metrics()
    total = len(state["risks"])
    approved = sum(a["status"] == "Approved in demo" for a in state["assessments"].values())
    x, y, z = st.columns(3)
    x.metric("RCSA coverage", f'{len(state["assessments"])} / {total}')
    y.metric("Approved in demo", approved)
    z.metric("Outside appetite (assessed)", outside)
    st.caption("An unassessed risk is not assumed to be within appetite. 'Approved in demo' is a local illustration, not independent approval.")
    st.subheader("Assessment register")
    rows = []
    for rid, a in state["assessments"].items():
        risk = state["risks"][rid]
        score = risk_score(a["residual_likelihood"], a["residual_impact"])
        rows.append({"Risk": rid, "Process": state["processes"][risk["process_id"]]["name"], "Residual": score, "Appetite": risk["appetite"], "QA prompts": len(assessment_checks(state, a)), "Status": a["status"]})
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else:
        st.info("No RCSA submissions in this browser session yet.")
    st.subheader("Local change log")
    if state["audit_log"]:
        st.dataframe(pd.DataFrame(reversed(state["audit_log"])), hide_index=True, width="stretch")
        st.download_button("Export audit log JSON", __import__("json").dumps(state["audit_log"], indent=2, ensure_ascii=False), "controlsphere_audit_log.json", "application/json")
    else:
        st.caption("Reviewed changes, rationalisation proposals and RCSA drafts will appear here.")
    st.caption("The log is an in-session illustration. It is editable by the running user and is not an immutable production audit trail.")
