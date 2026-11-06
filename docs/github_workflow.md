# Our GitHub Workflow

## The basic idea
- **`main`** is the official version of our project on GitHub.
- Nobody works directly on `main`.
- For every task, you make a **branch** (your own copy), work there, and then ask to add it to `main` with a **Pull Request (PR)**.

**This is always the same, whether you write new code, fix something or change something.**

---

## One-time setup
1. Accept the GitHub invitation (check your email).
2. In VS Code: `Ctrl+Shift+P` → `Git: Clone` → paste `https://github.com/NeilErtl/DSF_Project.git` → **Open**.

---

## Every task: 8 steps

**1. Get the latest version**
Bottom-left must say **main** → Source Control (`Ctrl+Shift+G`) → **Sync Changes**.

**2. Create a branch**
Click **main** (bottom-left) → **Create new branch** → give it a short name, e.g. `baseline-model`.

**3. Work**
Write or change your code. Save with `Ctrl+S`.
For notebooks: run *Restart → Run All* first to check that everything works.

**4. Stage**
Source Control → click **+** next to your file.

**5. Commit**
Write a short message (e.g. `Add baseline model`) → click **Commit**.

**6. Push**
Click **Publish Branch** (later: **Sync Changes**).

**7. Pull Request**
On GitHub → **Compare & pull request** → write what you did → choose a teammate as **Reviewer** → **Create pull request**.

**8. After the merge**
In VS Code switch back to **main** → **Sync Changes**. Done!

---

## Reviewing a teammate's PR
1. On GitHub → **Pull requests** → open it → **Files changed**.
2. Check: Does it make sense? Could I explain it?
3. All good → **Merge pull request** → **Delete branch**.
4. Something wrong → leave a comment. The author fixes it on the same branch and pushes again.

---

## Folder structure
Based on the course template (`files/example_project_structure`):

```
DSF_Project/
├── README.md            ← what the project is + how to run it
├── requirements.txt     ← Python packages we use
├── .gitignore           ← files Git should ignore (e.g. big data)
├── code/
│   ├── main.ipynb           ← runs all notebooks in order
│   ├── 01_preprocess.ipynb  ← clean the raw data
│   ├── 02_estimate.ipynb    ← train models, make predictions
│   └── 03_evaluate.ipynb    ← metrics, tables, plots
├── data/
│   ├── raw/             ← original data (never change it!)
│   └── processed/       ← cleaned data (created by the code)
├── output/
│   ├── figures/         ← plots
│   └── tables/          ← results tables
└── docs/                ← guides and notes (like this file)
```

Each notebook **reads files and saves files**. So we can split the work:
person A writes `01_preprocess` → saves clean data → person B uses it in `02_estimate`, and so on.

---

## Where to see our progress
**On GitHub** (github.com/NeilErtl/DSF_Project):

| Tab | What you see |
|---|---|
| **Code** | All folders and files on `main` + the README |
| **Issues** | Our to-do list: who does what |
| **Pull requests** | Work that is waiting for review |
| **Projects** | Board with *To do / In progress / Done* |
| **Commits** (clock icon on the Code tab) | History of all changes |
| **Insights → Network** | Picture of all branches and merges |

**In Nuvolos (VS Code):**
- **Explorer** (`Ctrl+Shift+E`): our folders and files
- **Source Control** (`Ctrl+Shift+G`): what you changed + graph of the history
- **Bottom-left corner**: which branch you are on

---

## Rules
1. **Never work directly on `main`.**
2. **Always sync before you create a branch.**
3. **One notebook = one person.** Never edit the same notebook at the same time.
4. **Big data files don't go on GitHub.** Share them via OneDrive instead.
5. **No passwords in the code.**
6. **Write down when you use AI.** We need it for the report.

---

## Help!
| Problem | Solution |
|---|---|
| I worked on `main` by mistake (not committed yet) | Just create a branch now. Your changes come with you. |
| Push doesn't work | Click **Sync Changes**. |
| Merge conflict | Don't panic. Ask the group and solve it together. |
| Not sure what's going on | Check the branch name in the bottom-left corner. |
