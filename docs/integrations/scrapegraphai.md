# ScrapeGraphAI integration probe

This is an **opt-in, manually triggered connectivity test**. It does not run as part of normal CI, scientific validation, or release workflows.

## Configure the GitHub secret

1. Open the repository's **Settings → Secrets and variables → Actions**.
2. Create a repository secret named `SGAI_API_KEY`.
3. Paste the API key into GitHub's secret field. Do not commit it to a file, issue, PR comment, or workflow log.

The secret cannot be created by this workflow; a repository administrator must add it through GitHub's protected settings UI.

## Run the test

1. Open **Actions → ScrapeGraphAI API Probe → Run workflow**.
2. First run with `run_scrape = false`. This checks authentication and account credit metadata only.
3. If that succeeds and you approve possible credit use, run again with `run_scrape = true` to request Markdown for one CPVS reference page.
4. Inspect the `scrapegraphai-probe-output` artifact. It is retained for seven days.

The workflow uses the official v2 API base URL by default. You may override it with a repository/environment variable named `SGAI_API_URL` only if needed.

## Scope and safety

- The key is read from the Actions secret and is never printed or written to artifacts.
- The first run does not scrape a page and should not consume scrape credits.
- The optional scrape can consume credits depending on the account plan.
- The output is evidence about API connectivity and extraction only. It is **not** scientific validation and must not alter CPVS selection thresholds, model artifacts, or the immutable v0.2.0 / released v1.0.1 baselines.
