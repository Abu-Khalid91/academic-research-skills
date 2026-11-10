"""Unit tests for alsamadani_score_calculator.py  (run: python3 -m pytest -q)."""

import math
import sys
from pathlib import Path

import pytest

# Skip cleanly (instead of a collection error) where the scientific stack is not installed,
# e.g. the repository-wide CI jobs that only install requirements-dev.txt.
np = pytest.importorskip("numpy")
pytest.importorskip("pandas")
pytest.importorskip("pyarrow")

sys.path.insert(0, str(Path(__file__).parent))
import alsamadani_score_calculator as A  # noqa: E402

HERE = Path(__file__).parent


# ---------------------------------------------------------------- core mathematics

def test_sigma_bounds():
    assert A.sparsity_index({k: None for k in A.BIOMARKER_KEYS}) == pytest.approx(1.0)
    assert A.sparsity_index({k: A.LabObservation(1.0, 0.0) for k in A.BIOMARKER_KEYS}) == pytest.approx(0.0)


def test_sigma_half_life_decay():
    lac = A.BIOMARKER_BY_KEY["lactate"]
    labs = {k: None for k in A.BIOMARKER_KEYS}
    labs["lactate"] = A.LabObservation(2.0, lac.half_life_h)  # one half-life old
    assert A.sparsity_index(labs) == pytest.approx(1.0 - 0.5 * lac.weight)


def test_sigma_rejects_unknown_key():
    with pytest.raises(ValueError):
        A.sparsity_index({"troponin": A.LabObservation(1.0, 0.0)})


