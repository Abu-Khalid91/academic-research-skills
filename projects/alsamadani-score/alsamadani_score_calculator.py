#!/usr/bin/env python3
"""
AlSamadani Score (S_AlSamadani in [0, 100])
===========================================

A fail-closed clinical governance and confidence-calibration framework for
recursive multi-agent LLM decision support in ICU / CVICU environments.

Author: Saud Khalid AlSamadani, MBBS, SB-ACCM
ORCID:  0009-0008-1007-4616

STATUS / INTENDED USE
---------------------
Research software. NOT a medical device, NOT validated on patient data, and
NOT for autonomous clinical use. Every output -- including the deterministic
guideline fallback -- is a prompt for review by a licensed clinician, who
retains full decision authority. All numerical results produced by
``run_monte_carlo_validation`` come from a *synthetic* generative model whose
assumptions are documented below; they demonstrate internal behaviour of the
score, not clinical performance.

Components
----------
1. Temporal-Physiological Sparsity Index  sigma(x_t) in [0, 1]
       sigma = 1 - sum_j w_j * m_j * exp(-lambda_j * dt_j),  lambda_j = ln2 / h_j
2. Collective Epistemic Drift  CED_R in [0, 1]
       CED_R = min(1, sum_{r=1..R} JSD2(pbar_{r-1}, pbar_r)
                     + gamma * max(0, dConf - dI_evid))
3. Dissent Collapse Ratio  rho_collapse in [0, 1]
       rho = max(0, 1 - D_R / D_0),  D_r = mean pairwise JSD2 between agents
       (entered into the score as the sparsity-weighted term sigma * rho)
4. Sparsity-Penalized Calibration Error with Epistemic Confidence Ceiling
       c_max = 1 - kappa * sigma
       SPCE_e = max(0, c_R - c_max) / kappa       (encounter level, in [0, 1])
       SPCE   = ECE(min(c, c_max)) + mean(SPCE_e) (cohort level)
5. Score
       S = 100 * (1 - [a_s*sigma + a_d*CED_R + a_r*sigma*rho + a_c*SPCE_e])
6. Counterfactual Value of Information
       VOI_j = S(x_t with biomarker j refreshed, dt_j = 0) - S(x_t)
       (first-order: the deliberation trace is held fixed)

Governance tiers
----------------
  Tier I   Grounded                   S >= 80.0
  Tier II  Guarded                    50.0 <= S < 80.0
  Tier III Mandatory AI Abstention    S < 50.0   (consensus_diagnosis_index = None)

Any validation failure or exception during scoring also resolves to Tier III
(fail-closed).

Run ``python3 alsamadani_score_calculator.py`` for the demonstration cases, the
privacy demo, the Monte Carlo suite and the scaling benchmark.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import itertools
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

__version__ = "0.1.0"

LN2 = math.log(2.0)
EPS = 1e-12

# --------------------------------------------------------------------------------------
# 1. Biomarker panel (expert-specified priors -- NOT learned from data)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Biomarker:
    key: str
    label: str
    unit: str
    weight: float          # w_j, relative decision weight; panel sums to 1
    half_life_h: float     # h_j, decision-relevance half-life (hours), not pharmacokinetic
    mimic_itemids: Tuple[int, ...]   # MIMIC-IV hosp.labevents itemids (verify vs d_labitems)
    eicu_labnames: Tuple[str, ...]   # eICU-CRD lab.labname values (verify vs local dictionary)

    @property
    def decay_rate(self) -> float:
        return LN2 / self.half_life_h


BIOMARKERS: Tuple[Biomarker, ...] = (
    Biomarker("lactate", "Arterial lactate", "mmol/L", 0.22, 2.0, (50813,), ("lactate",)),
    Biomarker("pf_ratio", "PaO2/FiO2 ratio", "mmHg", 0.15, 4.0, (50821,), ("paO2",)),
    Biomarker("creatinine", "Serum creatinine", "mg/dL", 0.13, 12.0, (50912,), ("creatinine",)),
    Biomarker("platelets", "Platelet count", "x10^9/L", 0.11, 24.0, (51265,), ("platelets x 1000",)),
    Biomarker("wbc", "White blood cell count", "x10^9/L", 0.10, 12.0, (51301,), ("WBC x 1000",)),
    Biomarker("inr", "INR", "ratio", 0.10, 24.0, (51237,), ("PT - INR",)),
    Biomarker("bicarbonate", "Bicarbonate", "mmol/L", 0.10, 6.0, (50882,), ("bicarbonate",)),
    Biomarker("bilirubin", "Total bilirubin", "mg/dL", 0.09, 24.0, (50885,), ("total bilirubin",)),
)
BIOMARKER_KEYS: Tuple[str, ...] = tuple(b.key for b in BIOMARKERS)
BIOMARKER_BY_KEY: Dict[str, Biomarker] = {b.key: b for b in BIOMARKERS}
assert abs(sum(b.weight for b in BIOMARKERS) - 1.0) < 1e-9, "biomarker weights must sum to 1"

# MIMIC-IV icu.chartevents itemid for FiO2 ("Inspired O2 Fraction"); verify vs d_items.
MIMIC_FIO2_CHART_ITEMID = 223835
EICU_FIO2_LABNAME = "FiO2"


@dataclass(frozen=True)
class ScoreParameters:
    gamma: float = 1.0        # confidence-laundering penalty weight in CED
    kappa: float = 0.5        # epistemic confidence ceiling slope
    a_sigma: float = 0.40     # weight on sparsity
    a_ced: float = 0.20       # weight on collective epistemic drift
    a_rho: float = 0.20       # weight on sparsity-weighted dissent collapse
    a_spce: float = 0.20      # weight on encounter-level ceiling excess
    tier1_min: float = 80.0
    tier2_min: float = 50.0
    d0_min: float = 1e-3      # below this initial dissent, rho is defined as 0

    def __post_init__(self) -> None:
        total = self.a_sigma + self.a_ced + self.a_rho + self.a_spce
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"component weights must sum to 1 (got {total})")
        if not (0.0 < self.kappa <= 1.0):
            raise ValueError("kappa must be in (0, 1]")


DEFAULT_PARAMS = ScoreParameters()

# --------------------------------------------------------------------------------------
# 2. Core mathematics
# --------------------------------------------------------------------------------------


@dataclass
class LabObservation:
    """A biomarker observation expressed in *relative* elapsed time only."""

    value: Optional[float]
    delta_t_h: Optional[float]  # hours elapsed between measurement and evaluation time

    @property
    def observed(self) -> bool:
        return (
            self.value is not None
            and self.delta_t_h is not None
            and np.isfinite(self.value)
            and np.isfinite(self.delta_t_h)
            and self.delta_t_h >= 0.0
        )


def freshness(obs: Optional[LabObservation], biomarker: Biomarker) -> float:
    """m_j * exp(-lambda_j * dt_j); 0 when unobserved."""
    if obs is None or not obs.observed:
        return 0.0
    return float(math.exp(-biomarker.decay_rate * float(obs.delta_t_h)))


def sparsity_index(labs: Mapping[str, Optional[LabObservation]]) -> float:
    """Temporal-Physiological Sparsity Index sigma(x_t) in [0, 1]."""
    unknown = set(labs) - set(BIOMARKER_KEYS)
    if unknown:
        raise ValueError(f"unknown biomarker keys: {sorted(unknown)}")
    info = sum(b.weight * freshness(labs.get(b.key), b) for b in BIOMARKERS)
    return float(min(1.0, max(0.0, 1.0 - info)))


def _normalize(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 0.0, None)
    s = p.sum(axis=-1, keepdims=True)
    if np.any(s <= 0):
        raise ValueError("probability vector with zero mass")
    return p / s


def jsd2(p: np.ndarray, q: np.ndarray) -> float:
    """Jensen-Shannon divergence, base 2, bounded in [0, 1]."""
    p = _normalize(p)
    q = _normalize(q)
    m = 0.5 * (p + q)

    def _kl(a: np.ndarray, b: np.ndarray) -> float:
        mask = a > 0
        return float(np.sum(a[mask] * (np.log2(a[mask]) - np.log2(b[mask] + EPS))))

    return float(min(1.0, max(0.0, 0.5 * _kl(p, m) + 0.5 * _kl(q, m))))


@dataclass
class DeliberationTrace:
    """Per-round, per-agent diagnostic distributions.

    probs: array of shape (R + 1, M, K); round 0 = independent first opinions.
    evidence_info: optional length R + 1 array of grounded evidence information
        I_evid,r in [0, 1] (e.g. 1 - sigma at that round if new data arrived
        during deliberation). Defaults to constant (no new evidence).
    diagnosis_labels: optional K labels.
    round0_rationales: optional M free-text rationales from round 0.
    """

    probs: np.ndarray
    evidence_info: Optional[np.ndarray] = None
    diagnosis_labels: Optional[Sequence[str]] = None
    round0_rationales: Optional[Sequence[str]] = None

    def __post_init__(self) -> None:
        self.probs = np.asarray(self.probs, dtype=float)
        if self.probs.ndim != 3:
            raise ValueError("probs must have shape (R+1, M, K)")
        n_rounds, m, k = self.probs.shape
        if n_rounds < 2 or m < 2 or k < 2:
            raise ValueError("need >=1 deliberation round, >=2 agents, >=2 diagnoses")
        if not np.all(np.isfinite(self.probs)) or np.any(self.probs < 0):
            raise ValueError("probs must be finite and non-negative")
        self.probs = _normalize(self.probs)
        if self.evidence_info is not None:
            self.evidence_info = np.asarray(self.evidence_info, dtype=float)
            if self.evidence_info.shape != (n_rounds,):
                raise ValueError("evidence_info must have length R+1")
        if self.diagnosis_labels is not None and len(self.diagnosis_labels) != k:
            raise ValueError("diagnosis_labels must have length K")

    @property
    def n_rounds(self) -> int:
        return self.probs.shape[0] - 1

    @property
    def n_agents(self) -> int:
        return self.probs.shape[1]

    def consensus(self, r: int) -> np.ndarray:
        return self.probs[r].mean(axis=0)

    def confidence(self, r: int) -> float:
        return float(self.consensus(r).max())

    def dissent(self, r: int) -> float:
        pairs = itertools.combinations(range(self.n_agents), 2)
        vals = [jsd2(self.probs[r, i], self.probs[r, j]) for i, j in pairs]
        return float(np.mean(vals))


def collective_epistemic_drift(trace: DeliberationTrace, params: ScoreParameters = DEFAULT_PARAMS) -> Dict[str, float]:
    """CED_R = min(1, path JSD drift + gamma * max(0, dConf - dI_evid))."""
    path = sum(jsd2(trace.consensus(r - 1), trace.consensus(r)) for r in range(1, trace.n_rounds + 1))
    d_conf = trace.confidence(trace.n_rounds) - trace.confidence(0)
    if trace.evidence_info is None:
        d_info = 0.0
    else:
        d_info = float(trace.evidence_info[-1] - trace.evidence_info[0])
    laundering = max(0.0, d_conf - d_info)
    ced = min(1.0, path + params.gamma * laundering)
    return {"ced": float(ced), "path_drift": float(path), "delta_conf": float(d_conf),
            "delta_info": float(d_info), "laundering": float(laundering)}


def dissent_collapse_ratio(trace: DeliberationTrace, params: ScoreParameters = DEFAULT_PARAMS) -> Dict[str, float]:
    d0 = trace.dissent(0)
    dr = trace.dissent(trace.n_rounds)
    rho = 0.0 if d0 < params.d0_min else max(0.0, min(1.0, 1.0 - dr / d0))
    return {"rho": float(rho), "dissent_round0": float(d0), "dissent_final": float(dr)}


def confidence_ceiling(sigma: float, params: ScoreParameters = DEFAULT_PARAMS) -> float:
    """Epistemic Confidence Ceiling c_max = 1 - kappa * sigma."""
    return float(1.0 - params.kappa * sigma)


def spce_encounter(confidence: float, sigma: float, params: ScoreParameters = DEFAULT_PARAMS) -> float:
    """Normalized ceiling excess in [0, 1]."""
    return float(max(0.0, confidence - confidence_ceiling(sigma, params)) / params.kappa)


def expected_calibration_error(conf: np.ndarray, correct: np.ndarray, n_bins: int = 10) -> float:
    conf = np.asarray(conf, dtype=float)
    correct = np.asarray(correct, dtype=float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(conf, bins[1:-1], right=True), 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        mask = idx == b
        if mask.any():
            ece += mask.mean() * abs(correct[mask].mean() - conf[mask].mean())
    return float(ece)


def spce_cohort(conf: np.ndarray, sigma: np.ndarray, correct: np.ndarray,
                params: ScoreParameters = DEFAULT_PARAMS, n_bins: int = 10) -> Dict[str, float]:
    """Cohort-level Sparsity-Penalized Calibration Error."""
    conf = np.asarray(conf, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    ceiling = 1.0 - params.kappa * sigma
    capped = np.minimum(conf, ceiling)
    excess = np.maximum(0.0, conf - ceiling) / params.kappa
    ece_raw = expected_calibration_error(conf, correct, n_bins)
    ece_capped = expected_calibration_error(capped, correct, n_bins)
    return {"ece_raw": ece_raw, "ece_capped": ece_capped,
            "mean_ceiling_excess": float(excess.mean()), "spce": float(ece_capped + excess.mean())}


# --------------------------------------------------------------------------------------
# 3. Score, tiers, VOI
# --------------------------------------------------------------------------------------

TIER_LABELS = {1: "Tier I - Grounded", 2: "Tier II - Guarded", 3: "Tier III - Mandatory AI Abstention"}


def governance_tier(score: float, params: ScoreParameters = DEFAULT_PARAMS) -> int:
    if not np.isfinite(score):
        return 3
    if score >= params.tier1_min:
        return 1
    if score >= params.tier2_min:
        return 2
    return 3


def _score_from_parts(sigma: float, ced: float, rho: float, conf: float, params: ScoreParameters) -> Tuple[float, Dict[str, float]]:
    spce_e = spce_encounter(conf, sigma, params)
    penalty = (params.a_sigma * sigma + params.a_ced * ced
               + params.a_rho * sigma * rho + params.a_spce * spce_e)
    score = 100.0 * (1.0 - min(1.0, max(0.0, penalty)))
    return float(round(score, 6)), {"spce_encounter": spce_e, "penalty": float(penalty),
                                     "ceiling": confidence_ceiling(sigma, params)}


def compute_score(labs: Mapping[str, Optional[LabObservation]], trace: DeliberationTrace,
                  params: ScoreParameters = DEFAULT_PARAMS) -> Dict[str, float]:
    sigma = sparsity_index(labs)
    ced = collective_epistemic_drift(trace, params)
    col = dissent_collapse_ratio(trace, params)
    conf = trace.confidence(trace.n_rounds)
    score, extra = _score_from_parts(sigma, ced["ced"], col["rho"], conf, params)
    out = {"score": score, "sigma": sigma, "final_confidence": conf}
    out.update(ced)
    out.update(col)
    out.update(extra)
    return out


def counterfactual_voi(labs: Mapping[str, Optional[LabObservation]], trace: DeliberationTrace,
                       params: ScoreParameters = DEFAULT_PARAMS) -> List[Dict[str, float]]:
    """Rank biomarkers by score recovery if refreshed now (dt_j = 0).

    First-order counterfactual: the agents' deliberation trace is held fixed,
    so VOI captures only the governance-layer recovery, not how agent beliefs
    would change after seeing the new value.
    """
    base = compute_score(labs, trace, params)["score"]
    out = []
    for b in BIOMARKERS:
        cf = dict(labs)
        cf[b.key] = LabObservation(value=0.0, delta_t_h=0.0)  # value is irrelevant to sigma
        s_cf = compute_score(cf, trace, params)["score"]
        out.append({"key": b.key, "label": b.label, "voi_points": round(s_cf - base, 4),
                    "score_if_refreshed": s_cf})
    out.sort(key=lambda d: (-d["voi_points"], d["key"]))
    return out


# --------------------------------------------------------------------------------------
# 4. Deterministic guideline fallback (SSC 2026 / KDIGO) on OBSERVED data only
# --------------------------------------------------------------------------------------


@dataclass
class BedsideObservations:
    map_mmhg: Optional[float] = None
    heart_rate: Optional[float] = None
    resp_rate: Optional[float] = None
    temp_c: Optional[float] = None
    spo2: Optional[float] = None
    gcs: Optional[int] = None
    age_years: Optional[float] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    sex: Optional[str] = None                   # "M" / "F"
    suspected_infection: bool = False
    on_vasopressor: bool = False
    mechanically_ventilated: bool = False
    urine_output_ml_kg_h_6h: Optional[float] = None
    creatinine_mg_dl: Optional[float] = None
    baseline_creatinine_mg_dl: Optional[float] = None
    creatinine_rise_48h_mg_dl: Optional[float] = None
    lactate_mmol_l: Optional[float] = None


@dataclass
class Recommendation:
    rule_id: str
    text: str
    source: str
    verification_note: str = ""


def predicted_body_weight(height_cm: float, sex: str) -> float:
    base = 50.0 if sex.upper().startswith("M") else 45.5
    return base + 0.91 * (height_cm - 152.4)


def kdigo_aki_stage(obs: BedsideObservations) -> Optional[int]:
    """KDIGO 2012 AKI staging from available creatinine / urine-output data."""
    stage = 0
    known = False
    cr, base = obs.creatinine_mg_dl, obs.baseline_creatinine_mg_dl
    if cr is not None and base is not None and base > 0:
        known = True
        ratio = cr / base
        if ratio >= 3.0 or cr >= 4.0:
            stage = max(stage, 3)
        elif ratio >= 2.0:
            stage = max(stage, 2)
        elif ratio >= 1.5:
            stage = max(stage, 1)
    if obs.creatinine_rise_48h_mg_dl is not None:
        known = True
        if obs.creatinine_rise_48h_mg_dl >= 0.3:
            stage = max(stage, 1)
    if obs.urine_output_ml_kg_h_6h is not None:
        known = True
        if obs.urine_output_ml_kg_h_6h < 0.5:
            stage = max(stage, 1)  # >=6 h window; stages 2-3 need 12-24 h windows
    return stage if known else None


def guideline_fallback(obs: BedsideObservations) -> List[Recommendation]:
    """Deterministic rule engine. Always returns >=1 item (coverage by construction).

    Recommendations are prompts for clinician review, not orders. Wording is a
    paraphrase; the clinician must consult the primary SSC 2026 and KDIGO texts.
    """
    recs: List[Recommendation] = []
    ssc = "Surviving Sepsis Campaign 2026 adult guideline (Crit Care Med / Intensive Care Med)"
    hypotension = obs.map_mmhg is not None and obs.map_mmhg < 65.0
    high_lactate = obs.lactate_mmol_l is not None and obs.lactate_mmol_l >= 2.0
    possible_shock = obs.suspected_infection and (hypotension or obs.on_vasopressor or high_lactate)

    if obs.suspected_infection:
        recs.append(Recommendation(
            "SSC-ABX", "Possible sepsis/septic shock: give antimicrobials immediately, ideally within 1 h of "
            "recognition when shock is possible; obtain cultures without delaying therapy.", ssc))
    if obs.suspected_infection and obs.lactate_mmol_l is None:
        recs.append(Recommendation(
            "SSC-LACT", "Lactate not available: measure arterial/venous lactate now (stat).", ssc,
            "Lactate measurement carried forward from SSC 2021; confirm 2026 wording."))
    if possible_shock and not obs.on_vasopressor:
        vol = f" (~{30.0 * obs.weight_kg:.0f} mL for {obs.weight_kg:.0f} kg)" if obs.weight_kg else ""
        recs.append(Recommendation(
            "SSC-FLUID", "Initial resuscitation with balanced crystalloid; consider 30 mL/kg within the first "
            f"3 h{vol}, individualized and reassessed with dynamic measures of fluid responsiveness.", ssc,
            "Strength/wording of the 30 mL/kg statement in SSC 2026 not verified from primary text."))
    if hypotension or obs.on_vasopressor:
        target = "60-65 mm Hg" if (obs.age_years is not None and obs.age_years >= 65) else "65 mm Hg"
        recs.append(Recommendation(
            "SSC-MAP", f"Vasopressor support: norepinephrine first line, titrate to an initial MAP target of "
            f"{target}; consider adding vasopressin if escalating.", ssc,
            "Age >=65 lower range per secondary summaries of SSC 2026; confirm against primary text."))
    if obs.mechanically_ventilated:
        if obs.height_cm is not None and obs.sex:
            pbw = predicted_body_weight(obs.height_cm, obs.sex)
            vt = f" (~{6.0 * pbw:.0f} mL at PBW {pbw:.1f} kg)"
        else:
            vt = " (height/sex needed to compute predicted body weight)"
        recs.append(Recommendation(
            "SSC-VENT", f"Lung-protective ventilation if sepsis-induced ARDS: tidal volume 6 mL/kg PBW{vt}, "
            "plateau pressure <= 30 cm H2O.", "SSC 2021/2026 ARDS recommendations",
            "Carried forward from SSC 2021; confirm 2026 wording."))
    aki = kdigo_aki_stage(obs)
    if aki is not None and aki >= 1:
        recs.append(Recommendation(
            "KDIGO-AKI", f"KDIGO AKI stage >= {aki}: avoid/stop nephrotoxins, review drug dosing, optimize "
            "volume status and perfusion, monitor creatinine and hourly urine output.",
            "KDIGO Clinical Practice Guideline for AKI (2012)"))
    if not recs:
        recs.append(Recommendation(
            "BASE-MONITOR", "No guideline trigger met on observed data: continue standard monitoring and "
            "re-evaluate when new observations arrive.", "Default safe-monitoring rule"))
    return recs


# --------------------------------------------------------------------------------------
# 5. Privacy layer: HMAC-SHA256 pseudonymization, PHI scrubbing, relative time
# --------------------------------------------------------------------------------------

SALT_ENV_VAR = "ALSAMADANI_HMAC_SALT"
DEMO_SALT = b"DEMO-ONLY-NOT-FOR-PRODUCTION"


class PrivacyError(RuntimeError):
    pass


class Pseudonymizer:
    """Salted, domain-separated HMAC-SHA256 tokens: ANON-<16 hex>.

    The salt must be secret, high-entropy and held outside the LLM context.
    Truncation to 64 bits keeps tokens short; collision probability is
    negligible for single-hospital cohorts but should be checked for very
    large linkage projects.
    """

    def __init__(self, salt: Optional[bytes] = None, allow_demo_salt: bool = False):
        if salt is None:
            env = os.environ.get(SALT_ENV_VAR)
            if env:
                salt = env.encode("utf-8")
            elif allow_demo_salt:
                salt = DEMO_SALT
            else:
                raise PrivacyError(f"no salt supplied and {SALT_ENV_VAR} unset (fail-closed)")
        if len(salt) < 16:
            raise PrivacyError("salt must be >= 16 bytes")
        self._salt = salt

    def token(self, kind: str, raw_identifier: str) -> str:
        if not raw_identifier:
            raise PrivacyError("empty identifier")
        msg = f"{kind}:{raw_identifier.strip()}".encode("utf-8")
        return "ANON-" + hmac.new(self._salt, msg, hashlib.sha256).hexdigest()[:16].upper()

    def patient(self, mrn: str) -> str:
        return self.token("patient", mrn)

    def unit(self, unit_identifier: str) -> str:
        return self.token("unit", unit_identifier)


PHI_PATTERNS: Tuple[Tuple[str, re.Pattern], ...] = (
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("PHONE", re.compile(r"(?:\+966|00966)[\s-]?\d{1,2}[\s-]?\d{3}[\s-]?\d{4}\b|\b05\d[\s-]?\d{3}[\s-]?\d{4}\b")),
    ("SAUDI_ID", re.compile(r"\b[12]\d{9}\b")),                      # national ID (1...) / Iqama (2...)
    ("MRN", re.compile(r"\b(?:MRN|Medical\s*Record(?:\s*No\.?|\s*Number)?|File\s*No\.?)\s*[:#]?\s*[A-Z0-9-]{4,}\b", re.I)),
    ("DATE", re.compile(r"\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}(?:[T ]\d{1,2}:\d{2}(?::\d{2})?)?\b|\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b")),
    ("NAME", re.compile(r"\b(?:Name|Patient|Pt)\s*[:\-]\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}")),
    ("FACILITY", re.compile(r"\b(?:King\s+Fahad\s+Medical\s+City|KFMC|King\s+Faisal\s+(?:Specialist\s+)?Hospital"
                            r"|[A-Z][a-z]+\s+(?:General\s+)?Hospital|Medical\s+City)\b")),
    ("LONG_ID", re.compile(r"\b\d{7,}\b")),
)


def scrub_phi(text: str) -> Tuple[str, Dict[str, int]]:
    """Replace PHI-like spans with [REDACTED-<TYPE>]. Returns text and counts."""
    counts: Dict[str, int] = {}
    for name, pat in PHI_PATTERNS:
        text, n = pat.subn(f"[REDACTED-{name}]", text)
        if n:
            counts[name] = counts.get(name, 0) + n
    return text, counts


def assert_no_phi(text: str) -> None:
    """Fail-closed guard: raise if any PHI pattern survives."""
    for name, pat in PHI_PATTERNS:
        if pat.search(text):
            raise PrivacyError(f"residual PHI pattern detected: {name}")


def to_relative_hours(timestamps: Iterable, index_time) -> List[float]:
    """Convert absolute timestamps to hours elapsed since index_time (dates dropped)."""
    import datetime as _dt

    def _parse(x):
        if isinstance(x, _dt.datetime):
            return x
        return _dt.datetime.fromisoformat(str(x))

    t0 = _parse(index_time)
    return [round((_parse(t) - t0).total_seconds() / 3600.0, 4) for t in timestamps]


def build_llm_context(pseudo: Pseudonymizer, mrn: str, unit_id: str, t_eval_h: float,
                      labs: Mapping[str, Optional[LabObservation]], obs: BedsideObservations,
                      free_text: str = "") -> str:
    """Assemble the only text allowed into an LLM prompt. Fail-closed on residual PHI."""
    lines = [f"patient_token: {pseudo.patient(mrn)}", f"unit_token: {pseudo.unit(unit_id)}",
             f"evaluation_time_h_since_icu_admission: {t_eval_h:.2f}"]
    for b in BIOMARKERS:
        o = labs.get(b.key)
        if o is not None and o.observed:
            lines.append(f"{b.key}: {o.value} {b.unit} (measured {o.delta_t_h:.2f} h before evaluation)")
        else:
            lines.append(f"{b.key}: NOT AVAILABLE")
    for k, v in asdict(obs).items():
        if v is not None:
            lines.append(f"{k}: {v}")
    if free_text:
        lines.append("note: " + scrub_phi(free_text)[0])
    ctx = "\n".join(lines)
    # tokens contain 16 hex chars -> mask them before the residual-PHI check
    assert_no_phi(re.sub(r"ANON-[0-9A-F]{16}", "ANON-TOKEN", ctx))
    if mrn in ctx or unit_id in ctx:
        raise PrivacyError("raw identifier leaked into context")
    return ctx


# --------------------------------------------------------------------------------------
# 6. Governance decision (fail-closed)
# --------------------------------------------------------------------------------------


@dataclass
class GovernanceDecision:
    score: Optional[float]
    tier: int
    tier_label: str
    consensus_diagnosis_index: Optional[int]
    consensus_diagnosis_label: Optional[str]
    calibrated_probability: Optional[float]
    differentials: List[Tuple[str, float]] = field(default_factory=list)
    dissent_rationales: List[str] = field(default_factory=list)
    voi_ranking: List[Dict[str, float]] = field(default_factory=list)
    guideline_fallback: List[Recommendation] = field(default_factory=list)
    components: Dict[str, float] = field(default_factory=dict)
    abstention_reason: Optional[str] = None


def evaluate_encounter(labs: Mapping[str, Optional[LabObservation]], trace: Optional[DeliberationTrace],
                       obs: BedsideObservations, params: ScoreParameters = DEFAULT_PARAMS) -> GovernanceDecision:
    """Score an encounter and apply the tier policy. Any failure -> Tier III."""
    fallback = guideline_fallback(obs)
    try:
        if trace is None:
            raise ValueError("no deliberation trace")
        comps = compute_score(labs, trace, params)
        score = comps["score"]
        tier = governance_tier(score, params)
        voi = counterfactual_voi(labs, trace, params)
    except Exception as exc:  # fail-closed
        return GovernanceDecision(None, 3, TIER_LABELS[3], None, None, None,
                                  guideline_fallback=fallback,
                                  abstention_reason=f"fail-closed: {type(exc).__name__}: {exc}")

    final = trace.consensus(trace.n_rounds)
    labels = list(trace.diagnosis_labels) if trace.diagnosis_labels else [f"dx_{i}" for i in range(len(final))]
    order = np.argsort(-final)
    ceiling = comps["ceiling"]

    if tier == 1:
        idx = int(order[0])
        return GovernanceDecision(score, 1, TIER_LABELS[1], idx, labels[idx],
                                  round(float(min(final[idx], ceiling)), 4), components=comps,
                                  voi_ranking=voi[:3], guideline_fallback=fallback)
    if tier == 2:
        diffs = [(labels[int(i)], round(float(min(final[int(i)], ceiling)), 4)) for i in order[:2]]
        rationales = list(trace.round0_rationales or [])
        return GovernanceDecision(score, 2, TIER_LABELS[2], None, None, None, differentials=diffs,
                                  dissent_rationales=rationales, voi_ranking=voi[:3],
                                  guideline_fallback=fallback, components=comps)
    return GovernanceDecision(score, 3, TIER_LABELS[3], None, None, None, voi_ranking=voi,
                              guideline_fallback=fallback, components=comps,
                              abstention_reason="S_AlSamadani < 50: mandatory AI abstention")


# --------------------------------------------------------------------------------------
# 7. Demonstration cases (illustrative vignettes, author-constructed)
# --------------------------------------------------------------------------------------

DX_LABELS = ("Septic shock", "Cardiogenic shock", "Hypovolemic shock", "Obstructive shock")


def demo_case_a() -> Tuple[Dict[str, LabObservation], DeliberationTrace, BedsideObservations]:
    """Case A: dense, fresh labs; agents agree early; confidence rises modestly with evidence."""
    labs = {
        "lactate": LabObservation(4.1, 0.25), "pf_ratio": LabObservation(210.0, 0.5),
        "creatinine": LabObservation(1.9, 1.0), "platelets": LabObservation(98.0, 1.0),
        "wbc": LabObservation(18.2, 1.0), "inr": LabObservation(1.6, 1.0),
        "bicarbonate": LabObservation(17.0, 0.5), "bilirubin": LabObservation(1.4, 1.0),
    }
    r0 = [[0.78, 0.10, 0.08, 0.04], [0.74, 0.14, 0.08, 0.04], [0.80, 0.08, 0.08, 0.04],
          [0.70, 0.18, 0.08, 0.04], [0.76, 0.12, 0.08, 0.04]]
    r1 = [[0.80, 0.10, 0.06, 0.04], [0.78, 0.12, 0.06, 0.04], [0.81, 0.09, 0.06, 0.04],
          [0.76, 0.14, 0.06, 0.04], [0.79, 0.11, 0.06, 0.04]]
    r2 = [[0.81, 0.10, 0.05, 0.04], [0.80, 0.11, 0.05, 0.04], [0.82, 0.09, 0.05, 0.04],
          [0.79, 0.12, 0.05, 0.04], [0.80, 0.11, 0.05, 0.04]]
    trace = DeliberationTrace(np.array([r0, r1, r2]), diagnosis_labels=DX_LABELS)
    obs = BedsideObservations(map_mmhg=61, heart_rate=118, resp_rate=26, temp_c=38.9, spo2=92, gcs=14,
                              age_years=58, weight_kg=80, height_cm=175, sex="M", suspected_infection=True,
                              mechanically_ventilated=False, creatinine_mg_dl=1.9,
                              baseline_creatinine_mg_dl=1.0, lactate_mmol_l=4.1)
    return labs, trace, obs


def demo_case_b() -> Tuple[Dict[str, LabObservation], DeliberationTrace, BedsideObservations]:
    """Case B: admission triage at T=0 h; no lactate/ABG; agents disagree, then converge with
    rising confidence and no new evidence (confidence laundering)."""
    labs = {
        "lactate": None, "pf_ratio": None,
        "creatinine": LabObservation(1.6, 3.0), "platelets": LabObservation(142.0, 3.0),
        "wbc": LabObservation(14.5, 3.0), "inr": None, "bicarbonate": None, "bilirubin": None,
    }
    r0 = [[0.45, 0.30, 0.15, 0.10], [0.20, 0.50, 0.20, 0.10], [0.35, 0.25, 0.30, 0.10],
          [0.25, 0.25, 0.20, 0.30], [0.40, 0.35, 0.15, 0.10]]
    r1 = [[0.60, 0.25, 0.10, 0.05], [0.45, 0.40, 0.10, 0.05], [0.55, 0.25, 0.15, 0.05],
          [0.50, 0.25, 0.10, 0.15], [0.60, 0.30, 0.05, 0.05]]
    r2 = [[0.85, 0.10, 0.03, 0.02], [0.82, 0.12, 0.04, 0.02], [0.84, 0.10, 0.04, 0.02],
          [0.83, 0.10, 0.03, 0.04], [0.86, 0.10, 0.02, 0.02]]
    rationales = ["Fever + leukocytosis favour sepsis", "JVP/edema not documented; cannot exclude cardiogenic",
                  "Possible GI losses; hypovolemia plausible", "Tachycardia + hypoxia: exclude PE/obstructive",
                  "Sepsis most likely but lactate unknown"]
    trace = DeliberationTrace(np.array([r0, r1, r2]), diagnosis_labels=DX_LABELS, round0_rationales=rationales)
    obs = BedsideObservations(map_mmhg=58, heart_rate=124, resp_rate=28, temp_c=38.4, spo2=91, gcs=13,
                              age_years=67, weight_kg=72, height_cm=165, sex="F", suspected_infection=True,
                              mechanically_ventilated=True, creatinine_mg_dl=1.6, creatinine_rise_48h_mg_dl=None)
    return labs, trace, obs


# --------------------------------------------------------------------------------------
# 8. Synthetic Monte Carlo validation + scaling benchmark
# --------------------------------------------------------------------------------------

SCENARIOS = {
    # name: (prob. each lab observed, max staleness as multiple of half-life, sharpening tau, description)
    "S0": (0.95, 1.0, 0.90, "dense, fresh labs; mild sharpening"),
    "S1": (0.60, 2.0, 0.90, "moderate sparsity"),
    "S2": (0.25, 3.0, 0.90, "high sparsity, no laundering"),
    "S3": (0.25, 3.0, 0.60, "high sparsity + confidence laundering"),
}


@dataclass(frozen=True)
class SimConfig:
    n_diagnoses: int = 4
    signal_scale: float = 3.0     # beta = signal_scale * (1 - sigma)
    shared_bias_sd: float = 1.0   # common-mode (same model family) prior error
    idio_sd: float = 1.0          # agent-specific noise
    conformity: float = 0.5       # eta: pull toward consensus per round


def _softmax(x: np.ndarray) -> np.ndarray:
    z = x - x.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def simulate_encounter(rng: np.random.Generator, scenario: str, n_agents: int = 5, n_rounds: int = 2,
                       catfish: bool = False, cfg: SimConfig = SimConfig()):
    q, stale_mult, tau, _ = SCENARIOS[scenario]
    labs: Dict[str, Optional[LabObservation]] = {}
    for b in BIOMARKERS:
        if rng.random() < q:
            labs[b.key] = LabObservation(1.0, float(rng.uniform(0.0, stale_mult * b.half_life_h)))
        else:
            labs[b.key] = None
    sigma = sparsity_index(labs)
    k = cfg.n_diagnoses
    y = int(rng.integers(k))
    beta = cfg.signal_scale * (1.0 - sigma)
    shared = rng.normal(0.0, cfg.shared_bias_sd, size=k)
    logits = beta * np.eye(k)[y] + shared + rng.normal(0.0, cfg.idio_sd, size=(n_agents, k))
    p = _softmax(logits)
    rounds = [p.copy()]
    for _ in range(n_rounds):
        pbar = p.mean(axis=0, keepdims=True)
        mixed = (1.0 - cfg.conformity) * p + cfg.conformity * pbar
        new = _normalize(mixed ** (1.0 / tau))
        if catfish:
            new[0] = rounds[0][0]  # dissenting agent holds its independent round-0 view
        p = new
        rounds.append(p.copy())
    trace = DeliberationTrace(np.stack(rounds))
    comps = compute_score(labs, trace)
    correct = int(np.argmax(trace.consensus(n_rounds)) == y)
    return comps, correct, sigma


def auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Mann-Whitney AUROC with tie handling."""
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=int)
    pos, neg = scores[labels == 1], scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    allv = np.concatenate([pos, neg])[order]
    ranks = np.empty(len(allv))
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        ranks[i:j + 1] = 0.5 * (i + j) + 1.0
        i = j + 1
    r = np.empty(len(allv))
    r[order] = ranks
    r_pos = r[: len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg)))


