---
name: analyze-dotnet-repository
description: Static repository and Git-history analysis for modern and legacy .NET codebases. Use when Codex needs to inspect a Git folder or source tree containing C#, VB.NET, .NET Framework, SDK-style projects, legacy .csproj/.vbproj files, packages.config, app.config/web.config, solution files, tests, pipelines, Dockerfiles, documentation, code hotspots, or knowledge silos, then generate a Markdown report with findings and improvement suggestions. This skill is read-only and must not run dotnet build/test/restore or repository scripts.
---

# Analyze .NET Repository

## Core rule

Perform static analysis only. Do not execute repository code, tests, build systems, package restore, database migrations, containers, local services, or scripts from the target repository.

Never run:

- `dotnet build`, `dotnet test`, `dotnet restore`, `dotnet run`, `dotnet list package`
- `msbuild`, `vstest`, `nuget restore`, `npm install`, `docker compose up`
- repo-local `.ps1`, `.bat`, `.cmd`, `.sh`, `.exe`, or project-specific scripts

Allowed actions:

- Read files and directory structure.
- Parse project, solution, config, pipeline, and source files.
- Run bundled skill scripts that only read files, such as `scripts/static_inventory.py`.
- Run read-only Git history queries through bundled skill scripts, such as `scripts/git_activity.py`, when a `.git` directory is present or the user asks for hotspot/ownership analysis.
- Create a report outside or inside the workspace when the user asks for an artifact.

## Workflow

1. Identify the analysis root. If the user gives no path, use the current workspace.
2. Detect whether `.git` exists by filesystem inspection. If present, include Git history analysis unless the user asks to skip it.
3. Prefer the multi-agent workflow in `references/subagent-workflow.md` when subagents are available and the repository is non-trivial.
4. Run `scripts/static_inventory.py <repo-root>` when useful to produce a quick JSON inventory. Treat the script as a helper, not a substitute for reading important files.
5. Run `scripts/git_activity.py <repo-root>` when Git history is available. Use bounded defaults (`--max-commits`) and add `--since` only when the user requests a date window.
6. Read representative files from each relevant category:
   - `.sln`, `.csproj`, `.vbproj`, `.fsproj`, `.props`, `.targets`
   - `packages.config`, `NuGet.config`, `Directory.Packages.props`
   - `appsettings*.json`, `app.config`, `web.config`, `.env*`
   - `.cs`, `.vb`, `.aspx`, `.ascx`, `.asmx`, `.ashx`, `.master`
   - CI/CD files: `.github/workflows/*`, `azure-pipelines*.yml`, `.gitlab-ci.yml`
   - `Dockerfile`, `docker-compose*.yml`, README/docs/ADR files
7. Apply the checklist in `references/dotnet-static-checklist.md`.
8. Generate the report using `references/report-template.md`.
9. Include execution metadata in the final report: multi-agent vs sequential mode, subagents used, fallback reason if any, scripts used, Git limits, and analysis constraints.
10. Explicitly state limitations: no build, no restore, no tests, no runtime verification. Also state Git limits such as maximum commits analyzed and date range if one was used.

## Multi-agent workflow

Use subagents to isolate context when the environment supports them. Keep each subagent read-only, scoped, and asked to return compact findings with evidence. The main agent should orchestrate, deduplicate, challenge weak claims, and write the final report.

Recommended subagents:

- Inventory agent: project structure, languages, target frameworks, dependency metadata, tests, CI/CD, documentation.
- Git activity agent: hotspots, churn, area hotspots, knowledge silos, noisy/generated hotspot caveats.
- Architecture and quality agent: dependency direction, layering, large files, legacy patterns, async/code-quality smells.
- Security and configuration agent: secrets, auth/authz, CORS, connection strings, risky config, SQL/path/command patterns.
- Report synthesis agent: optional only for large outputs; otherwise keep synthesis in the main agent.

Use `references/subagent-workflow.md` for ready-to-use prompts and expected return formats.

Fallback: if subagents are unavailable, run the same scopes sequentially in the main context and keep notes compact.

