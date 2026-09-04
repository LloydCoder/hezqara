"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Agent, AgentType } from "@/types/agent";
import type { AnalyticsSummary, DailyMetrics } from "@/types/analytics";
import type { Patient, Call } from "@/types/patient";

export function useAgents(clinicId: string) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    if (!clinicId) { setAgents([]); setLoading(false); return; }
    setLoading(true); setError(null);
    try { setAgents(await api.agents.list(clinicId)); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to load agents"); }
    finally { setLoading(false); }
  }, [clinicId]);
  useEffect(() => { void load(); }, [load]);
  const toggleAgent = useCallback(async (agentType: AgentType | string, enabled: boolean) => {
    if (!clinicId) return;
    const type = agentType as AgentType;
    try {
      await api.agents.toggle(clinicId, type, enabled);
      setAgents((current) => current.map((agent) => agent.id === type ? { ...agent, status: enabled ? "active" : "disabled" } : agent));
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to update agent"); }
  }, [clinicId]);
  return { agents, loading, error, reload: load, toggleAgent };
}

export function useAnalytics(clinicId: string) {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [daily, setDaily] = useState<DailyMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    if (!clinicId) { setLoading(false); return; }
    setLoading(true); setError(null);
    try {
      const date = new Date().toISOString().slice(0, 10);
      const [nextSummary, nextDaily] = await Promise.all([
        api.analytics.summary(clinicId, "today"),
        api.analytics.daily(clinicId, date),
      ]);
      setSummary(nextSummary); setDaily(nextDaily);
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to load analytics"); }
    finally { setLoading(false); }
  }, [clinicId]);
  useEffect(() => { void load(); }, [load]);
  return { summary, daily, loading, error, reload: load };
}

export function useCalls(clinicId: string) {
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    if (!clinicId) { setCalls([]); setLoading(false); return; }
    setLoading(true); setError(null);
    try { setCalls(await api.calls.list(clinicId)); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to load calls"); }
    finally { setLoading(false); }
  }, [clinicId]);
  useEffect(() => { void load(); }, [load]);
  return { calls, loading, error, reload: load };
}

export function usePatients(clinicId: string) {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    if (!clinicId) { setPatients([]); setLoading(false); return; }
    setLoading(true); setError(null);
    try { setPatients(await api.patients.list(clinicId)); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to load patients"); }
    finally { setLoading(false); }
  }, [clinicId]);
  useEffect(() => { void load(); }, [load]);
  return { patients, loading, error, reload: load };
}