def run_monte_carlo_validation(n_total: int = 1000, seed: int = 20261110, n_boot: int = 1000) -> Dict:
    rng = np.random.default_rng(seed)
    names = list(SCENARIOS)
    per = n_total // len(names)
    rows = []
    for s in names:
        for _ in range(per):
            comps, correct, sigma = simulate_encounter(rng, s)
            rows.append((s, comps["score"], correct, comps["final_confidence"], sigma))
    scores = np.array([r[1] for r in rows])
    correct = np.array([r[2] for r in rows])
    conf = np.array([r[3] for r in rows])
    sigma = np.array([r[4] for r in rows])
    auc = auroc(scores, correct)
    brng = np.random.default_rng(seed + 1)
    boots = []
    for _ in range(n_boot):
        idx = brng.integers(0, len(scores), len(scores))
        a = auroc(scores[idx], correct[idx])
        if np.isfinite(a):
            boots.append(a)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    auc_conf = auroc(conf, correct)
    per_scen = {}
    for s in names:
        m = np.array([r[0] == s for r in rows])
        tiers = np.array([governance_tier(x) for x in scores[m]])
        per_scen[s] = {
            "description": SCENARIOS[s][3], "n": int(m.sum()),
            "mean_sigma": float(sigma[m].mean()), "mean_score": float(scores[m].mean()),
            "consensus_accuracy": float(correct[m].mean()), "mean_confidence": float(conf[m].mean()),
            "tier1_frac": float((tiers == 1).mean()), "tier2_frac": float((tiers == 2).mean()),
            "tier3_frac": float((tiers == 3).mean()),
        }
    tiers_all = np.array([governance_tier(x) for x in scores])
    by_tier = {}
    for t in (1, 2, 3):
        m = tiers_all == t
        by_tier[f"tier{t}"] = {"n": int(m.sum()),
                               "consensus_accuracy": float(correct[m].mean()) if m.any() else float("nan")}
    cal = spce_cohort(conf, sigma, correct)
    return {"n": int(len(rows)), "seed": seed, "auroc_score": auc, "auroc_ci95": [float(lo), float(hi)],
            "auroc_raw_confidence": auc_conf, "per_scenario": per_scen, "by_tier": by_tier,
            "calibration": cal, "overall_accuracy": float(correct.mean())}


