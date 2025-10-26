import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "~/components/ui/dialog";
import { Button } from "./ui/button";
import { useAtomValue, useSetAtom } from "jotai";
import { currentTabAtom, stepAtom } from "~/lib/atom";

export default function SkipBtn() {
  const setStep = useSetAtom(stepAtom);
  const setCurrentTab = useSetAtom(currentTabAtom);

  function handleSkip() {
    setStep((prev) => prev + 1);
    setCurrentTab((prev) => {
      if (prev === "emt") return "medical";
      if (prev === "medical") return "insurance";
      if (prev === "insurance") return "report";
    });
  }

  return (
    <Dialog>
      <DialogTrigger
        asChild
        onClick={(e) => {
          e.stopPropagation();
        }}
      >
        <Button variant="destructive">Skip Case</Button>
      </DialogTrigger>
      <DialogContent
        onClick={(e) => {
          e.stopPropagation();
        }}
      >
        <DialogHeader>
          <DialogTitle>Are you absolutely sure?</DialogTitle>
          <DialogDescription>
            This may lead to inaccurate results. Though you may return to a step
            at any time.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="sm:justify-start">
          <DialogClose asChild>
            <Button type="button" variant="secondary" onClick={handleSkip}>
              Skip this case
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
