import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/query";
import { ThemeProvider } from "./components/ThemeProvider";
import Main from "./components/Main";

export default function App() {
  return (
    // Provide the client to your App
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <Main />
      </ThemeProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
