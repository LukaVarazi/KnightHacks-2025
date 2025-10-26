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
EMT PRESENCE:
data not provided

POLICE REPORT:
The accident was reported to the police, as indicated by the presence of a "POLICE REPORT (1).pdf". The police report is explicitly mentioned. Who was determined at fault is not stated.

INJURY ASSESSMENT:
data not provided

COVERAGE:
The client has auto insurance coverage with Progressive American Insurance Company and GEICO. Progressive's contact person is Manuel Martinez (Phone: 1-407-949-3712, 1-800-PROGRESSIVE, Fax: 1-407-618-8805). GEICO's adjuster is Dennis Tamisin. A policy number is not explicitly provided. The request for a PIP log indicates Personal Injury Protection coverage.

LOCATION:
The accident occurred in Jacksonville, FL, on April 13, 2019. The specific time of the accident and the precise address or intersection are not provided.

DEFENDANT INFORMATION:
data not provided

RECOMMENDATION: INSUFFICIENT DATA
Subject: Request for Missing Information - Case Regarding April 13, 2019 Incident

Dear Client,

We are currently reviewing the documentation provided for your case related to the incident on April 13, 2019. To ensure a thorough and complete assessment, we require some additional information.

The following details are currently missing from the provided records:

*   **EMT Presence**: Information regarding how you arrived at the hospital (e.g., by ambulance or personal vehicle) and whether EMT personnel were present at the scene.
*   **Injury Assessment**: Specifics about your injuries, including any scans performed (MRI, X-ray, CT, brain scan), the type of injury, if you lost consciousness, your pain level (0-10), when your treatment began, and details about any surgeries, broken bones, or additional medical findings.
*   **Defendant Information**: The name and any available contact information for the defendant, or their relationship to you.

Please provide these details at your earliest convenience. This information is crucial for the proper evaluation and advancement of your claim.

Thank you for your prompt attention to this matter.

Sincerely,

Morgan and Morgan Legal Team

`,
  "",
  "",
  "",
]);
export const loadingDataAtom = atom(false);

export const reportPartsAtom = atom<string[]>(["A", "B", "C", "D", "E"]);
