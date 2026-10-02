-- Migration 045: E10 tenant-integrity hardening
-- Cross-tenant references must be impossible at the database boundary.

ALTER TABLE patients
    ADD CONSTRAINT patients_clinic_id_id_key UNIQUE (clinic_id, id);

ALTER TABLE appointments
    ADD CONSTRAINT appointments_clinic_id_id_key UNIQUE (clinic_id, id);

ALTER TABLE patient_access_requests
    ADD CONSTRAINT patient_access_requests_clinic_id_id_key UNIQUE (clinic_id, id);

ALTER TABLE provider_schedules
    ADD CONSTRAINT provider_schedules_clinic_id_id_key UNIQUE (clinic_id, id);

ALTER TABLE schedule_slots
    ADD CONSTRAINT schedule_slots_clinic_id_id_key UNIQUE (clinic_id, id);

ALTER TABLE patient_access_requests
    ADD CONSTRAINT patient_access_requests_patient_tenant_fk
    FOREIGN KEY (clinic_id, patient_id)
    REFERENCES patients (clinic_id, id);

ALTER TABLE patient_intake_submissions
    ADD CONSTRAINT patient_intake_submissions_patient_tenant_fk
    FOREIGN KEY (clinic_id, patient_id)
    REFERENCES patients (clinic_id, id);

ALTER TABLE patient_intake_submissions
    ADD CONSTRAINT patient_intake_submissions_access_request_tenant_fk
    FOREIGN KEY (clinic_id, access_request_id)
    REFERENCES patient_access_requests (clinic_id, id);

ALTER TABLE schedule_slots
    ADD CONSTRAINT schedule_slots_schedule_tenant_fk
    FOREIGN KEY (clinic_id, schedule_id)
    REFERENCES provider_schedules (clinic_id, id);

ALTER TABLE schedule_slots
    ADD CONSTRAINT schedule_slots_appointment_tenant_fk
    FOREIGN KEY (clinic_id, appointment_id)
    REFERENCES appointments (clinic_id, id);

ALTER TABLE appointments
    ADD CONSTRAINT appointments_slot_tenant_fk
    FOREIGN KEY (clinic_id, slot_id)
    REFERENCES schedule_slots (clinic_id, id);

ALTER TABLE waitlist_entries
    ADD CONSTRAINT waitlist_entries_patient_tenant_fk
    FOREIGN KEY (clinic_id, patient_id)
    REFERENCES patients (clinic_id, id);

CREATE INDEX IF NOT EXISTS idx_access_requests_patient_tenant
    ON patient_access_requests(clinic_id, patient_id);

CREATE INDEX IF NOT EXISTS idx_intake_access_request_tenant
    ON patient_intake_submissions(clinic_id, access_request_id);
