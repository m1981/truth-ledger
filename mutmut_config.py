"""mutmut_config.py -- per-mutant test selection for mutmut 2.x.

WHY THIS FILE EXISTS

`--use-coverage` alone does NOT make mutmut 2 run fewer tests. Read
mutmut/__init__.py:470-488: coverage data is consulted by should_exclude(),
which decides which LINES are worth mutating. The runner command itself is
untouched, so every surviving mutant still pays the full 9.7s suite. On
kernel.py that is hours.

mutmut 2's actual hook for this is pre_mutation(context), which may rewrite
context.config.test_command before the mutant runs (mutmut/__init__.py:773).
Combined with coverage's dynamic_context="test_function", we can look up
exactly which tests executed the mutated line and run only those:
kernel.py averages 8.1 tests per covered line out of 394, and one test costs
~0.24s against ~9.7s for the suite.

WHY THE SELECTION IS SOUND

Line-level coverage is exact: a test that never executes the mutated line
cannot observe the mutation, so excluding it cannot turn a killed mutant into
a survivor. The one case that would break this is a line executed at IMPORT
time -- it runs outside any test, coverage files it under the empty context,
and naively filtering empties would silently skip module-level mutants
(constants, compiled regexes). That case falls back to the full suite instead.

test_command is assigned on EVERY call, never left from the previous mutant --
mutmut keeps one Config object for the whole run, so a stale narrow command
would under-test everything after the first selection.

THE TIMEOUT HAS TO MOVE WITH THE SELECTION

mutmut kills a hung mutant at baseline_time_elapsed * 10
(mutmut/__init__.py:865), and baseline_time_elapsed is measured once, on the
FULL suite. Leave it alone and every infinite-loop mutant costs 97s -- against
~0.25s for a normal selected run, that is ~400x, and a handful of them
dominates the whole run. Measured: kernel.py sat on a single looping mutant for
over a minute. So baseline_time_elapsed is rescaled per selection too, with a
2s floor (=20s kill) so that git-sandbox tests in a wide selection are not
falsely timed out, and never above the real full-suite baseline.

Regenerate .coverage with scripts/mutmut-coverage.sh after touching the suite.
A stale file under-selects, and an under-selected mutant reads as "survived".
"""
import os

_REPO = os.path.dirname(os.path.abspath(__file__))
_RUNNER = "scripts/mutmut-runner.sh"
_contexts_cache = None


def _contexts_by_file():
    """{abs source path: {lineno: [test context, ...]}} from .coverage."""
    global _contexts_cache
    if _contexts_cache is None:
        from coverage import Coverage

        cov = Coverage(os.path.join(_REPO, ".coverage"))
        cov.load()
        data = cov.get_data()
        _contexts_cache = {
            os.path.abspath(f): data.contexts_by_lineno(f)
            for f in data.measured_files()
        }
    return _contexts_cache


def _test_ids(contexts):
    """coverage labels tests '__main__.TestFoo.test_bar' (the suite runs as a
    script, so its module is __main__); unittest wants 'TestFoo.test_bar'.
    Some coverage versions append '|run'/'|setup' -- strip that too."""
    ids = set()
    for ctx in contexts:
        if not ctx:
            continue
        name = ctx.split("|")[0]
        if name.startswith("__main__."):
            name = name[len("__main__."):]
        ids.add(name)
    return sorted(ids)


_full_baseline = None


def _restore_full(config):
    config.test_command = config._default_test_command
    config.baseline_time_elapsed = _full_baseline


def pre_mutation(context):
    global _full_baseline
    config = context.config
    if _full_baseline is None:  # measured once, on the full suite
        _full_baseline = config.baseline_time_elapsed

    per_file = _contexts_by_file().get(os.path.abspath(context.filename))
    if per_file is None:  # file absent from .coverage -- do not guess
        _restore_full(config)
        return

    contexts = per_file.get(context.current_line_index + 1)
    if contexts is None:  # no test executes this line at all
        context.skip = True
        return

    ids = _test_ids(contexts)
    if not ids:  # executed only at import time; no owning test
        _restore_full(config)
        return

    config.test_command = _RUNNER + " " + " ".join(ids)
    config.baseline_time_elapsed = min(_full_baseline,
                                       max(2.0, 0.05 * len(ids)))
