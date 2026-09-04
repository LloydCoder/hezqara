const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";
type TokenProvider = () => Promise<string | null>;
let tokenProvider: TokenProvider | null = null;
export function setApiTokenProvider(provider: TokenProvider | null) { tokenProvider = provider; }
export class APIError extends Error { constructor(message: string, public status: number, public data?: unknown) { super(message); this.name = "APIError"; } }
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = tokenProvider ? await tokenProvider() : null;
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers, cache: "no-store" });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = typeof data === "object" && data && "detail" in data ? String(data.detail) : `API error ${response.status}`;
    throw new APIError(detail, response.status, data);
  }
  return response.json() as Promise<T>;
}
export type APIAgent={id:string;name:string;status:string;description?:string};
export type AnalyticsSummary={total_calls:number|null;total_appointments_booked:number|null;total_cost_savings_usd?:number|null};
export type APICall={id:string;call_type:string;intent:string|null;outcome:string|null;agent_type:string;duration_ms:number|null;started_at:string;ended_at:string|null};
export const api={
  get:<T>(path:string)=>request<T>(path), post:<T>(path:string,body:unknown)=>request<T>(path,{method:"POST",body:JSON.stringify(body)}), patch:<T>(path:string,body:unknown)=>request<T>(path,{method:"PATCH",body:JSON.stringify(body)}), delete:<T>(path:string)=>request<T>(path,{method:"DELETE"}),
  health:{check:()=>request<{status:string;service:string}>("/health")},
  patients:{list:(limit=50,offset=0)=>request<unknown[]>(`/api/v1/patients?limit=${limit}&offset=${offset}`),create:(input:unknown)=>request<unknown>("/api/v1/patients",{method:"POST",body:JSON.stringify(input)})},
  appointments:{list:(limit=50,offset=0)=>request<unknown[]>(`/api/v1/appointments?limit=${limit}&offset=${offset}`),create:(input:unknown)=>request<unknown>("/api/v1/appointments",{method:"POST",body:JSON.stringify(input)})},
  agents:{list:()=>request<APIAgent[]>("/api/v1/agents")}, analytics:{summary:()=>request<AnalyticsSummary>("/api/v1/analytics/summary")}, calls:{list:(limit=50,offset=0)=>request<APICall[]>(`/api/v1/calls?limit=${limit}&offset=${offset}`)},
};
export default api;
