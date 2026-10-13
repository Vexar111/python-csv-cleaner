"""Export selected public GitHub profile/repository fields. Python standard library only."""

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
# Pydroid: leave empty to run the fictional offline demo, or enter public usernames.
LIVE_USERNAMES = []  # Example: ["Vexar111"]
PROFILE_FIELDS = ("login", "name", "bio", "location", "followers", "following",
                  "public_repos", "html_url")
REPO_FIELDS = ("profile_login", "name", "description", "stargazers_count",
               "forks_count", "language", "html_url")
USERNAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\Z")


class ExportError(Exception):
    """An expected input, network, or response problem."""


def validate_username(value):
    if not isinstance(value, str) or not USERNAME.fullmatch(value) or "--" in value:
        raise ExportError("Use a GitHub username, not a URL, email, or path.")
    return value


def fetch_json(path):
    """One anonymous request; no retries, credentials, private data, or HTML scraping."""
    request = Request(
        "https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": "Python-Public-Profile-Exporter/1.0",
                 "X-GitHub-Api-Version": "2026-03-10"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response), dict(response.headers.items())
    except HTTPError as error:
        if error.code == 404:
            message = "GitHub could not find that public account/resource (404)."
        elif error.code in (403, 429):
            message = ("GitHub refused the request or applied a rate limit "
                       f"({error.code}). Stop and try later; do not bypass the limit.")
        else:
            message = f"GitHub returned HTTP {error.code}; no export was written."
        raise ExportError(message) from error
    except (URLError, TimeoutError, OSError) as error:
        raise ExportError("Could not reach GitHub. Check your internet connection.") from error
    except (ValueError, UnicodeError) as error:
        raise ExportError("GitHub returned an unreadable JSON response.") from error


def has_next_page(headers):
    link = next((value for key, value in headers.items() if key.lower() == "link"), "")
    return bool(re.search(r';\s*rel="next"', link))


def collect_profile(username, fetch=fetch_json, max_pages=5):
    username = validate_username(username)
    if not isinstance(max_pages, int) or isinstance(max_pages, bool) or not 1 <= max_pages <= 20:
        raise ExportError("max_pages must be an integer from 1 to 20.")
    raw, _ = fetch(f"/users/{username}")
    if not isinstance(raw, dict) or not isinstance(raw.get("login"), str):
        raise ExportError("Unexpected profile response; no export was written.")
    profile = {field: raw.get(field) for field in PROFILE_FIELDS}
    repositories = []
    seen = set()
    more = False
    for page in range(1, max_pages + 1):
        rows, headers = fetch(
            f"/users/{username}/repos?type=owner&sort=full_name&direction=asc&per_page=100&page={page}"
        )
        if not isinstance(rows, list) or any(
            not isinstance(row, dict) or not isinstance(row.get("id"), int)
            or not isinstance(row.get("name"), str) for row in rows
        ):
            raise ExportError("Unexpected repository response; no export was written.")
        for row in rows:
            # A changing live account can repeat a repository across pages.
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            selected = {field: row.get(field) for field in REPO_FIELDS[1:]}
            selected["profile_login"] = profile["login"]
            repositories.append(selected)
        more = has_next_page(headers)
        if not more:
            break
    return {"profile": profile, "repositories": repositories,
            "repository_pages_fetched": page, "repositories_complete": not more}


def csv_cell(value):
    """Reduce spreadsheet formula interpretation; JSON retains original text."""
    if value is None:
        return ""
    if isinstance(value, str) and (
        value.lstrip().startswith(("=", "+", "-", "@"))
        or value.startswith(("\t", "\r", "\n"))
    ):
        return "'" + value
    return value


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_cell(row.get(field)) for field in fields})


def write_exports(records, output_dir, mode):
    output_dir = Path(output_dir)
    # Refuse to overwrite a previous run or an input directory.
    output_dir.mkdir(parents=True, exist_ok=False)
    report = {
        "schema_version": 1,
        "mode": mode,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile_count": len(records),
        "repository_count": sum(len(item["repositories"]) for item in records),
        "all_repository_pages_fetched": all(item["repositories_complete"] for item in records),
        "activity_included": False,
        "profiles": records,
    }
    with (output_dir / "profiles.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    write_csv(output_dir / "profiles.csv", PROFILE_FIELDS,
              (item["profile"] for item in records))
    write_csv(output_dir / "repositories.csv", REPO_FIELDS,
              (row for item in records for row in item["repositories"]))
    return report


def demo_record():
    fixture = json.loads((BASE_DIR / "sample_api.json").read_text(encoding="utf-8"))

    def offline_fetch(path):
        if "/repos?" in path:
            return fixture["repositories"], {}
        return fixture["profile"], {}

    return collect_profile("portfolio-demo", fetch=offline_fetch)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--user", action="append", help="Public username; repeat for several profiles.")
    group.add_argument("--demo", action="store_true", help="Use fictional offline sample data.")
    parser.add_argument("--out", type=Path, help="A NEW directory for CSV and JSON outputs.")
    parser.add_argument("--max-pages", type=int, default=5, help="1-20 repository pages per user (default 5).")
    args = parser.parse_args(argv)
    usernames = [] if args.demo else (args.user if args.user is not None else LIVE_USERNAMES)
    mode = "live-public-api" if usernames else "fictional-offline-demo"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_dir = args.out or BASE_DIR / "runs" / stamp
    try:
        if not 1 <= args.max_pages <= 20:
            raise ExportError("--max-pages must be between 1 and 20.")
        unique_users = list(dict.fromkeys(validate_username(name).lower() for name in usernames))
        if output_dir.exists():
            raise ExportError("Output directory already exists; choose a new --out directory.")
        records = ([collect_profile(name, max_pages=args.max_pages) for name in unique_users]
                   if unique_users else [demo_record()])
        report = write_exports(records, output_dir, mode)
    except (ExportError, OSError, ValueError) as error:
        print(f"Export failed: {error}", file=sys.stderr)
        return 1
    print(f"Mode: {mode}")
    print(f"Exported {report['profile_count']} profile(s), {report['repository_count']} repositories to {output_dir}")
    if not report["all_repository_pages_fetched"]:
        print("WARNING: repository page limit reached. Output is partial; inspect profiles.json.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
