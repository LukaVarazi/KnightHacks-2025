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

export default function ChatPanel() {
  // const chatText = ;

  return (
    <Conversation className="relative w-full h-full">
      <ConversationContent>
        <Message from="assistant">
          {/* <MessageAvatar /> */}
          <MessageContent>Hi there!</MessageContent>
        </Message>
      </ConversationContent>
      <ConversationScrollButton />
    </Conversation>
  );
}
