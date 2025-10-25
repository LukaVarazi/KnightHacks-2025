import {
  IconFileMusic,
  IconFileMusicFilled,
  IconMicrophone2,
  IconPdf,
} from "@tabler/icons-react";
import { filesAtom } from "~/lib/atom";
import {
  Dropzone,
  DropzoneContent,
  DropzoneEmptyState,
} from "./ui/shadcn-io/dropzone";
import { useAtom, useAtomValue, useSetAtom } from "jotai";
import { Button } from "./ui/button";
import { UploadIcon } from "lucide-react";
import { Separator } from "./ui/separator";
import Continue from "./Continue";

export default function FileUpload() {
  const [files, setFiles] = useAtom(filesAtom);

  const handleDrop = (files: File[]) => {
    console.log(files);
    setFiles((prev) => [...prev, ...files]);
  };

  return (
    <div className="flex flex-col items-center overflow-x-auto size-full">
      <Dropzone
        maxFiles={100_000}
        onDrop={handleDrop}
        onError={console.error}
        src={files}
        className="overflow-x-auto h-full w-full rounded-none border-none"
        // disabled={files.length !== 0}
        disabled={false}
      >
        <DropzoneEmptyState />
        <DropzoneContent>
          {files.length !== 0 && <FilesPreview />}
        </DropzoneContent>
      </Dropzone>
    </div>
  );
}

function FilesPreview() {
  const files = useAtomValue(filesAtom);

  if (files.length === 0) return null;

  return (
    <div className="flex flex-col gap-5 h-full w-full">
      <h1 className="text-2xl">Tender 🍗 files to analyze</h1>

      <Separator className="" orientation="horizontal" />

      {files.map((file, i) => (
        <FilePreview key={i} i={i} file={file} />
      ))}

      <div className="mt-auto">
        <Continue />

        <Separator />

        <div className="flex flex-col items-center justify-center mt-5">
          <div className="flex size-32 items-center justify-center rounded-md bg-muted text-muted-foreground">
            <UploadIcon size={64} className="size-16" />
          </div>
          <p className="my-2 w-full truncate font-medium text-md"></p>
          <p className="w-full text-wrap text-muted-foreground text-2xl">
            Drag and drop / click to add more files for analysis
          </p>
        </div>
      </div>
    </div>
  );
}

function FilePreview({ file, i }: { file: File; i: number }) {
  const setFiles = useSetAtom(filesAtom);
  const deleteFile = () => {
    setFiles((prev) => [...prev.slice(0, i), ...prev.slice(i + 1)]);
  };

  return (
    <div className="flex h-8 items-center gap-2 w-full">
      <FileIcon file={file} />

      <span className="text-md overflow-x-auto">{file.name}</span>

      <Button
        variant="destructive"
        className="ml-auto"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          deleteFile();
        }}
      >
        Remove
      </Button>
    </div>
  );
}

function FileIcon({ file }: { file: File }) {
  const extension = getFileExtension(file)?.toLowerCase();
  if (!extension) return null;

  if (extension === "pdf") {
    return <IconPdf size={32} className="text-destructive size-8" />;
  }
  if (extension === "m4a") {
    return <IconFileMusicFilled size={32} className="text-green-300 size-8" />;
  }

  return null;
}

function getFileExtension(file: File) {
  // 1. Get the file name string
  const fileName = file.name;

  // 2. Find the index of the last '.' in the file name
  const lastDotIndex = fileName.lastIndexOf(".");

  // 3. Check if a dot was found and if it's not the very last character (i.e., not a folder name like "...")
  if (lastDotIndex !== -1 && lastDotIndex < fileName.length - 1) {
    // 4. Return the substring starting *after* the last dot, and convert to lowercase for consistency
    return fileName.substring(lastDotIndex + 1).toLowerCase();
  } else {
    // 5. Return null or an empty string if no valid extension is found
    return null;
  }
}
