import { cookies } from "next/headers";
import { NextResponse } from "next/server";
const base=process.env.NEXT_PUBLIC_API_BASE_URL??"http://127.0.0.1:8000/api/v1";
export async function PATCH(request:Request){const token=(await cookies()).get("mal3by_session")?.value;if(!token)return NextResponse.json({detail:"Unauthorized"},{status:401});const body=await request.json();const response=await fetch(`${base}/users/me/profile/language`,{method:"PATCH",headers:{Authorization:`Bearer ${token}`,"Content-Type":"application/json"},body:JSON.stringify({preferred_language:body.preferred_language})});const data=await response.json().catch(()=>({detail:"Unable to save language"}));return NextResponse.json(data,{status:response.status})}
