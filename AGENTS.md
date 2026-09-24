# PyRPL fork agent guidance

## Notebook version control (2026-09-24)

- The user explicitly requested version control for `test.ipynb` across all
  fork branches. Keep it unignored and commit the branch's own notebook;
  where none is tracked, use that branch's template if one exists. Do not
  copy another device/OS branch's notebook into it.
- Preserve notebook settings, measurements and saved outputs. Do not reset,
  sanitize, replace or execute a notebook without a specific user request.
  Tracking a notebook does not authorize contacting or programming hardware.
- Keep any `test.ipynb.template` as a clean starter. Never overwrite an
  existing working notebook when updating a template or switching branches.
- This request supersedes older ignored/local-only and never-stage notebook
  guidance below. Other workers' working directories remain untouched.

## Common-policy comparison

- At the start of each new agent/thread working on this repository, and
  after a clone, fetch or pull, compare the common AGENTS.md policies across
  all available local branches and remote-tracking branches before making
  changes. Repeat after branch/worktree switches or common-policy edits.
- Enumerate refs with `git for-each-ref refs/heads refs/remotes` and read
  instruction files with `git show <ref>:AGENTS.md`, without checking out
  other branches. Deduplicate identical file blobs; inspect referenced
  common-policy files too if the guidance has been split. Include the
  current checkout's uncommitted instructions without discarding them.
- This check covers locally available refs, not unseen remote branches.
  Do not fetch/pull merely to perform it. Note missing instructions or
  limited/shallow history when relevant; absence is not permission to
  ignore known user policies. Keep the check lightweight: no test suites
  and no repeated full scan each turn unless refs or policies changed.
- Before an agent switches branches, record the source branch/commit and any
  uncommitted instruction changes. After switching, reread the destination's
  AGENTS.md and compare its common policies with the source; use read-only
  Git diffs rather than switching other worktrees to inspect them.
- When starting work in another existing worktree, compare common policies
  with the previously used checkout when known. After editing common policy,
  identify which active compatibility branches still need that update.
- Compare shared workflow rules only (permissions, worktree management,
  branching, notebook preservation and validation proportionality). Preserve
  device/OS-specific instructions, FPGA constraints and validation evidence.
  A later timestamp or commit alone does not establish which policy is right.
- Report missing or conflicting common rules and reconcile them in the
  current task's authorized scope. Do not overwrite entire AGENTS.md files,
  modify another worker's files, or automatically commit/update all branches.
  Cross-branch propagation and hook installation require explicit approval.
  This is an agent workflow rule, not an installed Git hook.

