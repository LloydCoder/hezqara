import { api } from '@/lib/api';
export const patientsApi={list:()=>api.get('/api/v1/patients'),create:(input:unknown)=>api.post('/api/v1/patients',input)};
