import { NextResponse } from "next/server";
const base=process.env.NEXT_PUBLIC_API_BASE_URL??"http://127.0.0.1:8000/api/v1";
export async function POST(req:Request){const res=await fetch(`${base}/auth/register`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(await req.json())});const data=await res.json().catch(()=>({detail:"Registration failed"}));return NextResponse.json(res.ok?{ok:true}: {detail:typeof data.detail==="string"?data.detail:"Registration failed"},{status:res.status})}