## Execution metadata

Every final report must include an `Execution Metadata` section so the reader can tell whether subagents were used.

Record:

- Execution mode: `Multi-agent`, `Sequential`, or `Hybrid`.
- Subagents available: `Yes`, `No`, or `Unknown`.
- Subagents used: list each subagent name and status (`used`, `not used`, `failed`, `not applicable`).
- Sequential fallback reason: only when not fully multi-agent.
- Scripts used: `static_inventory.py`, `git_activity.py`, or none.
- Git analysis limits: `max_commits`, `since` if used, `top`, `silo_threshold`, `min_touches`.
- Prohibited actions confirmed: no build, restore, tests, services, containers, migrations, or repo scripts.

If the environment exposes actual subagent/tool traces, base this section on those traces. Otherwise state that subagent availability was unknown and that analysis was performed sequentially or hybrid based on observable execution.

## Files to ignore by default

Skip generated, dependency, binary, and output folders unless the user asks otherwise:

`.git`, `bin`, `obj`, `.vs`, `.idea`, `.vscode`, `node_modules`, `packages`, `TestResults`, `coverage`, `dist`, `build`, `artifacts`, `.nuget`, `.sonarqube`.

Avoid reading large files fully. Prefer samples, metadata, counts, or targeted searches.

## Analysis expectations

Cover modern .NET and legacy .NET together:

- C# projects: `.csproj`, `.cs`, SDK-style and old MSBuild formats.
- VB.NET projects: `.vbproj`, `.vb`, `My Project/*`, WinForms, WebForms, class libraries, services, console apps.
- Legacy indicators: `.NET Framework`, `packages.config`, `web.config`, `app.config`, COM references, `HintPath`, `.edmx`, `.xsd`, `.resx`, designer files, WebForms pages, WinForms designer files.
- Modern indicators: target frameworks like `net6.0`, `net7.0`, `net8.0`, `net9.0`, `PackageReference`, nullable references, implicit usings, minimal APIs, ASP.NET Core hosting.

For every material finding, include:

- Evidence: file path, setting, pattern, or representative code location.
- Impact: why it matters.
- Recommendation: concrete improvement.
- Priority: Critical, High, Medium, or Low.
- Effort: Low, Medium, or High.
- Confidence: High, Medium, or Low when inferred.

## Git history analysis

Use Git history to identify change risk, not to judge individuals. Phrase findings around maintainability, bus factor, review strategy, and knowledge distribution.

Analyze:

- Hotspots: files changed frequently, high churn, or both.
- Area hotspots: folders/projects with concentrated change activity.
- Knowledge silos: files or areas where one author accounts for most touches.
- Cross-cutting contributors: authors touching many areas.
- Legacy risk intersection: files that are both legacy/VB.NET/config-heavy and frequently changed.

Default interpretation:

- A hotspot is a candidate for refactoring, better tests, documentation, or ownership review.
- A knowledge silo is a maintainability risk when one author has >=75% of touches in a file/area with enough history.
- High churn in generated files, designer files, migrations, or lock files may be noise; call it out as such.

Do not include sensitive author emails in the executive summary. Use names when useful, and place emails only in appendices if the user needs exact identity data.

## Report style

Write in the user's requested language. If no language is specified, match the user's language.

Prioritize actionable findings over exhaustive listing. Include a top recommendations section and a phased improvement plan. Avoid claiming a package is vulnerable unless verified from a vulnerability source; otherwise say it is a candidate for dependency review.

Place `Execution Metadata` near the top of the report, after `Scope and Limitations`, so usage of subagents is visible without reading the appendix.

## Bundled resources

- `scripts/static_inventory.py`: read-only inventory helper for .NET repositories.
- `scripts/git_activity.py`: read-only Git history helper for hotspots and knowledge silos.
- `references/dotnet-static-checklist.md`: detailed checklist for static analysis.
- `references/report-template.md`: Markdown report structure.
- `references/subagent-workflow.md`: subagent scopes, prompts, and compact output contracts.
