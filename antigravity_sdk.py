#!/usr/bin/env python3
"""
antigravity_sdk.py — Python SDK Client for Antigravity AI Coding Agent
Provides full programmatic control over Antigravity sessions including enable_subagents=True (Tip 9).
"""

import subprocess
from typing import Optional, List


class AntigravitySDK:
    """
    Python SDK client for executing Antigravity Agent sessions.
    
    Args:
        enable_subagents (bool): Enable subagents for parallel research & codebase searching (*Tip 9*).
        non_interactive (bool): Run autonomously without waiting for human input (*Tip 17, 28*).
        auto_approve (bool): Automatically approve tool executions (file read/write, tests, git commit).
        extra_flags (list): Optional additional CLI flags.
    """

    def __init__(
        self,
        enable_subagents: bool = True,
        non_interactive: bool = True,
        auto_approve: bool = True,
        extra_flags: Optional[List[str]] = None,
    ):
        self.enable_subagents = enable_subagents
        self.non_interactive = non_interactive
        self.auto_approve = auto_approve
        self.extra_flags = extra_flags or []

    def build_command(self, prompt: str) -> List[str]:
        """Builds the execution command list for Antigravity CLI."""
        cmd = ["antigravity"]
        if self.non_interactive:
            cmd.append("--non-interactive")
        if self.enable_subagents:
            cmd.append("--enable-subagents")
        if self.auto_approve:
            cmd.append("--auto-approve")
        cmd.extend(self.extra_flags)
        cmd.extend(["--prompt", prompt])
        return cmd

    def run(self, prompt: str, cwd: Optional[str] = None) -> int:
        """
        Runs an Antigravity agent session with the specified prompt.
        Returns the exit code (0: Success, 1: Retry/Error, 2: Blocked).
        """
        cmd = self.build_command(prompt)
        print(f"🤖 [Antigravity SDK] Executing with enable_subagents={self.enable_subagents}...")
        try:
            result = subprocess.run(cmd, cwd=cwd)
            return result.returncode
        except FileNotFoundError:
            print("❌ Error: 'antigravity' binary not found in PATH.")
            return 1
