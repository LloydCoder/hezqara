import json
from datetime import datetime, timezone
from sqlalchemy import text

class PatientAccessRepository:
    def __init__(self, session):
        self.session = session

    async def create_access_request(self, clinic_id, data):
        result = await self.session.execute(text("""
            INSERT INTO patient_access_requests
                (clinic_id,patient_id,status,channel,request_type,reason,requested_start,requested_end,idempotency_key)
            VALUES (:clinic_id,:patient_id,'new',:channel,:request_type,:reason,:requested_start,:requested_end,:idempotency_key)
            ON CONFLICT (clinic_id,idempotency_key) DO UPDATE SET updated_at=patient_access_requests.updated_at
            RETURNING id,clinic_id,patient_id,status,channel,request_type,reason,requested_start,requested_end,
                      assigned_agent,idempotency_key,created_at,updated_at
        """), {"clinic_id":clinic_id,**data})
        return dict(result.mappings().one())

    async def list_access_requests(self, clinic_id, limit, offset):
        result=await self.session.execute(text("""
            SELECT id,patient_id,status,channel,request_type,reason,requested_start,requested_end,
                   assigned_agent,idempotency_key,created_at,updated_at
            FROM patient_access_requests WHERE clinic_id=:clinic_id
            ORDER BY created_at DESC LIMIT :limit OFFSET :offset
        """), {"clinic_id":clinic_id,"limit":limit,"offset":offset})
        return [dict(r) for r in result.mappings().all()]

    async def get_access_request_for_update(self, clinic_id, request_id):
        result=await self.session.execute(text("""
            SELECT id,patient_id,status,channel,request_type,reason,requested_start,requested_end,
                   assigned_agent,idempotency_key,created_at,updated_at
            FROM patient_access_requests
            WHERE clinic_id=:clinic_id AND id=:request_id
            FOR UPDATE
        """), {"clinic_id":clinic_id,"request_id":request_id})
        row=result.mappings().first()
        return dict(row) if row else None

    async def update_access_request(self, clinic_id, request_id, status):
        result=await self.session.execute(text("""
            UPDATE patient_access_requests SET status=:status,updated_at=NOW()
            WHERE clinic_id=:clinic_id AND id=:request_id
            RETURNING id,patient_id,status,channel,request_type,reason,requested_start,requested_end,
                      assigned_agent,idempotency_key,created_at,updated_at
        """), {"clinic_id":clinic_id,"request_id":request_id,"status":status})
        row=result.mappings().first()
        return dict(row) if row else None

    async def create_intake(self, clinic_id, data, actor):
        status="submitted" if data["submit"] else "draft"
        submitted_at=datetime.now(timezone.utc) if data["submit"] else None
        result=await self.session.execute(text("""
            INSERT INTO patient_intake_submissions
                (clinic_id,patient_id,access_request_id,form_version,status,responses,submitted_by,submitted_at)
            VALUES (:clinic_id,:patient_id,:access_request_id,:form_version,:status,
                    CAST(:responses AS jsonb),:submitted_by,:submitted_at)
            RETURNING id,patient_id,access_request_id,form_version,status,responses,submitted_by,submitted_at,
                      created_at,updated_at
        """), {"clinic_id":clinic_id,"patient_id":data["patient_id"],
               "access_request_id":data["access_request_id"],"form_version":data["form_version"],
               "status":status,"responses":json.dumps(data["responses"]),
               "submitted_by":actor,"submitted_at":submitted_at})
        return dict(result.mappings().one())

    async def list_intake(self, clinic_id, patient_id):
        result=await self.session.execute(text("""
            SELECT id,patient_id,access_request_id,form_version,status,responses,submitted_by,submitted_at,
                   reviewed_by,reviewed_at,created_at,updated_at
            FROM patient_intake_submissions
            WHERE clinic_id=:clinic_id AND patient_id=:patient_id ORDER BY created_at DESC
        """), {"clinic_id":clinic_id,"patient_id":patient_id})
        return [dict(r) for r in result.mappings().all()]

    async def create_schedule(self, clinic_id, data):
        result=await self.session.execute(text("""
            INSERT INTO provider_schedules
                (clinic_id,provider_id,service_type,specialty,timezone,planning_start,planning_end)
            VALUES (:clinic_id,:provider_id,:service_type,:specialty,:timezone,:planning_start,:planning_end)
            RETURNING id,provider_id,service_type,specialty,timezone,active,planning_start,planning_end,created_at,updated_at
        """), {"clinic_id":clinic_id,**data})
        return dict(result.mappings().one())

    async def create_slot(self, clinic_id, schedule_id, data):
        result=await self.session.execute(text("""
            INSERT INTO schedule_slots
                (clinic_id,schedule_id,provider_id,starts_at,ends_at,status,comment)
            SELECT :clinic_id,:schedule_id,provider_id,:starts_at,:ends_at,:status,:comment
            FROM provider_schedules WHERE clinic_id=:clinic_id AND id=:schedule_id AND active=TRUE
            RETURNING id,schedule_id,provider_id,starts_at,ends_at,status,appointment_id,overbooked,comment,created_at,updated_at
        """), {"clinic_id":clinic_id,"schedule_id":schedule_id,**data})
        row=result.mappings().first()
        if not row: raise ValueError("schedule not found or inactive")
        return dict(row)

    async def list_slots(self, clinic_id, schedule_id, start, end):
        result=await self.session.execute(text("""
            SELECT id,schedule_id,provider_id,starts_at,ends_at,status,appointment_id,overbooked,comment,created_at,updated_at
            FROM schedule_slots
            WHERE clinic_id=:clinic_id AND schedule_id=:schedule_id AND starts_at < :end AND ends_at > :start
            ORDER BY starts_at
        """), {"clinic_id":clinic_id,"schedule_id":schedule_id,"start":start,"end":end})
        return [dict(r) for r in result.mappings().all()]

    async def create_waitlist(self, clinic_id, data):
        result=await self.session.execute(text("""
            INSERT INTO waitlist_entries
                (clinic_id,patient_id,provider_id,service_type,requested_start,requested_end,priority,notification_channel,idempotency_key)
            VALUES (:clinic_id,:patient_id,:provider_id,:service_type,:requested_start,:requested_end,:priority,:notification_channel,:idempotency_key)
            ON CONFLICT (clinic_id,idempotency_key) DO UPDATE SET updated_at=waitlist_entries.updated_at
            RETURNING id,patient_id,provider_id,service_type,requested_start,requested_end,priority,status,
                      notification_channel,idempotency_key,created_at,updated_at
        """), {"clinic_id":clinic_id,**data})
        return dict(result.mappings().one())

    async def book_slot(self, clinic_id, slot_id, patient_id, reason, idempotency_key):
        existing=(await self.session.execute(text("""
            SELECT id,patient_id,provider_id,appointment_datetime,duration_minutes,reason,status,slot_id,created_at,updated_at
            FROM appointments WHERE clinic_id=:clinic_id AND booking_idempotency_key=:key
        """), {"clinic_id":clinic_id,"key":idempotency_key})).mappings().first()
        if existing: return dict(existing)
        slot=(await self.session.execute(text("""
            SELECT id,provider_id,starts_at,ends_at,status FROM schedule_slots
            WHERE clinic_id=:clinic_id AND id=:slot_id FOR UPDATE
        """), {"clinic_id":clinic_id,"slot_id":slot_id})).mappings().first()
        if not slot: raise ValueError("slot not found")
        if slot["status"] != "free": raise RuntimeError("slot is not available")
        appointment=(await self.session.execute(text("""
            INSERT INTO appointments
                (clinic_id,patient_id,provider_id,appointment_datetime,duration_minutes,reason,status,booked_by_agent,slot_id,booking_idempotency_key)
            VALUES (:clinic_id,:patient_id,:provider_id,:starts_at,
                    GREATEST(5,EXTRACT(EPOCH FROM (:ends_at-:starts_at))/60)::integer,
                    :reason,'scheduled','patient_access',:slot_id,:idempotency_key)
            RETURNING id,patient_id,provider_id,appointment_datetime,duration_minutes,reason,status,slot_id,created_at,updated_at
        """), {"clinic_id":clinic_id,"patient_id":patient_id,"provider_id":slot["provider_id"],
               "starts_at":slot["starts_at"],"ends_at":slot["ends_at"],"reason":reason,
               "slot_id":slot_id,"idempotency_key":idempotency_key}).mappings().one())
        await self.session.execute(text("""
            UPDATE schedule_slots SET status='busy',appointment_id=:appointment_id,updated_at=NOW()
            WHERE clinic_id=:clinic_id AND id=:slot_id
        """), {"clinic_id":clinic_id,"slot_id":slot_id,"appointment_id":appointment["id"]})
        return dict(appointment)

    async def get_schedule(self, clinic_id, schedule_id):
        result=await self.session.execute(text("""
            SELECT id,provider_id,service_type,specialty,timezone,active,planning_start,planning_end,created_at,updated_at
            FROM provider_schedules WHERE clinic_id=:clinic_id AND id=:schedule_id
        """), {"clinic_id":clinic_id,"schedule_id":schedule_id})
        row=result.mappings().first()
        return dict(row) if row else None

    async def get_slot(self, clinic_id, slot_id):
        result=await self.session.execute(text("""
            SELECT id,schedule_id,provider_id,starts_at,ends_at,status,appointment_id,overbooked,comment,created_at,updated_at
            FROM schedule_slots WHERE clinic_id=:clinic_id AND id=:slot_id
        """), {"clinic_id":clinic_id,"slot_id":slot_id})
        row=result.mappings().first()
        return dict(row) if row else None

    async def get_appointment(self, clinic_id, appointment_id):
        result=await self.session.execute(text("""
            SELECT id,patient_id,provider_id,appointment_datetime,duration_minutes,reason,status,slot_id,created_at,updated_at
            FROM appointments WHERE clinic_id=:clinic_id AND id=:appointment_id
        """), {"clinic_id":clinic_id,"appointment_id":appointment_id})
        row=result.mappings().first()
        return dict(row) if row else None

    async def cancel_appointment(self, clinic_id, appointment_id, idempotency_key):
        if await self._action_seen(clinic_id,idempotency_key):
            return await self.get_appointment(clinic_id,appointment_id)
        appointment=(await self.session.execute(text("""
            SELECT id,slot_id,status FROM appointments
            WHERE clinic_id=:clinic_id AND id=:appointment_id FOR UPDATE
        """), {"clinic_id":clinic_id,"appointment_id":appointment_id})).mappings().first()
        if not appointment: raise ValueError("appointment not found")
        if appointment["status"] == "cancelled":
            await self._record_action(clinic_id,appointment_id,"cancel",idempotency_key)
            return await self.get_appointment(clinic_id,appointment_id)
        if appointment["status"] not in ("scheduled","confirmed"):
            raise RuntimeError("appointment cannot be cancelled in its current state")
        await self.session.execute(text("""
            UPDATE appointments SET status='cancelled',updated_at=NOW()
            WHERE clinic_id=:clinic_id AND id=:appointment_id
        """), {"clinic_id":clinic_id,"appointment_id":appointment_id})
        if appointment["slot_id"]:
            await self.session.execute(text("""
                UPDATE schedule_slots SET status='free',appointment_id=NULL,updated_at=NOW()
                WHERE clinic_id=:clinic_id AND id=:slot_id AND appointment_id=:appointment_id
            """), {"clinic_id":clinic_id,"slot_id":appointment["slot_id"],"appointment_id":appointment_id})
        await self._record_action(clinic_id,appointment_id,"cancel",idempotency_key)
        return await self.get_appointment(clinic_id,appointment_id)

    async def reschedule_appointment(self, clinic_id, appointment_id, new_slot_id, idempotency_key):
        if await self._action_seen(clinic_id,idempotency_key):
            return await self.get_appointment(clinic_id,appointment_id)
        appointment=(await self.session.execute(text("""
            SELECT id,slot_id,status FROM appointments
            WHERE clinic_id=:clinic_id AND id=:appointment_id FOR UPDATE
        """), {"clinic_id":clinic_id,"appointment_id":appointment_id})).mappings().first()
        if not appointment: raise ValueError("appointment not found")
        if appointment["status"] not in ("scheduled","confirmed"):
            raise RuntimeError("appointment cannot be rescheduled in its current state")
        slot=(await self.session.execute(text("""
            SELECT id,provider_id,starts_at,ends_at,status FROM schedule_slots
            WHERE clinic_id=:clinic_id AND id=:slot_id FOR UPDATE
        """), {"clinic_id":clinic_id,"slot_id":new_slot_id})).mappings().first()
        if not slot: raise ValueError("new slot not found")
        if slot["status"] != "free": raise RuntimeError("new slot is not available")
        if appointment["slot_id"] == new_slot_id:
            await self._record_action(clinic_id,appointment_id,"reschedule",idempotency_key)
            return await self.get_appointment(clinic_id,appointment_id)
        old_slot_id=appointment["slot_id"]
        await self.session.execute(text("""
            UPDATE appointments SET provider_id=:provider_id,appointment_datetime=:starts_at,
                duration_minutes=GREATEST(5,EXTRACT(EPOCH FROM (:ends_at-:starts_at))/60)::integer,
                slot_id=:new_slot_id,updated_at=NOW()
            WHERE clinic_id=:clinic_id AND id=:appointment_id
        """), {"clinic_id":clinic_id,"appointment_id":appointment_id,"provider_id":slot["provider_id"],
               "starts_at":slot["starts_at"],"ends_at":slot["ends_at"],"new_slot_id":new_slot_id})
        if old_slot_id:
            await self.session.execute(text("""
                UPDATE schedule_slots SET status='free',appointment_id=NULL,updated_at=NOW()
                WHERE clinic_id=:clinic_id AND id=:slot_id AND appointment_id=:appointment_id
            """), {"clinic_id":clinic_id,"slot_id":old_slot_id,"appointment_id":appointment_id})
        await self.session.execute(text("""
            UPDATE schedule_slots SET status='busy',appointment_id=:appointment_id,updated_at=NOW()
            WHERE clinic_id=:clinic_id AND id=:slot_id
        """), {"clinic_id":clinic_id,"slot_id":new_slot_id,"appointment_id":appointment_id})
        await self._record_action(clinic_id,appointment_id,"reschedule",idempotency_key)
        return await self.get_appointment(clinic_id,appointment_id)

    async def _action_seen(self, clinic_id, idempotency_key):
        row=(await self.session.execute(text("""
            SELECT id FROM appointment_action_idempotency WHERE clinic_id=:clinic_id AND idempotency_key=:key
        """), {"clinic_id":clinic_id,"key":idempotency_key})).first()
        return row is not None

    async def _record_action(self, clinic_id, appointment_id, action, idempotency_key):
        await self.session.execute(text("""
            INSERT INTO appointment_action_idempotency(clinic_id,appointment_id,action,idempotency_key)
            VALUES (:clinic_id,:appointment_id,:action,:key)
            ON CONFLICT (clinic_id,idempotency_key) DO NOTHING
        """), {"clinic_id":clinic_id,"appointment_id":appointment_id,"action":action,"key":idempotency_key})

    async def cancel_waitlist(self, clinic_id, entry_id):
        result=await self.session.execute(text("""
            UPDATE waitlist_entries SET status='cancelled',updated_at=NOW()
            WHERE clinic_id=:clinic_id AND id=:entry_id AND status IN ('active','contacted')
            RETURNING id,patient_id,provider_id,service_type,requested_start,requested_end,priority,status,
                      notification_channel,idempotency_key,created_at,updated_at
        """), {"clinic_id":clinic_id,"entry_id":entry_id})
        row=result.mappings().first()
        if not row: raise ValueError("waitlist entry not found or cannot be cancelled")
        return dict(row)

    async def match_waitlist(self, clinic_id, provider_id, service_type, start, end, limit):
        result=await self.session.execute(text("""
            SELECT id,patient_id,provider_id,service_type,requested_start,requested_end,priority,status,
                   notification_channel,idempotency_key,created_at,updated_at
            FROM waitlist_entries
            WHERE clinic_id=:clinic_id AND status='active'
              AND (:provider_id IS NULL OR provider_id=:provider_id)
              AND (:service_type IS NULL OR service_type=:service_type)
              AND (requested_start IS NULL OR requested_start <= :end)
              AND (requested_end IS NULL OR requested_end >= :start)
            ORDER BY priority ASC, created_at ASC
            LIMIT :limit
        """), {"clinic_id":clinic_id,"provider_id":provider_id,"service_type":service_type,
               "start":start,"end":end,"limit":limit})
        return [dict(r) for r in result.mappings().all()]