def test_jsd_properties():
    p, q = np.array([0.7, 0.2, 0.1]), np.array([0.1, 0.2, 0.7])
    assert A.jsd2(p, p) == pytest.approx(0.0, abs=1e-9)
    assert A.jsd2(p, q) == pytest.approx(A.jsd2(q, p))
    assert A.jsd2(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(1.0, abs=1e-6)


def test_confidence_ceiling_and_spce():
    assert A.confidence_ceiling(0.0) == pytest.approx(1.0)
    assert A.confidence_ceiling(1.0) == pytest.approx(1.0 - A.DEFAULT_PARAMS.kappa)
    assert A.spce_encounter(0.6, 1.0) == pytest.approx(0.2)  # (0.6 - 0.5) / 0.5
    assert A.spce_encounter(0.4, 1.0) == 0.0


def test_laundering_offset_by_new_evidence():
    _, trace, _ = A.demo_case_b()
    base = A.collective_epistemic_drift(trace)["laundering"]
    trace.evidence_info = np.array([0.3, 0.6, 0.9])
    assert A.collective_epistemic_drift(trace)["laundering"] < base


def test_dissent_collapse_zero_when_no_initial_dissent():
    probs = np.tile(np.array([0.7, 0.2, 0.1]), (3, 4, 1))
    assert A.dissent_collapse_ratio(A.DeliberationTrace(probs))["rho"] == 0.0


def test_auroc_known_values():
    assert A.auroc(np.array([0.1, 0.2, 0.8, 0.9]), np.array([0, 0, 1, 1])) == pytest.approx(1.0)
    assert A.auroc(np.array([0.5, 0.5, 0.5, 0.5]), np.array([0, 1, 0, 1])) == pytest.approx(0.5)


def test_parameters_must_sum_to_one():
    with pytest.raises(ValueError):
        A.ScoreParameters(a_sigma=0.5)


# ---------------------------------------------------------------- tiers / demo cases

@pytest.mark.parametrize("score,tier", [(100, 1), (80.0, 1), (79.9, 2), (50.0, 2), (49.99, 3), (0, 3),
                                        (float("nan"), 3)])
def test_tier_thresholds(score, tier):
    assert A.governance_tier(score) == tier


def test_case_a_tier_one():
    labs, trace, obs = A.demo_case_a()
    d = A.evaluate_encounter(labs, trace, obs)
    assert d.score >= 80.0 and d.tier == 1
    assert d.consensus_diagnosis_index == 0
    assert d.calibrated_probability <= d.components["ceiling"] + 1e-9


def test_case_b_tier_three_blocks_consensus():
    labs, trace, obs = A.demo_case_b()
    d = A.evaluate_encounter(labs, trace, obs)
    assert d.score < 50.0 and d.tier == 3
    assert d.consensus_diagnosis_index is None
    assert d.consensus_diagnosis_label is None and d.calibrated_probability is None
    assert d.guideline_fallback, "Tier III must always carry a guideline fallback"


def test_case_b_lactate_is_top_voi():
    labs, trace, _ = A.demo_case_b()
    voi = A.counterfactual_voi(labs, trace)
    assert voi[0]["key"] == "lactate"
    assert voi[0]["voi_points"] > voi[1]["voi_points"] > 0
    # Value under the default, pre-specified parameters (regression guard). The +6.7 figure in
    # the original brief is NOT reproduced by these parameters -- see VERIFICATION_REPORT.md.
    assert voi[0]["voi_points"] == pytest.approx(17.4, abs=0.1)


def test_tier_two_surfaces_differentials_not_single_answer():
    labs, trace, obs = A.demo_case_b()
    labs = dict(labs)
    labs["lactate"] = A.LabObservation(3.2, 0.0)
    labs["pf_ratio"] = A.LabObservation(180.0, 0.5)
    d = A.evaluate_encounter(labs, trace, obs)
    assert d.tier == 2
    assert d.consensus_diagnosis_index is None and len(d.differentials) == 2
    assert len(d.voi_ranking) == 3 and len(d.dissent_rationales) == 5


# ---------------------------------------------------------------- fail-closed behaviour

def test_fail_closed_on_missing_trace():
    labs, _, obs = A.demo_case_a()
    d = A.evaluate_encounter(labs, None, obs)
    assert d.tier == 3 and d.consensus_diagnosis_index is None and d.score is None
    assert d.abstention_reason.startswith("fail-closed")


def test_fail_closed_on_bad_labs():
    _, trace, obs = A.demo_case_a()
    d = A.evaluate_encounter({"not_a_lab": A.LabObservation(1, 0)}, trace, obs)
    assert d.tier == 3 and d.consensus_diagnosis_index is None


def test_trace_validation_rejects_nan():
    probs = np.full((2, 3, 3), 1 / 3)
    probs[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        A.DeliberationTrace(probs)


# ---------------------------------------------------------------- guideline engine

def test_fallback_never_empty():
    assert A.guideline_fallback(A.BedsideObservations())[0].rule_id == "BASE-MONITOR"


def test_fallback_septic_shock_bundle():
    obs = A.BedsideObservations(map_mmhg=58, suspected_infection=True, weight_kg=70, age_years=50)
    ids = [r.rule_id for r in A.guideline_fallback(obs)]
    assert {"SSC-ABX", "SSC-LACT", "SSC-FLUID", "SSC-MAP"} <= set(ids)
    fluid = next(r for r in A.guideline_fallback(obs) if r.rule_id == "SSC-FLUID")
    assert "2100 mL" in fluid.text


def test_map_target_older_adult():
    obs = A.BedsideObservations(map_mmhg=55, age_years=72)
    mp = next(r for r in A.guideline_fallback(obs) if r.rule_id == "SSC-MAP")
    assert "60-65" in mp.text


def test_kdigo_staging():
    assert A.kdigo_aki_stage(A.BedsideObservations()) is None
    assert A.kdigo_aki_stage(A.BedsideObservations(creatinine_mg_dl=1.6, baseline_creatinine_mg_dl=1.0)) == 1
    assert A.kdigo_aki_stage(A.BedsideObservations(creatinine_mg_dl=2.1, baseline_creatinine_mg_dl=1.0)) == 2
    assert A.kdigo_aki_stage(A.BedsideObservations(creatinine_mg_dl=3.1, baseline_creatinine_mg_dl=1.0)) == 3
    assert A.kdigo_aki_stage(A.BedsideObservations(creatinine_rise_48h_mg_dl=0.3)) == 1


def test_predicted_body_weight():
    assert A.predicted_body_weight(175, "M") == pytest.approx(50 + 0.91 * (175 - 152.4))


# ---------------------------------------------------------------- privacy

SALT = b"unit-test-salt-0123456789abcdef"


def test_hmac_token_format_and_masking():
    p = A.Pseudonymizer(SALT)
    tok = p.patient("00123456")
    assert tok.startswith("ANON-") and len(tok) == 21
    assert "00123456" not in tok
    assert tok == p.patient("00123456")                       # deterministic
    assert tok != p.unit("00123456")                          # domain separation
    assert tok != A.Pseudonymizer(SALT + b"x").patient("00123456")  # salt-dependent


def test_pseudonymizer_fail_closed_without_salt(monkeypatch):
    monkeypatch.delenv(A.SALT_ENV_VAR, raising=False)
    with pytest.raises(A.PrivacyError):
        A.Pseudonymizer()
    with pytest.raises(A.PrivacyError):
        A.Pseudonymizer(b"short")


def test_phi_scrubber():
    txt = ("Name: Ahmed Alharbi MRN: 00123456 ID 1098765432 call +966 55 123 4567 "
           "admitted 2026-11-09 14:30 at King Fahad Medical City, email a.b@kfmc.med.sa")
    out, counts = A.scrub_phi(txt)
    for raw in ("Ahmed", "00123456", "1098765432", "123 4567", "2026-11-09", "King Fahad", "a.b@kfmc"):
        assert raw not in out
    A.assert_no_phi(out)
    assert counts["NAME"] == 1 and counts["SAUDI_ID"] == 1


def test_llm_context_has_no_raw_identifiers():
    labs, _, obs = A.demo_case_b()
    ctx = A.build_llm_context(A.Pseudonymizer(SALT), "00123456", "KFMC-CVICU-3", 0.0, labs, obs,
                              free_text="Pt: Sara Alqahtani seen 09/11/2026")
    assert "00123456" not in ctx and "KFMC" not in ctx and "Sara" not in ctx and "2026" not in ctx
    assert "lactate: NOT AVAILABLE" in ctx


def test_relative_time():
    assert A.to_relative_hours(["2026-11-09T14:30:00", "2026-11-09T12:00:00"], "2026-11-09T12:00:00") == [2.5, 0.0]


# ---------------------------------------------------------------- data loader (synthetic fixtures only)

def _write_mimic_fixture(root: Path):
    import pandas as pd
    (root / "icu").mkdir(parents=True)
    (root / "hosp").mkdir(parents=True)
    pd.DataFrame({"subject_id": [10000001], "stay_id": [30000001], "intime": ["2150-01-01 10:00:00"],
                  "first_careunit": ["Cardiac Vascular Intensive Care Unit (CVICU)"]}).to_csv(root / "icu/icustays.csv", index=False)
    pd.DataFrame({"subject_id": [10000001] * 4, "itemid": [50813, 50912, 50821, 51265],
                  "charttime": ["2150-01-01 09:00:00", "2150-01-01 08:00:00", "2150-01-01 09:30:00", "2149-12-28 09:00:00"],
                  "valuenum": [3.1, 1.4, 80.0, 150.0]}).to_csv(root / "hosp/labevents.csv", index=False)
    pd.DataFrame({"stay_id": [30000001], "itemid": [223835], "charttime": ["2150-01-01 09:15:00"],
                  "valuenum": [40.0]}).to_parquet(root / "icu/chartevents.parquet")


def test_mimic_loader(tmp_path):
    _write_mimic_fixture(tmp_path)
    df = A.load_mimic_iv_cohort_dataframe(tmp_path, eval_hours_after_admission=0.0,
                                          pseudonymizer=A.Pseudonymizer(SALT))
    r = df.iloc[0]
    assert r["lactate_value"] == 3.1 and r["lactate_dt_h"] == pytest.approx(1.0)
    assert r["pf_ratio_value"] == pytest.approx(200.0) and r["pf_ratio_dt_h"] == pytest.approx(0.5)
    assert r["platelets_value"] is None  # outside 72 h lookback
    assert 0.0 < r["sigma"] < 1.0
    flat = " ".join(map(str, r.values))
    assert "10000001" not in flat and "30000001" not in flat and "2150" not in flat


def test_eicu_loader(tmp_path):
    import pandas as pd
    pd.DataFrame({"patientunitstayid": [141], "uniquepid": ["002-1"], "hospitalid": [73],
                  "unittype": ["CTICU"]}).to_csv(tmp_path / "patient.csv", index=False)
    pd.DataFrame({"patientunitstayid": [141] * 3, "labresultoffset": [-60, -120, -30],
                  "labname": ["lactate", "creatinine", "paO2"], "labresult": [2.5, 1.1, 90.0]}).to_csv(tmp_path / "lab.csv", index=False)
    df = A.load_mimic_iv_cohort_dataframe(tmp_path, source="eicu", pseudonymizer=A.Pseudonymizer(SALT))
    r = df.iloc[0]
    assert r["lactate_dt_h"] == pytest.approx(1.0) and r["creatinine_dt_h"] == pytest.approx(2.0)
    assert r["pf_ratio_value"] is None  # no FiO2 recorded
    assert "002-1" not in " ".join(map(str, r.values))


# ---------------------------------------------------------------- simulation + manuscript consistency

def test_monte_carlo_reproducible_and_bounded():
    a = A.run_monte_carlo_validation(n_total=200, n_boot=50)
    b = A.run_monte_carlo_validation(n_total=200, n_boot=50)
    assert a["auroc_score"] == b["auroc_score"]
    assert 0.0 <= a["auroc_score"] <= 1.0


def test_catfish_reduces_collapse():
    sc = A.run_scaling_benchmark(agents=(5,), rounds=(4,), n_per_cell=50)
    c = sc["cells"][0]
    assert c["catfish_rho"] < c["naive_rho"]


def test_manuscript_macros_match_fresh_run(tmp_path):
    committed = (HERE / "alsamadani_results.tex").read_text(encoding="utf-8")
    out = tmp_path / "r.tex"
    A.export_tex_macros(out, A.run_all(verbose=False))
    assert out.read_text(encoding="utf-8") == committed, "re-run the calculator and commit alsamadani_results.tex"
