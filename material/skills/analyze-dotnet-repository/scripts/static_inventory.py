#!/usr/bin/env python3
"""Read-only static inventory for modern and legacy .NET repositories."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


IGNORE_DIRS = {
    ".git",
    ".vs",
    ".idea",
    ".vscode",
    "bin",
    "obj",
    "node_modules",
    "packages",
    "TestResults",
    "coverage",
    "dist",
    "build",
    "artifacts",
    ".nuget",
    ".sonarqube",
}

SOURCE_EXTS = {".cs", ".vb", ".fs"}
PROJECT_EXTS = {".csproj", ".vbproj", ".fsproj"}
CONFIG_NAMES = {
    "app.config",
    "web.config",
    "packages.config",
    "nuget.config",
    "global.json",
    "directory.build.props",
    "directory.build.targets",
    "directory.packages.props",
}
PIPELINE_NAMES = {
    "azure-pipelines.yml",
    "azure-pipelines.yaml",
    ".gitlab-ci.yml",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip_dir(path: Path) -> bool:
    return path.name in IGNORE_DIRS


def iter_files(root: Path):
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        dirs[:] = [d for d in dirs if not should_skip_dir(current_path / d)]
        for name in files:
            yield current_path / name


def read_text(path: Path, max_bytes: int = 512_000) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
    except OSError:
        return ""
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return ""


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_texts(root: ET.Element, name: str) -> list[str]:
    values = []
    for elem in root.iter():
        if local_name(elem.tag) == name and elem.text:
            values.append(elem.text.strip())
    return values


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.fromstring(read_text(path))
    except ET.ParseError:
        return None


def parse_project(path: Path, repo: Path) -> dict:
    text = read_text(path)
    xml = parse_xml(path)
    result = {
        "path": rel(path, repo),
        "language": {".csproj": "C#", ".vbproj": "VB.NET", ".fsproj": "F#"}[path.suffix.lower()],
        "sdk_style": "<Project Sdk=" in text or "Sdk=\"" in text[:500],
        "target_frameworks": [],
        "output_types": [],
        "package_references": [],
        "project_references": [],
        "assembly_references": [],
        "legacy_signals": [],
        "settings": {},
    }
    if xml is None:
        result["parse_error"] = True
        return result

    frameworks = []
    for key in ("TargetFramework", "TargetFrameworks", "TargetFrameworkVersion"):
        frameworks.extend(child_texts(xml, key))
    result["target_frameworks"] = sorted(set(frameworks))
    result["output_types"] = sorted(set(child_texts(xml, "OutputType")))

    for key in ("Nullable", "ImplicitUsings", "LangVersion", "TreatWarningsAsErrors", "AnalysisLevel", "OptionStrict", "OptionExplicit", "OptionInfer"):
        values = child_texts(xml, key)
        if values:
            result["settings"][key] = sorted(set(values))

    for elem in xml.iter():
        name = local_name(elem.tag)
        include = elem.attrib.get("Include") or elem.attrib.get("Update")
        if name == "PackageReference" and include:
            version = elem.attrib.get("Version")
            for child in elem:
                if local_name(child.tag) == "Version" and child.text:
                    version = child.text.strip()
            result["package_references"].append({"name": include, "version": version})
        elif name == "ProjectReference" and include:
            result["project_references"].append(include.replace("\\", "/"))
        elif name == "Reference" and include:
            hint = None
            for child in elem:
                if local_name(child.tag) == "HintPath" and child.text:
                    hint = child.text.strip()
            result["assembly_references"].append({"name": include, "hint_path": hint})
            if hint:
                result["legacy_signals"].append("HintPath assembly reference")
        elif name in {"COMReference", "COMFileReference"}:
            result["legacy_signals"].append(name)

    if path.suffix.lower() == ".vbproj":
        result["legacy_signals"].append("VB.NET project")
    if not result["sdk_style"]:
        result["legacy_signals"].append("Non SDK-style project")
    if "packages.config" in text.lower():
        result["legacy_signals"].append("packages.config reference")

    result["package_references"] = sorted(result["package_references"], key=lambda x: x["name"].lower())
    result["project_references"] = sorted(set(result["project_references"]))
    return result


def parse_packages_config(path: Path, repo: Path) -> dict:
    xml = parse_xml(path)
    packages = []
    if xml is not None:
        for elem in xml.iter():
            if local_name(elem.tag) == "package":
                package_id = elem.attrib.get("id")
                if package_id:
                    packages.append(
                        {
                            "name": package_id,
                            "version": elem.attrib.get("version"),
                            "target_framework": elem.attrib.get("targetFramework"),
                        }
                    )
    return {"path": rel(path, repo), "packages": sorted(packages, key=lambda x: x["name"].lower())}


def source_signals(path: Path, repo: Path) -> dict:
    text = read_text(path)
    suffix = path.suffix.lower()
    signals = []
    if suffix == ".vb":
        patterns = {
            "On Error Resume Next": r"\bOn\s+Error\s+Resume\s+Next\b",
            "Option Strict Off": r"\bOption\s+Strict\s+Off\b",
            "Option Explicit Off": r"\bOption\s+Explicit\s+Off\b",
            "Module declaration": r"^\s*Module\s+\w+",
            "My.Settings usage": r"\bMy\.Settings\b",
        }
    else:
        patterns = {
            "sync-over-async": r"\.(Result|Wait\(\)|GetAwaiter\(\)\.GetResult\(\))",
            "AllowAnyOrigin": r"\bAllowAnyOrigin\s*\(",
            "empty catch": r"catch\s*(\([^)]*\))?\s*\{\s*\}",
        }
    for label, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            signals.append(label)

    line_count = text.count("\n") + (1 if text else 0)
    result = {"path": rel(path, repo), "lines": line_count, "signals": signals}
    if line_count > 500:
        result["signals"].append("large source file")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only static inventory for .NET repositories.")
    parser.add_argument("repo", help="Repository/source folder to inspect")
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists() or not repo.is_dir():
        print(f"Not a directory: {repo}", file=sys.stderr)
        return 2

    files = list(iter_files(repo))
    extensions = Counter(p.suffix.lower() or "<none>" for p in files)
    projects = [parse_project(p, repo) for p in files if p.suffix.lower() in PROJECT_EXTS]
    packages_configs = [parse_packages_config(p, repo) for p in files if p.name.lower() == "packages.config"]

    source_files = [p for p in files if p.suffix.lower() in SOURCE_EXTS]
    sampled_sources = []
    for p in source_files:
        info = source_signals(p, repo)
        if info["signals"]:
            sampled_sources.append(info)

    package_versions = defaultdict(set)
    for project in projects:
        for package in project["package_references"]:
            if package.get("version"):
                package_versions[package["name"]].add(package["version"])
    for cfg in packages_configs:
        for package in cfg["packages"]:
            if package.get("version"):
                package_versions[package["name"]].add(package["version"])

    duplicate_versions = {
        name: sorted(versions)
        for name, versions in sorted(package_versions.items(), key=lambda item: item[0].lower())
        if len(versions) > 1
    }

    configs = []
    pipelines = []
    web_legacy = []
    for p in files:
        name = p.name.lower()
        rel_path = rel(p, repo)
        if name in CONFIG_NAMES or name.startswith("appsettings") and p.suffix.lower() == ".json":
            configs.append(rel_path)
        if name in PIPELINE_NAMES or ".github/workflows/" in rel_path:
            pipelines.append(rel_path)
        if p.suffix.lower() in {".aspx", ".ascx", ".asmx", ".ashx", ".master"}:
            web_legacy.append(rel_path)

    test_projects = [
        project
        for project in projects
        if re.search(r"(\.|/|\\)(test|tests|unittest|unittests|integrationtest|integrationtests)\b", project["path"], re.IGNORECASE)
        or any(pkg["name"].lower() in {"xunit", "nunit", "mstest.testframework"} for pkg in project["package_references"])
    ]

    inventory = {
        "root": str(repo),
        "git_directory_present": (repo / ".git").exists(),
        "counts": {
            "files": len(files),
            "projects": len(projects),
            "source_files": len(source_files),
            "csharp_files": sum(1 for p in source_files if p.suffix.lower() == ".cs"),
            "vb_files": sum(1 for p in source_files if p.suffix.lower() == ".vb"),
            "test_projects": len(test_projects),
        },
        "extensions": dict(sorted(extensions.items())),
        "solutions": sorted(rel(p, repo) for p in files if p.suffix.lower() == ".sln"),
        "projects": projects,
        "test_project_paths": [p["path"] for p in test_projects],
        "packages_config": packages_configs,
        "duplicate_package_versions": duplicate_versions,
        "config_files": sorted(configs),
        "pipeline_files": sorted(pipelines),
        "legacy_web_files_sample": sorted(web_legacy)[:100],
        "source_signals": sorted(sampled_sources, key=lambda x: x["path"])[:300],
    }

    text = json.dumps(inventory, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
