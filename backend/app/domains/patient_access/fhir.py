from datetime import timedelta

FHIR_R4 = "4.0.1"

def _instant(value):
    return value.isoformat().replace("+00:00","Z") if value else None

def schedule_resource(row):
    resource={"resourceType":"Schedule","id":row["id"],"active":bool(row["active"]),
              "actor":[{"reference":f"Practitioner/{row['provider_id']}"}]}
    if row.get("service_type"): resource["serviceType"]=[{"text":row["service_type"]}]
    if row.get("specialty"): resource["specialty"]=[{"text":row["specialty"]}]
    if row.get("planning_start") or row.get("planning_end"):
        resource["planningHorizon"]={}
        if row.get("planning_start"): resource["planningHorizon"]["start"]=_instant(row["planning_start"])
        if row.get("planning_end"): resource["planningHorizon"]["end"]=_instant(row["planning_end"])
    return resource

def slot_resource(row):
    return {"resourceType":"Slot","id":row["id"],
            "schedule":{"reference":f"Schedule/{row['schedule_id']}"},
            "status":row["status"],"start":_instant(row["starts_at"]),"end":_instant(row["ends_at"]),
            "overbooked":bool(row["overbooked"]),
            **({"comment":row["comment"]} if row.get("comment") else {})}

def appointment_resource(row):
    status={"scheduled":"booked","confirmed":"booked","completed":"fulfilled",
            "cancelled":"cancelled","no_show":"noshow"}.get(row["status"],"unknown")
    start=row.get("appointment_datetime")
    end=start+timedelta(minutes=row["duration_minutes"]) if start else None
    return {"resourceType":"Appointment","id":row["id"],"status":status,
            "start":_instant(start),"end":_instant(end),"minutesDuration":row["duration_minutes"],
            "slot":[{"reference":f"Slot/{row['slot_id']}"}] if row.get("slot_id") else [],
            "participant":[
                {"actor":{"reference":f"Patient/{row['patient_id']}"},"status":"accepted"},
                {"actor":{"reference":f"Practitioner/{row['provider_id']}"},"status":"accepted"},
            ],
            **({"description":row["reason"]} if row.get("reason") else {})}
