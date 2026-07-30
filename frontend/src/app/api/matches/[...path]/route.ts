import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

async function forward(request: Request, { params }: { params: Promise<{ path: string[] }> }) {
  const token = (await cookies()).get("mal3by_session")?.value;
  if (!token) return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  const { path } = await params;
  const [matchId, resource, requestId, action] = path;
  if (!/^\d+$/.test(matchId ?? "")) return NextResponse.json({ detail: "Unsupported match operation" }, { status: 404 });

  let backendPath: string | null = null;
  if (request.method === "POST" && path.length === 2 && ["join", "leave", "join-requests"].includes(resource)) {
    backendPath = `${matchId}/${resource}`;
  }
  if (
    request.method === "POST" &&
    path.length === 4 &&
    resource === "join-requests" &&
    /^\d+$/.test(requestId ?? "") &&
    ["withdraw", "approve", "reject"].includes(action)
  ) {
    backendPath = `${matchId}/join-requests/${requestId}/${action}`;
  }
  if (!backendPath) return NextResponse.json({ detail: "Unsupported match operation" }, { status: 404 });

  const body = resource === "join-requests" && path.length === 2 ? "{}" : undefined;
  const response = await fetch(`${base}/matches/${backendPath}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, Accept: "application/json", "Content-Type": "application/json" },
    body,
  });
  return new NextResponse(await response.text(), {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}

export const POST = forward;
