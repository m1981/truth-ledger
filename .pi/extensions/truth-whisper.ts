/**
 * Pre-edit whisper (ADR-005, consumer-side half) — pi port of
 * scripts/truth-whisper.py. META-REPO ONLY; harness wiring is consumer
 * policy (ADR-003 rule 2). Same two stages, same failure policies:
 *   deny stage, fails CLOSED  — tool_call blocked on paths matching
 *                               scripts/truth-whisper.deny.
 *   whisper stage, fails OPEN — visibly: `truth impact` exit 3 appends
 *                               the prediction to the edit tool's
 *                               result; errors print one stderr line.
 * Fatigue budget: first-touch-per-session dedup on (session, file,
 * ledger hash); appends to .git/truth-whisper.seen (the ADR-005
 * adoption-gate metric, shared with the Claude Code hook).
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { appendFileSync, readFileSync, realpathSync } from "node:fs";
import { join, relative, resolve } from "node:path";

const EDIT_TOOLS = new Set(["edit", "write", "multi-edit", "multiedit"]);

function realpathSafe(p: string): string {
	try {
		return realpathSync(p);
	} catch {
		return p;
	}
}

function repoRoot(): string | null {
	const r = spawnSync("git", ["rev-parse", "--show-toplevel"], { encoding: "utf8" });
	// realpath the root: git returns a symlink-resolved path, so relPath
	// must compare against the same canonical space (see relPath).
	return r.status === 0 && r.stdout.trim() ? realpathSafe(r.stdout.trim()) : null;
}

function relPath(event: any, root: string): string | null {
	const input = event.input ?? event.args ?? {};
	const fp = input.path ?? input.file_path;
	if (!fp) return null;
	// realpath BOTH sides: a symlinked path component must not make an
	// in-repo file look external -- that would skip the deny stage, and
	// deny must fail CLOSED (parity with the Python hook).
	const rel = relative(root, realpathSafe(resolve(process.cwd(), fp)));
	return rel.startsWith("..") ? null : rel;
}

export default function (pi: ExtensionAPI) {
	// One id per extension instance = per pi session (metric parity with
	// the Claude Code hook's session_id).
	const sid = `pi-${Date.now().toString(36)}`;
	const seen = new Set<string>();

	// ---- deny stage: fails closed on listed patterns --------------------
	pi.on("tool_call", async (event: any) => {
		if (!EDIT_TOOLS.has(event.toolName)) return;
		const root = repoRoot();
		if (!root) return;
		const rel = relPath(event, root);
		if (!rel) return;
		let patterns: string[] = [];
		try {
			patterns = readFileSync(join(root, "scripts", "truth-whisper.deny"), "utf8")
				.split("\n")
				.map((l) => l.trim())
				.filter((l) => l && !l.startsWith("#"));
		} catch {
			return; // no deny file -> no deny stage (same as the py hook)
		}
		for (const pat of patterns) {
			let rx: RegExp;
			try {
				rx = new RegExp(`^(?:${pat})`); // parity with Python re.match
			} catch {
				continue;
			}
			if (rx.test(rel)) {
				return {
					block: true,
					reason:
						`${rel} is deny-listed (${pat}): frozen, or append-only ` +
						"through the truth CLI, by policy (see AGENTS.md). A human " +
						"must deliberately lift the freeze before an edit here can " +
						"land -- that is not a step for you to take. Record status " +
						"changes as new ledger entries via `truth`, never by editing files.",
				};
			}
		}
	});

	// ---- whisper stage: fails open, visibly ------------------------------
	pi.on("tool_result", async (event: any) => {
		if (!EDIT_TOOLS.has(event.toolName) || event.isError) return;
		const root = repoRoot();
		if (!root) return;
		const rel = relPath(event, root);
		if (!rel) return;
		let r: ReturnType<typeof spawnSync>;
		try {
			r = spawnSync("python3", [join(root, "scripts", "truth"), "impact", rel], {
				encoding: "utf8",
				cwd: root,
				timeout: 15000,
			});
		} catch (e) {
			console.error(`truth impact unavailable: ${e}`);
			return;
		}
		const stdout = String(r.stdout ?? "").trim();
		if (r.status === 3 && stdout) {
			let lh = "noledger";
			try {
				lh = createHash("sha256")
					.update(readFileSync(join(root, ".truth", "claims.jsonl")))
					.digest("hex")
					.slice(0, 12);
			} catch {}
			const key = `${sid}:${rel}:${lh}`;
			if (seen.has(key)) return; // fatigue budget: already whispered this state
			seen.add(key);
			try {
				appendFileSync(join(root, ".git", "truth-whisper.seen"), key + "\n");
			} catch {}
			return {
				content: [
					...(event.content ?? []),
					{
						type: "text",
						text:
							"\ntruth-ledger whisper (mechanical prediction, not judgment):\n" +
							stdout,
					},
				],
			};
		}
		if (r.status !== 0 && r.status !== 3) {
			console.error(
				`truth impact unavailable (exit ${r.status}): ` +
					String(r.stderr ?? "").trim().slice(0, 200),
			);
		}
	});
}
