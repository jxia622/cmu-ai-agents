"""The Part 1 coding agent: fix a software issue and submit a git patch."""

from __future__ import annotations

import json
from typing import Any

from assignment.agent.base import (
    DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
    DEFAULT_COMPACTION_MAX_TOKENS,
    Agent,
)
from assignment.agent.tools import EXECUTE_TOOL, SEND_MESSAGE_TOOL
from assignment.env import Environment
from assignment.agent.base import (
    DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
    DEFAULT_COMPACTION_MAX_TOKENS,
    Agent,
    format_tool_output,
)

class CodeAgent(Agent):
    """An agent that fixes a software issue and submits a git patch."""

    def __init__(
        self,
        task: str,
        environment: Environment,
        model: str | None = None,
        logs_save_path: str | None = None,
        step_limit: int = 100,
        skills_path: str | None = None,
        auto_stop_environment: bool = True,
        compact_threshold_tokens: int | None = None,
        compaction_keep_recent_steps: int = DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
        compaction_max_tokens: int = DEFAULT_COMPACTION_MAX_TOKENS,
    ):
        super().__init__(
            environment=environment,
            model=model,
            logs_save_path=logs_save_path,
            step_limit=step_limit,
            skills_path=skills_path,
            auto_stop_environment=auto_stop_environment,
            compact_threshold_tokens=compact_threshold_tokens,
            compaction_keep_recent_steps=compaction_keep_recent_steps,
            compaction_max_tokens=compaction_max_tokens,
        )
        self.task = task
        self.submitted_patch = ""

        # TODO(Part 1.3): Make the `execute` and `send_message` tools available
        # to the agent.
        self.tools.extend([EXECUTE_TOOL, SEND_MESSAGE_TOOL])
        # TODO(1.1.b): Construct the system prompt and task_prompt. These
        # should be usable by the `Agent.build_prompt` method.
        self.system_prompt = (
            "You are a coding agent that solves software engineering tasks. "
            "Use the provided tools to inspect, modify, and test the codebase.\n\n"
            "<system_information>\n"
            + json.dumps(
                {
                    "machine": self.env.machine,
                    "release": self.env.release,
                    "system": self.env.system,
                    "version": self.env.version,
                },
                indent=2,
            )
            + "\n</system_information>"
        )

        self.task_prompt = self.task
        # TODO(1.4): If any skills are available to the agent, make their
        # descriptions/metadata available to the agent in the prompt.
        if self.skills:
            catalog = "\n".join(
                skill["metadata"]
                for skill in self.skills.values()
            )

            self.system_prompt += (
                "\n\nAvailable skills:\n"
                f"{catalog}\n"
                "Call `invoke_skill` with a skill name to load its full instructions."
            )

    def execute_tool_calls(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Execute ``execute`` and ``send_message`` calls in the code sandbox."""

        # TODO(Part 1.3): Parse each call, execute recognized tools, and return
        # one message per call (there may be multiple tool calls in one agent
        # response!). Malformed JSON and unknown tools must become recoverable
        # observations relayed to the agent instead of exceptions.
        observations = []

        for tool_call in tool_calls:
            tool_call_id = tool_call.get("id", "")

            try:
                function = tool_call.get("function", {})
                tool_name = function.get("name")
                raw_arguments = function.get("arguments", "{}")

                # The LLM gives arguments back as a JSON string
                arguments = json.loads(raw_arguments)

                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be a JSON object.")

                if tool_name == "execute":
                    command = arguments.get("command")

                    if command is None:
                        raise ValueError("execute requires a command.")

                    result = self.env.execute(
                        command,
                        shell=arguments.get("shell", True),
                        cwd=arguments.get("cwd"),
                        timeout=arguments.get("timeout"),
                        env=arguments.get("env"),
                    )

                    content = format_tool_output(result)

                elif tool_name == "send_message":
                    summary = arguments.get("summary")

                    if not isinstance(summary, str):
                        raise ValueError("send_message requires a string summary.")

                    content = summary

                    # send_message means the coding task is finished
                    self.finished = True

                elif tool_name == "invoke_skill":
                    name = arguments.get("name")

                    if not isinstance(name, str):
                        raise ValueError("invoke_skill requires a string name.")

                    if name not in self.skills:
                        raise ValueError(f"Unknown skill: {name}")

                    content = self.skills[name]["content"]

                else:
                    content = f"Unknown tool: {tool_name}"

            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                # Important: malformed tool calls should NOT crash the agent.
                # Give the error back to the LLM so it can recover.
                content = f"Tool call error: {exc}"

            observations.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": content,
                }
            )

        return observations
