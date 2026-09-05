from contextlib import asynccontextmanager
import uuid
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import configure_logging
from app.infrastructure.database import close_database
from app.api.v1 import health,patients,scheduling,agents,tasks,executions,operations,audit,workflows,approvals,communications,healthcare_admin,billing,integrations,analytics,ai_governance
from app.api.webhooks import clerk_router,stripe_router,retell_router,whatsapp_router
configure_logging(settings.log_level)
@asynccontextmanager
async def lifespan(app:FastAPI):
    yield
    await close_database()
app=FastAPI(title='HEZQARA API',version='9.0.0',lifespan=lifespan,docs_url='/docs' if settings.app_env!='production' else None)
origins=settings.authorized_parties or (['http://localhost:3004'] if settings.app_env!='production' else [])
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=['GET','POST','PATCH','PUT','DELETE','OPTIONS'],allow_headers=['Authorization','Content-Type','X-Request-ID','X-Hezqara-Signature'])
@app.middleware('http')
async def request_id_middleware(request:Request,call_next):
    request_id=request.headers.get('X-Request-ID') or str(uuid.uuid4()); request.state.request_id=request_id
    response=await call_next(request); response.headers['X-Request-ID']=request_id; return response
app.include_router(health.router)
for router in (patients.router,scheduling.router,agents.router,tasks.router,executions.router,operations.router,audit.router,workflows.router,approvals.router,communications.router,healthcare_admin.router,billing.router,integrations.router,analytics.router,ai_governance.router): app.include_router(router,prefix='/api/v1')
app.include_router(clerk_router);app.include_router(stripe_router);app.include_router(retell_router);app.include_router(whatsapp_router)
