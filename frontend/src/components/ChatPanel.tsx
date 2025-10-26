import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "#/ui/shadcn-io/ai/conversation";
import {
  Message,
  MessageAvatar,
  MessageContent,
} from "#/ui/shadcn-io/ai/message";
import { IconMessageCircle } from "@tabler/icons-react";
import { useAtomValue } from "jotai";
import { useContext } from "react";
import { stepOutputsAtom } from "~/lib/atom";
import StepContext from "~/lib/context";
import { Response } from "#/ui/shadcn-io/ai/response";

export default function ChatPanel() {
  const step = useContext(StepContext);
  const stepOutputs = useAtomValue(stepOutputsAtom);
  const chatText = stepOutputs[step - 1];

  if (!chatText) {
    return (
      <div className="size-full flex flex-col items-center justify-center p-4">
        <h2 className="text-xl">Nothing to see for now</h2>
        <h3 className="text-muted-foreground">
          Here is where your AI summary will be
        </h3>

        <IconMessageCircle className="size-8 text-muted-foreground" />
      </div>
    );
  }

  return (
    <Conversation className="relative w-full h-full overflow-y-auto">
      <ConversationContent>
        {chatText && (
          <Message from="assistant">
            <MessageContent className="max-h-[70vh] overflow-y-auto">
              <Response>{chatText}</Response>
            </MessageContent>
            <MessageAvatar src="/logo.png" />
          </Message>
        )}
      </ConversationContent>
      <ConversationScrollButton />
    </Conversation>
  );
}
