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
import { useAtomValue } from "jotai";
import { useContext } from "react";
import { stepOutputsAtom } from "~/lib/atom";
import StepContext from "~/lib/context";

export default function ChatPanel() {
  const step = useContext(StepContext);
  const stepOutputs = useAtomValue(stepOutputsAtom);
  const chatText = stepOutputs[step];

  return (
    <Conversation className="relative w-full h-full">
      <ConversationContent>
        {chatText && (
          <Message from="assistant">
            <MessageContent>test</MessageContent>
          </Message>
        )}
      </ConversationContent>
      <ConversationScrollButton />
    </Conversation>
  );
}
