import { api } from '@/lib/api';
export const schedulingApi={list:()=>api.get('/api/v1/appointments'),create:(input:unknown)=>api.post('/api/v1/appointments',input)};