def run_scaling_benchmark(agents: Sequence[int] = (3, 5, 7, 10), rounds: Sequence[int] = (1, 2, 4, 6),
                          n_per_cell: int = 200, scenario: str = "S3", seed: int = 20261111) -> Dict:
    out = []
    for m in agents:
        for r in rounds:
            cell = {"M": m, "R": r}
            for cat in (False, True):
                rng = np.random.default_rng(seed + 1000 * m + 10 * r)  # common random numbers across arms
                rho, sc, acc = [], [], []
                for _ in range(n_per_cell):
                    comps, correct, _ = simulate_encounter(rng, scenario, n_agents=m, n_rounds=r, catfish=cat)
                    rho.append(comps["rho"]); sc.append(comps["score"]); acc.append(correct)
                tag = "catfish" if cat else "naive"
                cell[f"{tag}_rho"] = float(np.mean(rho))
                cell[f"{tag}_score"] = float(np.mean(sc))
                cell[f"{tag}_accuracy"] = float(np.mean(acc))
            out.append(cell)
    return {"scenario": scenario, "n_per_cell": n_per_cell, "seed": seed, "cells": out}


# --------------------------------------------------------------------------------------
# 9. MIMIC-IV v3.1 / eICU-CRD loader
# --------------------------------------------------------------------------------------


