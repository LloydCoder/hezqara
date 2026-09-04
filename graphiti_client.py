"""
Graphiti Client — Persistent agent memory for Carenova.

Agents call this instead of raw context injection.
Result: 200 tokens of precise context, not 5,000 tokens of history.

Uses FalkorDB as the graph backend.
Multi-tenancy enforced via group_id = clinic_id.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GraphitiClient:
    """
    Wraps Graphiti for Carenova agent memory.

    Each clinic gets an isolated knowledge graph (group_id = clinic_id).
    Patient data, call history, and clinic preferences are stored as
    temporal graph nodes — facts carry timestamps so the agent knows
    what is current vs what has changed.
    """

    def __init__(
        self,
        graphiti_url: str = "http://localhost:8005",
        falkordb_url: str = "redis://localhost:6379",
    ) -> None:
        self.graphiti_url = graphiti_url
        self.falkordb_url = falkordb_url
        self._client = None

    async def get_clinic_context(self, clinic_id: str) -> dict:
        """
        Fetch minimal clinic context for agent session start.
        Returns structured dict, not raw history.
        """
        try:
            results = await self.search(
                query=f"clinic configuration for {clinic_id}",
                group_id=clinic_id,
                limit=5,
            )

            context = {
                "clinic_id": clinic_id,
                "ehr": None,
                "active_agents": [],
                "last_interaction": None,
                "patient_count": 0,
            }

            for result in results:
                if result.get("entity_type") == "clinic_config":
                    context.update(result.get("facts", {}))

            return context

        except Exception as e:
            logger.warning(
                "Graphiti unavailable for clinic %s: %s — using empty context",
                clinic_id, str(e)
            )
            return {
                "clinic_id": clinic_id,
                "ehr": None,
                "active_agents": [],
                "last_interaction": None,
                "patient_count": 0,
            }

    async def add_episode(
        self,
        clinic_id: str,
        call_id: str,
        episode_type: str,
        content: str,
        patient_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Store a call episode in the knowledge graph.
        Every call creates an episode — this is how memory accumulates.
        """
        try:
            import httpx

            payload = {
                "group_id": clinic_id,
                "episode_type": episode_type,
                "content": content,
                "metadata": {
                    "call_id": call_id,
                    "patient_id": patient_id,
                    **(metadata or {}),
                },
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.graphiti_url}/episodes",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.warning(
                "Failed to store episode for call %s: %s — continuing",
                call_id, str(e)
            )
            return {"episode_id": None, "error": str(e)}

    async def search(
        self,
        query: str,
        group_id: str,
        limit: int = 5,
    ) -> list:
        """
        Search the knowledge graph for relevant context.
        Uses hybrid retrieval: semantic + keyword + graph traversal.
        """
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.graphiti_url}/search",
                    params={
                        "query": query,
                        "group_id": group_id,
                        "limit": limit,
                    },
                )
                response.raise_for_status()
                return response.json().get("results", [])

        except Exception as e:
            logger.warning("Graphiti search failed: %s — returning empty", str(e))
            return []
