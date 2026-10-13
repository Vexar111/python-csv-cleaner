import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import export_profiles as app


class ProfileExportTests(unittest.TestCase):
    def test_fixture_round_trip_null_unicode_comma_and_newline(self):
        record = app.demo_record()
        record["profile"]["bio"] = "Hello, café\nsecond line"
        with tempfile.TemporaryDirectory() as parent:
            out = Path(parent) / "result"
            report = app.write_exports([record], out, "fictional-offline-demo")
            data = json.loads((out / "profiles.json").read_text())
            with (out / "profiles.csv").open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(report["repository_count"], 2)
            self.assertIsNone(data["profiles"][0]["profile"]["location"])
            self.assertEqual(rows[0]["location"], "")
            self.assertEqual(rows[0]["bio"], "Hello, café\nsecond line")
            self.assertFalse(data["activity_included"])

    def test_pagination_collects_all_pages_and_deduplicates_ids(self):
        calls = []

        def fetch(path):
            calls.append(path)
            if "/repos?" not in path:
                return {"login": "Example", "email": "excluded@example.com"}, {}
            if parse_qs(urlsplit(path).query)["page"] == ["1"]:
                return [{"id": 1, "name": "first"}], {"Link": '<unused>; rel="next"'}
            return [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}], {}

        result = app.collect_profile("Example", fetch=fetch)
        self.assertEqual([r["name"] for r in result["repositories"]], ["first", "second"])
        self.assertEqual(len(calls), 3)
        self.assertNotIn("email", result["profile"])
        self.assertTrue(result["repositories_complete"])

    def test_page_limit_marks_partial_output(self):
        def fetch(path):
            if "/repos?" not in path:
                return {"login": "example"}, {}
            return [{"id": 1, "name": "one"}], {"link": '<unused>; rel="next"'}
        result = app.collect_profile("example", fetch=fetch, max_pages=1)
        self.assertFalse(result["repositories_complete"])
        self.assertEqual(result["repository_pages_fetched"], 1)

    def test_empty_account_still_exports_csv_headers(self):
        def fetch(path):
            return ([], {}) if "/repos?" in path else ({"login": "empty"}, {})
        result = app.collect_profile("empty", fetch=fetch)
        with tempfile.TemporaryDirectory() as parent:
            out = Path(parent) / "empty"
            report = app.write_exports([result], out, "test")
            with (out / "repositories.csv").open(encoding="utf-8-sig") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows, [list(app.REPO_FIELDS)])
            self.assertEqual(report["repository_count"], 0)

    def test_bad_input_rejected_before_network(self):
        with patch.object(app, "urlopen") as network:
            for value in ["../x", "a/b", "a--b", "", "-abc", "abc-", "x" * 40, "a@b.com"]:
                with self.subTest(value=value), self.assertRaises(app.ExportError):
                    app.collect_profile(value)
            network.assert_not_called()

    def test_formula_like_text_hardened_in_csv_and_unchanged_in_json(self):
        record = app.demo_record()
        record["profile"]["bio"] = "  =1+1"
        with tempfile.TemporaryDirectory() as parent:
            out = Path(parent) / "result"
            app.write_exports([record], out, "test")
            with (out / "profiles.csv").open(encoding="utf-8-sig", newline="") as handle:
                bio = list(csv.DictReader(handle))[0]["bio"]
            data = json.loads((out / "profiles.json").read_text())
            self.assertEqual(bio, "'  =1+1")
            self.assertEqual(data["profiles"][0]["profile"]["bio"], "  =1+1")

    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as parent:
            marker = Path(parent) / "profiles.csv"
            marker.write_text("keep me")
            with self.assertRaises(FileExistsError):
                app.write_exports([app.demo_record()], Path(parent), "test")
            self.assertEqual(marker.read_text(), "keep me")

    def test_http_errors_stop_without_retries(self):
        for code in (403, 404, 429, 500):
            with self.subTest(code=code):
                error = HTTPError("https://api.github.com/users/example", code, "failure", {}, None)
                with patch.object(app, "urlopen", side_effect=error) as network:
                    with self.assertRaisesRegex(app.ExportError, str(code)):
                        app.fetch_json("/users/example")
                    network.assert_called_once()

    def test_network_errors_are_actionable(self):
        with patch.object(app, "urlopen", side_effect=URLError("offline")):
            with self.assertRaisesRegex(app.ExportError, "internet connection"):
                app.fetch_json("/users/example")

    def test_request_has_timeout_version_and_no_authentication(self):
        response = io.BytesIO(b'{"login": "example"}')
        response.headers = {}
        with patch.object(app, "urlopen", return_value=response) as network:
            data, _ = app.fetch_json("/users/example")
            request = network.call_args.args[0]
            headers = {key.lower(): value for key, value in request.header_items()}
            self.assertEqual(request.full_url, "https://api.github.com/users/example")
            self.assertEqual(network.call_args.kwargs["timeout"], 20)
            self.assertEqual(headers["x-github-api-version"], "2026-03-10")
            self.assertNotIn("authorization", headers)
            self.assertEqual(data["login"], "example")

    def test_malformed_json_rejected(self):
        response = io.BytesIO(b'<html>server error</html>')
        response.headers = {}
        with patch.object(app, "urlopen", return_value=response):
            with self.assertRaisesRegex(app.ExportError, "JSON response"):
                app.fetch_json("/users/example")

    def test_unexpected_api_shapes_rejected(self):
        with self.assertRaises(app.ExportError):
            app.collect_profile("example", fetch=lambda _: ([], {}))

        def fetch(path):
            return ({"login": "example"}, {}) if "/repos?" not in path else ([{"name": "no-id"}], {})
        with self.assertRaises(app.ExportError):
            app.collect_profile("example", fetch=fetch)

    def test_demo_cli_never_uses_network(self):
        with tempfile.TemporaryDirectory() as parent, patch.object(app, "urlopen") as network:
            out = Path(parent) / "cli"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = app.main(["--demo", "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertEqual(len(list(out.glob("*"))), 3)
            network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