def _read_table(root: Path, stem: str, usecols: Sequence[str], filters: Optional[Dict] = None):
    import pandas as pd

    for ext in (".parquet", ".csv.gz", ".csv"):
        p = root / f"{stem}{ext}"
        if p.exists():
            if ext == ".parquet":
                df = pd.read_parquet(p, columns=list(usecols))
            else:
                chunks = []
                for ch in pd.read_csv(p, usecols=list(usecols), chunksize=1_000_000, low_memory=False):
                    if filters:
                        for col, allowed in filters.items():
                            ch = ch[ch[col].isin(allowed)]
                    chunks.append(ch)
                df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=list(usecols))
            if filters and ext == ".parquet":
                for col, allowed in filters.items():
                    df = df[df[col].isin(allowed)]
            return df
    raise FileNotFoundError(f"{stem}.(parquet|csv.gz|csv) not found under {root}")


def load_mimic_iv_cohort_dataframe(root, source: str = "mimic-iv", eval_hours_after_admission: float = 0.0,
                                   lookback_hours: float = 72.0, pseudonymizer: Optional[Pseudonymizer] = None,
                                   stay_ids: Optional[Sequence[int]] = None):
    """Build one row per ICU stay with, for each biomarker, the latest value and its
    elapsed time dt_j (hours) before the evaluation time, plus sigma.

    source="mimic-iv": expects <root>/icu/icustays, <root>/hosp/labevents, <root>/icu/chartevents
    source="eicu":     expects <root>/patient, <root>/lab  (offsets in minutes)
    Files may be .parquet, .csv.gz or .csv. Raw identifiers are replaced by HMAC tokens;
    absolute times are dropped. Access to MIMIC-IV / eICU requires PhysioNet credentialing and
    a signed DUA; do not send rows to third-party LLM services that the DUA does not permit.
    """
    import pandas as pd

    root = Path(root)
    pseudo = pseudonymizer or Pseudonymizer()
    records = []

    if source == "mimic-iv":
        stays = _read_table(root / "icu", "icustays", ["subject_id", "stay_id", "intime", "first_careunit"])
        if stay_ids is not None:
            stays = stays[stays["stay_id"].isin(stay_ids)]
        stays = stays.assign(intime=pd.to_datetime(stays["intime"]))
        itemid_to_key = {i: b.key for b in BIOMARKERS for i in b.mimic_itemids}
        labs = _read_table(root / "hosp", "labevents", ["subject_id", "itemid", "charttime", "valuenum"],
                           filters={"itemid": list(itemid_to_key), "subject_id": list(stays["subject_id"].unique())})
        labs = labs.assign(charttime=pd.to_datetime(labs["charttime"]), key=labs["itemid"].map(itemid_to_key))
        try:
            fio2 = _read_table(root / "icu", "chartevents", ["stay_id", "itemid", "charttime", "valuenum"],
                               filters={"itemid": [MIMIC_FIO2_CHART_ITEMID], "stay_id": list(stays["stay_id"])})
            fio2 = fio2.assign(charttime=pd.to_datetime(fio2["charttime"]))
        except FileNotFoundError:
            fio2 = pd.DataFrame(columns=["stay_id", "itemid", "charttime", "valuenum"])
        for st in stays.itertuples(index=False):
            t_eval = st.intime + pd.Timedelta(hours=eval_hours_after_admission)
            lo = t_eval - pd.Timedelta(hours=lookback_hours)
            sub = labs[(labs["subject_id"] == st.subject_id) & (labs["charttime"] <= t_eval)
                       & (labs["charttime"] >= lo) & labs["valuenum"].notna()]
            fsub = fio2[(fio2["stay_id"] == st.stay_id) & (fio2["charttime"] <= t_eval) & fio2["valuenum"].notna()]
            row = {"patient_token": pseudo.patient(str(st.subject_id)), "stay_token": pseudo.token("stay", str(st.stay_id)),
                   "unit_token": pseudo.unit(str(st.first_careunit)), "eval_h_since_icu_admission": eval_hours_after_admission}
            for b in BIOMARKERS:
                bs = sub[sub["key"] == b.key].sort_values("charttime")
                val, dt = None, None
                if len(bs):
                    last = bs.iloc[-1]
                    val = float(last["valuenum"])
                    dt = (t_eval - last["charttime"]).total_seconds() / 3600.0
                    if b.key == "pf_ratio":
                        fs = fsub[fsub["charttime"] <= last["charttime"] + pd.Timedelta(hours=1)].sort_values("charttime")
                        if len(fs):
                            f = float(fs.iloc[-1]["valuenum"])
                            f = f / 100.0 if f > 1.0 else f
                            val = val / f if f > 0 else None
                        else:
                            val = None  # PaO2 without FiO2 -> ratio unavailable
                            dt = None
                row[f"{b.key}_value"] = val
                row[f"{b.key}_dt_h"] = None if dt is None else round(dt, 4)
            records.append(row)

    elif source == "eicu":
        pats = _read_table(root, "patient", ["patientunitstayid", "uniquepid", "hospitalid", "unittype"])
        if stay_ids is not None:
            pats = pats[pats["patientunitstayid"].isin(stay_ids)]
        name_to_key = {n.lower(): b.key for b in BIOMARKERS for n in b.eicu_labnames}
        lab = _read_table(root, "lab", ["patientunitstayid", "labresultoffset", "labname", "labresult"],
                          filters={"patientunitstayid": list(pats["patientunitstayid"])})
        lab = lab.assign(lname=lab["labname"].astype(str).str.strip().str.lower())
        t_eval_min = eval_hours_after_admission * 60.0
        for st in pats.itertuples(index=False):
            sub = lab[(lab["patientunitstayid"] == st.patientunitstayid) & (lab["labresultoffset"] <= t_eval_min)
                      & (lab["labresultoffset"] >= t_eval_min - lookback_hours * 60.0) & lab["labresult"].notna()]
            row = {"patient_token": pseudo.patient(str(st.uniquepid)),
                   "stay_token": pseudo.token("stay", str(st.patientunitstayid)),
                   "unit_token": pseudo.unit(f"{st.hospitalid}:{st.unittype}"),
                   "eval_h_since_icu_admission": eval_hours_after_admission}
            fio2 = sub[sub["lname"] == EICU_FIO2_LABNAME.lower()].sort_values("labresultoffset")
            for b in BIOMARKERS:
                bs = sub[sub["lname"].map(name_to_key) == b.key].sort_values("labresultoffset")
                val, dt = None, None
                if len(bs):
                    last = bs.iloc[-1]
                    val = float(last["labresult"])
                    dt = (t_eval_min - float(last["labresultoffset"])) / 60.0
                    if b.key == "pf_ratio":
                        fs = fio2[fio2["labresultoffset"] <= float(last["labresultoffset"]) + 60]
                        if len(fs):
                            f = float(fs.iloc[-1]["labresult"])
                            f = f / 100.0 if f > 1.0 else f
                            val = val / f if f > 0 else None
                        else:
                            val, dt = None, None
                row[f"{b.key}_value"] = val
                row[f"{b.key}_dt_h"] = None if dt is None else round(dt, 4)
            records.append(row)
    else:
        raise ValueError("source must be 'mimic-iv' or 'eicu'")

    df = pd.DataFrame.from_records(records)
    if len(df):
        df["sigma"] = [sparsity_index(row_to_labs(r)) for r in df.to_dict("records")]
    return df


