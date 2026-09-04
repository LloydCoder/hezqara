const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8004";
type TokenProvider=()=>Promise<string|null>; let tokenProvider:TokenProvider|null=null;
export function setApiTokenProvider(provider:TokenProvider|null){tokenProvider=provider;}
class APIError extends Error{constructor(message:string,public status:number,public data?:unknown){super(message);this.name="APIError";}}
async function request<T>(path:string,options:RequestInit={}):Promise<T>{
 const token=tokenProvider?await tokenProvider():null; const headers=new Headers(options.headers); headers.set("Content-Type","application/json"); if(token) headers.set("Authorization",`Bearer ${token}`);
 const response=await fetch(`${BASE_URL}${path}`,{...options,headers,cache:"no-store"}); if(!response.ok){const data=await response.json().catch(()=>({})); throw new APIError(typeof data==='object'&&data&&'detail' in data?String(data.detail):`API error ${response.status}`,response.status,data);} return response.json() as Promise<T>;
}
export const api={
 health:{check:()=>request<{status:string;service:string}>("/health")},
 patients:{list:(_scope?:string)=>request<unknown[]>("/api/v1/patients"),create:(input:unknown)=>request<unknown>("/api/v1/patients",{method:"POST",body:JSON.stringify(input)})},
 appointments:{list:(_scope?:string)=>request<unknown[]>("/api/v1/appointments"),create:(input:unknown)=>request<unknown>("/api/v1/appointments",{method:"POST",body:JSON.stringify(input)})},
 agents:{list:(_scope?:string)=>request<unknown[]>("/api/v1/agents")},
};
export {APIError}; export default api;
