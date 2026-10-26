"""CLI-Anything-inspired wrapper that delegates to the real Codex CLI.

The app-server path uses os.execv: the original subprocess owns stdin/stdout,
stderr, exit codes, authentication, permissions and protocol framing.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

import click
from . import __version__


def resolve_backend() -> str:
    """Require a real, separate installed Codex executable."""
    candidate = os.environ.get("CHATGPT_CLI_CODEX_BIN", "").strip()
    if candidate:
        path = Path(candidate).expanduser()
        if not path.is_absolute():
            raise click.ClickException("CHATGPT_CLI_CODEX_BIN must be an absolute path")
        if not path.is_file() or not os.access(path, os.X_OK):
            raise click.ClickException("Codex backend is not an executable file")
        backend = str(path.resolve())
    else:
        backend = shutil.which("codex")
        if backend is None:
            raise click.ClickException("Official Codex CLI is missing; install and sign in to Codex first")
        backend = str(Path(backend).resolve())
    own = Path(sys.argv[0]).resolve()
    if Path(backend).resolve() == own:
        raise click.ClickException("Codex backend cannot point to chatgpt-cli itself")
    return backend


def inspect_backend() -> dict:
    backend = resolve_backend()
    try:
        process = subprocess.run([backend, "--version"], text=True, capture_output=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise click.ClickException(f"Codex version probe failed: {type(error).__name__}") from error
    return {"backend": backend, "installed": process.returncode == 0,
            "version": process.stdout.strip()[:200] if process.returncode == 0 else None,
            "authenticated": "not_checked", "protocol": "codex app-server",
            "error": None if process.returncode == 0 else "Codex version probe failed"}


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--json", "json_output", is_flag=True, help="Machine-readable command output.")
@click.version_option(__version__, prog_name="chatgpt-cli")
@click.pass_context
def cli(ctx: click.Context, json_output: bool) -> None:
    """Local Codex bridge; never exposes the ChatGPT website session."""
    ctx.ensure_object(dict)["json_output"] = json_output
    if ctx.invoked_subcommand is None:
        if not sys.stdin.isatty():
            raise click.UsageError("Provide a subcommand for non-interactive use")
        repl()


@cli.group()
def agent() -> None:
    """Inspect the installed official Codex backend."""


@agent.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Report installation metadata; authentication is not inferred."""
    data = inspect_backend()
    if ctx.obj["json_output"]:
        click.echo(json.dumps(data, sort_keys=True))
    else:
        click.echo(f"Codex: {data['version'] or 'Unavailable'} ({data['backend']})")
        click.echo("Authentication: not checked")


@cli.command(name="app-server", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def app_server(ctx: click.Context) -> None:
    """Replace this process with the actual Codex app-server, unmodified."""
    backend = resolve_backend()
    os.execv(backend, [backend, "app-server", *ctx.args])


@cli.command()
def repl() -> None:
    """Interactive diagnostic console. App-server uses direct stdio instead."""
    if not sys.stdin.isatty():
        raise click.UsageError("REPL requires a terminal")
    click.echo("ChatGPT CLI / Codex passthrough (status, quit)")
    while True:
        try:
            command = input("chatgpt-cli> ").strip()
        except (KeyboardInterrupt, EOFError):
            click.echo()
            return
        if command in ("quit", "exit"):
            return
        if command == "status":
            click.echo(json.dumps(inspect_backend(), indent=2))
        elif command:
            click.echo("Unknown command. Available: status, quit")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
