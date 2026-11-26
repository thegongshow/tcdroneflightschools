# Drone School Tracker

Every day, GitHub opens Transport Canada's drone flight school page in a real browser, reads the full table,
saves it to `docs/schools.json`, and shows what's new on a web page. When new schools appear it also opens a GitHub
issue, which GitHub emails you about (and pushes to the GitHub mobile app).

## Setup (about 10 minutes, no coding)
1. Create a free GitHub account if you don't have one, then click **New repository** (name it `drone-school-tracker`, keep it Public so Pages is free).
2. On the new repo, choose **Add file → Upload files** and drag in everything from this folder, including the hidden `.github` folder (unzip first; on a phone, use a computer for this step). Commit.
3. **Settings → Pages**: Source = *Deploy from a branch*, Branch = `main`, Folder = `/docs`. Save.
4. **Actions** tab: if asked, enable workflows. Open **Check drone schools**, click **Run workflow**. Wait about 2 minutes.
5. Your tracker is at `https://YOUR-USERNAME.github.io/drone-school-tracker/`. On your phone, open it and choose **Add to Home Screen**.
6. In the repo, click **Watch → Custom → Issues** so you get notified when new schools show up.

The first run records a baseline, so nothing is flagged as new yet. From the next change on, new schools are flagged.

## If a run fails
GitHub emails you. Open the failed run in **Actions**, download the `debug` file, and send it to whoever helps you with this.
The script refuses to overwrite your data if the table looks empty or suspiciously small.
