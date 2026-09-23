import copy
import unittest

from domain import active_controls, approve_assessment, assessment_checks, control_quality, rationalisation_candidates
from sample_data import initial_state


class WorkbenchRules(unittest.TestCase):
    def setUp(self):
        self.state = initial_state()

    def test_sample_relationships_and_intentional_gap(self):
        self.assertEqual((len(self.state["processes"]), len(self.state["risks"]), len(self.state["controls"])), (7, 14, 24))
        for control in self.state["controls"].values():
            for risk_id in control["risk_ids"]:
                self.assertIn(risk_id, self.state["risks"])
                self.assertEqual(control["process_id"], self.state["risks"][risk_id]["process_id"])
        self.assertFalse(active_controls(self.state, "R14"))

    def test_duplicate_candidate_does_not_change_controls(self):
        before = copy.deepcopy(self.state["controls"])
        flags = rationalisation_candidates(self.state)
        self.assertTrue(any(x["kind"] == "Potential duplicate" and x["controls"] == "C09 + C10" for x in flags))
        self.assertEqual(self.state["controls"], before)

    def test_documentation_is_not_effectiveness(self):
        score, findings = control_quality(self.state["controls"]["C08"])
        self.assertLess(score, 100)
        self.assertTrue(findings)
        self.assertFalse(any("effective" in x.lower() for x in findings))

    def test_approval_blocks_contradictory_low_residual_and_missing_evidence(self):
        a = {"risk_id": "R07", "effectiveness": "Ineffective", "residual_likelihood": 1,
             "residual_impact": 2, "evidence": "", "rationale": "This is a draft claim",
             "action": "", "action_owner": ""}
        self.assertTrue(any("ineffective" in f.lower() for f in assessment_checks(self.state, a)))
        self.assertFalse(approve_assessment(self.state, a))

    def test_approval_requires_action_outside_appetite(self):
        a = {"risk_id": "R07", "effectiveness": "Partially effective", "residual_likelihood": 3,
             "residual_impact": 4, "evidence": "Synthetic worksheet 7", "rationale": "Exceptions remain open",
             "action": "", "action_owner": ""}
        self.assertFalse(approve_assessment(self.state, a))
        a.update(action="Improve exception review", action_owner="Index Operations Lead")
        self.assertTrue(approve_assessment(self.state, a))

    def test_synthetic_baseline_is_internally_consistent(self):
        assessments = self.state["assessments"]
        self.assertEqual(len(assessments), 8)
        self.assertEqual(sum(a["status"] == "Approved in demo" for a in assessments.values()), 7)
        self.assertEqual(sum(a["residual_likelihood"] * a["residual_impact"] > self.state["risks"][rid]["appetite"] for rid, a in assessments.items()), 2)
        for assessment in assessments.values():
            if assessment["status"] == "Approved in demo":
                self.assertTrue(approve_assessment(self.state, assessment), assessment["risk_id"])
        self.assertFalse(approve_assessment(self.state, assessments["R06"]))


if __name__ == "__main__":
    unittest.main()
