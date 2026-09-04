"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Agent, AgentType } from "@/types/agent";

export function useAgents(clinicId: string) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!clinicId) {
      setAgents([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setAgents(await api.agents.list(clinicId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load agents");
    } finally {
      setLoading(false);
    }
  }, [clinicId]);

  useEffect(() => {
    void load();
  }, [load]);

  const toggleAgent = useCallback(async (agentType: AgentType | string, enabled: boolean) => {
    if (!clinicId) return;
    const type = agentType as AgentType;
    try {
      await api.agents.toggle(clinicId, type, enabled);
      setAgents((current) => current.map((agent) =>
        agent.id === type ? { ...agent, status: enabled ? "active" : "disabled" } : agent,
      ));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update agent");
    }
  }, [clinicId]);

  return { agents, loading, error, reload: load, toggleAgent };
}
