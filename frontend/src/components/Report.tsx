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
      <div className="flex justify-around relative">
        <GenerateReport />

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
          <h2 className="text-2xl font-semibold">Con's</h2>

          <p className="p-3 prose-neutral border-2 border-accent overflow-y-auto rounded-lg size-full">
            <ReactMarkdown>{consText}</ReactMarkdown>
          </p>
        </div>
      </div>
    </div>
  );
}

import { toast } from "sonner";
import { getDefaultStore, useAtom, useSetAtom } from "jotai";
import {
  filesAtom,
  loadingDataAtom,
  reportProstom,
  stepAtom,
  stepOutputsAtom,
} from "~/lib/atom";
import { useContext } from "react";
import StepContext from "~/lib/context";

const API_URL = import.meta.env.VITE_API_URL as string;

function GenerateReport() {
  const setStepOutputs = useSetAtom(stepOutputsAtom);
  const trueStep = useContext(StepContext);
  const [step, setStep] = useAtom(stepAtom);
  const [files, setFiles] = useAtom(filesAtom);
  const setLoadingDataAtom = useSetAtom(loadingDataAtom);

  const onClick = async () => {
    setLoadingDataAtom(true);

    const [text, ok] = await apiReq(files);

    setLoadingDataAtom(false);

    if (!ok) {
      toast.warning(
        "Missing files for analysis, read AI feedback and add needed files to continue!\n You may use the skip case button to continue anyways"
      );
    } // We good
    else {
      // setFiles([]);
      setStep((prev) => prev + 1);
      toast.success("Analysis complete!");
    }

    setStepOutputs((prev) => {
      const copy = [...prev];

      copy[trueStep - 1] = text;
      return copy;
    });
  };

  return (
    <Button
      className="m-2 absolute top-0 left-0"
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onClick();
      }}
      variant="destructive"
    >
      Generate Report
    </Button>
  );
}

async function apiReq(files: File[]): Promise<[string, boolean]> {
  const formData = new FormData();
  for (let file of files) {
    formData.append("files[]", file);
  }

  const res = await fetch(`${API_URL}/${4}`, {
    method: "POST",
    body: formData,
  });

  const data: Record<string, string> = await res.json();
  const text = data.result;
  if (!data.good) {
    console.error(text);
    return [text, false];
  }

  // Report step
  const defaultStore = getDefaultStore();
  defaultStore.set(reportStatusAtom, data.status);
  defaultStore.set(reportProstom, data.pros);
  defaultStore.set(reportConsAtom, data.cons);
  const [percent, explanation] = data.percent.split(/\r?\n/, 2);
  defaultStore.set(reportPercentAtom, percent);
  defaultStore.set(reportPercentExplanationAtom, explanation);

  return [text, true];
}
