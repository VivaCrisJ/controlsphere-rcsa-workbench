"""Entirely fictional, deliberately imperfect demonstration records."""

from datetime import date, timedelta

PROCESSES = [
    ("P01", "Source onboarding", "Market Data Operations"),
    ("P02", "Market data ingestion", "Market Data Operations"),
    ("P03", "Data validation", "Market Data Operations"),
    ("P04", "Corporate actions", "Index Operations"),
    ("P05", "Benchmark calculation", "Index Operations"),
    ("P06", "Pre-publication review", "Index Operations"),
    ("P07", "Publication and distribution", "Client Delivery"),
]

# ID, process, risk, likelihood, impact, appetite threshold (score)
RISKS = [
    ("R01", "P01", "Unauthorised data source approved", 3, 4, 8),
    ("R02", "P01", "Source licence expires without renewal", 3, 3, 6),
    ("R03", "P02", "Source feed missing or delayed", 4, 4, 8),
    ("R04", "P02", "Duplicate market data ingested", 3, 4, 8),
    ("R05", "P03", "Incorrect source prices accepted", 4, 5, 8),
    ("R06", "P03", "Data anomalies not investigated", 4, 4, 8),
    ("R07", "P04", "Corporate action applied incorrectly", 4, 5, 8),
    ("R08", "P04", "Corporate action missed before cut-off", 3, 5, 8),
    ("R09", "P05", "Calculation configuration changed improperly", 3, 5, 8),
    ("R10", "P05", "Calculation error goes undetected", 4, 5, 8),
    ("R11", "P06", "Material exceptions cleared without review", 3, 5, 8),
    ("R12", "P06", "Review approval lacks traceable evidence", 3, 4, 8),
    ("R13", "P07", "Incorrect file published to clients", 3, 5, 8),
    ("R14", "P07", "Distribution outage not escalated", 4, 4, 8),
]

# Each control may map to multiple risk IDs. IDs preserve traceability through decisions.
CONTROLS = [
    ("C01", "P01", ["R01"], "Approve source onboarding", "Data Governance Lead approves each new source against an approved-source checklist before activation; approval is retained in the register.", "Data Governance Lead", "Per source", "Signed onboarding checklist", "Preventive", "Manual"),
    ("C02", "P01", ["R02"], "Track data licences", "Vendor Manager reviews the licence expiry register monthly and escalates contracts within 60 days of expiry; dated review and follow-up are retained.", "Vendor Manager", "Monthly", "Dated licence register", "Detective", "Manual"),
    ("C03", "P02", ["R03"], "Check feed completeness", "Operations Analyst compares expected and received feed counts before daily processing and escalates missing feeds; exception log records resolution.", "Operations Analyst", "Daily", "Feed reconciliation and exception log", "Detective", "IT-dependent manual"),
    ("C04", "P02", ["R03"], "Monitor feed arrivals", "Operations Analyst compares expected and received feed counts before daily processing and escalates missing feeds; exception log records resolution.", "Operations Analyst", "Daily", "Feed reconciliation and exception log", "Detective", "IT-dependent manual"),
    ("C05", "P02", ["R04"], "Reject duplicate records", "Ingestion service rejects duplicate source and timestamp combinations before records enter the staging table; rejected-record log is retained.", "Data Engineering Lead", "Per ingestion", "Rejected-record system log", "Preventive", "Automated"),
    ("C06", "P03", ["R05"], "Apply price tolerance", "Validation service flags price moves above approved thresholds before calculation; exceptions are retained for review.", "Data Engineering Lead", "Daily", "Threshold exception report", "Preventive", "Automated"),
    ("C07", "P03", ["R05", "R06"], "Review price exceptions", "Data Quality Manager reviews the daily price exception report before calculation, investigates threshold breaches and records sign-off and resolution.", "Data Quality Manager", "Daily", "Signed exception report and resolution notes", "Detective", "Manual"),
    ("C08", "P03", ["R06"], "Monitor data quality", "Team monitors data quality regularly.", "", "", "", "Detective", "Manual"),
    ("C09", "P04", ["R07"], "Validate corporate actions", "Index Operations Lead reconciles corporate action inputs with an independent source before calculation and retains differences and approval.", "Index Operations Lead", "Daily", "Reconciliation and approval log", "Detective", "Manual"),
    ("C10", "P04", ["R07", "R08"], "Cross-check corporate actions", "Index Operations Lead reconciles corporate action inputs with an independent source before calculation and retains differences and approval.", "Index Operations Lead", "Daily", "Reconciliation and approval log", "Detective", "Manual"),
    ("C11", "P04", ["R08"], "Escalate cut-off exceptions", "Operations Manager reviews unprocessed events at the daily cut-off and escalates outstanding material events before calculation; action log is retained.", "Operations Manager", "Daily", "Cut-off exception and escalation log", "Detective", "Manual"),
    ("C12", "P05", ["R09"], "Approve configuration changes", "Engineering Lead authorises configuration changes through ticketed peer review and tests before deployment; approvals and test results are retained.", "Engineering Lead", "Per change", "Change ticket and test result", "Preventive", "IT-dependent manual"),
    ("C13", "P05", ["R10"], "Recalculate sample values", "Index Analyst independently recalculates a sample of published candidate values each day and records differences and sign-off before release.", "Index Analyst", "Daily", "Recalculation workbook and sign-off", "Detective", "Manual"),
    ("C14", "P05", ["R10"], "Keep team informed", "Team is aware of calculation policies.", "Index Manager", "", "", "Preventive", "Manual"),
    ("C15", "P06", ["R11"], "Review material exceptions", "Review Lead signs off material exceptions against the release threshold before publication, recording rationale and unresolved items.", "Review Lead", "Daily", "Exception approval log", "Detective", "Manual"),
    ("C16", "P06", ["R12"], "Approve release review", "Review Lead signs the pre-publication checklist before release and retains the approved version with timestamp.", "Review Lead", "Daily", "", "Preventive", "Manual"),
    ("C17", "P07", ["R13"], "Match outgoing file", "Distribution service compares the approved output checksum with the scheduled client file and stops mismatches before transmission; logs are retained.", "Delivery Engineering Lead", "Per publication", "Checksum comparison log", "Preventive", "Automated"),
    ("C18", "P07", ["R13"], "Verify publication", "Client Delivery Analyst compares the published version to approved release metadata and logs discrepancies and escalation.", "Client Delivery Analyst", "Per publication", "Release comparison record", "Detective", "Manual"),
    # R14 is intentionally uncovered so the mapping and RCSA QA expose a real gap.
    ("C19", "P03", [], "Legacy spreadsheet check", "An old spreadsheet is saved to the shared folder each Friday.", "Operations Analyst", "Weekly", "", "Detective", "Manual"),
    ("C20", "P02", ["R03"], "Review delayed feeds", "Feed Support Lead reviews delayed-feed alerts daily and investigates breaches of the arrival cut-off; actions are retained in a ticket.", "Feed Support Lead", "Daily", "Alert and incident ticket", "Detective", "Manual"),
    ("C21", "P04", ["R07"], "Second-source check", "Corporate Action Analyst compares high-impact events with a secondary provider before processing and records differences.", "Corporate Action Analyst", "Per event", "Secondary-provider comparison", "Detective", "Manual"),
    ("C22", "P05", ["R09"], "Restrict deployment rights", "Access Administrator reviews production deployment privileges quarterly and removes exceptions; access report and approval are retained.", "Access Administrator", "Quarterly", "Approved access report", "Preventive", "IT-dependent manual"),
    ("C23", "P06", ["R11", "R12"], "Verify release checklist", "Release Manager checks the exception disposition and dated reviewer approval before granting release permission; signed checklist is retained.", "Release Manager", "Daily", "Release gate checklist", "Preventive", "Manual"),
    ("C24", "P07", ["R13"], "Reconcile client deliveries", "Client Delivery Lead reconciles scheduled and completed deliveries daily and investigates rejected transmissions; reconciliation is retained.", "Client Delivery Lead", "Daily", "Delivery reconciliation", "Detective", "Manual"),
]


