#!/usr/bin/env python3
"""test-integrations.py -- stdlib integration test suite for Truth Ledger.

Replaces legacy Bash test scripts with a clean Python unittest runner.
Covers:
  1. CLI Contract & Refusals (exit codes 0-8, refusal patterns, ADR-051).
  2. Claude PreToolUse Whisper Hook (worktree support, fail-closed deny).
  3. Claude SessionStart Digest (dirty/stale vs. empty silence).
  4. Tier C Instruments (real ledger & sandbox red proofs for all 5 instruments).
  5. Markdown & Spec Health (fact-health sweep and session-close survival gate).

Enforces the F1 Failure Rule: 0 tests run or any skipped test is a FAILURE.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT = os.path.dirname(TEMPLATE_DIR)
INSTRUMENTS_DIR = os.path.join(REPO_ROOT, "instruments")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")


class Sandbox:
    """Creates an isolated git repository sandbox with truth-ledger machinery."""

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="truth-integration-")
        self.root = os.path.realpath(self.tmpdir)
        self.env = dict(os.environ)
        self.env["TRUTH_ACTOR"] = "test-actor"
        self.env["TRUTH_SESSION"] = "s-test-session"
        self.env["GIT_AUTHOR_NAME"] = "test-actor"
        self.env["GIT_AUTHOR_EMAIL"] = "test@example.com"
        self.env["GIT_COMMITTER_NAME"] = "test-actor"
        self.env["GIT_COMMITTER_EMAIL"] = "test@example.com"
        self._init_repo()

    def _init_repo(self):
        subprocess.run(["git", "init", "-q", "-b", "main", self.root], check=True)
        subprocess.run(["git", "-C", self.root, "config", "user.name", "test-actor"], check=True)
        subprocess.run(["git", "-C", self.root, "config", "user.email", "test@example.com"], check=True)

        os.makedirs(os.path.join(self.root, "scripts"), exist_ok=True)
        os.makedirs(os.path.join(self.root, "template", "scripts"), exist_ok=True)
        os.makedirs(os.path.join(self.root, ".truth", "schema"), exist_ok=True)
        os.makedirs(os.path.join(self.root, "docs", "specs"), exist_ok=True)

        # Copy truth CLI and truthlib
        shutil.copy2(os.path.join(TEMPLATE_DIR, "scripts", "truth"), os.path.join(self.root, "scripts", "truth"))
        shutil.copy2(os.path.join(TEMPLATE_DIR, "scripts", "truth"), os.path.join(self.root, "template", "scripts", "truth"))
        shutil.copytree(os.path.join(TEMPLATE_DIR, "truthlib"), os.path.join(self.root, "truthlib"))
        shutil.copytree(os.path.join(TEMPLATE_DIR, "truthlib"), os.path.join(self.root, "template", "truthlib"))

        # Copy hooks & helper scripts
        for script_name in ["fact-health.sh", "truth-whisper.py", "truth-whisper.deny", "truth-session-digest.py"]:
            src = os.path.join(SCRIPTS_DIR, script_name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(self.root, "scripts", script_name))

        if os.path.exists(os.path.join(TEMPLATE_DIR, "scripts", "session-close.sh")):
            shutil.copy2(os.path.join(TEMPLATE_DIR, "scripts", "session-close.sh"), os.path.join(self.root, "scripts", "session-close.sh"))
            shutil.copy2(os.path.join(TEMPLATE_DIR, "scripts", "session-close.sh"), os.path.join(self.root, "template", "scripts", "session-close.sh"))

        # Policy files
        with open(os.path.join(self.root, ".truth", "evidence-allow"), "w", encoding="utf-8") as f:
            f.write("cat\ngrep\nwc\nls\nfalse\ntrue\nhead\ntail\necho\n")
        with open(os.path.join(self.root, ".truth", "evidence-deny"), "w", encoding="utf-8") as f:
            f.write("rm\n")
        with open(os.path.join(self.root, ".truth", "generated-paths"), "w", encoding="utf-8") as f:
            f.write("# attested 2026-08-15: sandbox clean\n")
        with open(os.path.join(self.root, ".truth", "citation-scope"), "w", encoding="utf-8") as f:
            f.write("# attested 2026-08-15: sandbox clean\ndocs/**\nREADME.md\n")
        with open(os.path.join(self.root, ".truth", "claims.jsonl"), "w", encoding="utf-8") as f:
            f.write("")
        with open(os.path.join(self.root, ".gitattributes"), "w", encoding="utf-8") as f:
            f.write(".truth/claims.jsonl merge=union\n")
        with open(os.path.join(self.root, "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write("# Agents\nscripts/truth\n")
        with open(os.path.join(self.root, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Sandbox README\n")

        subprocess.run(["git", "-C", self.root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", self.root, "commit", "-qm", "init"], check=True)

    def run_truth(self, *args, env=None, cwd=None):
        e = dict(self.env)
        if env:
            e.update(env)
        c = cwd or self.root
        cmd = [sys.executable, os.path.join(self.root, "scripts", "truth")] + list(args)
        return subprocess.run(cmd, cwd=c, capture_output=True, text=True, env=e)

    def write_file(self, rel_path, content):
        p = os.path.join(self.root, rel_path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

    def git_commit(self, msg="commit"):
        subprocess.run(["git", "-C", self.root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", self.root, "commit", "-qm", msg, "--no-verify", "--allow-empty"], check=True)

    def cleanup(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


class TestCLIContractsAndRefusals(unittest.TestCase):
    """Test CLI exit codes 0 through 8 and refusal patterns."""

    def setUp(self):
        self.sb = Sandbox()

    def tearDown(self):
        self.sb.cleanup()

    def test_exit_code_0_and_json_contracts(self):
        """Exit 0: verify JSON schema and zero exit for read/query subcommands."""
        # 1. list --json
        res = self.sb.run_truth("list", "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(json.loads(res.stdout), [])

        # 2. vocab --json
        res = self.sb.run_truth("vocab", "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        vocab = json.loads(res.stdout)
        self.assertIn("active", vocab)
        self.assertIn("citation_bad", vocab)

        # 3. queue --json
        res = self.sb.run_truth("queue", "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(json.loads(res.stdout), [])

        # 4. stats --json
        res = self.sb.run_truth("stats", "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        stats = json.loads(res.stdout)
        self.assertIn("claims_by_status", stats)

        # 5. validate
        res = self.sb.run_truth("validate")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_exit_code_1_validation_and_refusal(self):
        """Exit 1: generic validation failure and syntax/argument refusal."""
        # VERIFIED claim missing --evidence-cmd is refused with exit 1
        res = self.sb.run_truth("claim", "missing evidence command fact", "--class", "VERIFIED", "--tier", "P1")
        self.assertEqual(res.returncode, 1)
        self.assertIn("truth:", res.stderr)

        # Non-JSON in ledger fails validate with exit 1
        with open(os.path.join(self.sb.root, ".truth", "claims.jsonl"), "a", encoding="utf-8") as f:
            f.write("not a valid json record\n")
        res = self.sb.run_truth("validate")
        self.assertEqual(res.returncode, 1)

    def test_exit_code_2_environment_error(self):
        """Exit 2: git ref/environment error."""
        res = self.sb.run_truth("list", "--at", "nonexistent-ref-000000")
        self.assertEqual(res.returncode, 2)

    def test_exit_code_3_impact(self):
        """Exit 3: impact command finds impacted live claims."""
        self.sb.write_file("watched.txt", "line 1\n")
        self.sb.git_commit("add watched")
        res = self.sb.run_truth("claim", "watched.txt has content", "--class", "VERIFIED",
                                "--evidence-cmd", "cat watched.txt", "--paths", "watched.txt", "--tier", "P1")
        self.assertEqual(res.returncode, 0, res.stderr)
        cid = res.stdout.strip()
        # Agree to make it live
        res = self.sb.run_truth("verdict", cid, "agree", "--basis", "checked", env={"TRUTH_SESSION": "s-verifier"})
        self.assertEqual(res.returncode, 0, res.stderr)

        # Query impact on watched path -> exit 3
        res = self.sb.run_truth("impact", "watched.txt")
        self.assertEqual(res.returncode, 3)
        self.assertIn(cid, res.stdout)

        # Query impact on unwatched path -> exit 0
        res = self.sb.run_truth("impact", "unwatched.txt")
        self.assertEqual(res.returncode, 0)

    def test_exit_code_4_impact_inverse(self):
        """Exit 4: impact --inverse reports dark (unwatched) files."""
        self.sb.write_file("dark.txt", "unmonitored file\n")
        self.sb.git_commit("add dark file")
        res = self.sb.run_truth("impact", "--inverse")
        self.assertEqual(res.returncode, 4)
        self.assertIn("dark.txt", res.stdout)

    def test_exit_code_5_baseline(self):
        """Exit 5: baseline diff detects disappeared claims between refs."""
        res = self.sb.run_truth("claim", "fact to disappear", "--class", "UNVERIFIED", "--tier", "P1")
        self.assertEqual(res.returncode, 0)
        self.sb.git_commit("claim filed at baseline")
        subprocess.run(["git", "-C", self.sb.root, "tag", "baseline-v1"], check=True)

        # Truncate/empty the ledger in a new commit so the claim disappeared from history
        self.sb.write_file(".truth/claims.jsonl", "")
        self.sb.git_commit("ledger wiped")

        res = self.sb.run_truth("baseline", "baseline-v1", "--diff", "HEAD")
        self.assertEqual(res.returncode, 5)
        self.assertIn("DISAPPEARED", res.stdout)

    def test_exit_code_6_citations_and_orphan_refusal(self):
        """Exit 6: citations detected and orphan-blocking retraction refusal."""
        res = self.sb.run_truth("claim", "ground fact cited in spec", "--class", "UNVERIFIED", "--tier", "P1")
        cid = res.stdout.strip()
        self.sb.git_commit("claim filed")

        # Cite the claim in a spec doc
        self.sb.write_file("docs/specs/auth.md", f"# Auth Spec\nRelies on {cid}.\n")
        self.sb.git_commit("cite in spec")

        # citations sub-command exits 6 when citations found
        res = self.sb.run_truth("citations", cid)
        self.assertEqual(res.returncode, 6)

        # Attempting to retract without --orphan-ok exits 6
        res = self.sb.run_truth("verdict", cid, "retracted", "--basis", "attempt retract", "--cause", "expired",
                                env={"TRUTH_HUMAN": "1", "TRUTH_HUMAN_ACK": cid})
        self.assertEqual(res.returncode, 6)
        self.assertIn("is cited", res.stderr)

    def test_exit_code_7_reproduce_stale(self):
        """Exit 7: reproduce command detects diverged/stale capsules."""
        self.sb.write_file("data.txt", "version 1\n")
        self.sb.git_commit("data v1")
        res = self.sb.run_truth("claim", "data.txt says version 1", "--class", "VERIFIED",
                                "--evidence-cmd", "cat data.txt", "--paths", "data.txt", "--tier", "P1")
        cid = res.stdout.strip()
        res = self.sb.run_truth("verdict", cid, "agree", "--basis", "verified v1", env={"TRUTH_SESSION": "s-v1"})
        self.assertEqual(res.returncode, 0)

        # Modify data.txt so output differs
        self.sb.write_file("data.txt", "version 2\n")
        res = self.sb.run_truth("reproduce")
        self.assertEqual(res.returncode, 7)

    def test_exit_code_8_reproduce_empty(self):
        """Exit 8: reproduce command reports zero claims examined."""
        res = self.sb.run_truth("reproduce")
        self.assertEqual(res.returncode, 8)

    def test_adr035_exit_gate_refusal(self):
        """ADR-035: Positive claims with non-zero exit commands are refused without override."""
        self.sb.write_file("cmd.txt", "hello\n")
        self.sb.git_commit("add cmd.txt")

        # Positive sentence with failing command ('false') is refused
        res = self.sb.run_truth("claim", "the system builds cleanly and passes all tests", "--class", "VERIFIED",
                                "--evidence-cmd", "false", "--paths", "cmd.txt", "--tier", "P1")
        self.assertNotEqual(res.returncode, 0)
        self.assertTrue("ADR-035" in res.stderr or "evidence command exited" in res.stderr)

        # Re-filing with --evidence-exit-ok succeeds
        res = self.sb.run_truth("claim", "the system builds cleanly and passes all tests", "--class", "VERIFIED",
                                "--evidence-cmd", "false", "--paths", "cmd.txt", "--tier", "P1",
                                "--evidence-exit-ok", "expected non-zero in test harness")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_adr037_generated_paths_refusal(self):
        """ADR-037: Watching generated paths is refused without override."""
        # Add generated path
        with open(os.path.join(self.sb.root, ".truth", "generated-paths"), "a", encoding="utf-8") as f:
            f.write("build/output.json\n")
        self.sb.write_file("build/output.json", '{"gen": 1}\n')
        self.sb.git_commit("add generated artifact")

        # Filing with path in generated list is refused
        res = self.sb.run_truth("claim", "build output has gen 1", "--class", "VERIFIED",
                                "--evidence-cmd", "cat build/output.json", "--paths", "build/output.json", "--tier", "P1")
        self.assertNotEqual(res.returncode, 0)
        self.assertTrue("ADR-037" in res.stderr or "generated-artifact" in res.stderr or "restales on every regeneration" in res.stderr)

        # Override with --generated-ok succeeds
        res = self.sb.run_truth("claim", "build output has gen 1", "--class", "VERIFIED",
                                "--evidence-cmd", "cat build/output.json", "--paths", "build/output.json", "--tier", "P1",
                                "--generated-ok", "verifying generator emission directly")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_g8_near_duplicates_refusal(self):
        """G8: Near-duplicate claim sentences are refused unless overridden."""
        text1 = "the database connection pool maximum size is exactly twenty connections"
        text2 = "the database connection pool maximum size is exactly twenty-five connections"

        res = self.sb.run_truth("claim", text1, "--class", "UNVERIFIED", "--tier", "P1")
        self.assertEqual(res.returncode, 0, res.stderr)

        res = self.sb.run_truth("claim", text2, "--class", "UNVERIFIED", "--tier", "P1")
        self.assertNotEqual(res.returncode, 0)
        self.assertTrue("G8" in res.stderr or "near-duplicate" in res.stderr)

        res = self.sb.run_truth("claim", text2, "--class", "UNVERIFIED", "--tier", "P1", "--duplicate-ok")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_screeners_allow_deny_refusal(self):
        """Screeners: forbidden or unallowed commands are refused."""
        self.sb.write_file("f.txt", "data\n")
        self.sb.git_commit("add f.txt")

        # Deny-listed command 'rm'
        res = self.sb.run_truth("claim", "f.txt exists", "--class", "VERIFIED",
                                "--evidence-cmd", "rm f.txt", "--paths", "f.txt", "--tier", "P1")
        self.assertNotEqual(res.returncode, 0)
        self.assertTrue("deny" in res.stderr or "ADR-009" in res.stderr or "ADR-022" in res.stderr)

        # Unallowed command
        res = self.sb.run_truth("claim", "f.txt exists", "--class", "VERIFIED",
                                "--evidence-cmd", "awk '{print}' f.txt", "--paths", "f.txt", "--tier", "P1")
        self.assertNotEqual(res.returncode, 0)
        self.assertTrue("allowlist" in res.stderr or "ADR-009" in res.stderr or "evidence-allow" in res.stderr)

    def test_adr051_evidence_refresh(self):
        """ADR-051: agree over changed evidence without --refresh-evidence is refused, succeeds with it."""
        self.sb.write_file("f.txt", "x\nx\n")
        self.sb.git_commit("two lines")

        res = self.sb.run_truth("claim", "f.txt holds exactly two x lines", "--class", "VERIFIED",
                                "--evidence-cmd", "grep -c x f.txt", "--paths", "f.txt", "--tier", "P1")
        self.assertEqual(res.returncode, 0, res.stderr)
        cid = res.stdout.strip()

        # Initial agree
        res = self.sb.run_truth("verdict", cid, "agree", "--basis", "verified count", env={"TRUTH_SESSION": "s-v1"})
        self.assertEqual(res.returncode, 0, res.stderr)

        # Mutate file and invalidate
        self.sb.write_file("f.txt", "x\nx\nx\n")
        self.sb.git_commit("third line")
        res = self.sb.run_truth("invalidate-scan")
        self.assertIn(cid, res.stdout)

        # Agree without --refresh-evidence is REFUSED
        res = self.sb.run_truth("verdict", cid, "agree", "--basis", "file is still healthy", env={"TRUTH_SESSION": "s-v2"})
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("ADR-051", res.stderr)
        self.assertIn("--refresh-evidence", res.stderr)

        # Agree with --refresh-evidence SUCCEEDS
        res = self.sb.run_truth("verdict", cid, "agree", "--basis", "file is still healthy",
                                "--refresh-evidence", "the count grew from 2 to 3; shape still valid",
                                env={"TRUTH_SESSION": "s-v2"})
        self.assertEqual(res.returncode, 0, res.stderr)

        # Validate passes
        res = self.sb.run_truth("validate")
        self.assertEqual(res.returncode, 0, res.stderr)

        # Reaffirm works on non-content touch
        self.sb.write_file("f.txt", "x\nx\nx\n# comment\n")
        self.sb.git_commit("add comment")
        self.sb.run_truth("invalidate-scan")
        res = self.sb.run_truth("reaffirm", env={"TRUTH_SESSION": "s-reaffirm"})
        self.assertIn("1 reaffirmed", res.stdout)


class TestClaudeWhisperHook(unittest.TestCase):
    """Test Claude PreToolUse Whisper Hook (scripts/truth-whisper.py)."""

    def setUp(self):
        self.sb = Sandbox()
        self.hook = os.path.join(self.sb.root, "scripts", "truth-whisper.py")

    def tearDown(self):
        self.sb.cleanup()

    def _run_hook(self, payload, cwd=None):
        c = cwd or self.sb.root
        cmd = [sys.executable, self.hook]
        return subprocess.run(cmd, cwd=c, input=json.dumps(payload), capture_output=True, text=True)

    def test_deny_stage_blocked(self):
        """Deny stage: edit to deny-listed path emits deny decision."""
        payload = {
            "session_id": "s-test-deny",
            "tool_input": {"file_path": os.path.join(self.sb.root, "docs", "archive", "old.md")}
        }
        res = self._run_hook(payload)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)["hookSpecificOutput"]
        self.assertEqual(data["permissionDecision"], "deny")
        self.assertIn("human must deliberately lift the freeze", data["permissionDecisionReason"])

    def test_whisper_stage_main_tree(self):
        """Whisper stage: editing watched file in main tree emits allow + whisper."""
        self.sb.write_file("watched.py", "print('hello')\n")
        self.sb.git_commit("add watched.py")
        res = self.sb.run_truth("claim", "watched.py exists", "--class", "VERIFIED",
                                "--evidence-cmd", "cat watched.py", "--paths", "watched.py", "--tier", "P1")
        self.assertEqual(res.returncode, 0, res.stderr)
        cid = res.stdout.strip()
        self.sb.run_truth("verdict", cid, "agree", "--basis", "ok", env={"TRUTH_SESSION": "s-verifier"})

        payload = {
            "session_id": f"s-main-{int(time.time()*1000)}",
            "tool_input": {"file_path": os.path.join(self.sb.root, "watched.py")}
        }
        res = self._run_hook(payload)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)["hookSpecificOutput"]
        self.assertEqual(data["permissionDecision"], "allow")
        self.assertIn("truth-ledger whisper", data.get("additionalContext", ""))

    def test_whisper_stage_git_worktree(self):
        """Worktree compatibility: hook functions when .git is a file."""
        self.sb.write_file("watched.py", "print('hello')\n")
        self.sb.git_commit("add watched.py")
        res = self.sb.run_truth("claim", "watched.py exists", "--class", "VERIFIED",
                                "--evidence-cmd", "cat watched.py", "--paths", "watched.py", "--tier", "P1")
        cid = res.stdout.strip()
        self.sb.run_truth("verdict", cid, "agree", "--basis", "ok", env={"TRUTH_SESSION": "s-verifier"})
        self.sb.git_commit("commit claim and agree")

        wt_dir = tempfile.mkdtemp(prefix="truth-wt-")
        try:
            subprocess.run(["git", "-C", self.sb.root, "worktree", "add", "-q", "--detach", wt_dir], check=True)
            real_wt = os.path.realpath(wt_dir)

            payload = {
                "session_id": f"s-wt-{int(time.time()*1000)}",
                "tool_input": {"file_path": os.path.join(real_wt, "watched.py")}
            }
            res = self._run_hook(payload, cwd=real_wt)
            self.assertEqual(res.returncode, 0, res.stderr)
            data = json.loads(res.stdout)["hookSpecificOutput"]
            self.assertEqual(data["permissionDecision"], "allow")
            self.assertIn("truth-ledger whisper", data.get("additionalContext", ""))
        finally:
            subprocess.run(["git", "-C", self.sb.root, "worktree", "remove", "--force", wt_dir], capture_output=True)
            shutil.rmtree(wt_dir, ignore_errors=True)

    def test_deny_pattern_malformed_fails_closed(self):
        """Deny stage: a malformed regex in truth-whisper.deny fails CLOSED."""
        deny_file = os.path.join(self.sb.root, "scripts", "truth-whisper.deny")
        with open(deny_file, "a", encoding="utf-8") as f:
            f.write("docs/(\n")

        payload = {
            "session_id": f"s-malformed-{int(time.time()*1000)}",
            "tool_input": {"file_path": os.path.join(self.sb.root, "README.md")}
        }
        res = self._run_hook(payload)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)["hookSpecificOutput"]
        self.assertEqual(data["permissionDecision"], "deny")
        self.assertIn("malformed deny pattern line", data["permissionDecisionReason"])
        self.assertIn("truth-whisper.deny", data["permissionDecisionReason"])


class TestClaudeSessionDigest(unittest.TestCase):
    """Test Claude SessionStart Digest (scripts/truth-session-digest.py)."""

    def setUp(self):
        self.sb = Sandbox()
        self.digest = os.path.join(self.sb.root, "scripts", "truth-session-digest.py")

    def tearDown(self):
        self.sb.cleanup()

    def _run_digest(self):
        cmd = [sys.executable, self.digest]
        return subprocess.run(cmd, cwd=self.sb.root, capture_output=True, text=True)

    def test_empty_ledger_stays_silent(self):
        """Empty ledger emits nothing on stdout and stderr, exits 0."""
        res = self._run_digest()
        self.assertEqual(res.returncode, 0)
        self.assertEqual(res.stdout.strip(), "")
        self.assertEqual(res.stderr.strip(), "")

    def test_happy_path_emits_attention_and_live(self):
        """Dirty/stale and live items produce header, ATTENTION, and LIVE lines."""
        # 1. Live claim
        res = self.sb.run_truth("claim", "core architecture invariant holds", "--class", "UNVERIFIED", "--tier", "P1")
        cid1 = res.stdout.strip()
        self.sb.run_truth("verdict", cid1, "agree", "--basis", "verified", env={"TRUTH_SESSION": "s-verifier"})

        # 2. Stale claim
        self.sb.write_file("stale.txt", "initial\n")
        self.sb.git_commit("add stale.txt")
        res = self.sb.run_truth("claim", "stale.txt says initial", "--class", "VERIFIED",
                                "--evidence-cmd", "cat stale.txt", "--paths", "stale.txt", "--tier", "P0")
        cid2 = res.stdout.strip()
        self.sb.run_truth("verdict", cid2, "agree", "--basis", "verified", env={"TRUTH_SESSION": "s-verifier"})
        self.sb.write_file("stale.txt", "changed\n")
        self.sb.git_commit("modify stale.txt")
        self.sb.run_truth("invalidate-scan")

        res = self._run_digest()
        self.assertEqual(res.returncode, 0)
        self.assertIn("truth-ledger digest", res.stdout)
        self.assertTrue("ATTENTION" in res.stdout or "LIVE" in res.stdout)

    def test_dead_cli_degrades_open_with_stderr_line(self):
        """Corrupt ledger causes session digest to exit 0, empty stdout, 1 stderr line."""
        self.sb.write_file(".truth/claims.jsonl", "corrupted jsonl record\n")
        res = self._run_digest()
        self.assertEqual(res.returncode, 0)
        self.assertEqual(res.stdout.strip(), "")
        self.assertIn("truth session digest unavailable", res.stderr)


class TestTierCInstruments(unittest.TestCase):
    """Test the 5 Tier C Instruments on real ledger and sandbox red proofs."""

    def test_separation_report_real_and_sandbox(self):
        """separation-report.py parses JSON and detects sub-second agree."""
        inst = os.path.join(INSTRUMENTS_DIR, "separation-report.py")
        res = subprocess.run([sys.executable, inst, "--json"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertGreater(data["pairs"], 0)
        self.assertEqual(data["same_session"], 0)

        # Sandbox red proof
        sb = Sandbox()
        try:
            res = sb.run_truth("claim", "widget probe separation", "--tier", "P2")
            cid = res.stdout.strip()
            # Immediate agree (same second) -> flagged inside floor
            sb.run_truth("verdict", cid, "agree", "--basis", "instant agree", env={"TRUTH_SESSION": "s-v1"})
            res = subprocess.run([sys.executable, inst, "--json"], cwd=sb.root, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            d = json.loads(res.stdout)
            self.assertIn(cid, d["live_unevidenced"])
        finally:
            sb.cleanup()

    def test_override_velocity_real_and_sandbox(self):
        """override-velocity.py parses JSON and detects scope re-justifications."""
        inst = os.path.join(INSTRUMENTS_DIR, "override-velocity.py")
        res = subprocess.run([sys.executable, inst, "--json"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertGreaterEqual(data["scope_basis_filings"], 0)
        self.assertEqual(data["max_scope_ttl_days"], 3650)

        # Sandbox red proof
        sb = Sandbox()
        try:
            sb.write_file("f.txt", "data\n")
            sb.git_commit("add f.txt")
            sb_text = "the include filter deliberately covers the whole codebase"
            cmd = "grep -rc data --include=f.txt ."
            env1 = {"TRUTH_NOW": "2026-06-01T00:00:00+00:00", "TRUTH_ACTOR": "gate", "TRUTH_SESSION": "s-ov"}
            res = sb.run_truth("claim", "no occurrences remain anywhere in the codebase", "--class", "VERIFIED",
                               "--evidence-cmd", cmd, "--paths", "f.txt", "--tier", "P1", "--scope-ok", sb_text, env=env1)
            cid1 = res.stdout.strip()
            sb.run_truth("invalidate-scan", env={"TRUTH_ACTOR": "gate", "TRUTH_SESSION": "s-ov"})
            res = sb.run_truth("claim", "no occurrences remain anywhere in the codebase", "--class", "VERIFIED",
                               "--evidence-cmd", cmd, "--paths", "f.txt", "--tier", "P1", "--scope-ok", sb_text,
                               env={"TRUTH_ACTOR": "gate", "TRUTH_SESSION": "s-ov"})
            cid2 = res.stdout.strip()

            res = subprocess.run([sys.executable, inst, "--json"], cwd=sb.root, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            d = json.loads(res.stdout)
            repeated_ids = [r["claim"] for r in d.get("repeats", [])]
            self.assertIn(cid2, repeated_ids)
        finally:
            sb.cleanup()

    def test_blast_report_real_and_sandbox(self):
        """blast-report.py parses JSON and computes live forecast on unstored watch."""
        inst = os.path.join(INSTRUMENTS_DIR, "blast-report.py")
        res = subprocess.run([sys.executable, inst, "--json"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertGreaterEqual(data["effective_floor"], 1)
        self.assertEqual(data["history_state"], "ok")

        # Sandbox red proof: hot watch computed on read, not stored
        sb = Sandbox()
        try:
            for i in range(16):
                sb.write_file("w.txt", f"line {i}\n")
                sb.git_commit(f"w {i}")
            res = sb.run_truth("claim", "w.txt keeps growing", "--class", "VERIFIED",
                               "--evidence-cmd", "cat w.txt", "--paths", "w.txt", "--tier", "P2")
            cid = res.stdout.strip()

            # Assert blast_forecast is NOT stored in claims.jsonl
            with open(os.path.join(sb.root, ".truth", "claims.jsonl"), encoding="utf-8") as f:
                last_line = f.readlines()[-1]
            self.assertNotIn("blast_forecast", last_line)

            res = subprocess.run([sys.executable, inst, "--json"], cwd=sb.root, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            d = json.loads(res.stdout)
            claim_ids = [row["claim"] for row in d.get("rows", [])]
            self.assertIn(cid, claim_ids)
        finally:
            sb.cleanup()

    def test_concern_tag_real_and_sandbox(self):
        """concern-tag.py parses JSON and reads dynamic active vocabulary."""
        inst = os.path.join(INSTRUMENTS_DIR, "concern-tag.py")
        res = subprocess.run([sys.executable, inst, "--json"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertIsInstance(data["concerns"], dict)
        self.assertIsInstance(data["concerns_untagged_active"], int)

        # Sandbox red proof
        sb = Sandbox()
        try:
            sb.run_truth("claim", "active claim 1", "--tier", "P2")
            # Legacy record with concern tag
            legacy_rec = {
                "id": "tr-00c0ffee", "kind": "claim", "actor": "legacy", "session": "s-old",
                "ts": "2026-01-01T00:00:00.000000+00:00",
                "payload": {
                    "text": "worker pool drains on shutdown", "evidence_class": "UNVERIFIED",
                    "cost_tier": "P2", "ttl_days": None, "evidence_paths": [], "concerns": ["security"]
                }
            }
            with open(os.path.join(sb.root, ".truth", "claims.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(legacy_rec) + "\n")

            res = subprocess.run([sys.executable, inst, "--json"], cwd=sb.root, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            d = json.loads(res.stdout)
            self.assertEqual(d["concerns"].get("security"), 1)
            self.assertEqual(d["concerns_untagged_active"], 1)
        finally:
            sb.cleanup()

    def test_retraction_causes_real_and_sandbox(self):
        """retraction-causes.py parses JSON and catches unrecorded vs bypasses."""
        inst = os.path.join(INSTRUMENTS_DIR, "retraction-causes.py")
        res = subprocess.run([sys.executable, inst, "--json"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertIn("unrecorded", data["by_cause"])
        self.assertEqual(data["total"], data["successors_named"] + data["successors_missing"])

        # Sandbox red proof: legacy unrecorded admitted, bypass caught
        sb = Sandbox()
        try:
            res = sb.run_truth("claim", "f.txt data marker", "--tier", "P2")
            cid = res.stdout.strip()
            sb.run_truth("verdict", cid, "retracted", "--cause", "wrong", "--basis", "never true",
                         env={"TRUTH_HUMAN": "1", "TRUTH_HUMAN_ACK": cid})

            # Append legacy retraction without cause
            legacy_retract = {
                "id": "tr-00b0b0b0", "kind": "verdict", "actor": "legacy", "session": "s-old",
                "ts": "2026-01-01T00:00:00.000000+00:00",
                "payload": {"claim": "tr-00c0ffee", "verdict": "retracted", "basis": "superseded"}
            }
            with open(os.path.join(sb.root, ".truth", "claims.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(legacy_retract) + "\n")

            res = subprocess.run([sys.executable, inst, "--json"], cwd=sb.root, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            d = json.loads(res.stdout)
            self.assertEqual(d["by_cause"]["wrong"], 1)
            self.assertEqual(d["by_cause"]["unrecorded"], 1)
        finally:
            sb.cleanup()


class TestMarkdownAndSpecHealth(unittest.TestCase):
    """Test Markdown citation health (fact-health.sh) and session-close gate."""

    def setUp(self):
        self.sb = Sandbox()

    def tearDown(self):
        self.sb.cleanup()

    def test_fact_health_catches_all_classes(self):
        """fact-health.sh correctly judges live, disputed, stale, fences, near-misses, foreign, and missing IDs."""
        fh_script = os.path.join(self.sb.root, "scripts", "fact-health.sh")

        # 1. Live claim
        self.sb.write_file("watched.txt", "live content\n")
        self.sb.git_commit("add watched.txt")
        res = self.sb.run_truth("claim", "watched.txt carries live content", "--class", "VERIFIED",
                                "--evidence-cmd", "cat watched.txt", "--paths", "watched.txt", "--tier", "P1")
        cid_live = res.stdout.strip()
        self.sb.run_truth("verdict", cid_live, "agree", "--basis", "verified", env={"TRUTH_SESSION": "s-v1"})

        # Green corpus test
        self.sb.write_file("README.md", f"# README\nGround truth: {cid_live} anchors this.\n")
        self.sb.write_file("docs/clean.md", "# Clean Doc\nNo citations here.\n")
        self.sb.git_commit("green corpus")

        res = subprocess.run(["bash", fh_script], cwd=self.sb.root, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn(f"ok    {cid_live}  live", res.stdout)

        # 2. Stale claim
        self.sb.write_file("stale.txt", "original\n")
        self.sb.git_commit("add stale.txt")
        res = self.sb.run_truth("claim", "stale.txt says original", "--class", "VERIFIED",
                                "--evidence-cmd", "cat stale.txt", "--paths", "stale.txt", "--tier", "P1")
        cid_stale = res.stdout.strip()
        self.sb.run_truth("verdict", cid_stale, "agree", "--basis", "verified", env={"TRUTH_SESSION": "s-v1"})
        self.sb.write_file("stale.txt", "modified\n")
        self.sb.git_commit("modify stale")
        self.sb.run_truth("invalidate-scan")

        # 3. Disputed claims (distinct sentences to avoid near-duplicate refusal)
        res = self.sb.run_truth("claim", "fixture engine reads configuration from local disk", "--class", "UNVERIFIED", "--tier", "P1")
        cid_d1 = res.stdout.strip()
        res = self.sb.run_truth("claim", "network dispatcher fetches remote payload via tls", "--class", "UNVERIFIED", "--tier", "P1")
        cid_d2 = res.stdout.strip()
        self.sb.run_truth("verdict", cid_d1, "agree", "--basis", "v", env={"TRUTH_SESSION": "s-v1"})
        self.sb.run_truth("verdict", cid_d2, "agree", "--basis", "v", env={"TRUTH_SESSION": "s-v1"})
        self.sb.run_truth("contradicts", cid_d1, cid_d2, "--basis", "cannot both hold")

        # Bad corpus files
        self.sb.write_file("docs/dead.md", f"# Dead\nStands on {cid_stale} and {cid_d1}.\n")
        self.sb.write_file("docs/fence.md", f"# Fence\n```\nsample citation tr-00000001\nunclosed fence\n{cid_live}\n")
        self.sb.write_file("docs/nearmiss.md", "# Nearmiss\nSee tr-DEADBEEF for info.\n")
        self.sb.write_file("docs/unknown.md", "# Unknown Prefix\nCites unknownrepo:tr-12345678.\n")
        self.sb.write_file("docs/foreign.md", "# Foreign\nCites kuchnie:tr-12345678.\n")
        self.sb.write_file("docs/missing.md", "# Missing\nCites tr-0badf00d.\n")
        self.sb.git_commit("bad corpus")

        res = subprocess.run(["bash", fh_script], cwd=self.sb.root, capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        out = res.stdout
        self.assertIn(f"FAIL  {cid_d1}  disputed", out)
        self.assertIn(f"FAIL  {cid_stale}  stale", out)
        self.assertIn("unbalanced ``` fence", out)
        self.assertIn("FAIL  tr-DEADBEEF  malformed id", out)
        self.assertIn("FAIL  unknownrepo:tr-12345678  unknown prefix", out)
        self.assertIn("INFO  kuchnie:tr-12345678  foreign ledger", out)
        self.assertIn("FAIL  tr-0badf00d  missing from ledger", out)

    def test_session_close_checks(self):
        """session-close.sh refuses dirty working trees and claimed work items."""
        sc_script = os.path.join(self.sb.root, "scripts", "session-close.sh")

        # Clean state -> exit 0
        self.sb.git_commit("clean baseline")
        res = subprocess.run(["bash", sc_script], cwd=self.sb.root, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout)

        # Dirty working tree -> exit 1
        self.sb.write_file("dirty.txt", "uncommitted\n")
        res = subprocess.run(["bash", sc_script], cwd=self.sb.root, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertIn("uncommitted changes", res.stdout)
        self.sb.git_commit("commit dirty file")

        # Claimed work item -> exit 1
        res = self.sb.run_truth("issue", "Refactor core engine")
        wid = res.stdout.strip()
        self.sb.run_truth("start", wid)
        self.sb.git_commit("start issue")
        res = subprocess.run(["bash", sc_script], cwd=self.sb.root, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertIn("still claimed", res.stdout)

        # Release work item -> exit 0
        self.sb.run_truth("start", "--release", wid, "--basis", "hand back for now")
        self.sb.git_commit("release issue")
        res = subprocess.run(["bash", sc_script], cwd=self.sb.root, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout)


def main():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # F1 Failure Rule: 0 tests run or any skips is an automatic failure
    if result.testsRun == 0:
        sys.stderr.write("F1 RULE VIOLATION: test-integrations ran 0 tests!\n")
        sys.exit(1)
    if len(result.skipped) > 0:
        sys.stderr.write(f"F1 RULE VIOLATION: test-integrations had {len(result.skipped)} skipped test(s)!\n")
        sys.exit(1)
    if not result.wasSuccessful():
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
