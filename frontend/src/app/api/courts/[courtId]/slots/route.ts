import { NextResponse } from "next/server";
const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
export async function GET(request: Request, { params }: { params: Promise<{ courtId: string }> }) {
  const { courtId } = await params;
  const date = new URL(request.url).searchParams.get("date");
  if (!date) return NextResponse.json({ detail: "date is required" }, { status: 422 });
  if (!/^\d+$/.test(courtId)) return NextResponse.json({ detail: "Invalid court" }, { status: 422 });
  const response = await fetch(`${base}/courts/${courtId}/available-slots?date=${encodeURIComponent(date)}&duration_minutes=60`);
  return new NextResponse(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
}