# Synthetic baseline judgments illustrate the management view. Evidence IDs are placeholders,
# not files or claims that testing was performed. R06 deliberately remains a draft.
ASSESSMENTS = [
    ("R03", "Effective", 2, 3, "SYN-FEED-01", "Daily completeness checks reduce the likelihood of an undetected late feed; material outages remain possible.", "", "", "Approved in demo"),
    ("R05", "Partially effective", 2, 4, "SYN-PRICE-02", "Threshold checks detect many anomalies, while unusual market movements still need manual challenge.", "", "", "Approved in demo"),
    ("R06", "Not assessed", 2, 4, "", "", "", "", "Draft"),
    ("R07", "Partially effective", 3, 4, "SYN-CA-03", "Recent exception review indicates that high-impact events can remain unresolved near cut-off.", "Calibrate event escalation thresholds and retest exception review", "Index Operations Lead", "Approved in demo"),
    ("R09", "Effective", 2, 4, "SYN-CHANGE-04", "Ticket approval and peer review reduce the likelihood of an improper configuration release.", "", "", "Approved in demo"),
    ("R10", "Partially effective", 3, 4, "SYN-CALC-05", "Sample recalculation can miss errors outside the selected population; monitoring needs broader coverage.", "Expand sample coverage and document independent review criteria", "Index Manager", "Approved in demo"),
    ("R12", "Effective", 2, 3, "SYN-RELEASE-06", "A separate release gate retains an approval record even though one linked control needs a clearer evidence standard.", "", "", "Approved in demo"),
    ("R13", "Effective", 2, 4, "SYN-DIST-07", "Checksum validation and release comparison reduce the risk of an incorrect client file.", "", "", "Approved in demo"),
]


def initial_state():
    recent_review = (date.today() - timedelta(days=30)).isoformat()
    stale_review = (date.today() - timedelta(days=700)).isoformat()
    risk_names = {i: name for i, _, name, *_ in RISKS}
    return {
        "processes": {i: {"id": i, "name": n, "unit": u} for i, n, u in PROCESSES},
        "risks": {i: {"id": i, "process_id": p, "name": n, "likelihood": l, "impact": m, "appetite": a} for i, p, n, l, m, a in RISKS},
        "controls": {i: {"id": i, "process_id": p, "risk_ids": list(rs), "name": n,
                         "objective": f'Reduce exposure to {risk_names[rs[0]].lower()}' if rs else "Objective to confirm with process owner",
                         "description": d, "owner": o, "frequency": f, "evidence": e,
                         "type": t, "mode": mode, "key": bool(rs and next(r[4] for r in RISKS if r[0] == rs[0]) >= 5),
                         "last_review": stale_review if i == "C19" else recent_review,
                         "status": "Active"} for i, p, rs, n, d, o, f, e, t, mode in CONTROLS},
        "assessments": {rid: {"risk_id": rid, "effectiveness": effectiveness,
                              "residual_likelihood": likelihood, "residual_impact": impact,
                              "evidence": evidence, "rationale": rationale, "action": action,
                              "action_owner": action_owner, "notes": "Synthetic baseline case",
                              "status": status}
                        for rid, effectiveness, likelihood, impact, evidence, rationale, action, action_owner, status in ASSESSMENTS},
        "decisions": {}, "audit_log": [],
    }
