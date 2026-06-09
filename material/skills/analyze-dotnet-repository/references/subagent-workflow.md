# Subagent Workflow

Use subagents when available to reduce context pressure and isolate analysis. Every subagent must be read-only and must not run build, restore, tests, containers, services, migrations, or repository scripts.

## Coordination rules

- Give each subagent the repository path, the static-analysis constraint, and one narrow scope.
- Ask for compact Markdown or JSON-like bullets, not a full report.
- Require evidence for every finding: file path, setting, pattern, or metric.
- Ask each subagent to include limitations and confidence.
- The main agent owns final synthesis, deduplication, severity calibration, and user-facing recommendations.
- Do not merge findings that lack evidence unless clearly marked as hypotheses.

## Shared return format

```md
## Scope

- Area:
- Execution role:
- Subagent status: used / failed / not applicable
- Files/inputs inspected:
- Limits:

## Key Signals

- 

## Findings

### Finding title

- Evidence:
- Impact:
- Recommendation:
- Priority:
- Effort:
- Confidence:

## Open Questions / Caveats

- 
```

## Inventory agent prompt

```text
Use the analyze-dotnet-repository skill at <skill-path> to inspect <repo-root> in read-only mode.

Scope: technical inventory only. Run scripts/static_inventory.py if useful. Do not run dotnet, build, restore, tests, containers, services, migrations, package managers, or repository scripts.

Return compact findings covering solutions, projects, languages, target frameworks, SDK-style vs legacy projects, VB.NET indicators, dependency metadata, test project signals, CI/CD files, Docker/config/docs signals, and notable inventory risks. Include evidence paths and limitations.

In the Scope section, set Execution role to "Inventory agent" and Subagent status to "used".
```

## Git activity agent prompt

```text
Use the analyze-dotnet-repository skill at <skill-path> to inspect Git history for <repo-root> in read-only mode.

Scope: Git activity only. Run scripts/git_activity.py if available. Do not run dotnet, build, restore, tests, containers, services, migrations, package managers, checkout, reset, clean, or repository scripts.

Return compact findings covering file hotspots, area hotspots, churn, knowledge silos by file/area, noisy hotspot caveats, and intersections with legacy/config/security-sensitive files. Include command limits, evidence metrics, recommendations, and confidence. Frame contributor concentration as maintainability and bus-factor risk, not blame.

In the Scope section, set Execution role to "Git activity agent" and Subagent status to "used". Include git_activity.py parameters used.
```

## Architecture and quality agent prompt

```text
Use the analyze-dotnet-repository skill at <skill-path> to inspect <repo-root> in read-only mode.

Scope: architecture and code quality. Do not run dotnet, build, restore, tests, containers, services, migrations, package managers, or repository scripts.

Return compact findings covering project reference direction, layering, large files/classes, business logic in UI/controllers/code-behind, C# async/code-quality smells, VB.NET legacy patterns such as Option Strict Off, On Error Resume Next, modules/global state, WinForms/WebForms code-behind, and generated-file caveats. Include evidence paths and recommendations.

In the Scope section, set Execution role to "Architecture and quality agent" and Subagent status to "used".
```

## Security and configuration agent prompt

```text
Use the analyze-dotnet-repository skill at <skill-path> to inspect <repo-root> in read-only mode.

Scope: security and configuration. Do not run dotnet, build, restore, tests, containers, services, migrations, package managers, or repository scripts.

Return compact findings covering possible secrets, connection strings, appsettings/web.config/app.config risks, CORS, auth/authz signals, SQL/path/command/deserialization patterns, logging of sensitive data, Docker/pipeline secret risks, and legacy framework security concerns. Do not claim confirmed vulnerabilities unless directly evidenced. Include evidence paths, recommendations, priority, effort, and confidence.

In the Scope section, set Execution role to "Security and configuration agent" and Subagent status to "used".
```

## Report synthesis guidance

The main agent should:

- Combine subagent outputs into `report-template.md`.
- Resolve duplicates by keeping the strongest evidence.
- Escalate priority when Git hotspots overlap with security, legacy, large files, weak tests, or core architecture.
- Downgrade findings based only on naming heuristics or sparse evidence.
- Include a short limitations section with subagent scopes and command limits.
- Fill the report `Execution Metadata` section from observed subagent calls and returned Scope blocks.
- If no subagents were actually called, mark execution mode as `Sequential` and provide the fallback reason.
