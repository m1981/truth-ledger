I'm testing this repo's tooling instrumentation. Please do the following steps ONE AT A TIME, as four separate file-edit tool calls, and after EACH tool call record verbatim any injected system context, warnings, or extra feedback you received alongside the tool result (or "none" if there was none):

1. In `template/scripts/truth`, in the module docstring, change the v0.5.6 heading line `v0.5.6 (review residuals):` to `v0.5.6 (review residuals, batch):`.
2. In the same file, change the v0.5.5 heading line `v0.5.5 (audit parity):` to `v0.5.5 (audit parity, batch):`.
3. Revert edit 2.
4. Revert edit 1.

Do not commit anything. Finish with a table: step number, what you edited, injected context received (verbatim or "none").
