import { Spinner } from "@/components/ui/spinner";
import { Surface } from "@/components/ui/surface";

export function LoadingState({ label }: { label: string }) {
  return <Surface role="status" aria-live="polite" aria-busy="true" className="flex min-h-40 items-center justify-center"><Spinner label={label} /></Surface>;
}
