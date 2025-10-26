import ReactMarkdown from "react-markdown";
import { Button } from "#/ui/button";
import { useAtomValue } from "jotai";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "~/components/ui/dialog";
import {
  reportConsAtom,
  reportPartsAtom,
  reportPercentAtom,
  reportPercentExplanationAtom,
  reportProstom as reportProsAtom,
  reportStatusAtom,
} from "~/lib/atom";

type FinalReportData = {
  caseStatus: string;
  percent: string;
  percentBreakdown: string;
  proText: string;
  consText: string;
};

export default function ReportWrapper() {
  const reportStatus = useAtomValue(reportStatusAtom);
  const reportPros = useAtomValue(reportProsAtom);
  const reportCons = useAtomValue(reportConsAtom);
  const reportPercent = useAtomValue(reportPercentAtom);
  const reportPercentExplanation = useAtomValue(reportPercentExplanationAtom);

  return (
    <Report
      caseStatus={reportStatus}
      percent={reportPercent}
      percentBreakdown={reportPercentExplanation}
      proText={reportPros}
      consText={reportCons}
    />
  );
}

function Report({
  caseStatus,
  percent,
  percentBreakdown: percentBreakdownSummary,
  proText,
  consText,
}: FinalReportData) {
  return (
    <div className="flex flex-col gap-4 bg-input/30 size-full px-8 py-4">
      <div className="flex justify-around">
        <div className="p-2 border-accent border-2 rounded-xl h-min">
          Case Status: {caseStatus}
        </div>

        <Dialog>
          <DialogTrigger>
            <div className="flex flex-col gap-1">
              <Button>P.B.S: {percent}</Button>
              <span className="text-sm text-muted-foreground">
                Click for breakdown
              </span>
            </div>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Percentage Breakdown Summary</DialogTitle>
              <DialogDescription>{percentBreakdownSummary}</DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex gap-4 justify-around size-full">
        <div className="flex flex-col gap-2 grow items-center">
          <h2 className="text-2xl font-semibold">Pro's</h2>

          <p className="p-3 prose-neutral border-2 border-accent overflow-y-auto rounded-lg size-full">
            <ReactMarkdown>{proText}</ReactMarkdown>
          </p>
        </div>

        <div className="flex flex-col gap-2 grow items-center">
          <h2 className="text-2xl font-semibold">Cons's</h2>

          <p className="p-3 prose-neutral border-2 border-accent overflow-y-auto rounded-lg size-full">
            <ReactMarkdown>{consText}</ReactMarkdown>
          </p>
        </div>
      </div>
    </div>
  );
}
