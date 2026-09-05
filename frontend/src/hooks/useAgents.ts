"use client";
import {useCallback,useEffect,useState} from 'react';
import {api,type APIAgent,type APICall,type AnalyticsSummary,type Execution,type OperationsSummary,type Patient,type Task} from '@/lib/api';
function useLoad<T>(loader:()=>Promise<T>,initial:T){const[value,setValue]=useState(initial);const[loading,setLoading]=useState(true);const[error,setError]=useState<string|null>(null);const load=useCallback(async()=>{setLoading(true);setError(null);try{setValue(await loader())}catch(e){setError(e instanceof Error?e.message:'Request failed')}finally{setLoading(false)}},[loader]);useEffect(()=>{void load()},[load]);return{value,loading,error,reload:load}}
export function useAgents(){const loader=useCallback(()=>api.agents.list(),[]);const r=useLoad<APIAgent[]>(loader,[]);return{agents:r.value,loading:r.loading,error:r.error,reload:r.reload}}
export function useAnalytics(){const loader=useCallback(()=>api.analytics.summary(),[]);const r=useLoad<AnalyticsSummary|null>(loader,null);return{summary:r.value,daily:null,loading:r.loading,error:r.error,reload:r.reload}}
export function useCalls(){const loader=useCallback(()=>api.calls.list(),[]);const r=useLoad<APICall[]>(loader,[]);return{calls:r.value,loading:r.loading,error:r.error,reload:r.reload}}
export function usePatients(search=''){const loader=useCallback(()=>api.patients.list(50,0,search),[search]);const r=useLoad<Patient[]>(loader,[]);return{patients:r.value,loading:r.loading,error:r.error,reload:r.reload}}
export function useTasks(status?:string){const loader=useCallback(()=>api.tasks.list(50,0,status),[status]);const r=useLoad<Task[]>(loader,[]);return{tasks:r.value,loading:r.loading,error:r.error,reload:r.reload}}
export function useExecutions(){const loader=useCallback(()=>api.executions.list(),[]);const r=useLoad<Execution[]>(loader,[]);return{executions:r.value,loading:r.loading,error:r.error,reload:r.reload}}
export function useOperationsSummary(){const loader=useCallback(()=>api.operations.summary(),[]);const r=useLoad<OperationsSummary|null>(loader,null);return{summary:r.value,loading:r.loading,error:r.error,reload:r.reload}}
