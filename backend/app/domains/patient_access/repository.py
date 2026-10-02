import json
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

class PatientAccessRepository:
    def __init__(self, session):
        self.session = session

    async def create_access_request(self, clinic_id, data):
        try:
            result = await self.session.execute(text("""
                INSERT INTO patient_access_requests
                    (clinic_id, patient_id, status, channel, request_type, reason,
                     requested_start, requested_end, idempotency_key)
                VALUES
                    (:clinic_id, :patient_id, 'new', :channel, :request_type, :reason,
                     :requested_start, :requested_end, :idempotency_key)
                ON CONFLICT (clinic_id, idempotency_key)
                DO UPDATE SET updated_at = patient_access_requests.updated_at
                RETURNING id, clinic_id, patient_id, status, channel, request_type, reason,
                          requested_start, requested_end, assigned_agent, idempotency_key,
                          created_at, updated_at
            """), {"clinic_id":clinic_id, **data})
            row = result.mappings().one()
            return dict(row)
        except IntegrityError:
            raise

    async def list_access_requests(self, clinic_id, limit, offset):
        result = await self.session.execute(text("""
            SELECT id, patient_id, status, channel, request_type, reason,
                   requested_start, requested_end, assigned_agent, idempotency_key,
                   created_at, updated_at
            FROM patient_access_requests
            WHERE clinic_id = :clinic_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """), {"clinic_id":clinic_id,"limit":limit,"offset":offset})
        return [dict(r) for r in result.mappings().all()]

    async def update_access_request(self, clinic_id, request_id, status):
        result = await self.session.execute(text("""
            UPDATE patient_access_requests
            SET status=:status, updated_at=NOW()
            WHERE clinic_id=:clinic_id AND id=:request_id
            RETURNING id, patient_id, status, channel, request_type, reason,
                      requested_start, requested_end, assigned_agent, idempotency_key,
                      created_at, updated_at
        """), {"clinic_id":clinic_id,"request_id":request_id,"status":status})
        row=result.mappings().first()
        return dict(row) if row else None

    async def create_intake(self, clinic_id, data, actor):
        status="submitted" if data["submit"] else "draft"
        submitted_at=datetime.utcnow() if data["submit"] else None
        result=await self.session.execute(text("""
            INSERT INTO patient_intake_submissions
                (clinic_id, patient_id, access_request_id, form_version, status,
                 responses, submitted_by, submitted_at)
            VALUES
                (:clinic_id,:patient_id,:access_request_id,:form_version,:status,
                 CAST(:responses AS jsonb),:submitted_by,:submitted_at)
            RETURNING id, patient_id, access_request_id, form_version, status,
                      responses, submitted_by, submitted_at, created_at, updated_at
        """), {"clinic_id":clinic_id,"patient_id":data["patient_id"],
               "access_request_id":data["access_request_id"],"form_version":data["form_version"],
               "status":status,"responses":json.dumps(data["responses"]),
               "submitted_by":actor,"submitted_at":submitted_at})
        return dict(result.mappings().one())

    async def list_intake(self, clinic_id, patient_id):
        result=await self.session.execute(text("""
            SELECT id, patient_id, access_request_id, form_version, status,
                   responses, submitted_by, submitted_at, reviewed_by, reviewed_at,
                   created_at, updated_at
            FROM patient_intake_submissions
            WHERE clinic_id=:clinic_id AND patient_id=:patient_id
            ORDER BY created_at DESC
        """), {"clinic_id":clinic_id,"patient_id":patient_id})
        return [dict(r) for r in result.mappings().all()]

    async def create_schedule(self, clinic_id, data):
        result=await self.session.execute(text("""
            INSERT INTO provider_schedules
                (clinic_id,provider_id,service_type,specialty,timezone,planning_start,planning_end)
            VALUES (:clinic_id,:provider_id,:service_type,:specialty,:timezone,:planning_start,:planning_end)
            RETURNING id, provider_id, service_type, specialty, timezone, active,
                      planning_start, planning_end, created_at, updated_at
        """), {"clinic_id":clinic_id,**data})
        return dict(result.mappings().one())

    async def create_slot(self, clinic_id, schedule_id, data):
        result=await self.session.execute(text("""
            INSERT INTO schedule_slots
                (clinic_id,schedule_id,provider_id,starts_at,ends_at,status,comment)
            SELECT :clinic_id,:schedule_id,provider_id,:starts_at,:ends_at,:status,:comment
            FROM provider_schedules
            WHERE clinic_id=:clinic_id AND id=:schedule_id AND active=TRUE
            RETURNING id, schedule_id, provider_id, starts_at, ends_at, status,
                      appointment_id, overbooked, comment, created_at, updated_at
        """), {"clinic_id":clinic_id,"schedule_id":schedule_id,**data})
        row=result.mappings().first()
        if not row: raise ValueError("schedule not found or inactive")
        return dict(row)

    async def list_slots(self, clinic_id, schedule_id, start, end):
        result=await self.session.execute(text("""
            SELECT id, schedule_id, provider_id, starts_at, ends_at, status,
                   appointment_id, overbooked, comment, created_at, updated_at
            FROM schedule_slots
            WHERE clinic_id=:clinic_id AND schedule_id=:schedule_id
              AND starts_at < :end AND ends_at > :start
            ORDER BY starts_at
        """), {"clinic_id":clinic_id,"schedule_id":schedule_id,"start":start,"end":end})
        return [dict(r) for r in result.mappings().all()]

    async def create_waitlist(self, clinic_id, data):
        result=await self.session.execute(text("""
            INSERT INTO waitlist_entries
                (clinic_id,patient_id,provider_id,service_type,requested_start,
                 requested_end,priority,notification_channel)
            VALUES (:clinic_id,:patient_id,:provider_id,:service_type,:requested_start,
                    :requested_end,:priority,:notification_channel)
            RETURNING id, patient_id, provider_id, service_type, requested_start,
                      requested_end, priority, status, notification_channel,
                      created_at, updated_at
        """), {"clinic_id":clinic_id,**data})
        return dict(result.mappings().one())

    async def book_slot(self, clinic_id, slot_id, patient_id, reason):
        slot=(await self.session.execute(text("""
            SELECT id, provider_id, starts_at, ends_at, status
            FROM schedule_slots
            WHERE clinic_id=:clinic_id AND id=:slot_id
            FOR UPDATE
        """), {"clinic_id":clinic_id,"slot_id":slot_id})).mappings().first()
        if not slot: raise ValueError("slot not found")
        if slot["status"] != "free": raise RuntimeError("slot is not available")
        appointment=(await self.session.execute(text("""
            INSERT INTO appointments
                (clinic_id,patient_id,provider_id,appointment_datetime,duration_minutes,
                 reason,status,booked_by_agent,slot_id)
            VALUES
                (:clinic_id,:patient_id,:provider_id,:starts_at,
                 GREATEST(5,EXTRACT(EPOCH FROM (:ends_at-:starts_at))/60)::integer,
                 :reason,'scheduled','patient_access',:slot_id)
            RETURNING id, patient_id, provider_id, appointment_datetime,
                      duration_minutes, reason, status, slot_id, created_at, updated_at
        """), {"clinic_id":clinic_id,"patient_id":patient_id,"provider_id":slot["provider_id"],
               "starts_at":slot["starts_at"],"ends_at":slot["ends_at"],
               "reason":reason,"slot_id":slot_id})).mappings().one()
        await self.session.execute(text("""
            UPDATE schedule_slots
            SET status='busy', appointment_id=:appointment_id, updated_at=NOW()
            WHERE clinic_id=:clinic_id AND id=:slot_id
        """), {"clinic_id":clinic_id,"slot_id":slot_id,"appointment_id":appointment["id"]})
        return dict(appointment)
