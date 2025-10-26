import { Navbar01 } from "#/ui/shadcn-io/navbar-01";
import AddData from "./AddData";
import LoadingOverlay from "./LoadingOverlay";

export default function Main() {
  return (
    <main className="bg-background flex flex-col items-center gap-5 size-full">
      <Navbar01 />

      <div className="flex flex-col items-center justify-center grow w-full p-10">
        <AddData />
      </div>

      <LoadingOverlay />
    </main>
  );
}
