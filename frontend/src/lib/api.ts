import { ApiError, type Booking, type Court, type MatchParticipant, type OwnerDashboard, type RatingSummary, type Review, type User } from "@/lib/types";
import { isJoinRequestArray, isMatch, isMatchArray, isParticipantArray } from "@/lib/match-validation";

const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
if (!/^https?:\/\//.test(base)) throw new Error("NEXT_PUBLIC_API_BASE_URL must be an http(s) URL");
async function request<T>(path:string,init?:RequestInit):Promise<T>{const response=await fetch(`${base}${path}`,{...init,headers:{Accept:"application/json","Content-Type":"application/json",...init?.headers},next:{revalidate:30}});if(!response.ok){const body=await response.json().catch(()=>null);throw new ApiError(response.status,typeof body?.detail==="string"?body.detail:"Unable to complete request")}return response.json() as Promise<T>}
const auth=(token:string):RequestInit=>({headers:{Authorization:`Bearer ${token}`},cache:"no-store"});
async function validated<T>(promise:Promise<unknown>,guard:(value:unknown)=>value is T,label:string){const data=await promise;if(!guard(data))throw new ApiError(502,`Invalid ${label} response`);return data}
const all=new URLSearchParams({limit:"100"});
async function matches(token:string,query=new URLSearchParams()){return validated(request<unknown>(`/matches${query.size?`?${query}`:""}`,auth(token)),isMatchArray,"match")}
async function match(token:string,id:string){return validated(request<unknown>(`/matches/${encodeURIComponent(id)}`,auth(token)),isMatch,"match")}
async function myMatchRequests(token:string){return validated(request<unknown>(`/matches/me/join-requests?${all}`,auth(token)),isJoinRequestArray,"join request")}
async function matchRequests(token:string,id:string){return validated(request<unknown>(`/matches/${encodeURIComponent(id)}/join-requests?status=pending&${all}`,auth(token)),isJoinRequestArray,"join request")}
async function matchParticipants(token:string,id:string):Promise<MatchParticipant[]>{return validated(request<unknown>(`/matches/${encodeURIComponent(id)}/participants`,auth(token)),isParticipantArray,"participant")}

export const api={
  courts:()=>request<Court[]>("/courts"),court:(id:string)=>request<Court>(`/courts/${id}`,{cache:"no-store"}),reviews:(id:string)=>request<Review[]>(`/courts/${id}/reviews`),summary:(id:string)=>request<RatingSummary>(`/courts/${id}/rating-summary`),slots:(id:string,date:string)=>request<{slots?:{start_time:string;end_time:string}[]}>(`/courts/${id}/available-slots?date=${encodeURIComponent(date)}`),me:(token:string)=>request<User>("/users/me",auth(token)),bookings:(token:string)=>request<Booking[]>("/bookings/me",auth(token)),booking:(token:string,id:string)=>request<Booking>(`/bookings/${id}`,auth(token)),matches,
  myCreatedMatches:(token:string)=>validated(request<unknown>(`/matches/me/created?${all}`,auth(token)),isMatchArray,"match"),
  myJoinedMatches:(token:string)=>validated(request<unknown>(`/matches/me/joined?${all}`,auth(token)),isMatchArray,"match"),
  match,myMatchRequests,matchRequests,matchParticipants,ownerDashboard:(token:string)=>request<OwnerDashboard>("/owner/dashboard",auth(token)),
};
