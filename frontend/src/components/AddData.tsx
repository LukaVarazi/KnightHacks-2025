import FileUpload from "./FileUpload";
import MissingFiles from "./MissingFiles";

export default function AddData() {
  return (
    <div className="flex gap-5 justify-center size-full">
      <FileUpload />
      <MissingFiles />
    </div>
  );
}
