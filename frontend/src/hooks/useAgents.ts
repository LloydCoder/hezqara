"use client";

// Custom hooks for data fetching

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import type { Agent, AgentType } from "@/types/agent";
import type { Call } from "@/types/patient";
import type { AnalyticsSummary } from "@/types/analytics";

// ── useAgents ─────────────────────────────────────────────────────────────────

export function useAgents(clinicId: string) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.agents.list(clinicId);
      setAgents(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load agents");
    } finally {
      setLoading(false);
    }
  }, [clinicId]);

  useEffect(() => {
    if (clinicId) fetchAgents();
  }, [clinicId, fetchAgents]);

  const toggleAgent = async (agentType: AgentType, enabled: boolean) => {
    await api.agents.toggle(clinicId, agentType, enabled);
    await fetchAgents();
  };

  return { agents, loading, error, refetch: fetchAgents, toggleAgent };
}

// ── useCalls ──────────────────────────────────────────────────────────────────

export function useCalls(clinicId: string, limit = 50) {
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCalls = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.calls.list(clinicId, limit);
      setCalls(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load calls");
    } finally {
      setLoading(false);
    }
  }, [clinicId, limit]);

  useEffect(() => {
    if (clinicId) fetchCalls();
  }, [clinicId, fetchCalls]);

  return { calls, loading, error, refetch: fetchCalls };
}

// ── useAnalytics ──────────────────────────────────────────────────────────────

export function useAnalytics(
  clinicId: string,
  period: "today" | "week" | "month" = "today"
) {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!clinicId) return;

    const fetch = async () => {
      try {
        setLoading(true);
        const data = await api.analytics.summary(clinicId, period);
        setSummary(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, [clinicId, period]);

  return { summary, loading, error };
}

// ── usePatients ───────────────────────────────────────────────────────────────

export function usePatients(clinicId: string) {
  const [patients, setPatients] = useState<
    import("@/types/patient").Patient[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!clinicId) return;

    const fetch = async () => {
      try {
        setLoading(true);
        const data = await api.patients.list(clinicId, search || undefined);
        setPatients(data);
      } catch {
        setPatients([]);
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, [clinicId, search]);

  return { patients, loading, search, setSearch };
}
