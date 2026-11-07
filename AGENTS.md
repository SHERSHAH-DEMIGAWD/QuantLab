# QuantLab session rules

These rules apply to the entire repository. The user's current authorization
controls what may be implemented.

Before changing the project, read:

1. `docs/PROJECT_CHARTER.md`
2. `docs/ROADMAP.md`
3. `docs/PROJECT_STATUS.md`
4. `docs/DECISIONS.md`
5. The latest report in `docs/session-reports/`.

- Implement only the explicitly authorized phase or continuation. A roadmap
  entry or a proposed next task is not authorization. Stop after that phase.
- Phase 0 contains documentation and empty directory placeholders only.
- Keep the core independent of HTTP, persistence, and presentation. Prefer
  small functions and explicit data structures over speculative frameworks.
- Keep one instrument, daily bars, integer shares, long-only, and no leverage.
- Never silently change timing, sizing, costs, adjustment policy, or metrics.
  Review the applicable proposed decisions before implementing them.
- Validate external input; never silently drop or repair invalid market rows.
- Use deterministic fixtures and independent reference calculations. Report
  only verification actually executed; distinguish proposals from working code.
- Require explicit approval for major scope or architecture changes. Record the
  problem, benefits, complexity, dependencies, and roadmap impact first.
- Do not add providers, services, strategies, or infrastructure outside scope.
- Keep documentation concise and assign each fact one primary home.
- End every development session with the next sequential `SESSION_NN_PHASE_N.md`
  report, including all A-L sections specified in the charter. Update status,
  decisions, and roadmap as necessary. Mark unfinished work PARTIAL or BLOCKED.
- Identify learning topics, one or two functions to recreate once code exists,
  five technical questions, three finance questions when applicable, and one
  independent exercise. Do not attribute AI-assisted work to independent work.

Consult project status and the latest explicit user instruction for phase
authorization at the beginning of each session. Planned work is not permission.
