/**
 * DorkCraft: common dork patterns
 * -------------------------------
 * The reference list shown beside the search box. Each entry is a pattern with
 * placeholders, not a ready-made search. Keep the list inside what the backend
 * blocklist allows: nothing aimed at credentials, personal data or exploits.
 */

export interface CommonDork {
  /** Short name shown above the explanation. */
  name: string;
  dork: string;
  explanation: string;
}

export const COMMON_DORKS: CommonDork[] = [
  {
    name: 'Documents on one site',
    dork: 'site:example.com filetype:pdf',
    explanation:
      'Every PDF Google has indexed on one domain. Swap pdf for docx, xlsx or pptx to find other document types.',
  },
  {
    name: 'University slides',
    dork: 'site:.edu filetype:pptx "topic"',
    explanation:
      'Lecture slides about a topic, limited to university domains. site:.edu matches any address ending in .edu.',
  },
  {
    name: 'Government pages',
    dork: 'site:.gov intext:"keyword"',
    explanation:
      'Government pages that mention the keyword in the body text, not only in the title or the address.',
  },
  {
    name: 'Words in the title',
    dork: 'allintitle: word1 word2',
    explanation:
      'Pages with all of the words in the title, in any order. Looser than a quoted phrase, so it matches more pages.',
  },
  {
    name: 'LinkedIn profiles',
    dork: 'site:linkedin.com/in "role" "city"',
    explanation:
      'Public LinkedIn profiles that mention a role and a place. The /in part keeps company and job pages out.',
  },
  {
    name: 'GitHub repositories',
    dork: 'site:github.com intitle:"keyword"',
    explanation:
      'GitHub pages with the keyword in the title, which is mostly repositories and their descriptions.',
  },
  {
    name: 'Open directory listings',
    dork: 'intitle:"index of" "parent directory"',
    explanation:
      'Folders a web server shows as a plain file list. Add a keyword after it to narrow down what the folder holds.',
  },
  {
    name: 'Phrase minus a noisy site',
    dork: '"exact phrase" -site:pinterest.com',
    explanation:
      'The phrase exactly as written, with one site removed from the results. Repeat -site: to remove more.',
  },
  {
    name: 'Mentions elsewhere',
    dork: '"company name" -site:company.com',
    explanation:
      'What other sites say about a company, with its own website left out of the results.',
  },
  {
    name: 'Recent pages only',
    dork: '"keyword" after:2025-01-01',
    explanation:
      'Pages Google dates after 1 January 2025. Add before: with a second date to search inside a window.',
  },
];
