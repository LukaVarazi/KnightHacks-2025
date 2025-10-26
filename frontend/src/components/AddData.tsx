import FileUpload from "./FileUpload";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "#/ui/resizable";
import ChatPanel from "./ChatPanel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import StepContext from "~/lib/context";
import { useAtomValue } from "jotai";
import { stepAtom } from "~/lib/atom";
import Report from "./Report";

export default function AddData() {
  const step = useAtomValue(stepAtom);

  return (
    <div className="flex flex-col gap-4 size-full">
      <Tabs defaultValue="emt" className="size-full">
        <TabsList className="w-full flex items-center">
          <TabsTrigger value="emt">EMT / Ambulance</TabsTrigger>
          <TabsTrigger
            // disabled={step <= 2}
            value="medical"
          >
            Medical Records
          </TabsTrigger>
          <TabsTrigger
            // disabled={step <= 3}
            value="insurance"
          >
            Insurnace Policy
          </TabsTrigger>
          <TabsTrigger
            // disabled={step <= 4}
            value="report"
          >
            Report
          </TabsTrigger>
        </TabsList>

        <TabsContent value="emt">
          <ResizablePortion step={1} />
        </TabsContent>
        <TabsContent value="medical">
          <ResizablePortion step={2} />
        </TabsContent>
        <TabsContent value="insurance">
          <ResizablePortion step={3} />
        </TabsContent>
        <TabsContent value="report">
          <Report />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ResizablePortion({ step }: { step: number }) {
  return (
    <StepContext.Provider value={step}>
      <ResizablePanelGroup direction="horizontal" className="rounded-lg border">
        <ResizablePanel defaultSize={40}>
          <FileUpload />
        </ResizablePanel>

        <ResizableHandle withHandle />

        <ResizablePanel minSize={30} defaultSize={60}>
          <ChatPanel />
        </ResizablePanel>
      </ResizablePanelGroup>
    </StepContext.Provider>
  );
}