def row_to_labs(row: Mapping) -> Dict[str, Optional[LabObservation]]:
    out: Dict[str, Optional[LabObservation]] = {}
    for b in BIOMARKERS:
        v, dt = row.get(f"{b.key}_value"), row.get(f"{b.key}_dt_h")
        ok = v is not None and dt is not None and not (isinstance(v, float) and math.isnan(v)) \
            and not (isinstance(dt, float) and math.isnan(dt))
        out[b.key] = LabObservation(float(v), float(dt)) if ok else None
    return out


# --------------------------------------------------------------------------------------
# 10. Reporting / CLI
# --------------------------------------------------------------------------------------


def _fmt(x: float, nd: int = 1) -> str:
    return f"{x:.{nd}f}"


def export_tex_macros(path: Path, results: Dict) -> None:
    a, b = results["case_a"], results["case_b"]
    mc, sc = results["monte_carlo"], results["scaling"]
    top = b["voi"][0]
    m = {
        "CaseAScore": _fmt(a["score"]), "CaseASigma": _fmt(a["sigma"], 3), "CaseATier": "I",
        "CaseBScore": _fmt(b["score"]), "CaseBSigma": _fmt(b["sigma"], 3), "CaseBTier": "III",
        "CaseBCED": _fmt(b["ced"], 3), "CaseBRho": _fmt(b["rho"], 3), "CaseBConf": _fmt(b["final_confidence"], 3),
        "CaseBCeiling": _fmt(b["ceiling"], 3), "CaseBLaundering": _fmt(b["laundering"], 3),
        "CaseARho": _fmt(a["rho"], 3), "CaseACED": _fmt(a["ced"], 3), "CaseAConf": _fmt(a["final_confidence"], 3),
        "CaseACeiling": _fmt(a["ceiling"], 3),
        "TopVOILabel": top["label"], "TopVOIPoints": _fmt(top["voi_points"]),
        "SecondVOILabel": b["voi"][1]["label"], "SecondVOIPoints": _fmt(b["voi"][1]["voi_points"]),
        "ThirdVOILabel": b["voi"][2]["label"], "ThirdVOIPoints": _fmt(b["voi"][2]["voi_points"]),
        "MCN": str(mc["n"]), "MCAUROC": _fmt(mc["auroc_score"], 3),
        "MCAUROCLo": _fmt(mc["auroc_ci95"][0], 3), "MCAUROCHi": _fmt(mc["auroc_ci95"][1], 3),
        "MCAUROCConf": _fmt(mc["auroc_raw_confidence"], 3),
        "MCECERaw": _fmt(mc["calibration"]["ece_raw"], 3), "MCECECapped": _fmt(mc["calibration"]["ece_capped"], 3),
        "MCTierOneAcc": _fmt(100 * mc["by_tier"]["tier1"]["consensus_accuracy"]),
        "MCTierThreeAcc": _fmt(100 * mc["by_tier"]["tier3"]["consensus_accuracy"]),
        "MCTierOneN": str(mc["by_tier"]["tier1"]["n"]), "MCTierTwoN": str(mc["by_tier"]["tier2"]["n"]),
        "MCTierThreeN": str(mc["by_tier"]["tier3"]["n"]),
    }
    lines = ["% AUTO-GENERATED by alsamadani_score_calculator.py -- do not edit by hand."]
    for k, v in m.items():
        lines.append(f"\\newcommand{{\\{k}}}{{{v}}}")
    # Table rows
    rows = []
    for s, d in mc["per_scenario"].items():
        rows.append(f"{s} & {d['description']} & {d['n']} & {d['mean_sigma']:.3f} & {d['mean_score']:.1f} & "
                    f"{100*d['consensus_accuracy']:.1f} & {100*d['tier1_frac']:.1f} & {100*d['tier2_frac']:.1f} & "
                    f"{100*d['tier3_frac']:.1f} \\\\")
    lines.append("\\newcommand{\\MCScenarioRows}{" + "\n".join(rows) + "}")
    srows = []
    for c in sc["cells"]:
        srows.append(f"{c['M']} & {c['R']} & {c['naive_rho']:.3f} & {c['catfish_rho']:.3f} & "
                     f"{c['naive_score']:.1f} & {c['catfish_score']:.1f} & {100*c['naive_accuracy']:.1f} & "
                     f"{100*c['catfish_accuracy']:.1f} \\\\")
    lines.append("\\newcommand{\\ScalingRows}{" + "\n".join(srows) + "}")
    vrows = [f"{i+1} & {v['label']} & {v['voi_points']:+.1f} & {v['score_if_refreshed']:.1f} \\\\"
             for i, v in enumerate(b["voi"])]
    lines.append("\\newcommand{\\VOIRows}{" + "\n".join(vrows) + "}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_all(verbose: bool = True) -> Dict:
    results: Dict = {}
    for name, builder, expect in (("case_a", demo_case_a, 1), ("case_b", demo_case_b, 3)):
        labs, trace, obs = builder()
        comps = compute_score(labs, trace)
        dec = evaluate_encounter(labs, trace, obs)
        comps["tier"] = dec.tier
        comps["consensus_diagnosis_index"] = dec.consensus_diagnosis_index
        comps["voi"] = counterfactual_voi(labs, trace)
        comps["fallback"] = [r.rule_id for r in dec.guideline_fallback]
        if dec.tier != expect:
            raise AssertionError(f"{name}: expected tier {expect}, got {dec.tier} (score {comps['score']:.2f})")
        results[name] = comps
        if verbose:
            print(f"\n=== {name.upper()} ===")
            print(f"  S_AlSamadani = {comps['score']:.2f}  -> {dec.tier_label}")
            print(f"  sigma={comps['sigma']:.3f}  CED={comps['ced']:.3f} (path={comps['path_drift']:.3f}, "
                  f"laundering={comps['laundering']:.3f})  rho={comps['rho']:.3f}  "
                  f"conf={comps['final_confidence']:.3f}  ceiling={comps['ceiling']:.3f}")
            print(f"  consensus_diagnosis_index = {dec.consensus_diagnosis_index}"
                  + (f" ({dec.consensus_diagnosis_label}, calibrated p={dec.calibrated_probability})"
                     if dec.consensus_diagnosis_index is not None else ""))
            print("  VOI ranking: " + ", ".join(f"{v['label']} {v['voi_points']:+.1f}" for v in comps["voi"][:3]))
            print("  Guideline fallback: " + ", ".join(comps["fallback"]))

    pseudo = Pseudonymizer(allow_demo_salt=True)
    p_tok, u_tok = pseudo.patient("MRN-00123456"), pseudo.unit("KFMC-CVICU-3")
    note = "Pt: Ahmed Alharbi, MRN: 00123456, Iqama 2123456789, seen 2026-11-09 at King Fahad Medical City"
    scrubbed, counts = scrub_phi(note)
    results["privacy"] = {"patient_token": p_tok, "unit_token": u_tok, "scrub_counts": counts, "scrubbed": scrubbed}
    if verbose:
        print("\n=== PRIVACY (demo salt; tokens change with the production salt) ===")
        print(f"  patient token: {p_tok}\n  unit token:    {u_tok}\n  scrubbed note: {scrubbed}")

    mc = run_monte_carlo_validation()
    results["monte_carlo"] = mc
    if verbose:
        print(f"\n=== MONTE CARLO (synthetic, N={mc['n']}) ===")
        print(f"  AUROC(S -> correct consensus) = {mc['auroc_score']:.3f} "
              f"[95% bootstrap CI {mc['auroc_ci95'][0]:.3f}-{mc['auroc_ci95'][1]:.3f}]; "
              f"raw confidence AUROC = {mc['auroc_raw_confidence']:.3f}")
        for s, d in mc["per_scenario"].items():
            print(f"  {s}: sigma={d['mean_sigma']:.3f} S={d['mean_score']:.1f} acc={d['consensus_accuracy']:.3f} "
                  f"tiers I/II/III={d['tier1_frac']:.2f}/{d['tier2_frac']:.2f}/{d['tier3_frac']:.2f}")
        print(f"  ECE raw={mc['calibration']['ece_raw']:.3f}  ECE capped={mc['calibration']['ece_capped']:.3f}")
        print("  accuracy by tier: " + ", ".join(f"{k} {v['consensus_accuracy']:.3f} (n={v['n']})"
                                                for k, v in mc["by_tier"].items()))

    sc = run_scaling_benchmark()
    results["scaling"] = sc
    if verbose:
        print(f"\n=== SCALING BENCHMARK ({sc['scenario']}, n={sc['n_per_cell']}/cell) ===")
        print("   M  R  rho(naive) rho(catfish)  S(naive) S(catfish)  acc(naive) acc(catfish)")
        for c in sc["cells"]:
            print(f"  {c['M']:2d} {c['R']:2d}   {c['naive_rho']:.3f}      {c['catfish_rho']:.3f}       "
                  f"{c['naive_score']:5.1f}    {c['catfish_score']:5.1f}      {c['naive_accuracy']:.3f}      "
                  f"{c['catfish_accuracy']:.3f}")
    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--export-tex", default=str(Path(__file__).with_name("alsamadani_results.tex")))
    ap.add_argument("--export-json", default=str(Path(__file__).with_name("alsamadani_results.json")))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    results = run_all(verbose=not args.quiet)
    if args.export_tex:
        export_tex_macros(Path(args.export_tex), results)
    if args.export_json:
        Path(args.export_json).write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    if not args.quiet:
        print(f"\nWrote {args.export_tex} and {args.export_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
