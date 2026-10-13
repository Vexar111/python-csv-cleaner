# Public GitHub Profile Exporter — portfolio demo

A small Python command-line tool that turns selected **public GitHub profile and repository metadata** into CSV and JSON. It uses GitHub's documented REST API and Python's standard library. No paid API, password, browser automation, or extra pip packages are required.

This is a **portfolio demonstration, not paid client work**. Included sample records are fictional. Live use needs internet access and must respect GitHub's terms and API limits.

## What it exports

- Profile: username, public name/bio/location, follower/following counts, public repository count, profile URL.
- Owned public repositories: name, description, stars, forks, primary language, URL.
- Three files: `profiles.csv`, `repositories.csv`, and `profiles.json` with collection time, counts, mode, and completeness flags.

Handles multiple supplied usernames, paginated repositories, empty accounts, missing optional values, HTTP errors, and timeouts. Duplicate repository IDs across pages are removed. It stops on access/rate-limit errors instead of retrying repeatedly. An explicit page cap marks partial exports rather than claiming they are complete.

## Try it on Pydroid 3

1. Download and extract this repository.
2. Open `github_profile_exporter/export_profiles.py` in Pydroid 3 with `sample_api.json` alongside it.
3. Tap Run. With the default settings, it uses the **fictional offline demo**.
4. Open the newly created folder inside `github_profile_exporter/runs/` to see the outputs.

For a live public profile, change `LIVE_USERNAMES = []` near the top of the script to `LIVE_USERNAMES = ["Vexar111"]` and run again. Do not put a password or token in that list. Android file permissions and connectivity can affect live runs.

## Command-line examples

Run from this folder:

```sh
python export_profiles.py --demo --out demo-run
python export_profiles.py --user Vexar111 --out vexar-profile
python export_profiles.py --user Vexar111 --user octocat --max-pages 3 --out two-profiles
python -m unittest discover -s . -p 'test_*.py' -v
```

Each `--out` must be a **new directory**. Existing outputs are never overwritten. No username means demo mode unless `LIVE_USERNAMES` has been configured. `--demo` always forces offline mode.

Exit codes: `0` successful export; `1` an input/network/output error; `2` export created but capped before all repository pages were fetched. An invalid command-line syntax also uses argparse's exit code `2`; in that case no export is created.

## Example output

The [example_output](example_output/) folder contains generated results for one fictional profile and two fictional repositories. Empty optional values are `null` in JSON and blank in CSV. CSV uses UTF-8 with a BOM for spreadsheet compatibility.

## Scope and limits

- **No email collection, private information, follower lists, repository source code, or recent activity export.** Recent activity would be a separately scoped extension.
- Anonymous API requests: GitHub documents a limit of **60 requests per hour per originating IP**, with additional limits possible. Each profile uses one profile request plus one request per repository page. No credentials are supported by this demo.
- The default cap is five repository pages per user, with up to 100 items per page. The allowed cap is 1–20 pages. Live account changes between requests mean an export is not a transactional snapshot.
- Formula-like text is prefixed with an apostrophe in CSV to reduce spreadsheet formula interpretation; JSON retains the original text. Treat imported data as text and inspect it before using it in another workflow.
- No email/phone enrichment, large-scale lead harvesting, scheduling, GUI, database, or promised live integration with a client's workflow.
- Processing keeps the selected results in memory. This is designed for a few specified public profiles, not bulk collection.
- An output disk error can leave an incomplete new directory; an error is reported and existing directories are not modified.

## Validation

Validation on 13 October 2026 using Python 3.12.14:

- **13 automated tests passed**, covering pagination, truncation, null/Unicode/multiline CSV values, duplicate IDs, missing accounts, refusal/rate limits, malformed responses, output preservation, and an offline CLI run. These tests use controlled responses and synthetic data.
- A live anonymous API run for `Vexar111` successfully exported one profile and six repositories, with all repository pages fetched. Live output is not committed; only fictional sample output is included in this folder.
- The offline sample successfully generated all three example output files.

**Execution on an Android phone has not yet been verified for this new demo.** Run it in Pydroid 3 and confirm the client's exact fields and scale before promising a delivery deadline. The earlier CSV and Excel projects' phone tests do not establish this script's Android compatibility.

## Official API references

- [Public user profiles](https://docs.github.com/en/rest/users/users#get-a-user)
- [Public repositories for a user](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user)
- [REST API rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [API versions](https://docs.github.com/en/rest/about-the-rest-api/api-versions)

## Honest portfolio description

> Developed a Python portfolio demo that exports selected public GitHub profiles and repository metadata into CSV and JSON. Added pagination, rate-limit handling, input validation, completeness reporting, and automated tests with synthetic fixtures. Live deployment remains subject to a successful integration check and an agreed client scope.
