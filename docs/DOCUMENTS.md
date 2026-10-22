# Documents, presentations and ASD-STE100 from the chat

Every answer in the chat can be saved as a document. Below an answer, click **Save as PowerPoint**, **Word**, **PDF**,
**Excel** or **More…** (HTML, Markdown, text, Jupyter notebook, JSON, CSV).

## The Save dialog

1. **Format**: the buttons at the top. The line under them says what that format gets.
2. **Title** and **Author**: the title comes from the first `#` heading. The author is remembered.
3. **Template**: colours, fonts, page size, header and footer. The colour squares show the template.
4. **Text**: the Markdown that is saved. Change it here before saving; **Reset** brings back the answer.
   **+ slide break** inserts `---`; **+ notes** adds speaker notes for the slide at the cursor.
5. **Slides** shows the slides PowerPoint will get. **ASD-STE100 check** shows the findings.
6. **Save as …**: choose where. Diagrams are drawn first and put in as pictures.

## How the text becomes slides

| In the text | In PowerPoint |
|---|---|
| The first `# Title` and the line under it | The title slide (title, subtitle, author and date) |
| Each `## Heading` (or a `---` line) | A new slide with that title |
| `- bullets`, nested with two spaces | Bullets and sub-bullets (PowerPoint text, editable) |
| `1. steps` | PowerPoint numbering |
| A table | A PowerPoint table (12 rows per slide; more rows continue) |
| A ```` ```mermaid ```` or ```` ```svg ```` block | The diagram as a picture |
| A code block | A code box (leave it out with "include code blocks") |
| A paragraph that starts with `Notes:` | The speaker notes of the slide |
| `> WARNING: …` | A notice (bold, no bullet) |

More than seven bullets continue on a "(continued)" slide. Choose **a new slide only at ---** to decide every break.

Every slide uses the deck's own layouts (Title, Title and Content, Section, Title Only). In PowerPoint, edit any text,
add slides with **New Slide**, or change the look of all slides with **Design → Themes** or **View → Slide Master**.

## Templates

Built in: **Swarm Lab**, **Corporate**, **Minimal**, **Dark**, **Forest** and **ASD-STE100 technical**.

**New…** copies the selected template into `.swarmlab/templates/documents/<name>.json` and opens it. **Edit template…**
opens your template (a built-in one is copied first). Example:

```json
{
  "id": "acme",
  "name": "ACME",
  "extends": "corporate",
  "colors": { "primary": "7A0019", "accent": "FFCC33", "tableHeader": "7A0019" },
  "fonts": { "heading": "Georgia", "body": "Calibri" },
  "page": "Letter",
  "slides": "16:9",
  "header": "{title}",
  "footer": "ACME internal · {date}",
  "numberedHeadings": false,
  "wordTemplate": "templates/acme-letterhead.dotx"
}
```

- Colours are hex without `#`: `primary`, `accent`, `text`, `muted`, `background`, `titleBackground`, `titleText`,
  `tableHeader`, `tableHeaderText`, `codeBackground`. Fields you leave out come from `extends`.
- `header` and `footer` accept `{title}`, `{author}` and `{date}`.
- `wordTemplate` (or the **Word file…** button): a `.docx` or `.dotx` in the project. Word exports keep its styles,
  theme, headers, footers and page setup; styles it does not have (Code, Notice…) are added.
- A template with a problem (a wrong colour, bad JSON) is listed under the dialog and skipped.

## ASD-STE100 Simplified Technical English

- `/ste procedure <task>`, `/ste description <subject>`, `/ste report <subject>`: the assistant writes in STE.
- `/ste rewrite <text>`: the same meaning, rewritten in STE.
- `/stecheck`: checks the last answer and lists the findings.
- The template **ASD-STE100 technical** numbers the headings, uses Arial and saves `<name>.ste-check.md` next to the
  document.

The check finds sentences that are too long (20 words in procedures, 25 in descriptions), paragraphs of more than six
sentences, passive voice, -ing forms, two instructions in one sentence, common unapproved words and phrasal verbs
(with the STE word to use), and warnings that do not start with a command. It does not know the meanings in the STE
dictionary: a trained writer makes the final check against the ASD-STE100 specification.

## Reports, presentations and analyses

- `/report <topic>`: executive summary, sections, tables, a diagram where useful, risks, recommendations, sources.
- `/slides <topic>` (or `/presentation`, `/deck`): 8 to 14 slides with speaker notes.
- `/analysis <topic>`: question, data and method, findings with evidence, options compared, recommendation, risks.

Then **Save as** under the answer. **Export this chat…** (Chat tab, or *Swarm Lab: Export chat*) saves the whole
conversation in any format.

## Limits

- PDF uses the standard PDF fonts: Western European characters. Other scripts (Greek, Cyrillic, Chinese…) become `?`;
  save as Word or HTML for those.
- A diagram that Mermaid cannot draw is saved as its code.
- Excel gets the tables as data; charts are not created.
