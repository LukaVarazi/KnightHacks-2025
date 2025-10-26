import { atom } from "jotai";
export const filesAtom = atom<File[]>([]);
export const neededFilesAtom = atom<Record<string, boolean>>({
  "kill your self": true,
  NOW: false,
  ඞ: false,
});
export const needsNewFileAtom = atom((get) => {
  const needed = get(neededFilesAtom);
  return Object.values(needed).every((b) => b);
});
export const stepAtom = atom(1);

export const stepOutputsAtom = atom<string[]>(["", "", "", ""]);
export const loadingDataAtom = atom(false);

export const reportPartsAtom = atom<string[]>(["A", "B", "C", "D", "E"]);
export const reportDataAtom = atom<Record<string, any>>({});
export const reportStatusAtom = atom("");
export const reportProstom = atom("");
export const reportConsAtom = atom("");
export const reportPercentAtom = atom("")
export const reportPercentExplanationAtom = atom("")

export const currentTabAtom = atom<string>("emt");
