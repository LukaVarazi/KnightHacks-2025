import { useAtomValue } from "jotai";
import { loadingDataAtom } from "~/lib/atom";
import { Spinner } from "./ui/spinner";

export default function LoadingOverlay() {
  const loading = useAtomValue(loadingDataAtom);
  if (!loading) return null;
  return (
    <div
      className="absolute z-50 bg-slate-300 w-screen h-screen flex flex-col items-center justify-center gap-5"
      style={{
        backgroundColor: "rgba(0, 0, 0, 0.3)",
        backdropFilter: "blur(5px)",
        WebkitBackdropFilter: "blur(5px)",
      }}
    >
      <span className="text-center text-3xl">Analyzing your files</span>
      <span className="text-center text-2xl text-muted-foreground">
        This may take a while
      </span>
      <Spinner className="size-16" />
    </div>
  );
}
