"use client";
import { useCallback, useEffect, useState } from "react";
import { api, type APIAgent, type AnalyticsSummary, type APICall } from "@/lib/api";
export type FrontendAgent=APIAgent;
function useDeferredLoad<T>(loader:()=>Promise<T>,initial:T){const[value,setValue]=useState(initial);const[loading,setLoading]=useState(true);const[error,setError]=useState<string|null>(null);const load=useCallback(async()=>{setLoading(true);setError(null);try{setValue(await loader())}catch(e){setError(e instanceof Error?e.message:"Request failed")}finally{setLoading(false)}},[loader]);useEffect(()=>{const id=window.setTimeout(()=>{void load()},0);return()=>window.clearTimeout(id)},[load]);return{value,loading,error,reload:load}}
export function useAgents(){const loader=useCallback(()=>api.agents.list(),[]);const result=useDeferredLoad<FrontendAgent[]>(loader,[]);return{agents:result.value,loading:result.loading,error:result.error,reload:result.reload}}
export function useAnalytics(){const loader=useCallback(()=>api.analytics.summary(),[]);const result=useDeferredLoad<AnalyticsSummary|null>(loader,null);return{summary:result.value,daily:null,loading:result.loading,error:result.error,reload:result.reload}}
export function useCalls(){const loader=useCallback(()=>api.calls.list(),[]);const result=useDeferredLoad<APICall[]>(loader,[]);return{calls:result.value,loading:result.loading,error:result.error,reload:result.reload}}
export function usePatients(search=""){const loader=useCallback(()=>api.patients.list(50,0,search),[search]);const result=useDeferredLoad<unknown[]>(loader,[]);return{patients:result.value,loading:result.loading,error:result.error,reload:result.reload}}
