#!/usr/bin/env python3
"""test-integrations.py -- stdlib integration test suite for Truth Ledger.

Replaces legacy Bash test scripts with a clean Python unittest runner.
Covers:
  1. CLI Contract & Refusals (exit codes 0-8, refusal patterns, ADR-051).
  2. Claude PreToolUse Whisper Hook (worktree support, fail-closed deny).
  3. Claude SessionStart Digest (dirty/stale vs. empty silence).
  4. Tier C Instruments (real-ledger and throwaway-tree red proofs; WHICH
     instruments is declared in TestTierCInstruments and reconciled against
     instruments/ by test_every_instrument_is_classified -- this line used
     to carry a count, and carried "all 5" for a set of nine).
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

        # Step 2.6: the `reaffirm` tail is gone with the verb. What it
        # proved -- an unchanged capsule needs no new judgment -- is now
        # `truth reproduce`'s job, and it files NOTHING when it holds.
        self.sb.write_file("f.txt", "x\nx\nx\n# comment\n")
        self.sb.git_commit("add comment")
        ledger = os.path.join(self.sb.root, ".truth", "claims.jsonl")
        before = open(ledger, encoding="utf-8").read().count("\n")
        res = self.sb.run_truth("reproduce")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("reproduces", res.stdout)
        self.assertEqual(open(ledger, encoding="utf-8").read().count("\n"), before,
                         "reproduce must file nothing on a green sweep")


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
    """Tier C instruments on the real ledger plus a sandbox red proof.

    Coverage is DECLARED below and checked in both directions, rather
    than described in this docstring. A prose count is the thing this
    repository keeps catching itself getting wrong: the wording here was
    once "all 5 instruments" for a set that had grown to nine, then
    "6 of the 10 scripts" for a directory of eleven. So the two sets are
    data, `test_every_instrument_is_classified` reconciles them against
    the directory, and adding an instrument fails this suite until
    somebody says which set it belongs to. The gap itself is real and
    filed (wk-15dfc164)."""

    # Instruments with an arm in this class.
    COVERED_INSTRUMENTS = frozenset((
        "separation-report.py", "override-velocity.py", "blast-report.py",
        "concern-tag.py", "retraction-causes.py", "semantic-audit.py",
        "register-index.py", "waiver-index.py",
    ))
    # Instruments with no arm here. Listed, not omitted: an unexamined
    # instrument that nobody wrote down is indistinguishable from one
    # nobody noticed.
    UNCOVERED_INSTRUMENTS = frozenset((
        "arm-index.py", "capsule-blindness.py", "field-consumers.py",
        "label-coupling.py", "watch-derivation.py",
        # Appeared 2026-08-25 while this suite was being edited, and this
        # arm refused until it was classified -- which is the arm working.
        # Listed as UNCOVERED rather than judged: naming the gap is the
        # honest state, and whoever knows what it does can move it.
        "map.py",
    ))

    def test_every_instrument_is_classified(self):
        """Neither set may drift from the directory.

        Forward: every name declared above is a file that exists -- a
        stale name reads as coverage of something that is gone. Reverse:
        every *.py in instruments/ appears in exactly one set -- a new
        instrument must be classified, not silently uncovered. This is
        the same both-directions rule register-index.py was rebuilt for,
        applied to this suite's own account of itself.
        """
        on_disk = set(n for n in os.listdir(INSTRUMENTS_DIR)
                      if n.endswith(".py"))
        declared = self.COVERED_INSTRUMENTS | self.UNCOVERED_INSTRUMENTS
        self.assertEqual(
            self.COVERED_INSTRUMENTS & self.UNCOVERED_INSTRUMENTS, set(),
            "an instrument is declared both covered and uncovered")
        self.assertEqual(
            declared - on_disk, set(),
            "declared instrument(s) no longer in instruments/ -- the "
            "declaration outlived its subject")
        self.assertEqual(
            on_disk - declared, set(),
            "instrument(s) in instruments/ classified neither covered nor "
            "uncovered here -- add an arm, or name it in "
            "UNCOVERED_INSTRUMENTS so the gap is on the page")

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
        """override-velocity.py parses JSON and detects scope re-justifications (INV-U).

        Named subject on purpose: this arm is INV-U's only gate since ADR-046
        moved the section out of the template CLI and 32022c6 replaced the
        scaffolding it had moved to. arm-index reconciles both directions.
        """
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
            # Step 2.5: a path invalidation no longer kills anything, and
            # ADR-033's repeat detector keys on the earlier claim being DEAD.
            # A judge's diverge is the ungated route to that (ADR-010: the
            # verdict must not come from the claim's own session).
            sb.run_truth("verdict", cid1, "diverge", "--basis", "the count moved",
                         env={"TRUTH_ACTOR": "gate", "TRUTH_SESSION": "s-judge"})
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
            # Step 3.2: a hot watch is refused unless the breadth is
            # accepted. This instrument test is about blast-report.py
            # computing the forecast ON READ, not about the gate, so the
            # fixture states the basis and moves on.
            res = sb.run_truth("claim", "w.txt keeps growing", "--class", "VERIFIED",
                               "--evidence-cmd", "cat w.txt", "--paths", "w.txt", "--tier", "P2",
                               "--paths-ok", "the claim is about this file growing; the hot watch is its subject")
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

    def test_semantic_audit_extracts_and_never_reaches_the_network(self):
        """semantic-audit.py (ADR-059): the justification sentences of ACTIVE
        claims, PLUS orphan_basis from retracted ones, deterministically,
        with no networking imported."""
        inst = os.path.join(INSTRUMENTS_DIR, "semantic-audit.py")

        # THE HARD CONTRACT FIRST (ADR-059). An extractor that grew a
        # `requests.post` would still pass every behavioural assertion
        # below while shipping this repository's justification text to a
        # third party. Nothing else in the suite would notice, so the pin
        # is structural: the module's source may not name a transport.
        with open(inst, encoding="utf-8") as f:
            source = f.read()
        body = "\n".join(l for l in source.splitlines()
                          if not l.lstrip().startswith("#"))
        code = body.split('"""', 2)[-1]      # drop the module docstring,
        for banned in ("requests", "http.client", "urllib",             # which discusses them
                       "socket", "httpx", "urlopen", "smtplib"):
            # assertTrue, not assertNotIn: the latter dumps the whole
            # module into the failure message and buries the sentence.
            self.assertTrue(banned not in code,
                            f"semantic-audit.py names {banned!r} outside "
                            "its docstring -- ADR-059 forbids network I/O "
                            "in the extractor; the send belongs in CI")

        res = subprocess.run([sys.executable, inst], cwd=REPO_ROOT,
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        rows = json.loads(res.stdout)
        self.assertIsInstance(rows, list)
        for r in rows:
            self.assertEqual(sorted(r), ["basis", "id", "record", "type"])
            self.assertTrue(r["basis"].strip())
        # Deterministic: a CI diff must mean the LEDGER moved.
        again = subprocess.run([sys.executable, inst], cwd=REPO_ROOT,
                               capture_output=True, text=True)
        self.assertEqual(res.stdout, again.stdout)
        # The census is on stderr and names every type, including the
        # ones reading zero -- a dark arm has to be visible.
        self.assertIn("scope_basis=", res.stderr)
        self.assertIn("orphan_basis=", res.stderr)

        # Sandbox red proof: a live claim's scope_basis is extracted, and
        # the SAME sentence disappears once the claim leaves the active
        # set -- the scope decision, made falsifiable.
        sb = Sandbox()
        try:
            sb.write_file("f.txt", "data\n")
            sb.git_commit("add f.txt")
            basis = "the include filter deliberately covers the whole codebase"
            res = sb.run_truth(
                "claim", "no occurrences remain anywhere in the codebase",
                "--class", "VERIFIED", "--evidence-cmd",
                "grep -rc data --include=f.txt .", "--paths", "f.txt",
                "--tier", "P1", "--scope-ok", basis,
                env={"TRUTH_ACTOR": "gate", "TRUTH_SESSION": "s-sa"})
            cid = res.stdout.strip()

            out = subprocess.run([sys.executable, inst], cwd=sb.root,
                                 capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            got = [r for r in json.loads(out.stdout) if r["id"] == cid]
            self.assertEqual(len(got), 1, out.stdout)
            self.assertEqual(got[0]["type"], "scope_basis")
            self.assertEqual(got[0]["basis"], basis)

            sb.run_truth("verdict", cid, "diverge", "--basis", "the count moved",
                         env={"TRUTH_ACTOR": "gate", "TRUTH_SESSION": "s-judge"})
            out = subprocess.run([sys.executable, inst], cwd=sb.root,
                                 capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(
                [r for r in json.loads(out.stdout) if r["id"] == cid], [],
                "a diverged claim's justification is history -- extracting "
                "it spends L2 tokens on a finding nobody can act on")

            # THE ORPHAN BRANCH, which is the one exception and therefore
            # the one most likely to be lost in a later tidy-up. A
            # retraction filed with --orphan-ok defends an ACT, not a
            # fact: the dangling citations are still in the corpus, so the
            # sentence stays auditable after its claim dies. It also
            # cannot be exercised any other way -- validate_events refuses
            # orphan_basis on a non-retracted verdict, so an active-only
            # scope makes this field structurally unreachable.
            res = sb.run_truth("claim", "the widget registry lists four entries",
                               "--tier", "P2",
                               env={"TRUTH_ACTOR": "gate", "TRUTH_SESSION": "s-sa"})
            dead = res.stdout.strip()
            orphan_basis = "the citations are pattern exemplars, not facts anyone stands on"
            res = sb.run_truth("verdict", dead, "retracted", "--basis", "wrong at filing",
                               "--cause", "wrong", "--orphan-ok", orphan_basis,
                               # ADR-011, both halves: the env var alone is
                               # refused headless (canary FAULT H1), so the
                               # sandbox fixture supplies the id-specific ack
                               # exactly as the other suite fixtures do.
                               env={"TRUTH_ACTOR": "gate", "TRUTH_SESSION": "s-judge",
                                    "TRUTH_HUMAN": "1", "TRUTH_HUMAN_ACK": dead})
            self.assertEqual(res.returncode, 0, res.stderr)

            out = subprocess.run([sys.executable, inst], cwd=sb.root,
                                 capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            got = [r for r in json.loads(out.stdout) if r["id"] == dead]
            self.assertEqual([r["type"] for r in got], ["orphan_basis"],
                             "orphan_basis must be extracted from a RETRACTED "
                             "claim, and nothing else may leak in with it")
            self.assertEqual(got[0]["basis"], orphan_basis)
            self.assertIn("orphan_basis=1", out.stderr)

            # ...and the branch is gated on the claim's STATUS, not on the
            # field being present. validate_events refuses orphan_basis on
            # any non-retracted verdict, so the only way this record exists
            # is a raw append -- a forgery, or a hand-edited ledger. It must
            # not reach the audit: `cid` is DIVERGED, and a sentence
            # excusing dangling citations for a claim nobody retracted is
            # an argument about an act that never happened.
            #
            # Pinned because the extractor CLAIMS this protection in a
            # comment, and a guard nothing exercises is a guard that gets
            # tidied away. Seeding it by widening ORPHAN_STATUSES to
            # include "diverged" must turn this red.
            forged = {
                "id": "tr-00fa15e0", "kind": "verdict", "actor": "forger",
                "session": "s-forge",
                "ts": "2026-01-01T00:00:00.000000+00:00",
                "payload": {"claim": cid, "verdict": "diverge",
                            "basis": "raw append",
                            "orphan_basis": "smuggled past intake"},
            }
            with open(os.path.join(sb.root, ".truth", "claims.jsonl"),
                      "a", encoding="utf-8") as f:
                f.write(json.dumps(forged) + "\n")
            out = subprocess.run([sys.executable, inst], cwd=sb.root,
                                 capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertNotIn("smuggled past intake", out.stdout,
                             "an orphan_basis raw-appended onto a NON-retracted "
                             "claim reached the audit -- the branch is keyed on "
                             "the field, not on the claim's status")
            self.assertIn("orphan_basis=1", out.stderr)
        finally:
            sb.cleanup()

    # ---- register-index (ADR-061: this gate is here because it was made
    # to go red for each condition below, not because it compiles) --------

    @staticmethod
    def _mini_register_tree(root, decisions, archived, roadmap, baseline=""):
        """A throwaway repository shaped like the meta-repo's registers.

        register-index resolves its ROOT from its own __file__, so the
        instrument is COPIED in rather than pointed at this tree: running
        the real file against a fake root would silently sweep the real
        repository instead, which is the class of mistake this instrument
        exists to catch.
        """
        os.makedirs(os.path.join(root, "instruments"))
        os.makedirs(os.path.join(root, "docs", "decisions"))
        os.makedirs(os.path.join(root, "docs", "archive", "adr"))
        os.makedirs(os.path.join(root, ".truth"))
        shutil.copy2(os.path.join(INSTRUMENTS_DIR, "register-index.py"),
                     os.path.join(root, "instruments", "register-index.py"))
        for name in decisions:
            with open(os.path.join(root, "docs", "decisions", name), "w") as f:
                f.write("# probe\n")
        for name in archived:
            with open(os.path.join(root, "docs", "archive", "adr", name),
                      "w") as f:
                f.write("# probe\n")
        with open(os.path.join(root, "docs", "roadmap-v3.md"), "w") as f:
            f.write(roadmap)
        # Every location exists and every live doc under docs/ falls inside
        # one, so a clean tree is genuinely clean and every failure below is
        # the seeded one rather than scenery.
        with open(os.path.join(root, "docs", "registers.md"), "w") as f:
            f.write(
                "| register | purpose | location | status | currency evidence |\n"
                "|---|---|---|---|---|\n"
                "| index | itself | `docs/registers.md` | live | `instruments/register-index.py` check (a) |\n"
                "| ADR | decisions | `docs/decisions` and `docs/archive/adr` | live | `instruments/register-index.py` check (b) |\n"
                "| roadmap | the plan | `docs/roadmap-v3.md` | live | `instruments/register-index.py` check (b) |\n")
        with open(os.path.join(root, ".truth", "register-index-baseline"),
                  "w") as f:
            f.write(baseline)
        return os.path.join(root, "instruments", "register-index.py")

    def _ri(self, inst, root):
        return subprocess.run([sys.executable, inst], cwd=root,
                              capture_output=True, text=True)

    def test_register_index_on_the_real_repository(self):
        """register-index.py reads THIS repository and measures something.

        Deliberately not asserting exit 0: check (b) carries a real
        backlog, and a test that demanded green here would be satisfied by
        somebody baselining the backlog away. What it does demand is that
        the sweep RAN -- exit 8 (examined nothing) and exit 3 (could not
        read an input) both fail this arm, which is ADR-042 rule 2 applied
        to the gate rather than to the instrument.
        """
        inst = os.path.join(INSTRUMENTS_DIR, "register-index.py")
        res = subprocess.run([sys.executable, inst, "--json"], cwd=REPO_ROOT,
                             capture_output=True, text=True)
        self.assertIn(res.returncode, (0, 1),
                      "register-index neither passed nor found: %s"
                      % res.stderr)
        data = json.loads(res.stdout)
        self.assertGreater(data["registers"], 0)
        self.assertGreater(data["locations"], 0)
        self.assertGreater(data["docs_examined"], 0)
        self.assertTrue(data["adr_accounting"]["measured"],
                        "the ADR accounting check did not run")
        # A location the index names that is not on disk is never excusable.
        self.assertEqual(data["missing_locations"], [])
        self.assertEqual(data["malformed_locations"], [])
        self.assertEqual(data["unlocated_rows"], [])
        self.assertEqual(data["currency_findings"], [])
        self.assertEqual(data["unreasoned_baseline_keys"], [])

    def test_register_index_check_b_runs_in_both_directions(self):
        """The defeat this instrument was rebuilt for: an id the plan names
        that has no record. One comment naming ADR-063..ADR-200 used to
        pre-account every future decision in silence, because ids
        mentioned-but-not-filed were never examined."""
        tmp = tempfile.mkdtemp(prefix="register-index-")
        try:
            inst = self._mini_register_tree(
                tmp, ["002-b.md"], ["001-a.md"], "ADR-001 ADR-002\n")
            clean = self._ri(inst, tmp)
            self.assertEqual(clean.returncode, 0,
                             "a control tree with nothing seeded must pass, or nothing "
                             "the probes below prove is about the seeded defect: %s%s"
                             % (clean.stdout, clean.stderr))

            # forward: a filed decision the plan mentions nowhere
            with open(os.path.join(tmp, "docs", "roadmap-v3.md"), "w") as f:
                f.write("ADR-001\n")
            fwd = self._ri(inst, tmp)
            self.assertEqual(fwd.returncode, 1)
            self.assertIn("ADR-002 has a file in the decision register",
                          fwd.stdout)

            # reverse: an id the plan names that has no record at all
            with open(os.path.join(tmp, "docs", "roadmap-v3.md"), "w") as f:
                f.write("ADR-001 ADR-002 ADR-099\n")
            rev = self._ri(inst, tmp)
            self.assertEqual(rev.returncode, 1)
            self.assertIn("ADR-099 is mentioned in", rev.stdout)
            self.assertIn("has no decision record", rev.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_register_index_tells_a_deleted_record_from_a_resolution(self):
        """A baselined id stops being a finding for two opposite reasons.

        Reporting both as "the roadmap now mentions it" made the
        prescribed remedy -- drop the line -- the regression itself: a
        deleted decision record became exit 0. The number-space arm below
        is why dropping the line no longer buries it either.
        """
        tmp = tempfile.mkdtemp(prefix="register-index-")
        try:
            inst = self._mini_register_tree(
                tmp, ["002-b.md", "003-c.md"], ["001-a.md"], "ADR-001\n",
                baseline=("adr-unaccounted:ADR-002  baseline 2026-01-01, "
                          "unresolved: probe\n"
                          "adr-unaccounted:ADR-003  baseline 2026-01-01, "
                          "unresolved: probe\n"))
            self.assertEqual(self._ri(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            # (i) resolution: the roadmap now mentions ADR-002
            with open(os.path.join(tmp, "docs", "roadmap-v3.md"), "w") as f:
                f.write("ADR-001 ADR-002\n")
            res = self._ri(inst, tmp)
            self.assertEqual(res.returncode, 1)
            self.assertIn("now mentions it", res.stdout)
            self.assertIn("drop the line", res.stdout)

            # (ii) regression: the RECORD vanished. Same baseline entry,
            # opposite cause, and the remedy must be the opposite too.
            with open(os.path.join(tmp, "docs", "roadmap-v3.md"), "w") as f:
                f.write("ADR-001\n")
            os.remove(os.path.join(tmp, "docs", "decisions", "002-b.md"))
            gone = self._ri(inst, tmp)
            self.assertEqual(gone.returncode, 1)
            self.assertIn("RECORD VANISHED", gone.stdout)
            self.assertIn("Do NOT drop the line", gone.stdout)
            self.assertNotIn("now mentions it", gone.stdout,
                             "a vanished record must not be reported as a "
                             "resolution -- the remedies are opposite")

            # and following the OLD remedy still does not bury it: the
            # number space has a hole where ADR-002 was.
            with open(os.path.join(tmp, ".truth", "register-index-baseline"),
                      "w") as f:
                f.write("adr-unaccounted:ADR-003  baseline 2026-01-01, "
                        "unresolved: probe\n")
            dropped = self._ri(inst, tmp)
            self.assertEqual(dropped.returncode, 1)
            self.assertIn("ADR-002 has no record in", dropped.stdout)
        finally:
            shutil.rmtree(tmp)

    # ---- waiver-index: the register of ways to bypass a gate ----------

    # A stub CLI whose `--help` this suite controls. The instrument
    # harvests its inventory by RUNNING the CLI, so the honest way to seed
    # a divergence is to control that output rather than to patch the
    # instrument. Built from a list of lines rather than a nested
    # triple-quoted literal, because a program inside a program inside a
    # test is where quoting goes to die.
    STUB_CLI_LINES = [
        "#!/usr/bin/env python3",
        "import sys",
        "VERBS = {verbs!r}",
        "FLAGS = {flags!r}",
        # Flags rendered in the USAGE line only, never in `options:`.
        # argparse never does this; the point is that if this reader ever
        # disagrees with itself about one parser, it must say so rather
        # than silently prefer one rendering.
        "USAGE_ONLY = {usage_only!r}",
        "argv = [x for x in sys.argv[1:] if x != '--help']",
        "if not argv:",
        "    print('usage: truth [-h] {{' + ','.join(VERBS) + '}} ...')",
        "    print()",
        "    print('positional arguments:')",
        "    for v in VERBS:",
        "        print('    %-18s do the %s thing' % (v, v))",
        "    raise SystemExit(0)",
        "verb = argv[0]",
        "if verb not in VERBS:",
        "    raise SystemExit(2)",
        "flags = FLAGS.get(verb, [])",
        "extra = USAGE_ONLY.get(verb, [])",
        "opts = ''.join(' [' + f + ']' for f in flags + extra)",
        "print('usage: truth ' + verb + ' [-h]' + opts)",
        "print()",
        "print('positional arguments:')",
        "print('  text')",
        "print()",
        "print('options:')",
        "print('  -h, --help            show this help message and exit')",
        "for f in flags:",
        "    print('  ' + f + '   help text for ' + f.split()[0])",
        "raise SystemExit(0)",
    ]

    def _mini_waiver_tree(self, root, verbs, flags, rows, ledger=(),
                          policy=None, declare_env=True,
                          declare_policy_file=True):
        """A throwaway tree with a stub CLI and a seven-column register."""
        os.makedirs(os.path.join(root, "instruments"))
        os.makedirs(os.path.join(root, "docs"))
        os.makedirs(os.path.join(root, "scripts"))
        os.makedirs(os.path.join(root, ".truth"))
        shutil.copy2(os.path.join(INSTRUMENTS_DIR, "waiver-index.py"),
                     os.path.join(root, "instruments", "waiver-index.py"))
        self._write_stub(root, verbs, flags)
        # A real repository always reads SOMETHING from the environment,
        # and the ADR-042 guard now refuses a carrier that harvested
        # nothing while the register lists nothing for it -- correctly,
        # because a zero there is a broken harvest rather than a clean
        # surface. A fixture with no env read at all is not a repository,
        # so every tree gets one, declared in FIXTURE_POLICY.
        with open(os.path.join(root, "scripts", "fixture-env.sh"), "w") as f:
            f.write('X="${FIXTURE_BASELINE_ENV:-}"\n')
        self._write_register(root, rows)
        with open(os.path.join(root, ".truth", "claims.jsonl"), "w") as f:
            for rec in ledger:
                f.write(json.dumps(rec) + "\n")
        # Every harvested carrier must be classified -- flags, environment
        # names AND the .truth/ files the tree itself has. The two the
        # helper creates are declared here so an arm's policy argument
        # only ever carries what that arm is about.
        self._write_policy(root, policy or "", declare_env=declare_env,
                           declare_policy_file=declare_policy_file)
        return os.path.join(root, "instruments", "waiver-index.py")

    # The .truth/ files the fixture itself creates. Every tree has them,
    # and the `file` carrier is harvested from that directory, so they
    # must be classified or every arm fails on the fixture rather than on
    # what it is testing.
    FIXTURE_POLICY = (
        "file:.truth/claims.jsonl  the ledger itself, not a policy.\n"
        "file:.truth/waiver-not-an-override  the fixture's own policy.\n"
        "env:FIXTURE_BASELINE_ENV  a constant in the fixture so the tree "
        "harvests a non-empty env carrier.\n")

    @staticmethod
    def _write_policy(root, body, declare_env=True, declare_policy_file=True):
        # An arm that gives the fixture's env name a REGISTER ROW must not
        # also declare it -- one waiver, one side, which the sweep checks.
        head = TestTierCInstruments.FIXTURE_POLICY
        if not declare_env:
            head = "".join(l for l in head.splitlines(True)
                           if not l.startswith("env:"))
        if not declare_policy_file:
            head = "".join(l for l in head.splitlines(True)
                           if "waiver-not-an-override" not in l)
        with open(os.path.join(root, ".truth",
                               "waiver-not-an-override"), "w") as f:
            f.write("# probe\n" + head + body)

    def _write_stub(self, root, verbs, flags, usage_only=None):
        body = "\n".join(self.STUB_CLI_LINES).format(
            verbs=verbs, flags=flags, usage_only=usage_only or {})
        cli = os.path.join(root, "scripts", "truth")
        with open(cli, "w") as f:
            f.write(body + "\n")
        os.chmod(cli, 0o755)

    # The register must SAY it is not total, and the sweep checks the
    # sentence is there. Every throwaway register carries it, so an arm
    # that removes it is testing the check rather than the fixture.
    LIMIT_LINE = "THIS REGISTER IS NOT TOTAL.\n\n"

    @staticmethod
    def _write_register(root, rows, limit=True):
        header = ("| carrier | name | where it applies | gate it lifts | "
                  "admitted on | stamp on the record | decays | "
                  "governing record |\n"
                  "|---|---|---|---|---|---|---|---|\n")
        body = ""
        for row in rows:
            carrier, name, where, admitted, stamp = row
            body += ("| %s | `%s` | %s | a gate | %s | %s | no | ADR-000 |\n"
                     % (carrier, name, ", ".join(where), admitted,
                        stamp if stamp.startswith("NOT COUNTABLE")
                        else (("`%s`" % stamp) if stamp
                              else "NOT COUNTABLE")))
        limit_text = (TestTierCInstruments.LIMIT_LINE if limit else "")
        with open(os.path.join(root, "docs", "waivers.md"), "w") as f:
            f.write("# Waivers\n\n" + limit_text + header + body + "\n")

    def _wi(self, inst, root):
        return subprocess.run([sys.executable, inst], cwd=root,
                              capture_output=True, text=True)

    def test_waiver_index_runs_in_both_directions(self):
        """The register of overrides, checked against the parser both ways.

        REVERSE is the direction that matters and the one whose absence
        cost this repository months: `--exit-ok`, a flag that has never
        existed, lived in three documents at once because nothing ever
        walked from the parser back to the list.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            inst = self._mini_waiver_tree(
                tmp, ["claim", "verdict"],
                {"claim": ["--scope-ok SENTENCE", "--duplicate-ok"],
                 "verdict": ["--orphan-ok SENTENCE"]},
                [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis"),
                 ("flag", "--duplicate-ok", ["claim"], "nothing", "overridden_duplicates"),
                 ("flag", "--orphan-ok", ["verdict"], "SENTENCE", "orphan_basis")])
            clean = self._wi(inst, tmp)
            self.assertEqual(clean.returncode, 0,
                             "a control tree with nothing seeded must pass: "
                             "%s%s" % (clean.stdout, clean.stderr))

            # REVERSE: the parser grows a bypass the register never heard of
            self._write_stub(tmp, ["claim", "verdict"],
                             {"claim": ["--scope-ok SENTENCE",
                                        "--duplicate-ok", "--brand-new-ok"],
                              "verdict": ["--orphan-ok SENTENCE"]})
            rev = self._wi(inst, tmp)
            self.assertEqual(rev.returncode, 1,
                             "a new bypass flag with no row passed: %s"
                             % rev.stdout)
            self.assertIn("--brand-new-ok", rev.stdout)
            self.assertIn("NOTHING classifies it", rev.stdout)

            # FORWARD: the register lists a flag the parser does not accept
            self._write_stub(tmp, ["claim", "verdict"],
                             {"claim": ["--scope-ok SENTENCE",
                                        "--duplicate-ok"],
                              "verdict": ["--orphan-ok SENTENCE"]})
            self._write_register(
                tmp,
                [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis"),
                 ("flag", "--duplicate-ok", ["claim"], "nothing", "overridden_duplicates"),
                 ("flag", "--exit-ok", ["verdict"], "SENTENCE", "orphan_basis")])
            fwd = self._wi(inst, tmp)
            self.assertEqual(fwd.returncode, 1)
            self.assertIn("--exit-ok", fwd.stdout)
            self.assertIn("accepts on NO verb", fwd.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_checks_what_a_waiver_is_admitted_on(self):
        """A bare flag described as taking a sentence is the defect that
        made ADR-059's opening premise false: three of the eight overrides
        are admitted on NOTHING, and they are exactly the three that lift
        an execution screen rather than a quality-of-justification gate.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            base = [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis"),
                    ("flag", "--duplicate-ok", ["claim"], "nothing", "overridden_duplicates")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"],
                {"claim": ["--scope-ok SENTENCE", "--duplicate-ok"]}, base)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            # the register claims a rationale where the parser takes none
            self._write_register(
                tmp, [base[0],
                      ("flag", "--duplicate-ok", ["claim"], "SENTENCE", "overridden_duplicates")])
            lie = self._wi(inst, tmp)
            self.assertEqual(lie.returncode, 1)
            self.assertIn("the parser says", lie.stdout)

            # ...and the other way: a sentence flag described as bare
            self._write_register(
                tmp, [("flag", "--scope-ok", ["claim"], "nothing", "scope_basis"),
                      base[1]])
            other = self._wi(inst, tmp)
            self.assertEqual(other.returncode, 1)
            self.assertIn("the parser says", other.stdout)

            # the register names the wrong verbs
            self._write_register(
                tmp, [("flag", "--scope-ok", ["verdict"], "SENTENCE", "scope_basis"),
                      base[1]])
            verbs = self._wi(inst, tmp)
            self.assertEqual(verbs.returncode, 1)
            self.assertIn("the parser accepts it on", verbs.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_counts_the_population_structurally(self):
        """A nested field with a required value is invisible to a
        substring scan. The first version of this instrument reported 0
        for `accept.screened = false` where the truth was 5 -- an
        under-reporting population count, which is the shrinking
        measurement this repository keeps catching in other places.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            ledger = [
                {"id": "tr-1", "kind": "claim",
                 "payload": {"accept": {"screened": False}}},
                {"id": "tr-2", "kind": "claim",
                 "payload": {"accept": {"screened": True}}},
                {"id": "tr-3", "kind": "claim",
                 "payload": {"scope_basis": "because"}},
            ]
            inst = self._mini_waiver_tree(
                tmp, ["claim"],
                {"claim": ["--scope-ok SENTENCE", "--accept-unsafe-ok"]},
                [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis"),
                 ("flag", "--accept-unsafe-ok", ["claim"], "nothing", "accept.screened = false")],
                ledger=ledger)
            out = self._wi(inst, tmp)
            self.assertEqual(out.returncode, 0,
                             "a control tree with nothing seeded must pass: "
                             "%s%s" % (out.stdout, out.stderr))
            # 1, not 2: the record whose screen was NOT lifted must not
            # count as a bypass, which is why the value is part of the key
            self.assertRegex(out.stdout,
                             r"accept\.screened = false\s+1 record")
            self.assertRegex(out.stdout, r"scope_basis\s+1 record")

            # a ledger line that will not parse must be COUNTED, not skipped
            with open(os.path.join(tmp, ".truth", "claims.jsonl"), "a") as f:
                f.write("{not json\n")
            broken = self._wi(inst, tmp)
            self.assertEqual(broken.returncode, 1)
            self.assertIn("could not be parsed as JSON", broken.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_refuses_to_report_health_over_nothing(self):
        """ADR-042 rule 2, both halves, plus the environment split.

        An empty register agrees with an empty parser, so a sweep that
        read neither would report a clean escape surface having harvested
        nothing at all -- the most comfortable way to be wrong about how
        many gates can be bypassed.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]}, rows)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            # Zero rows with a live parser is a DIVERGENCE, not an empty
            # sweep: every flag the CLI accepts is now unlisted.
            waivers = os.path.join(tmp, "docs", "waivers.md")
            with open(waivers, "w") as f:
                f.write("# Waivers\n\nno table here\n")
            lost = self._wi(inst, tmp)
            self.assertEqual(lost.returncode, 1)
            self.assertIn("NOTHING classifies it", lost.stdout)
            self.assertIn("no eight-column table header row", lost.stdout)

            # a parser with no overrides and a register with one is a
            # DIVERGENCE, not an empty sweep
            self._write_register(tmp, rows)
            self._write_stub(tmp, ["claim"], {"claim": []})
            none = self._wi(inst, tmp)
            self.assertEqual(none.returncode, 1)
            self.assertIn("accepts on NO verb", none.stdout)

            # both empty: the sweep must not agree with itself
            with open(waivers, "w") as f:
                f.write("# Waivers\n\nno table here\n")
            self.assertEqual(self._wi(inst, tmp).returncode, 8,
                             "an empty register agreed with an empty parser")

            # a CLI whose top-level help lists NO verbs is ENVIRONMENT:
            # the inventory would be empty and every row would read as
            # "accepts on NO verb", which is a confident wrong answer
            # rather than an admission that nothing was harvested.
            self._write_register(tmp, rows)
            self._write_stub(tmp, [], {})
            noverbs = self._wi(inst, tmp)
            self.assertEqual(noverbs.returncode, 3,
                             "zero verbs harvested was reported as findings")
            self.assertIn("listed no subcommands", noverbs.stderr)

            # a CLI that cannot run at all is ENVIRONMENT, not a finding
            self._write_register(tmp, rows)
            cli = os.path.join(tmp, "scripts", "truth")
            os.remove(cli)
            os.makedirs(cli)
            env = self._wi(inst, tmp)
            self.assertEqual(env.returncode, 3)
            self.assertIn("the sweep did NOT run", env.stderr)
            self.assertNotIn("Traceback", env.stderr,
                             "an environment failure must be a sentence, "
                             "never a stack trace")

            # ...and the harder half, which the previous case cannot
            # isolate: a CLI that prints PERFECTLY USABLE help and then
            # exits non-zero. Removing the returncode guard leaves the
            # empty-help guard to catch the case above, so without this
            # one the returncode branch could be deleted unnoticed.
            # Trusting a parser that reported failure is reading an
            # inventory from a program that said it was broken.
            shutil.rmtree(cli)
            self._write_stub(tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]})
            with open(cli) as f:
                good = f.read()
            with open(cli, "w") as f:
                f.write(good.replace("raise SystemExit(0)",
                                     "raise SystemExit(3)"))
            os.chmod(cli, 0o755)
            noisy = self._wi(inst, tmp)
            self.assertEqual(noisy.returncode, 3,
                             "a CLI that exited non-zero was trusted anyway")
            self.assertIn("exited 3", noisy.stderr)
            self.assertNotIn("Traceback", noisy.stderr,
                             "an environment failure must be a sentence, "
                             "never a stack trace")
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_classifies_every_flag_not_just_the_ok_ones(self):
        """The reverse direction is TOTAL, and it has to be.

        Scoping it to a naming convention was wrong twice in one file:
        `--refresh-evidence` lifts a hard ADR-051 refusal and takes a
        sentence with no `-ok` suffix, and `--single-run` skips the G6
        determinism double-run with neither. A flag nobody has judged is
        a gate nobody knows can be lifted, so every flag the parser
        accepts must be a waiver row or a declared non-override.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"],
                {"claim": ["--scope-ok SENTENCE", "--json"]}, rows,
                policy="flag:--json  selects machine output; read-only.\n")
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            # a NEW flag matching neither historical override shape
            self._write_stub(tmp, ["claim"],
                             {"claim": ["--scope-ok SENTENCE", "--json",
                                        "--single-run"]})
            new = self._wi(inst, tmp)
            self.assertEqual(new.returncode, 1,
                             "an unclassified flag passed: %s" % new.stdout)
            self.assertIn("--single-run", new.stdout)
            self.assertIn("NOTHING classifies it", new.stdout)

            # declaring it not-an-override clears it -- that is the judgement
            self._write_policy(tmp, "flag:--json  selects machine output; read-only.\n"
                                    "flag:--single-run  a probe entry.\n")
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            # a declaration with no reason does not
            self._write_policy(tmp, "flag:--json  selects machine output; read-only.\n"
                                    "flag:--single-run\n")
            bare = self._wi(inst, tmp)
            self.assertEqual(bare.returncode, 1)
            self.assertIn("with no reason", bare.stdout)

            # mirror: a declaration whose flag is gone
            self._write_policy(tmp, "flag:--json  selects machine output; read-only.\n"
                                    "flag:--single-run  a probe entry.\n"
                                    "flag:--long-gone  a probe entry.\n")
            stale = self._wi(inst, tmp)
            self.assertEqual(stale.returncode, 1)
            self.assertIn("--long-gone", stale.stdout)
            self.assertIn("outlived its subject", stale.stdout)

            # a flag on BOTH sides is a contradiction, not a pass
            self._write_policy(tmp, "flag:--json  selects machine output; read-only.\n"
                                    "flag:--single-run  a probe entry.\n"
                                    "flag:--scope-ok  a probe entry.\n")
            both = self._wi(inst, tmp)
            self.assertEqual(both.returncode, 1)
            self.assertIn("BOTH a row in", both.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_harvests_every_carrier_it_claims_to(self):
        """A register of FLAGS whose title reads over BYPASSES is a
        mis-scoped partition, and a domain left unstated reads as
        universal. Two carriers besides flags CAN be enumerated -- the
        environment, from every `os.environ` read and `${NAME:-}` idiom in
        the tree, and `.truth/`, from the directory listing -- so both get
        a real reverse direction rather than a hand-kept list.

        The finding that forced this: `TRUTH_SELF_VERDICT=1` lifts the
        ADR-010 author-is-not-verifier refusal. No flag names it, it
        stamps nothing, and it is deliberately absent from the refusal
        text. A register of flags cannot hold it.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE",
                     "scope_basis")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]}, rows)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            # env, reverse: a source file starts reading a new name
            probe = os.path.join(tmp, "instruments", "probe.py")
            with open(probe, "w") as f:
                f.write('import os\nos.environ.get("TRUTH_NEW_ESCAPE")\n')
            env = self._wi(inst, tmp)
            self.assertEqual(env.returncode, 1,
                             "a new environment name passed: %s" % env.stdout)
            self.assertIn("TRUTH_NEW_ESCAPE", env.stdout)
            self.assertIn("NOTHING classifies it", env.stdout)

            # ...and the shell half of the same harvest
            os.remove(probe)
            sh = os.path.join(tmp, "scripts", "probe.sh")
            with open(sh, "w") as f:
                f.write('X="${TRUTH_SHELL_ESCAPE:-}"\n')
            shell = self._wi(inst, tmp)
            self.assertEqual(shell.returncode, 1,
                             "a shell-carried name passed: %s" % shell.stdout)
            self.assertIn("TRUTH_SHELL_ESCAPE", shell.stdout)

            # a name ASSIGNED in the same file is a local, not inherited
            with open(sh, "w") as f:
                f.write('TRUTH_SHELL_ESCAPE=1\nX="${TRUTH_SHELL_ESCAPE:-}"\n')
            local = self._wi(inst, tmp)
            self.assertEqual(local.returncode, 0,
                             "a name assigned WITHOUT reading itself must not be\n                             "
                             "reported as inherited: %s" % local.stdout)
            os.remove(sh)

            # file, reverse: a new .truth/ policy file
            newpol = os.path.join(tmp, ".truth", "brand-new-opt-out")
            with open(newpol, "w") as f:
                f.write("# probe\n")
            fil = self._wi(inst, tmp)
            self.assertEqual(fil.returncode, 1,
                             "a new .truth/ file passed: %s" % fil.stdout)
            self.assertIn("brand-new-opt-out", fil.stdout)
            os.remove(newpol)

            # forward, env: a row naming a name nothing reads
            self._write_register(
                tmp, rows + [("env", "TRUTH_NOBODY_READS", ["nowhere"],
                              "nothing", "")])
            ghost = self._wi(inst, tmp)
            self.assertEqual(ghost.returncode, 1)
            self.assertIn("TRUTH_NOBODY_READS", ghost.stdout)
            self.assertIn("outlived it", ghost.stdout)

            # forward, file: a row naming a policy file that is not there
            self._write_register(
                tmp, rows + [("file", ".truth/not-here", ["nowhere"],
                              "nothing", "")])
            nofile = self._wi(inst, tmp)
            self.assertEqual(nofile.returncode, 1)
            self.assertIn(".truth/not-here", nofile.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_checks_admitted_on_for_every_carrier(self):
        """The controlled vocabulary is not a flag-only rule.

        It was checked below the `carrier != "flag"` return, so 21 of 32
        rows could hold arbitrary prose in that column while the summary
        line counted them in neither bucket -- announcing a total larger
        than its own parts. A reading that silently shrinks, in the column
        a previous adversarial pass had already hardened for flags.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE",
                     "scope_basis"),
                    ("env", "FIXTURE_BASELINE_ENV", ["scripts/fixture-env.sh"],
                     "nothing", "")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]}, rows,
                policy="", declare_env=False)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            for carrier, name, where in (
                    ("env", "FIXTURE_BASELINE_ENV", ["scripts/fixture-env.sh"]),
                    ("syntax", "<something>", ["nowhere"])):
                # keep BOTH baseline rows: dropping the env row would
                # leave the fixture's env read unclassified, and that
                # failure would mask the one under test
                self._write_register(
                    tmp, [rows[0], rows[1]] + ([] if carrier == "env" else
                                               [(carrier, name, where,
                                                 "whatever prose I like, "
                                                 "banana", "")])
                    if carrier != "env" else
                    [rows[0], (carrier, name, where,
                               "whatever prose I like, banana", "")])
                got = self._wi(inst, tmp)
                self.assertEqual(
                    got.returncode, 1,
                    "prose in `admitted on` passed on carrier %r: %s"
                    % (carrier, got.stdout))
                self.assertIn("must be exactly", got.stdout)
                self.assertIn("on every carrier", got.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_checks_where_a_non_flag_waiver_applies(self):
        """A row may abbreviate; it may not point somewhere false.

        SUBSET, not equality -- a register that must list all six readers
        of a policy file is one nobody reads. What it may not do is name
        a place the thing does not apply, and the harvest already has the
        answer two lines away.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE",
                     "scope_basis"),
                    ("env", "FIXTURE_BASELINE_ENV", ["scripts/fixture-env.sh"],
                     "nothing", "")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]}, rows,
                declare_env=False)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            # abbreviating is fine: name nothing at all
            self._write_register(
                tmp, [rows[0], ("env", "FIXTURE_BASELINE_ENV", [],
                                "nothing", "")])
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                             "a `where` cell must be allowed to name the place that "
                             "matters rather than every reader")

            # pointing at a file that does not read it is not
            self._write_register(
                tmp, [rows[0], ("env", "FIXTURE_BASELINE_ENV",
                                ["scripts/nobody-reads-this.py"],
                                "nothing", "")])
            ghost = self._wi(inst, tmp)
            self.assertEqual(ghost.returncode, 1)
            self.assertIn("and it does not", ghost.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_harvest_reaches_the_shapes_this_repo_uses(self):
        """Three shapes the first harvest missed, all at exit 0.

        `NAME="${NAME:-}"` is the commonest bash way to READ an inherited
        variable, and treating the assignment as proof of locality missed
        exactly the idiom this repository's own scripts use -- an earlier
        version of this suite ASSERTED that miss as correct. The CLI entry
        point `scripts/truth` is Python with no suffix. And the hook
        directory is where gate-disabling lives, so every hook name counts,
        not the three that happen to exist.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE",
                     "scope_basis"),
                    ("env", "FIXTURE_BASELINE_ENV", ["scripts/fixture-env.sh"],
                     "nothing", "")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]}, rows,
                declare_env=False)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")
            os.makedirs(os.path.join(tmp, ".githooks"), exist_ok=True)

            for rel, body in (
                    ("scripts/self-assign.sh",
                     'TRUTH_SELF_ASSIGN_BYPASS="${TRUTH_SELF_ASSIGN_BYPASS:-}"\n'),
                    ("scripts/no-suffix-entry",
                     '#!/usr/bin/env python3\n'
                     'import os\nos.environ.get("TRUTH_ENTRYPOINT_BYPASS")\n'),
                    (".githooks/post-commit",
                     '#!/usr/bin/env bash\nX="${TRUTH_POSTCOMMIT_BYPASS:-}"\n'),
                    # NO shebang: only the hook-name list reaches this
                    # one, so it is what isolates HOOK_NAMES from the
                    # shebang path. With a shebang the two overlap and
                    # neither check can be shown to be load-bearing.
                    (".githooks/post-merge",
                     'X="${TRUTH_POSTMERGE_BYPASS:-}"\n'),
                    # `env NAME=value cmd` is the third shell idiom the
                    # register advertises; without an arm it contributed
                    # nothing measurable to the harvest.
                    ("scripts/envrun.sh",
                     'env TRUTH_ENVRUN_BYPASS=1 true\n')):
                path = os.path.join(tmp, rel)
                with open(path, "w") as f:
                    f.write(body)
                got = self._wi(inst, tmp)
                self.assertEqual(
                    got.returncode, 1,
                    "the harvest walked past %s: %s" % (rel, got.stdout))
                self.assertIn("BYPASS", got.stdout)
                os.remove(path)

            # a genuine local -- assigned without reading itself -- is not
            # reported, or the harvest would cry on every shell script
            local = os.path.join(tmp, "scripts", "genuine-local.sh")
            with open(local, "w") as f:
                f.write('TRUTH_REAL_LOCAL=1\nX="${TRUTH_REAL_LOCAL:-}"\n')
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                             "a name assigned without reading itself must not be reported "
                             "as inherited")
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_refuses_a_carrier_that_harvested_nothing(self):
        """ADR-042 rule 2, per carrier.

        This repository always has flags, environment reads and `.truth/`
        files. A zero for any of them is a broken harvest, not a clean
        escape surface -- and guarding only rows-and-flags left the two
        new carriers able to agree with an empty register.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE",
                     "scope_basis"),
                    ("env", "FIXTURE_BASELINE_ENV", ["scripts/fixture-env.sh"],
                     "nothing", "")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]}, rows,
                declare_env=False)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            # remove the tree's only env read AND its row: empty agrees
            # with empty, which is the case that must not exit 0
            os.remove(os.path.join(tmp, "scripts", "fixture-env.sh"))
            self._write_register(tmp, [rows[0]])
            self._write_policy(tmp, "")
            empty = self._wi(inst, tmp)
            self.assertEqual(empty.returncode, 8,
                             "an empty carrier agreed with an empty register: "
                             "%s%s" % (empty.stdout, empty.stderr))
            self.assertIn("harvested ZERO for carrier(s) env", empty.stderr)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_marks_only_the_row_a_finding_is_about(self):
        """The per-row FAIL mark must be name-scoped, not a substring
        search over every failure line.

        The real case: `.truth/waiver-not-an-override` is itself a row in
        this register -- the escape surface's own escape surface -- and
        almost every failure message NAMES that path, because it is where
        an unclassified thing must be declared. Under a substring match
        that row showed FAIL whenever anything else failed. Same defect as
        reading the `admitted on` column by substring, which a prior
        review had already found once; a fix reported as self-caught and
        held by nothing is not a fix.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE",
                     "scope_basis"),
                    ("env", "FIXTURE_BASELINE_ENV", ["scripts/fixture-env.sh"],
                     "nothing", ""),
                    # the row whose NAME is inside other messages
                    ("file", ".truth/waiver-not-an-override",
                     ["instruments/waiver-index.py"], "SENTENCE", "")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE", "--json"]},
                rows, policy="flag:--json  read-only.\n", declare_env=False,
                declare_policy_file=False)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                             "a control tree with nothing seeded must pass")

            # seed a failure ABOUT --json, whose message names the policy
            # path -- and therefore names the `file` row above
            self._write_policy(tmp, "", declare_env=False,
                               declare_policy_file=False)
            got = self._wi(inst, tmp)
            self.assertEqual(got.returncode, 1)
            self.assertIn("--json", got.stdout)
            # a ROW line carries the name immediately after the mark;
            # a FAILURE line merely mentions it somewhere, which is the
            # whole point of this arm
            row_line = [l for l in got.stdout.splitlines()
                        if l.startswith("OK    .truth/waiver-not-an-override")
                        or l.startswith("FAIL  .truth/waiver-not-an-override")]
            self.assertEqual(len(row_line), 1, got.stdout)
            self.assertTrue(
                row_line[0].startswith("OK "),
                "the row for .truth/waiver-not-an-override was marked FAIL "
                "because an unrelated failure line merely NAMED it; the mark "
                "must be scoped to the row the finding is about: %r"
                % row_line[0])
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_finds_the_register_table_by_its_shape(self):
        """`docs/waivers.md` carries more than one table.

        Matching a header on its first cell alone binds the parser to
        whichever table comes first, and the register would then be read
        from the wrong one -- reporting every real row as sitting below a
        blank line. The eight-column shape is what keeps the two apart,
        and until this arm existed that fix was held by nothing.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE",
                     "scope_basis"),
                    ("env", "FIXTURE_BASELINE_ENV", ["scripts/fixture-env.sh"],
                     "nothing", "")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]}, rows,
                declare_env=False)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                             "a control tree with nothing seeded must pass")

            # a SECOND table above the register, whose first cell is also
            # `carrier` -- exactly the shape of the domain statement in
            # the real file
            reg = os.path.join(tmp, "docs", "waivers.md")
            with open(reg, encoding="utf-8") as f:
                body = f.read()
            decoy = ("| carrier | enumerated from | reverse direction |\n"
                     "|---|---|---|\n"
                     "| flag | the parser | gated |\n\n")
            with open(reg, "w", encoding="utf-8") as f:
                f.write(body.replace("| carrier | name |", decoy +
                                     "| carrier | name |", 1))
            got = self._wi(inst, tmp)
            self.assertEqual(
                got.returncode, 0,
                "the register must be found by the EIGHT-COLUMN header, "
                "not by a first cell that another table also uses: the "
                "parser bound to the wrong table: %s%s"
                % (got.stdout, got.stderr))
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_requires_the_register_to_state_its_own_limit(self):
        """Three carriers cannot be enumerated from any source, so the
        register must say it is not total -- in itself, where a reader of
        it alone will see it.

        The sentence is GATED because a limit held by nothing is the first
        thing a redraft deletes. This same effort lost a finding about six
        overdue gate-metrics reviews exactly that way, replaced by a
        sentence that could not be checked.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE",
                     "scope_basis")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]}, rows)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            self._write_register(tmp, rows, limit=False)
            gone = self._wi(inst, tmp)
            self.assertEqual(gone.returncode, 1,
                             "the register dropped its limit statement and "
                             "still passed: %s" % gone.stdout)
            self.assertIn("does not contain the marker", gone.stdout)
            self.assertIn("concludes it covers every way a gate can be "
                          "lifted", gone.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_records_unbounded_carriers_without_checking_them(self):
        """`syntax`, `config` and `code` have no list to walk back from.

        A `<path>#<selector>` entry is exempt from the one-path and churn
        budgets by ADR-055: the bypass is carried by PATH SYNTAX, so no
        flag names it and no directory holds it. Rows in these carriers
        are recorded and NOT reverse-checked, and the sweep says so rather
        than implying a coverage it cannot have. An unrecognised carrier
        is refused, because a typo would silently buy that exemption.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE",
                     "scope_basis")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]}, rows)

            # an unbounded row names something no source enumerates, and
            # passes precisely because there is nothing to check it against
            self._write_register(
                tmp, rows + [("syntax", "<path>#<selector>", ["--paths"],
                              "nothing", "")])
            ok = self._wi(inst, tmp)
            self.assertEqual(ok.returncode, 0,
                             "an unbounded row must pass: there is no source "
                             "to check it against: %s%s"
                             % (ok.stdout, ok.stderr))
            self.assertIn("unbounded carriers", ok.stdout)
            self.assertIn("<path>#<selector>", ok.stdout)
            self.assertIn("NOT total", ok.stdout)

            # a carrier nobody declared is refused, not silently exempted
            self._write_register(
                tmp, rows + [("sintax", "<path>#<typo>", ["--paths"],
                              "nothing", "")])
            typo = self._wi(inst, tmp)
            self.assertEqual(typo.returncode, 1,
                             "a misspelled carrier bought an exemption: %s"
                             % typo.stdout)
            self.assertIn("is not one of", typo.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_policy_keys_name_their_carrier(self):
        """One name can be a flag on one carrier and nothing on another,
        and a bare key cannot say which list it is excused FROM."""
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE",
                     "scope_basis")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"],
                {"claim": ["--scope-ok SENTENCE", "--json"]}, rows,
                policy="flag:--json  read-only.\n")
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            self._write_policy(tmp, "--json  read-only.\n")
            bare = self._wi(inst, tmp)
            self.assertEqual(bare.returncode, 1)
            self.assertIn("is not a namespaced key", bare.stdout)

            self._write_policy(tmp, "syntax:--json  read-only.\n")
            unb = self._wi(inst, tmp)
            self.assertEqual(unb.returncode, 1,
                             "an unbounded carrier was used as an excuse "
                             "namespace: %s" % unb.stdout)
            self.assertIn("which is not harvested", unb.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_earns_not_countable_rather_than_asserting_it(self):
        """NOT COUNTABLE is a claim that no separating predicate exists,
        and it has to be earned like any other claim.

        Two ways it was asserted instead of earned, both fixed here:

        A file-carried waiver's uses ARE its lines -- one non-comment
        entry is one standing excusal, and `wc -l` is the count. Marking
        those unmeasurable suppressed 209 of them, and turned the
        DELIBERATE emptiness of `.truth/generated-paths` (whose own header
        says emptiness is a statement) into an absence.

        And `--ttl-days` was declared uncountable on the claim that its
        override is "the ABSENCE of `ttl_default`, which no presence test
        separates". The separating predicate is one line of the grammar
        below and it answers 2, not "unmeasurable".

        Over-suppression reads as humility and hides a number. It is the
        mirror of the earlier, correct decision that a WRONG population is
        worse than none -- so a missing one must be earned too.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            ledger = [
                # carries a decaying basis, an explicit shelf life, no
                # default stamp: the one shape that IS the override
                {"id": "tr-1", "kind": "claim",
                 "payload": {"scope_basis": "why", "ttl_days": 3650}},
                # ttl_days present but NULL -- what a claim filed WITHOUT
                # the flag looks like, and what turned 2 into 6
                {"id": "tr-2", "kind": "claim",
                 "payload": {"scope_basis": "why", "ttl_days": None}},
                # decayed by default, so not an override of the decay
                {"id": "tr-3", "kind": "claim",
                 "payload": {"scope_basis": "why", "ttl_days": 30,
                             "ttl_default": True}},
                # a shelf life with no override basis at all
                {"id": "tr-4", "kind": "claim", "payload": {"ttl_days": 90}},
                # a SECOND default-decayed record. Without it the negation
                # could be inverted and the count stayed 1 -- the mutation
                # swapped WHICH record was counted, not how many, and an
                # arm that asserts a number cannot see that.
                {"id": "tr-5", "kind": "claim",
                 "payload": {"paths_basis": "why", "ttl_days": 30,
                             "ttl_default": True}},
            ]
            inst = self._mini_waiver_tree(
                tmp, ["claim"],
                {"claim": ["--scope-ok SENTENCE", "--ttl-days N"]},
                [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis"),
                 ("flag", "--ttl-days", ["claim"], "a value",
                  "(scope_basis/paths_basis/generated_ok_basis) + ttl_days "
                  "+ !ttl_default"),
                 ("file", ".truth/waiver-not-an-override",
                  ["instruments/waiver-index.py"], "SENTENCE", "ENTRIES"),
                 ("env", "FIXTURE_BASELINE_ENV", ["scripts/fixture-env.sh"],
                  "nothing", "")],
                ledger=ledger, declare_env=False,
                declare_policy_file=False)
            out = self._wi(inst, tmp)
            self.assertEqual(out.returncode, 0,
                             "a control tree with nothing seeded must pass: "
                             "%s%s" % (out.stdout, out.stderr))

            # exactly one of the four records is the override
            self.assertRegex(
                out.stdout, r"\+ !ttl_default\s+1 record",
                "the separating predicate must count only the record that "
                "carries a basis, an explicit shelf life and no default "
                "stamp: %s" % out.stdout)
            # a file-carried waiver is counted by its entries
            self.assertRegex(
                out.stdout, r"waiver-not-an-override\s+\d+ standing entr",
                "a file-carried waiver's uses are its lines and must be "
                "counted: %s" % out.stdout)
            # and the genuinely uncountable one still says so
            self.assertIn("NOT COUNTABLE", out.stdout)
            self.assertIn("FIXTURE_BASELINE_ENV", out.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_refuses_to_print_a_population_it_cannot_take(self):
        """A stamp whose presence does not mean the waiver was used.

        `ttl_days` is on every claim; `evidence_paths` on every
        path-claim; `session` and `ts` on every record. Counting those
        measured the ledger and called it the escape surface -- 268
        "uses" of --ttl-days on a ledger of 268 claims. A wrong
        population is worse than a missing one, because it reads as a
        measurement, so such rows carry NOT COUNTABLE and no number is
        printed for them.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            ledger = [{"id": "tr-%d" % i, "kind": "claim",
                       "payload": {"ttl_days": 30, "scope_basis": "why"}}
                      for i in range(3)]
            inst = self._mini_waiver_tree(
                tmp, ["claim"],
                {"claim": ["--scope-ok SENTENCE", "--ttl-days N"]},
                [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis"),
                 # the REAL shape: a marker AND a backticked field, so the
                 # convention is what suppresses the count. A cell with no
                 # field at all cannot tell the two apart, and an earlier
                 # version of this arm could not make the check go red.
                 ("flag", "--ttl-days", ["claim"], "a value",
                  "NOT COUNTABLE -- `ttl_days` is on every claim")],
                ledger=ledger)
            out = self._wi(inst, tmp)
            self.assertEqual(out.returncode, 0,
                             "a control tree with nothing seeded must pass: "
                             "%s%s" % (out.stdout, out.stderr))
            self.assertRegex(out.stdout, r"scope_basis\s+3 record")
            self.assertIn("NOT COUNTABLE", out.stdout)
            self.assertIn("--ttl-days", out.stdout)
            self.assertNotRegex(out.stdout, r"ttl_days\s+3 record",
                                "a field present in ordinary traffic must not "
                                "be counted as a waiver population")
            self.assertIn("LOWER BOUND", out.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_refuses_a_reason_abandoned_mid_clause(self):
        """A half-written reason is worse than a missing one.

        It reads as a judgement somebody made, so nothing prompts anyone
        to finish it, and the flag stays excused on half an argument.
        Three entries in the real policy file were truncated exactly this
        way on the first pass -- `--basis` ("so it is the opposite"),
        `--watch-policy` ("the alternative to an") and `--ttl-days`
        ("visible opt-out, so").

        The narrow half matters as much: pronouns and negations DO end
        sentences, and a first cut that failed on them produced five
        false positives against legitimate reasons. A check that fires on
        a valid input is worse than one that misses.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE", "--json"]},
                rows, policy="flag:--json  selects machine output; read-only.\n")
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            # the three real truncations, each in its own shape
            for reason, needle in (
                    ("the reasoning basis, so it is the opposite",
                     "'opposite'"),
                    ("names a reviewed watch set, the alternative to an",
                     "joining word 'an'"),
                    ("the shelf life; a large value is the opt-out, so",
                     "joining word 'so'"),
                    ("a joining word with a full stop after it, so.",
                     "joining word 'so'")):
                self._write_policy(tmp, "flag:--json  %s\n" % reason)
                got = self._wi(inst, tmp)
                self.assertEqual(
                    got.returncode, 1,
                    "an unfinished reason passed: %r -> %s"
                    % (reason, got.stdout))
                self.assertIn("not a finished sentence", got.stdout)
                self.assertIn(needle, got.stdout)

            # ...and the negative controls, which must NOT fire
            for reason in (
                    "selects machine output; read-only.",
                    "the screen that may refuse it is lifted by --x, never by this.",
                    "ADR-013 refuses it, so a refusal acts on it rather than through it.",
                    "it changes where input comes from and nothing about what it does.",
                    "a rendering choice only!",
                    "which transition runs?"):
                self._write_policy(tmp, "flag:--json  %s\n" % reason)
                ok = self._wi(inst, tmp)
                self.assertEqual(
                    ok.returncode, 0,
                    "a finished sentence must be accepted, whatever word "
                    "it ends on: %r -> %s" % (reason, ok.stdout))
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_harvests_flag_shapes_argparse_really_prints(self):
        """The usage line is not a reliable inventory.

        argparse renders required arguments unbracketed, alternation
        groups with `|`, lowercase metavars, digits in names, and wraps
        all of it. A reader that assumes `[--flag METAVAR]` walks past
        every one of those, at exit 0 -- which is a fail-open in the one
        direction this register exists for. The inventory is taken from
        the `options:` section and cross-checked against usage.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]}, rows)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            for shape, needle in (
                    ("--sneaky-ok reason", "--sneaky-ok"),
                    ("--g8-ok", "--g8-ok"),
                    ("--refresh-evidence SENTENCE", "--refresh-evidence"),
                    ("--mandatory-ok SENTENCE", "--mandatory-ok"),
                    ("--choice {a,b}", "--choice")):
                self._write_stub(tmp, ["claim"],
                                 {"claim": ["--scope-ok SENTENCE", shape]})
                got = self._wi(inst, tmp)
                self.assertEqual(
                    got.returncode, 1,
                    "the harvester walked past %r: %s" % (shape, got.stdout))
                self.assertIn(needle, got.stdout)

            # the two renderings of ONE parser disagreeing. argparse never
            # does this, so if this reader sees it, the reader is wrong
            # about at least one rendering -- and a reader quietly wrong
            # about the shape of a flag is how an override goes unlisted.
            self._write_stub(tmp, ["claim"],
                             {"claim": ["--scope-ok SENTENCE"]},
                             usage_only={"claim": ["--ghost-ok"]})
            ghost = self._wi(inst, tmp)
            self.assertEqual(ghost.returncode, 1,
                             "the two renderings disagreed silently: %s"
                             % ghost.stdout)
            self.assertIn("--ghost-ok", ghost.stdout)
            self.assertIn("and not the other", ghost.stdout)

            # one flag, two shapes: a sweep that averaged these would be
            # confidently wrong about what admits the override
            self._write_stub(tmp, ["claim", "verdict"],
                             {"claim": ["--scope-ok SENTENCE"],
                              "verdict": ["--scope-ok"]})
            two = self._wi(inst, tmp)
            self.assertEqual(two.returncode, 1,
                             "a flag with two shapes passed: %s" % two.stdout)
            self.assertIn("one flag, two shapes", two.stdout)

            # a verb whose name carries a digit takes its flags out of
            # scope entirely if the verb regex cannot see it
            self._write_stub(tmp, ["claim", "claim2"],
                             {"claim": ["--scope-ok SENTENCE"],
                              "claim2": ["--evil-ok"]})
            verb = self._wi(inst, tmp)
            self.assertEqual(verb.returncode, 1,
                             "a verb with a digit hid its flags: %s"
                             % verb.stdout)
            self.assertIn("--evil-ok", verb.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_reads_the_table_as_a_block(self):
        """The register's own parser, held to the rule it states.

        A missing trailing pipe renders identically in GFM; a blank line
        ends the table and orphans every row below it. Both used to be
        invisible, and the second produced a message prescribing "add the
        row" for a row that was already there, three lines down.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis"),
                    ("flag", "--duplicate-ok", ["claim"], "nothing", "overridden_duplicates")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"],
                {"claim": ["--scope-ok SENTENCE", "--duplicate-ok"]}, rows)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            reg = os.path.join(tmp, "docs", "waivers.md")
            with open(reg, encoding="utf-8") as f:
                table = f.read()

            # (a) a body row missing its trailing pipe
            with open(reg, "w", encoding="utf-8") as f:
                f.write(table.replace("| no | ADR-000 |\n",
                                      "| no | ADR-000 \n", 1))
            bare = self._wi(inst, tmp)
            self.assertEqual(bare.returncode, 1,
                             "a row missing its trailing pipe passed")
            self.assertIn("is not a row", bare.stdout)

            # (b) the wrong column count
            with open(reg, "w", encoding="utf-8") as f:
                f.write(table.replace("| no | ADR-000 |\n",
                                      "| no | ADR-000 | eighth |\n", 1))
            wide = self._wi(inst, tmp)
            self.assertEqual(wide.returncode, 1)
            self.assertIn("columns, not the eight", wide.stdout)

            # (c) a blank line mid-table orphans the rows below it
            lines = table.splitlines(True)
            cut = max(i for i, l in enumerate(lines)
                      if l.startswith("| flag | `--"))
            with open(reg, "w", encoding="utf-8") as f:
                f.write("".join(lines[:cut]) + "\n" + "".join(lines[cut:]))
            blank = self._wi(inst, tmp)
            self.assertEqual(blank.returncode, 1)
            self.assertIn("silently truncated", blank.stdout)

            # (d) a duplicate row is one waiver with two homes. Inserted
            # INSIDE the block: appended after it, the truncation finding
            # fires first and this would test the wrong thing.
            dup_row = ("| flag | `--scope-ok` | claim | a gate | SENTENCE "
                       "| `scope_basis` | no | ADR-000 |\n")
            with open(reg, "w", encoding="utf-8") as f:
                f.write(table.replace(dup_row, dup_row + dup_row, 1))
            dup = self._wi(inst, tmp)
            self.assertEqual(dup.returncode, 1)
            self.assertIn("two rows", dup.stdout)

            # (e) a first cell with no backticked flag
            with open(reg, "w", encoding="utf-8") as f:
                f.write(table.replace("| flag | `--duplicate-ok` |",
                                      "| flag | duplicate-ok |", 1))
            nof = self._wi(inst, tmp)
            self.assertEqual(nof.returncode, 1)
            self.assertIn("names no backticked flag", nof.stdout)

            # (f) the header not followed by its separator
            with open(reg, "w", encoding="utf-8") as f:
                f.write(table.replace("|---|---|---|---|---|---|---|\n", "", 1))
            nosep = self._wi(inst, tmp)
            self.assertEqual(nosep.returncode, 1)
            self.assertIn("separator", nosep.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_admitted_on_is_a_controlled_vocabulary(self):
        """Substring-matching the column fired on legitimate wording.

        `bare = "nothing" in cell.lower()` read `SENTENCE, never nothing`
        as bare. A check that fires on a legitimate input is worse than
        one that misses, so the column is exactly `SENTENCE` or
        `nothing` and anything else is its own finding.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            rows = [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis")]
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]}, rows)
            self.assertEqual(self._wi(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            self._write_register(
                tmp, [("flag", "--scope-ok", ["claim"], "SENTENCE, never nothing", "scope_basis")])
            prose = self._wi(inst, tmp)
            self.assertEqual(prose.returncode, 1)
            self.assertIn("must be exactly", prose.stdout)
            self.assertNotIn("the parser says", prose.stdout,
                             "prose in the column must be refused as prose, "
                             "not compared against the parser")
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_population_says_when_it_cannot_measure(self):
        """A stamp column with no field, and a ledger that is not there.

        `--single-run` writes NO field, so its population is not zero --
        it is unavailable, and printing 0 would read as "never used". A
        missing ledger is the same shape one level up.
        """
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            inst = self._mini_waiver_tree(
                tmp, ["claim"],
                {"claim": ["--scope-ok SENTENCE", "--single-run"]},
                [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis"),
                 ("flag", "--single-run", ["claim"], "nothing", "")],
                ledger=[{"id": "tr-1", "kind": "claim",
                         "payload": {"scope_basis": "because"}}])
            out = self._wi(inst, tmp)
            self.assertEqual(out.returncode, 0,
                             "a control tree with nothing seeded must pass: "
                             "%s%s" % (out.stdout, out.stderr))
            self.assertIn("NOT COUNTABLE", out.stdout)
            self.assertIn("--single-run", out.stdout)

            os.remove(os.path.join(tmp, ".truth", "claims.jsonl"))
            gone = self._wi(inst, tmp)
            self.assertIn("population unknown", gone.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_waiver_index_usage_guards(self):
        """Exit 2 is usage, and is not to be confused with a finding."""
        tmp = tempfile.mkdtemp(prefix="waiver-index-")
        try:
            inst = self._mini_waiver_tree(
                tmp, ["claim"], {"claim": ["--scope-ok SENTENCE"]},
                [("flag", "--scope-ok", ["claim"], "SENTENCE", "scope_basis")])
            bad = subprocess.run([sys.executable, inst, "--nope"], cwd=tmp,
                                 capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertIn("unknown argument", bad.stderr)

            os.remove(os.path.join(tmp, "docs", "waivers.md"))
            missing = self._wi(inst, tmp)
            self.assertEqual(missing.returncode, 2)
            self.assertIn("not found", missing.stderr)
        finally:
            shutil.rmtree(tmp)

    def test_register_index_refuses_an_index_broader_than_its_register(self):
        """A register may declare it does not cover its whole subject. The
        index row describing it must carry the same declaration.

        Otherwise the index is BROADER than the thing it indexes, and a
        reader who never opens the register takes the row's description as
        the whole of it -- which is the mis-scoped partition this
        repository keeps finding, one level up. It was found here: the
        waiver register limited itself honestly in its own text while
        `docs/registers.md` still said "every gate that can be lifted".

        Both directions. A limit stated only in the INDEX is a promise the
        register never made, and the register is where a reader ends up.
        """
        tmp = tempfile.mkdtemp(prefix="register-index-")
        try:
            inst = self._mini_register_tree(
                tmp, ["002-b.md"], ["001-a.md"], "ADR-001 ADR-002\n")
            index = os.path.join(tmp, "docs", "registers.md")
            with open(index, encoding="utf-8") as f:
                table = f.read()
            self.assertEqual(self._ri(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            # the register self-limits; the row does not acknowledge it
            with open(os.path.join(tmp, "docs", "roadmap-v3.md"), "a") as f:
                f.write("\nTHIS REGISTER IS NOT TOTAL.\n")
            broad = self._ri(inst, tmp)
            self.assertEqual(broad.returncode, 1,
                             "an index row outran its register: %s"
                             % broad.stdout)
            self.assertIn("BROADER than the thing it indexes", broad.stdout)

            # acknowledging it in the row clears it
            with open(index, "w", encoding="utf-8") as f:
                f.write(table.replace("| roadmap | the plan |",
                                      "| roadmap | the plan, NOT TOTAL |", 1))
            self.assertEqual(self._ri(inst, tmp).returncode, 0,
                             "an index row that acknowledges the register's own limit "
                             "must pass")

            # ...and the reverse: a limit only the index claims
            with open(os.path.join(tmp, "docs", "roadmap-v3.md"), "w") as f:
                f.write("ADR-001 ADR-002\n")
            promise = self._ri(inst, tmp)
            self.assertEqual(promise.returncode, 1)
            self.assertIn("promise the register never made", promise.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_register_index_reads_the_index_as_a_block_not_a_filter(self):
        """One deleted trailing pipe used to un-administer a register.

        GFM renders a body row without its trailing pipe identically, so
        the index looks unchanged to a reader and to doc-health's link
        check. The old parser skipped the line, and a skipped row is
        invisible by construction: nothing distinguishes "rejected" from
        "never there". The only trace was a register count that no arm
        asserted. Registers whose location is outside docs/ went fully
        dark, because the coverage check never sees them.
        """
        tmp = tempfile.mkdtemp(prefix="register-index-")
        try:
            inst = self._mini_register_tree(
                tmp, ["002-b.md"], ["001-a.md"], "ADR-001 ADR-002\n")
            clean = self._ri(inst, tmp)
            self.assertEqual(clean.returncode, 0,
                             "a control tree with nothing seeded must pass: "
                             "%s%s" % (clean.stdout, clean.stderr))
            before = clean.stdout.count("OK   ")

            index = os.path.join(tmp, "docs", "registers.md")
            with open(index, encoding="utf-8") as f:
                table = f.read()

            # (a) a body row missing its trailing pipe
            with open(index, "w", encoding="utf-8") as f:
                f.write(table.replace(
                    "| roadmap | the plan | `docs/roadmap-v3.md` | live | "
                    "`instruments/register-index.py` check (b) |",
                    "| roadmap | the plan | `docs/roadmap-v3.md` | live | "
                    "`instruments/register-index.py` check (b)", 1))
            bare = self._ri(inst, tmp)
            self.assertEqual(bare.returncode, 1,
                             "a row missing its trailing pipe passed: %s"
                             % bare.stdout)
            self.assertIn("is not a row", bare.stdout)
            self.assertLess(bare.stdout.count("OK   "), before,
                            "the register really did leave the sweep")

            # (b) the wrong column count, which the old parser did catch --
            # kept so the block rewrite cannot have lost it
            with open(index, "w", encoding="utf-8") as f:
                f.write(table.replace("| live | `instruments/register-index.py` "
                                      "check (b) |",
                                      "| live | `instruments/register-index.py` "
                                      "check (b) | sixth |", 1))
            wide = self._ri(inst, tmp)
            self.assertEqual(wide.returncode, 1)
            self.assertIn("columns, not the five", wide.stdout)

            # (c) a stray non-row line inside the block
            with open(index, "w", encoding="utf-8") as f:
                f.write(table.replace("| roadmap |", "stray text\n| roadmap |", 1))
            stray = self._ri(inst, tmp)
            self.assertEqual(stray.returncode, 1)
            self.assertIn("is not a row", stray.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_register_index_coverage_runs_in_both_directions(self):
        """Check (c): the reverse sweep the instrument was built for.

        Forward: a live doc under docs/ that no register's location
        contains. Reverse: a baseline entry whose finding has gone, and a
        baseline entry whose SUBJECT has gone -- the second used to be
        reported as the first, whose remedy deletes a real finding.
        """
        tmp = tempfile.mkdtemp(prefix="register-index-")
        try:
            inst = self._mini_register_tree(
                tmp, ["002-b.md"], ["001-a.md"], "ADR-001 ADR-002\n")
            self.assertEqual(self._ri(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            stray = os.path.join(tmp, "docs", "loose-note.md")
            with open(stray, "w") as f:
                f.write("# covered by nothing\n")
            fwd = self._ri(inst, tmp)
            self.assertEqual(fwd.returncode, 1)
            self.assertIn("docs/loose-note.md is covered by no register",
                          fwd.stdout)

            base = os.path.join(tmp, ".truth", "register-index-baseline")
            with open(base, "w") as f:
                f.write("docs/loose-note.md  baseline 2026-01-01, "
                        "unresolved: probe\n")
            self.assertEqual(self._ri(inst, tmp).returncode, 0,
                             "a baselined path must be excused, or the baseline excuses "
                             "nothing")

            # reverse (i): it is covered now, so the entry outlived its
            # finding
            os.remove(stray)
            os.makedirs(os.path.join(tmp, "docs", "notes"))
            with open(os.path.join(tmp, "docs", "notes", "x.md"), "w") as f:
                f.write("# x\n")
            with open(base, "w") as f:
                f.write("docs/notes/x.md  baseline 2026-01-01, "
                        "unresolved: probe\n")
            index = os.path.join(tmp, "docs", "registers.md")
            with open(index, encoding="utf-8") as f:
                table = f.read()
            with open(index, "w", encoding="utf-8") as f:
                f.write(table.replace("`docs/registers.md`",
                                      "`docs/registers.md` and `docs/notes`", 1))
            resolved = self._ri(inst, tmp)
            self.assertEqual(resolved.returncode, 1)
            self.assertIn("no longer uncovered", resolved.stdout)

            # reverse (ii): the subject itself is gone -- a different
            # message, because the remedy is different
            with open(index, "w", encoding="utf-8") as f:
                f.write(table)
            os.remove(os.path.join(tmp, "docs", "notes", "x.md"))
            gone = self._ri(inst, tmp)
            self.assertEqual(gone.returncode, 1)
            self.assertIn("no longer exists", gone.stdout)
            self.assertNotIn("no longer uncovered", gone.stdout,
                             "a path whose SUBJECT is gone must not be "
                             "reported as newly covered")

            # ADR-042 rule 2: zero docs to judge is not a pass
            shutil.rmtree(os.path.join(tmp, "docs", "notes"))
            for leftover in ("registers.md", "roadmap-v3.md"):
                os.rename(os.path.join(tmp, "docs", leftover),
                          os.path.join(tmp, leftover))
            empty = self._ri(inst, tmp)
            self.assertEqual(empty.returncode, 2,
                             "with the index moved away this is a usage "
                             "error, not a silent pass")
        finally:
            shutil.rmtree(tmp)

    def test_register_index_sweeps_the_currency_column(self):
        """Column five is the file's stated reason to exist.

        A dead path there is a register whose decay nothing reports. An
        EMPTY cell is a failure. A cell full of prose naming no path is
        NOT a failure -- one real register measures currency by a review
        date -- but it must be counted and NAMED, or it is
        indistinguishable from a row whose paths were all checked.
        """
        tmp = tempfile.mkdtemp(prefix="register-index-")
        try:
            inst = self._mini_register_tree(
                tmp, ["002-b.md"], ["001-a.md"], "ADR-001 ADR-002\n")
            clean = self._ri(inst, tmp)
            self.assertEqual(clean.returncode, 0,
                             "a control tree with nothing seeded must pass: "
                             "%s%s" % (clean.stdout, clean.stderr))
            self.assertIn("path(s) checked across", clean.stdout)
            self.assertIn("0 row(s) name no checkable path", clean.stdout)

            index = os.path.join(tmp, "docs", "registers.md")
            with open(index, encoding="utf-8") as f:
                table = f.read()

            with open(index, "w", encoding="utf-8") as f:
                f.write(table.replace("`instruments/register-index.py` check (b) |",
                                      "`instruments/gone-forever.py` check (b) |", 1))
            dead = self._ri(inst, tmp)
            self.assertEqual(dead.returncode, 1)
            self.assertIn("currency evidence names", dead.stdout)

            with open(index, "w", encoding="utf-8") as f:
                f.write(table.replace("| `instruments/register-index.py` check (b) |",
                                      "|  |", 1))
            blank = self._ri(inst, tmp)
            self.assertEqual(blank.returncode, 1)
            self.assertIn("currency evidence cell is empty", blank.stdout)

            # prose with no path: not a failure, but it must be NAMED
            with open(index, "w", encoding="utf-8") as f:
                f.write(table.replace("| `instruments/register-index.py` check (b) |",
                                      "| a monthly hand-audit, by eye |", 1))
            prose = self._ri(inst, tmp)
            self.assertEqual(prose.returncode, 0,
                             "a prose-only currency cell must not fail")
            self.assertIn("1 row(s) name no checkable path", prose.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_register_index_baseline_entries_must_carry_a_reason(self):
        """A bare key excuses a finding while recording nothing about why.

        And `--record-baseline` must preserve each entry's FIRST-SEEN
        date: restamping every line with today would erase the one thing
        this file measures about itself, inside the mechanism built to
        stop staleness.
        """
        tmp = tempfile.mkdtemp(prefix="register-index-")
        try:
            inst = self._mini_register_tree(
                tmp, ["002-b.md"], ["001-a.md"], "ADR-001\n",
                baseline=("adr-unaccounted:ADR-002  baseline 2026-01-01, "
                          "unresolved: probe\n"))
            self.assertEqual(self._ri(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            base = os.path.join(tmp, ".truth", "register-index-baseline")
            with open(base, "w") as f:
                f.write("adr-unaccounted:ADR-002\n")
            bare = self._ri(inst, tmp)
            self.assertEqual(bare.returncode, 1)
            self.assertIn("with no reason", bare.stdout)

            with open(base, "w") as f:
                f.write("adr-unaccounted:ADR-002  baseline 2026-01-01, "
                        "unresolved: probe\n")
            rec = subprocess.run([sys.executable, inst, "--record-baseline"],
                                 cwd=tmp, capture_output=True, text=True)
            self.assertEqual(rec.returncode, 0,
                             "recording a baseline over a read corpus must "
                             "succeed: %s" % rec.stderr)
            with open(base) as f:
                written = f.read()
            self.assertIn("baseline 2026-01-01", written,
                          "--record-baseline restamped a first-seen date")
            self.assertIn("first seen 2026-01-01", rec.stdout,
                          "--record-baseline did not print the key it recorded")
        finally:
            shutil.rmtree(tmp)

    def test_register_index_refuses_to_record_a_reading_it_did_not_take(self):
        """`--record-baseline` must not bless a corpus it never read.

        With an ADR directory absent the measure is SUSPENDED, so the
        unaccounted/phantom/gap sets are empty because nothing was
        measured -- and writing them DELETED the real backlog and its
        first-seen dates at exit 0, while the ordinary sweep was refusing
        to so much as report the same reading.
        """
        tmp = tempfile.mkdtemp(prefix="register-index-")
        try:
            inst = self._mini_register_tree(
                tmp, ["002-b.md"], ["001-a.md"], "ADR-001\n",
                baseline=("adr-unaccounted:ADR-002  baseline 2026-01-01, "
                          "unresolved: probe\n"))
            base = os.path.join(tmp, ".truth", "register-index-baseline")
            with open(base) as f:
                before = f.read()

            shutil.rmtree(os.path.join(tmp, "docs", "archive", "adr"))
            suspended = self._ri(inst, tmp)
            self.assertEqual(suspended.returncode, 1)
            self.assertIn("SUSPENDED", suspended.stdout)

            rec = subprocess.run([sys.executable, inst, "--record-baseline"],
                                 cwd=tmp, capture_output=True, text=True)
            self.assertEqual(rec.returncode, 8,
                             "--record-baseline recorded a suspended reading")
            self.assertIn("refusing to record", rec.stderr)
            with open(base) as f:
                self.assertEqual(before, f.read(),
                                 "the backlog was overwritten anyway")
        finally:
            shutil.rmtree(tmp)

    def test_register_index_fails_loudly_on_a_missing_or_unreadable_input(self):
        """ADR-042 rule 2 and the environment/ governance split.

        A sweep that read nothing has not passed (exit 8), and an input it
        could not read is an ENVIRONMENT failure with its own code (exit
        3) -- never a traceback, and never counted as a finding.
        """
        tmp = tempfile.mkdtemp(prefix="register-index-")
        try:
            inst = self._mini_register_tree(
                tmp, ["002-b.md"], ["001-a.md"], "ADR-001 ADR-002\n")
            self.assertEqual(self._ri(inst, tmp).returncode, 0,
                                         "a control tree with nothing seeded must pass, or nothing the probes below prove is about the seeded defect")

            index = os.path.join(tmp, "docs", "registers.md")
            # A row whose location is not backticked yields no location.
            # It used to print OK -- a register un-administered in silence.
            with open(index, encoding="utf-8") as f:
                table = f.read()
            with open(index, "w", encoding="utf-8") as f:
                f.write(table.replace("| `docs/roadmap-v3.md` |",
                                      "| docs/roadmap-v3.md |", 1))
            bare = self._ri(inst, tmp)
            self.assertEqual(bare.returncode, 1)
            self.assertIn("names no location this sweep can read", bare.stdout)
            self.assertIn("FAIL  roadmap", bare.stdout)

            # An absolute location: check (a) was satisfiable by any path
            # on the machine.
            with open(index, "w", encoding="utf-8") as f:
                f.write(table.replace("`docs/roadmap-v3.md`",
                                      "`/etc/passwd`", 1))
            absolute = self._ri(inst, tmp)
            self.assertEqual(absolute.returncode, 1)
            self.assertIn("is an absolute path", absolute.stdout)

            # ...and the other half of the same refusal, which had no arm:
            # a relative path that walks OUT of the repository.
            with open(index, "w", encoding="utf-8") as f:
                f.write(table.replace("`docs/roadmap-v3.md`",
                                      "`../roadmap-v3.md`", 1))
            escape = self._ri(inst, tmp)
            self.assertEqual(escape.returncode, 1)
            self.assertIn("escapes the repository", escape.stdout)

            # ADR-042 rule 2: no readable rows at all.
            with open(index, "w", encoding="utf-8") as f:
                f.write("# no table here\n")
            empty = self._ri(inst, tmp)
            self.assertEqual(empty.returncode, 8)
            self.assertIn("read ZERO register rows", empty.stderr)

            # --record-baseline must not bless a corpus it never read.
            before = open(os.path.join(tmp, ".truth",
                                       "register-index-baseline")).read()
            rec = subprocess.run([sys.executable, inst, "--record-baseline"],
                                 cwd=tmp, capture_output=True, text=True)
            self.assertEqual(rec.returncode, 8)
            self.assertEqual(
                before,
                open(os.path.join(tmp, ".truth",
                                  "register-index-baseline")).read(),
                "--record-baseline rewrote the baseline after reading zero "
                "registers")

            # Unreadable input: a directory where a file belongs. Chosen
            # over chmod 000 because a privileged runner can read that.
            os.remove(index)
            os.makedirs(index)
            unreadable = self._ri(inst, tmp)
            self.assertEqual(unreadable.returncode, 3)
            self.assertIn("the sweep did NOT run", unreadable.stderr)
            self.assertNotIn("Traceback", unreadable.stderr,
                             "an environment failure must be a sentence, "
                             "never a stack trace")
        finally:
            shutil.rmtree(tmp)


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
        # Step 2.5/2.6: `stale` is reachable ONLY through TTL expiry, and
        # ADR-057 makes that expiry a READ-TIME derivation -- so backdating
        # the claim past its ttl_days is the whole fixture. The
        # `run_truth("ttl-scan")` line that used to follow is gone: the
        # verb no longer exists, and because nothing asserted its exit code
        # it kept "passing" as a silent argparse failure while the read-time
        # clock did the real work. A call nobody checks is not a step.
        res = self.sb.run_truth("claim", "stale.txt says original", "--class", "VERIFIED",
                                "--evidence-cmd", "cat stale.txt", "--paths", "stale.txt", "--tier", "P1",
                                "--ttl-days", "1", env={"TRUTH_NOW": "2026-06-01T00:00:00+00:00"})
        cid_stale = res.stdout.strip()
        self.sb.run_truth("verdict", cid_stale, "agree", "--basis", "verified", env={"TRUTH_SESSION": "s-v1"})
        self.sb.write_file("stale.txt", "modified\n")
        self.sb.git_commit("modify stale")

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
