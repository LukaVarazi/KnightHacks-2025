import { capitalize, countBy } from "es-toolkit";
import { useAtom, useAtomValue } from "jotai";
import { neededFilesAtom } from "~/lib/atom";
import { Checkbox } from "./ui/checkbox";
import { Label } from "./ui/label";
import { Separator } from "./ui/separator";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "#/ui/table";

export default function MissingFiles() {
  const [neededFiles, setNeededFiles] = useAtom(neededFilesAtom);
  const numMissing = countBy(Object.entries(neededFiles), ([_key, val]) =>
    val ? "true" : "false"
  ).true;

  if (Object.keys(neededFiles).length === 0) return null;

  return (
    <div className="p-4 border bg-background shadow-xs dark:border-input flex flex-col gap-5">
      <h2 className="text-xl font-bold">Files</h2>
      <Separator orientation="horizontal" />
      {/* <div className="flex flex-col gap-5">
        {Object.keys(neededFiles).map((key) => (
          <NeededFile key={key} name={key} />
        ))}
      </div> */}

      <Table>
        <TableCaption>
          A list of the files missing to complete the tender analysis
        </TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">Name</TableHead>
            <TableHead className="self-end text-end">Missing</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Object.keys(neededFiles).map((files) => (
            <TableRow key={files}>
              <TableCell className="font-medium">{files}</TableCell>
              <TableCell className="self-end">
                <div className="flex">
                  <Checkbox
                    className="ml-auto"
                    checked={neededFiles[files]}
                    onCheckedChange={(b) =>
                      setNeededFiles((prev) => ({
                        ...prev,
                        [files]: Boolean(b),
                      }))
                    }
                  />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell colSpan={1}>Missing</TableCell>
            <TableCell className="text-right">{numMissing}</TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    </div>
  );
}

function NeededFile({ name }: { name: string }) {
  const [neededFiles, setNeededFiles] = useAtom(neededFilesAtom);
  const file = neededFiles[name];

  const onCheckedChange = (val: boolean) => {
    setNeededFiles((prev) => ({
      ...prev,
      [name]: val,
    }));
  };

  return (
    <div className="flex justify-between gap-6 items-center">
      <Label className="text-md" htmlFor={name}>
        {capitalize(name)}
      </Label>

      <Checkbox checked={file} onCheckedChange={onCheckedChange} id={name} />
    </div>
  );
}
