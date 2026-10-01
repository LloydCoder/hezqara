# Phase 9 AI Evaluation Report

## Evidence status
This repository contains a synthetic golden dataset and deterministic evaluation engine. It does **not** claim a production model accuracy benchmark from the presence of fixtures.

## Dataset
`backend/tests/fixtures/phase9_golden_dataset.json` is labelled `synthetic_only` and versioned `phase9-v1`. It covers scheduling, billing, missing data, prompt injection, PHI boundaries and clinical/high-impact requests. Additional cases can be added as versioned suite cases.

## Dimensions
1. Structured-output validity.
2. Expected administrative action.
3. Evidence/grounding requirement.
4. Safety pass/fail.
5. Failure category.
6. Latency and token usage when observations provide them.

## Scoring
A case passes only when the structured output is valid and the expected deterministic constraints are satisfied. Safety is separately recorded. Aggregate rates are undefined when no observations exist; the system must not convert an empty denominator into a fabricated zero or success rate.

## Reproducibility
Create a versioned evaluation suite, register versioned cases, create an evaluation run, execute the governed capability in an evaluation-safe environment, then persist observed output through the evaluation result API. The stored run retains suite/capability lineage. Re-running after a prompt/model/tool-policy change requires a new version.

## Limitations
- No real patient data is used.
- No production accuracy claim is made.
- Confidence values from models are not treated as calibrated probabilities.
- External-provider behavior is configuration dependent.
- Clinical decisions remain outside autonomous AI authority.
