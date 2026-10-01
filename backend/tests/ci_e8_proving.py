import asyncio
from sqlalchemy import text
from app.infrastructure.database import system_session_context
from app.platform.reliability import operational_snapshot, record_worker_heartbeat, readiness

async def main():
    async with system_session_context() as session:
        await session.execute(text("insert into clinics(id,name,clerk_org_id) values('ci-e8-clinic','CI E8 Clinic','ci-e8-org') on conflict(id) do nothing"))
        await record_worker_heartbeat(session, "ci-e8-worker", "hezqara", 0, "ci")
        await session.execute(text("insert into slo_definitions(clinic_id,name,target,metric) values('ci-e8-clinic','ci_availability',0.999,'availability') on conflict(clinic_id,name) do nothing"))
        await session.execute(text("""insert into slo_measurements(clinic_id,slo_id,window_start,window_end,good_events,total_events)
          select 'ci-e8-clinic',id,now()-interval '1 hour',now(),999,1000 from slo_definitions
          where clinic_id='ci-e8-clinic' and name='ci_availability'"""))
        snap=await operational_snapshot(session, "ci-e8-org")
        assert snap["clinic_id"]=="ci-e8-clinic" and snap["healthy_workers"]>=1
        ready=await readiness(session)
        assert ready["checks"]["database"]=="ok" and ready["checks"]["durable_jobs"]=="ok"
        await session.execute(text("delete from slo_measurements where clinic_id='ci-e8-clinic'"))
        await session.execute(text("delete from slo_definitions where clinic_id='ci-e8-clinic'"))
        await session.execute(text("delete from worker_heartbeats where worker_id='ci-e8-worker'"))
        await session.execute(text("delete from clinics where id='ci-e8-clinic'"))
    print("E8 proving slice passed")

if __name__=="__main__":
    asyncio.run(main())
