# SAMAI website

Single-page site for SAMAI, the Student Applied Math & AI Reading Group.
Everything lives in `index.html` — there is no build step, no dependencies, no framework.

## Adding a paper

Edit `papers.json` only — never `index.html`. Add an object anywhere in the array;
entries are sorted by date automatically.

```json
{
  "date": "2026-08-03",
  "presenter": "Name",
  "title": "Paper title",
  "authors": "Lastname et al., 2025",
  "url": "https://arxiv.org/abs/...",
  "summary": "https://optional-blogpost...",
  "upcoming": true
}
```

Only `date`, `presenter` and `title` are required. `upcoming: true` puts the entry
in the "Next" table instead of "Papers presented" — drop that field once the session
has happened. Commit and push; the site updates in about a minute.

## Deploying to GitHub Pages

The site is hosted as a **user/organization page**, which is what gives the
`NAME.github.io` URL:

Pick an organization name (`appliedmathai` below) and use it in both places.

1. Create a GitHub **organization** named `appliedmathai` (+ → New organization; the
   free plan is fine). An organization rather than a personal account means other
   students can be given push access without sharing a login, and the site outlives
   whoever set it up.
2. In that org, create a repository named **exactly** `appliedmathai.github.io`,
   **public**, with no README/gitignore (this repo already has them).
3. Push this directory to it:

   ```
   git init
   git add .
   git commit -m "Initial site"
   git branch -M main
   git remote add origin git@github.com:appliedmathai/appliedmathai.github.io.git
   git push -u origin main
   ```

4. Repo → Settings → Pages → Source: "Deploy from a branch", branch `main`, folder
   `/ (root)`. Save.

The site goes live at **https://appliedmathai.github.io** within a minute or two.
The repo name *must* match the org name exactly, otherwise you get a project page at
`appliedmathai.github.io/reponame` instead. The repo must be public — Pages from a
private repo needs a paid plan.

## Before going live

- Replace `discord.gg/REPLACE-ME` in `index.html` with the real invite link. Use a **non-expiring**
  invite (Discord → invite → Edit invite link → Expire after: Never, Max uses: No limit),
  otherwise the link on the site dies after 7 days.
