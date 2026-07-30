import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Surface } from "@/components/ui/surface";
import { copy } from "@/lib/copy";

export default async function MatchLoading({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const text = copy[locale === "en" ? "en" : "ar"];
  return (
    <section className="page-wrap" aria-busy="true">
      <span className="sr-only"><Spinner label={text.matchLoading} /></span>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(19rem,.65fr)]">
        <Surface padding="lg">
          <Skeleton variant="text" className="h-5 w-32" />
          <Skeleton variant="text" className="mt-4 h-10 w-3/4" />
          <div className="mt-8 grid gap-5 sm:grid-cols-2">
            {Array.from({ length: 8 }, (_, index) => <Skeleton key={index} className="h-14" />)}
          </div>
        </Surface>
        <Surface padding="lg"><Skeleton className="h-14" /></Surface>
      </div>
    </section>
  );
}
