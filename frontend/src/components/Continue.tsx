import { toast } from "sonner";
import { useAtom, useAtomValue, useSetAtom } from "jotai";
import { Button } from "./ui/button";
import {
  filesAtom,
  loadingDataAtom,
  stepAtom,
  stepOutputsAtom,
} from "~/lib/atom";
import { delay } from "es-toolkit";

const API_URL = import.meta.env.VITE_API_URL as string;

export default function Continue() {
  const setStepOutputs = useSetAtom(stepOutputsAtom);
  const [step, setStep] = useAtom(stepAtom);
  const files = useAtomValue(filesAtom);
  const setLoadingDataAtom = useSetAtom(loadingDataAtom);

  const onClick = async () => {
    setLoadingDataAtom(true);

    const [text, ok] = await apiReq(step, files);

    setLoadingDataAtom(false);

    if (!ok) {
      toast.warning(
        "Missing files for analysis, read AI feedback and add needed files to continue!"
      );
    } // We good
    else {
      setStep((prev) => prev + 1);
    }

    setStepOutputs((prev) => {
      const copy = [...prev];

      copy[step - 1] = text;
      return copy;
    });
  };

  return (
    <Button
      className="m-2 text-xl"
      size="lg"
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onClick();
      }}
      variant="destructive"
    >
      Continue analysis
    </Button>
  );
}

async function apiReq(step: number, files: File[]): Promise<[string, boolean]> {
  const formData = new FormData();
  for (let file of files) {
    formData.append("files[]", file);
  }

  const res = await fetch(`${API_URL}/${step}`, {
    method: "POST",
    body: formData,
  });

  const text = await res.text();
  if (!res.ok) {
    console.error(text);
    return [text, false];
  }

  return [text, true];
}
