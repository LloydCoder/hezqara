import { api } from '@/lib/api';
export const agentsApi={list:()=>api.get('/api/v1/agents'),execute:(name:string,input:unknown,idempotencyKey:string)=>api.post(`/api/v1/agents/${encodeURIComponent(name)}/execute`,{task:name,input,idempotency_key:idempotencyKey})};
