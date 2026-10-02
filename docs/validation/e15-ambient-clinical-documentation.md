# E15 — Ambient Clinical Documentation / AI Scribe

Status: IMPLEMENTED — awaiting CI/evidence gate

## Objective

Provide an ambient clinical documentation workflow in which a clinician can conduct an encounter, receive an AI-generated draft, edit it, approve it and commit the resulting documentation into a governed record/workflow.

## Architecture

Hezqara owns:

- encounter context
- consent and recording lifecycle
- transcript provenance
- documentation templates
- note drafting orchestration
- clinician editing
- approval/sign-off
- audit events
- provenance
- EHR/record commit boundary
- downstream workflow ownership

A replaceable speech provider supplies:

- speech recognition
- streaming/batch transcription
- speaker diarization
- timestamps
- medical terminology recognition

The repository deliberately does not embed a foundational speech model.

## Current provider strategy

The speech adapter is intentionally provider-neutral. Current market candidates for the production bake-off include AssemblyAI Medical Mode, Deepgram Nova-3 Medical and AWS HealthScribe. AssemblyAI currently documents a HIPAA BAA and Medical Mode for medical terminology; Deepgram documents Nova-3 Medical, HIPAA BAA availability and managed/self-hosted options; AWS HealthScribe is a HIPAA-eligible service combining speech recognition and generative clinical-note capabilities.

Vendor claims and pricing are not treated as acceptance evidence. Hezqara must run its own clinical benchmark before commercial selection.

## Governance

The workflow is:

recording → transcription → draft → clinician review/edit → clinician approval → governed commit.

A draft is never treated as an authoritative clinical record. The commit endpoint requires an approved note and approval permission.

Audio is referenced through a storage abstraction rather than embedded in the relational database. Retention is explicit and should be configured by clinic policy.

## Clinical safety boundary

This phase does not provide:

- autonomous diagnosis
- autonomous treatment recommendation
- autonomous clinical decision-making
- symptom-checker/triage authority

The AI drafting prompt explicitly instructs the model not to invent findings or unsupported treatment recommendations.

## Provenance

Each note records its source transcript. Field-level/segment provenance can be expanded through scribe_note_provenance. Provider name, model version, template version and audit events are retained.

## External standards/research context

ONC's HTI-1 final rule established algorithm-transparency requirements for certified health IT and emphasizes fairness, appropriateness, validity, effectiveness and safety. HTI-4 added current interoperability criteria around electronic prior authorization and related APIs. These rules reinforce the need for explicit model/version/evaluation and human-governance records even though Hezqara is not claiming ONC certification in E15.

## Exit gates

- [x] Consent-aware encounter lifecycle.
- [x] Replaceable speech-provider contract.
- [x] Transcript persistence and provenance.
- [x] Draft-note generation boundary.
- [x] Clinician edit path.
- [x] Approval gate.
- [x] Governed record commit.
- [x] Audit events.
- [x] Tenant isolation/RLS.
- [x] Automated tests.
- [ ] CI/workflows fully green.
- [ ] Database/RLS/security evidence fully green.
- [ ] Main merge.
- [ ] E16 starts only after every E15 gate passes.
