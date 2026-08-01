import { NextResponse } from "next/server";
import { cookies } from "next/headers";
const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
const dateTime = (value: unknown) => typeof value === "string" && !Number.isNaN(Date.parse(value));
async function forward(request: Request, { params }: { params: Promise<{ path: string[] }> }) {
  const token = (await cookies()).get("mal3by_session")?.value;
  if (!token) return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  const { path } = await params; const id = path.length === 1 && /^\d+$/.test(path[0]) ? path[0] : null;
  let backendPath: string | null = null; let body: string | undefined;
  if (request.method === "GET" && path.length === 1 && path[0] === "me") backendPath = "me";
  if (request.method === "GET" && id) backendPath = id;
  if (request.method === "GET" && path.length === 2 && /^\d+$/.test(path[0]) && path[1] === "hold-status") backendPath = `${path[0]}/hold-status`;
  if (request.method === "POST" && path.length === 1 && path[0] === "hold") { const input = await request.json().catch(() => null); if (!input || Object.keys(input).some(key => !["court_id","start_time","end_time"].includes(key)) || !Number.isInteger(input.court_id) || !dateTime(input.start_time) || !dateTime(input.end_time)) return NextResponse.json({ detail: "Invalid hold request" }, { status: 422 }); backendPath = "hold"; body = JSON.stringify({ court_id: input.court_id, start_time: input.start_time, end_time: input.end_time }); }
  if (request.method === "POST" && path.length === 2 && /^\d+$/.test(path[0]) && ["cancel","cancel-hold"].includes(path[1])) { const input = await request.json().catch(() => ({})); if (input && (typeof input !== "object" || Object.keys(input).some(key => key !== "cancellation_reason") || (input.cancellation_reason !== undefined && typeof input.cancellation_reason !== "string"))) return NextResponse.json({ detail: "Invalid booking request" }, { status: 422 }); backendPath = `${path[0]}/${path[1]}`; body = JSON.stringify(input ?? {}); }
  if (!backendPath) return NextResponse.json({ detail: "Unsupported booking operation" }, { status: 404 });
  const response = await fetch(`${base}/bookings/${backendPath}`, { method: request.method, headers: { Authorization: `Bearer ${token}`, Accept: "application/json", "Content-Type": "application/json" }, body });
  return new NextResponse(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
}
export const GET = forward; export const POST = forward;
