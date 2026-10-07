from fastapi import HTTPException

class PatientAccessService:
    def __init__(self, repo):
        self.repo=repo

    async def update_access_request(self, clinic_id, request_id, status):
        allowed={"new":{"in_progress","cancelled"},"in_progress":{"ready","escalated","cancelled"},"ready":{"completed","escalated","cancelled"},"escalated":{"in_progress","completed","cancelled"},"completed":set(),"cancelled":set()}
        if hasattr(self.repo, "get_access_request_for_update"):
            row=await self.repo.get_access_request_for_update(clinic_id,request_id)
        else:
            current=await self.repo.list_access_requests(clinic_id,1000,0)
            row=next((x for x in current if x["id"]==request_id),None)
        if not row: raise HTTPException(404,"access request not found")
        if status not in allowed[row["status"]]: raise HTTPException(409,"invalid access request state transition")
        return await self.repo.update_access_request(clinic_id,request_id,status)
