import FileUpload from "./FileUpload";
import MissingFiles from "./MissingFiles";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "#/ui/resizable";
import ChatPanel from "./ChatPanel";
import Continue from "./Continue";

export default function AddData() {
  return (
    <ResizablePanelGroup direction="vertical" className="rounded-lg border">
      <ResizablePanel defaultSize={0}>
        <ChatPanel />
      </ResizablePanel>

      <ResizableHandle withHandle />

      <ResizablePanel defaultSize={100}>
        <ResizablePanelGroup direction="horizontal">
          <ResizablePanel defaultSize={100}>
            <FileUpload />
          </ResizablePanel>

          <ResizableHandle withHandle />

          <ResizablePanel maxSize={20} defaultSize={0}>
            <MissingFilesAndContinue />
          </ResizablePanel>
        </ResizablePanelGroup>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}

function MissingFilesAndContinue() {
  return (
    <div className="flex flex-col justify-between h-full">
      <MissingFiles />

      <Continue />
    </div>
  );
}
