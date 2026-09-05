"use client";
import {useCallback,useEffect,useState} from 'react';
import {api,type APIAgent,type APICall,type AnalyticsSummary,type Execution,type OperationsSummary,type Patient,type Task} from '@/lib/api';
function useLoad<T>(loader:()=>Promise<T>,initial:T){const[value,setValue]=useState(initial);const[loading,setLoading]=useState(true);const[error,setError]=useState<string|null>(null);const load=useCallback(async()=>{setLoading(true);setError(null);try{setValue(await loader())}catch(e){setError(e instanceof Error?e.message:'Request failed')}finally{setLoading(false)}},[loader]);useEffect(()=>{void load()},[load]);return{value,loading,error,reload:load}}
export function useAgents(){const r=useLoad<APIAgent[]>(()=>api.agents.list(),[]);return{agents:r.value,loading:r.loading,error:r.error,reload:r.reload}}
export function useAnalytics(){const r=useLoad<AnalyticsSummary|null>(()=>api.analytics.summary(),null);return{summary:r.value,daily:null,loading:r.loading,error:r.error,reload:r.reload}}
export function useCalls(){const r=useLoad<APICall[]>(()=>api.calls.list(),[]);return{calls:r.value,loading:r.loading,error:r.error,reload:r.reload}}
export function usePatients(search=''){const r=useLoad<Patient[]>(()=>api.patients.list(50,0,search),[]);return{patients:r.value,loading:r.loading,error:r.error,reload:r.reload}}
export function useTasks(status?:string){const r=useLoad<Task[]>(()=>api.tasks.list(50,0,status),[]);return{tasks:r.value,loading:r.loading,error:r.error,reload:r.reload}}
export function useExecutions(){const r=useLoad<Execution[]>(()=>api.executions.list(),[]);return{executions:r.value,loading:r.loading,error:r.error,reload:r.reload}}
export function useOperationsSummary(){const r=useLoad<OperationsSummary|null>(()=>api.operations.summary(),null);return{summary:r.value,loading:r.loading,error:r.error,reload:r.reload}}
