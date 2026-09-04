"use client";
import { useCallback,useEffect,useState } from "react";
import { api } from "@/lib/api";
export type FrontendAgent={id:string;name:string;status:string};
export type AnalyticsSummary={total_calls?:number;total_appointments_booked?:number;total_cost_savings_usd?:number;receptionist_hours_saved?:number};
export function useAgents(scope?:string){
 const [agents,setAgents]=useState<FrontendAgent[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState<string|null>(null);
 const load=useCallback(async()=>{setLoading(true);setError(null);try{setAgents(await api.agents.list(scope) as FrontendAgent[]);}catch(e){setError(e instanceof Error?e.message:"Unable to load agents");setAgents([]);}finally{setLoading(false);}},[scope]);
 useEffect(()=>{const id=window.setTimeout(()=>{void load();},0);return()=>window.clearTimeout(id);},[load]);
 return {agents,loading,error,reload:load,toggleAgent:async()=>{throw new Error("agent provisioning is managed by the authorized backend")}};
}
export function useAnalytics(_scope?:string,_period?:string){const [summary,setSummary]=useState<AnalyticsSummary|null>(null);const [loading,setLoading]=useState(true);const [error,setError]=useState<string|null>(null);const load=useCallback(async()=>{setLoading(false);setSummary(null);},[]);useEffect(()=>{const id=window.setTimeout(()=>{void load();},0);return()=>window.clearTimeout(id);},[load]);return {summary,daily:null,loading,error,reload:load};}
export function useCalls(_scope?:string){const [calls,setCalls]=useState<unknown[]>([]);const [loading,setLoading]=useState(false);const [error]=useState<string|null>(null);return {calls,setCalls,loading,error,reload:async()=>{}};}
export function usePatients(_scope?:string){const [patients,setPatients]=useState<unknown[]>([]);const [loading,setLoading]=useState(false);const [error]=useState<string|null>(null);return {patients,setPatients,loading,error,reload:async()=>{}};}
