# Static .NET Repository Checklist

Use this checklist for read-only repository analysis. Do not execute build, restore, tests, services, containers, migrations, or repo-local scripts.

## Inventory

- Identify solution files and projects: `.sln`, `.csproj`, `.vbproj`, `.fsproj`.
- Classify projects by language, SDK-style vs legacy MSBuild, output type, and target framework.
- Detect common application types: ASP.NET Core, ASP.NET MVC/WebForms, WinForms, WPF, worker/service, console app, class library, test project.
- Identify shared build files: `Directory.Build.props`, `Directory.Build.targets`, `Directory.Packages.props`, `NuGet.config`, `global.json`.

Improvement suggestions:

- Document the purpose of each project when naming and folder structure are not self-explanatory.
- Consolidate common project properties in `Directory.Build.props`.
- Separate generated/output/dependency folders from source control if present.

## Git history, hotspots, and knowledge silos

Review with bounded read-only history queries:

- Files with the highest number of commits/touches.
- Files with the highest churn, using added plus deleted lines when available.
- Areas or project folders with concentrated change frequency.
- Authors per file and per area.
- Files or areas where one author owns most touches.
- Hotspots that overlap with legacy VB.NET, WebForms, WinForms designer files, EF migrations, configuration, or security-sensitive code.

Improvement suggestions:

- Add tests around high-churn files before refactoring.
- Prioritize cleanup where high churn overlaps with large files, weak boundaries, or legacy patterns.
- Reduce knowledge silos with pairing, rotation, documentation, code reviews, and ownership backup.
- Treat generated files, designer files, migrations, and lock files carefully; they may inflate hotspot metrics.
- Avoid person-focused blame. Frame findings as team resilience and maintainability risks.

## Project configuration

Review:

- `TargetFramework` / `TargetFrameworks` / `TargetFrameworkVersion`
- `Nullable`, `ImplicitUsings`, `LangVersion`, `TreatWarningsAsErrors`, `AnalysisLevel`
- `OutputType`, `RootNamespace`, `AssemblyName`
- `ProjectReference`, `Reference`, `PackageReference`
- Legacy references with `HintPath`, COM references, GAC dependencies, local DLLs

Improvement suggestions:

- Enable nullable analysis progressively in C# projects where feasible.
- Use central package management for multi-project repos with repeated versions.
- Replace manual DLL references with package or project references where practical.
- Plan modernization for unsupported or near end-of-support frameworks.

## VB.NET and legacy .NET

Review:

- `.vbproj` format and target framework.
- `Option Strict`, `Option Explicit`, `Option Infer`.
- `Module` files with global state or broad utility behavior.
- `On Error Resume Next`.
- `My.Settings`, `My.Resources`, `My Project/*`.
- WinForms `.Designer.vb`, `.resx`, UI event handlers with business logic.
- WebForms `.aspx`, `.ascx`, `.master`, `.asmx`, `.ashx` and code-behind `.vb`.
- `.edmx`, `.xsd`, typed datasets, strongly coupled generated code.

Improvement suggestions:

- Turn `Option Strict On` progressively, starting with low-risk modules.
- Move business logic out of forms, pages, and event handlers.
- Inventory COM/local DLL dependencies before migration planning.
- Prefer incremental modernization over a full rewrite unless business constraints justify it.

## Architecture

Review:

- Project references and direction of dependencies.
- Presence of domain/application/infrastructure/API boundaries.
- Controllers, minimal APIs, code-behind, or UI components containing business logic.
- Cross-cutting concerns: validation, logging, error handling, authorization.
- Naming patterns like `Helper`, `Manager`, `Util`, `Common` that may hide mixed responsibilities.

Improvement suggestions:

- Keep domain/application code independent from infrastructure and UI concerns.
- Extract repeated logic into cohesive services or domain types.
- Avoid introducing abstractions unless they remove real duplication or reduce coupling.

## Code quality

Review:

- Very large files/classes and long methods by line-count heuristics.
- Duplicated patterns across projects.
- Excessive static/global state.
- Swallowed exceptions, broad catches, empty catches.
- Sync-over-async patterns in C#: `.Result`, `.Wait()`, `GetAwaiter().GetResult()`.
- Dynamic SQL or string-built paths/commands.

Improvement suggestions:

- Split large files by responsibility.
- Replace broad exception swallowing with explicit handling and structured logging.
- Remove dead/commented code when safe.
- Add analyzers and formatting rules in shared configuration.

## Testing

Review:

- Test projects by name and package references: xUnit, NUnit, MSTest, FluentAssertions, Moq, NSubstitute, AutoFixture.
- Gaps between production projects and test projects.
- Integration test markers: WebApplicationFactory, TestServer, containers, fixture collections.
- Legacy projects with no apparent tests.

Improvement suggestions:

- Add tests around domain logic, critical services, and risky legacy code before refactoring.
- Add integration tests for API and persistence boundaries.
- Avoid over-mocking behavior that should be verified through public contracts.

## Security

Review:

- Secrets in `appsettings*.json`, `.env*`, `web.config`, `app.config`, source files.
- Connection strings, API keys, tokens, passwords, certificates, private keys.
- CORS settings such as `AllowAnyOrigin`.
- Authentication/authorization registration and endpoint policies.
- SQL string concatenation, command execution, path handling, deserialization.
- Logging of PII, tokens, credentials, or full request bodies.

Improvement suggestions:

- Move secrets to environment variables or a secret manager.
- Make authorization explicit at endpoints/controllers where sensitive operations exist.
- Use parameterized queries and safe path handling.
- Review permissive CORS and debug settings before production deployment.

## APIs and contracts

Review:

- Controllers, minimal APIs, route conventions, DTOs, validation, OpenAPI/Swagger.
- Exposing EF entities or domain entities directly through API contracts.
- Error response consistency and Problem Details usage.
- API versioning if external consumers are likely.

Improvement suggestions:

- Keep public contracts separate from persistence/domain internals.
- Normalize validation and error responses.
- Document external-facing endpoints and versioning expectations.

## Data access

Review:

- EF Core/EF6 DbContext, migrations, repositories, Unit of Work, Dapper, raw SQL.
- `.edmx`, typed datasets, stored procedure heavy designs.
- Potential N+1 patterns, large `Include` chains, unbounded queries.
- Transaction and concurrency patterns.

Improvement suggestions:

- Review complex queries and pagination.
- Keep data access concerns out of UI/controllers.
- Document migration strategy and database ownership.

## Observability

Review:

- Logging frameworks: Microsoft.Extensions.Logging, Serilog, NLog, log4net.
- Health checks, OpenTelemetry, Application Insights.
- Correlation/request IDs.
- Error handling middleware or global exception filters.

Improvement suggestions:

- Use structured logs with stable event properties.
- Add health checks for critical dependencies.
- Add tracing/correlation for distributed or async workflows.

## CI/CD and operations

Review:

- GitHub Actions, Azure Pipelines, GitLab CI, Jenkins files.
- Whether pipelines appear to build, test, scan, package, and deploy.
- Dockerfiles and compose files by inspection only.
- Environment config and deployment scripts without executing them.

Improvement suggestions:

- Ensure CI performs restore/build/test/scans even though this skill does not run them.
- Pin base images and avoid secrets in pipeline files.
- Separate build, test, package, and deploy stages.

## Documentation

Review:

- README, setup instructions, architecture docs, ADRs, runbooks.
- Local development prerequisites and external dependencies.
- Known limitations and deployment notes.

Improvement suggestions:

- Add a reproducible local setup guide.
- Document architecture and key decisions.
- Add runbooks for critical operational flows.
