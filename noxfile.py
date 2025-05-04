import platform
import re
import shutil
import sys
import textwrap
import typing as T
from pathlib import Path

import nox
from nox import Session, parametrize, session

nox.options.error_on_external_run = True
nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["lint", "type_check", "test"]


def get_project_version() -> str:
    for line in open("pyproject.toml"):
        # Expected line:
        #   version = "0.11.0"
        m = re.search(
            r"""
                ^
                \s* version \s* = \s*
                "
                ( (\d|\.)+ )
                "
                $
            """,
            line,
            re.VERBOSE,
        )
        if m:
            return T.cast(str, m.group(1))
    raise Exception("could not find `findx` version in `pyproject.toml`")


def get_target_os() -> str:
    if sys.platform.startswith("linux"):
        target_os = "linux"
    elif sys.platform.startswith("darwin"):
        target_os = "darwin"
    elif sys.platform.startswith("win"):
        target_os = "windows"
    else:
        target_os = "unknown"
    return target_os


def get_target_arch() -> str:
    arch = platform.machine().lower()
    if arch == "amd64":
        arch = "x86_64"
    elif arch == "arm64":
        arch = "aarch64"
    return arch


def rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


@session(python=["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"])
def test(s: Session) -> None:
    s.install(".", "pytest", "pytest-cov")
    s.run(
        "python",
        "-m",
        "pytest",
        "--cov=findx",
        "--cov-report=html",
        "--cov-report=term",
        "tests",
        *s.posargs,
    )


# For some sessions, set `venv_backend="none"` to simply execute scripts within
# the existing `uv` environment.
@session(venv_backend="none")
def fmt(s: Session) -> None:
    s.run("ruff", "check", ".", "--select", "I", "--fix")
    s.run("ruff", "format", ".")


@session(venv_backend="none")
@parametrize(
    "command",
    [
        ["ruff", "check", "."],
        ["ruff", "format", "--check", "."],
    ],
)
def lint(s: Session, command: T.List[str]) -> None:
    s.run(*command)


@session(venv_backend="none")
def lint_fix(s: Session) -> None:
    s.run("ruff", "check", ".", "--fix")


@session(venv_backend="none")
def type_check(s: Session) -> None:
    s.run("mypy", "src", "tests", "noxfile.py")


@session
def licenses(s: Session) -> None:
    # Install only main dependencies for license report.
    s.run_install(
        "uv",
        "sync",
        "--locked",
        "--no-default-groups",
        "--no-install-project",
        f"--python={s.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": s.virtualenv.location},
    )
    s.run_install(
        "uv",
        "pip",
        "install",
        "pip-licenses",
        f"--python={s.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": s.virtualenv.location},
    )
    s.run("pip-licenses", *s.posargs)


@session(venv_backend="none")
def build(s: Session) -> None:
    version = get_project_version()
    target_os = get_target_os()
    target_arch = get_target_arch()
    target_platform = f"{target_arch}-{target_os}"
    if target_os == "windows":
        suffix = ".exe"
    else:
        suffix = ""
    dist_path = Path("dist") / target_platform
    work_path = Path("build") / target_platform
    github_path = Path("dist") / "github"
    rmtree(dist_path)
    rmtree(work_path)
    github_path.mkdir(parents=True, exist_ok=True)
    s.run("uv", "sync")

    def _build_helper(entry_point: str) -> None:
        dist_exe_path = dist_path / (entry_point + suffix)
        github_exe_path = (
            github_path / f"{entry_point}-{version}-{target_platform}{suffix}"
        )
        github_exe_path.unlink(missing_ok=True)

        args = ["pyinstaller"]
        args.append("--onefile")
        args.extend(["--name", entry_point])
        args.extend(["--distpath", str(dist_path)])
        args.extend(["--specpath", str(work_path)])
        args.extend(["--workpath", str(work_path)])
        # Copy metadata so that `importlib.metadata.version("findx"))` works.
        args.extend(["--copy-metadata", "findx"])
        args.append(f"--add-data=../../README.rst:{entry_point}")
        args.extend(["--log-level", "WARN"])
        args.append(f"{entry_point}-wrapper.py")
        s.run(*args)
        s.log(f"copy {dist_exe_path} -> {github_exe_path}")
        shutil.copy(dist_exe_path, github_exe_path)

    _build_helper("findx")
    _build_helper("ffx")
    _build_helper("ffg")


@session(venv_backend="none")
def build_linux(s: Session) -> None:
    # Remove any stray container if it exists; use
    # `success_codes` to prevent `nox` failure if the
    # container does not exist and `docker rm` fails.
    s.run("docker", "rm", "findx-build", success_codes=[0, 1], silent=True)
    s.run("docker", "build", ".", "-t", "findx-build")
    s.run(
        "docker", "create", "--name", "findx-build", "findx-build", silent=True
    )
    s.run("docker", "cp", "findx-build:/dist/.", "dist/")
    s.run("docker", "rm", "findx-build", silent=True)


@session(venv_backend="none")
def release(s: Session) -> None:
    version = get_project_version()
    rmtree(Path("dist"))
    rmtree(Path("build"))
    s.log("NOTE: safe to perform Windows steps now...")
    s.run("uv", "sync")
    # Build the `findx` executable for Linux:
    build_linux(s)
    s.run("uv", "build")
    print(
        textwrap.dedent(
            f"""
        ** Remaining manual steps:

        On Windows machine:
          uv run nox -s build
        Alternatively, unzip from CI:
          unzip -d dist/ dist-windows-latest.zip

        Tag and push:
          git tag -am 'Release v{version}.' v{version}
          git push; git push --tags

        Upload to PyPI:
          PYPI_PASSWORD=<TOKEN PASSWORD>
          uv publish -u __token__ -p "$PYPI_PASSWORD"

        Create Github release for {version} from tree:
          dist/github/
        """
        )
    )
