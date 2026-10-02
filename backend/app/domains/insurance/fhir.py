from datetime import date

FHIR_R4="4.0.1"

def coverage_resource(row):
    resource={
        "resourceType":"Coverage","id":row["id"],
        "status":"active" if row.get("status")=="active" else ("cancelled" if row.get("status") in {"inactive","expired"} else "draft"),
        "beneficiary":{"reference":f"Patient/{row['patient_id']}"},
        "payor":[{"display":row["payer_name"]}],
        "subscriberId":row["member_id"],
        "order":row.get("priority",1),
    }
    if row.get("plan_name"): resource["class"]=[{"type":{"text":"plan"},"value":row["plan_name"]}]
    if row.get("effective_date") or row.get("termination_date"):
        resource["period"]={}
        if row.get("effective_date"): resource["period"]["start"]=row["effective_date"].isoformat()
        if row.get("termination_date"): resource["period"]["end"]=row["termination_date"].isoformat()
    return resource

def eligibility_request_resource(row):
    return {
        "resourceType":"CoverageEligibilityRequest","id":row["id"],"status":"active",
        "purpose":["validation","benefits","auth-requirements"],
        "patient":{"reference":f"Patient/{row['patient_id']}"},
        "created":row["requested_at"].isoformat() if row.get("requested_at") else None,
        "insurer":{"display":row["payer_name"]},
        "insurance":[{"focal":True,"coverage":{"reference":f"Coverage/{row['coverage_id']}"}}] if row.get("coverage_id") else [],
    }

def eligibility_response_resource(row):
    outcome_map={"eligible":"complete","ineligible":"complete","additional_information_required":"partial",
                 "unavailable":"error","provider_error":"error","failed":"error","queued":"queued","submitted":"queued"}
    return {
        "resourceType":"CoverageEligibilityResponse","id":row["id"],"status":"active",
        "purpose":["validation","benefits","auth-requirements"],
        "patient":{"reference":f"Patient/{row['patient_id']}"},
        "outcome":outcome_map.get(row["status"],"error"),
        "disposition":row.get("status"),
        "insurance":[{"coverage":{"reference":f"Coverage/{row['coverage_id']}"},"inforce":row["status"]=="eligible"}] if row.get("coverage_id") else [],
    }

def authorization_task_resource(row):
    status_map={"draft":"draft","ready_for_review":"requested","approved_for_submission":"ready",
                "submitted":"in-progress","pending":"in-progress","additional_information_required":"on-hold",
                "approved":"completed","denied":"failed","expired":"cancelled","cancelled":"cancelled"}
    return {
        "resourceType":"Task","id":row["id"],"status":status_map.get(row["status"],"unknown"),
        "intent":"order","priority":"routine",
        "for":{"reference":f"Patient/{row['patient_id']}"},
        "focus":{"reference":f"ServiceRequest/{row['id']}"},
        "code":{"text":"Prior authorization"},
        "authoredOn":row["created_at"].isoformat() if row.get("created_at") else None,
    }
