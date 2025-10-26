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

export const stepOutputsAtom = atom<string[]>([
  `
Output for Stage 1 - Insufficient Data Case:

EMT PRESENCE: Client arrived at the hospital by ambulance. EMT was present at the scene.

POLICE REPORT: The accident was reported to police, and a police report is implied to exist, though not fully provided to the client. The other driver was determined at fault.

INJURY ASSESSMENT: No scans were performed (MRI, X-ray, CT, brain scan) based on the provided data. The type of injury is whiplash, resulting from an auto accident, and back pain was also mentioned. The client did not lose consciousness. The pain level (0-10) is data not provided. Treatment began the same day as the accident. No surgeries, broken bones, or additional findings are mentioned.

COVERAGE: The client has auto insurance coverage through Geico, policy number 4589-GH33.

LOCATION: The accident occurred last Friday around 4 PM near NW 27th Ave, Miami.

DEFENDANT INFORMATION: data not provided

RECOMMENDATION: INSUFFICIENT DATA Subject: Follow-up Required: Missing Information for Your Case

Dear Client,

Thank you for providing the initial details regarding your car accident. We have begun organizing the information, and to ensure we can proceed effectively, we require some additional details.

The following information is currently missing from your case file:

Injury Assessment: We need to know your pain level on a scale of 0-10, whether any scans were performed (MRI, X-ray, CT, brain scan), if you lost consciousness, or if there were any surgeries, broken bones, or additional findings from your medical examination.
Defendant Information: We need the name and contact information of the other driver involved in the accident, or their relationship to you.
Location: While you mentioned "last Friday," providing the exact date of the accident would be helpful.
Please provide these details at your earliest convenience. This will allow us to complete the initial assessment and move forward with your case.

Thank you for your cooperation.

Sincerely,

Your Legal Team

`,
  "",
  "",
  "",
]);
export const loadingDataAtom = atom(false);

export const reportPartsAtom = atom<string[]>(["A", "B", "C", "D", "E"]);
