# Carnegie Mellon University · 11-768: AI Agents

**Course project portfolio for Carnegie Mellon University's 11-768: AI Agents, offered by the Language Technologies Institute (LTI), School of Computer Science.**

This repository collects my implementations and practice projects from the course. Each project includes its source code, setup instructions, and a description of the work and available results. New projects will be added as the course progresses.

[Course website](https://www.cmu-agents.com/) · [CMU LTI course catalog](https://lti.cs.cmu.edu/misc-pages/intranet-course-info.html)

## Projects

| Project | Focus | Implementation and evidence |
| --- | --- | --- |
| [01 · Build an Agent Harness](projects/01-agent-harness/) | Shared ReAct loop, coding agent, context compaction, chess agent, reusable skills, and sandboxed Python tool calls | Implemented agent components; 15 offline tests pass. Includes an agent-generated chess repair patch and saved-run summary. Some experiment evidence remains unavailable; see the project README. |

## Start here

```bash
git clone --recurse-submodules https://github.com/jxia622/cmu-ai-agents.git
cd cmu-ai-agents/projects/01-agent-harness
make setup
make test
```

Project 1 requires Python 3.11 or newer and [uv](https://docs.astral.sh/uv/). Its offline tests do not require cloud credentials. Running the agents requires an OpenAI-compatible model endpoint and Modal authentication; see the [project setup](projects/01-agent-harness/README.md#setup).

## Adding future course projects

Place each project in `projects/` using a numbered, descriptive folder, such as `02-project-name/`. Give it a README with the objective, your contributions, setup steps, validation, results, and course-source attribution. Add a row to the table above, then commit and push from this repository.

## Attribution

This is a personal student course project portfolio. The project instructions, starter infrastructure, tests, and chess application originate from the CMU course repositories. Project READMEs identify the original sources and the files containing my implementation.

