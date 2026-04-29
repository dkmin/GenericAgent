# GenericAgent — Codebase Guide for AI Agents

> Minimalist self-evolving autonomous agent. ~3K LOC core, 9 atomic tools, hierarchical memory, composable system prompt. Reference implementation for the `self-gen-agent` pattern.

## Overview

GenericAgent runs an LLM-driven control loop that gives any chat model system-level access (browser, terminal, FS, kbd/mouse, vision, ADB) through a **fixed, atomic** tool kit. Capability growth comes not from adding tools but from **growing memory** (L0~L4) — the agent writes its own SOPs and lessons, and they are reinjected on later turns.

Three pillars (also see `memory/self-gen-agent` skill):

1. **Atomic tool kit** — small, composable, OS-aware (`assets/tools_schema.json`).
2. **Hierarchical memory** with action-verified axioms (`memory/`, L0~L4).
3. **Composable system prompt** assembled per turn (`assets/sys_prompt*.txt` + `get_global_memory()`).

## Directory Structure

```
agentmain.py        # GeneraticAgent orchestrator: queue, run loop, LLM session mgmt #260429-21
agent_loop.py       # agent_runner_loop — turn-by-turn LLM step driver
ga.py               # GenericAgentHandler + atomic tool dispatch (code_run, web, vision, …)
llmcore.py          # LLM transport: OAI/Claude/native sessions, MixinSession, log writer
simphtml.py         # Browser/JS execution helpers (works with TMWebDriver/CDP)
TMWebDriver.py      # CDP bridge for Chrome control
hub.pyw             # legacy entrypoint (predecessor of launch.pyw)
launch.pyw          # default entrypoint: starts Streamlit + optional bots/scheduler
gatui.py            # terminal CLI (TUI) frontend — raw-mode ESC/Ctrl-C handling #260429-21
mykey_template*.py  # copy to mykey.py and fill in API keys
pyproject.toml      # extras: [ui], [all-frontends]; minimal core only by default

frontends/          # all UI surfaces share the same backend API
  stapp.py            # default Streamlit (web) — launched by launch.pyw
  stapp2.py           # alternative Streamlit style
  qtapp.py            # Qt desktop app
  desktop_pet*.pyw    # floating desktop pet companion
  tgapp/qqapp/fsapp/wecomapp/dingtalkapp/wechatapp.py  # bot frontends
  chatapp_common.py   # slash command dispatcher shared by chat_id-based bots
  continue_cmd.py     # /continue session restore — monkey-patches GeneraticAgent

memory/             # persistent agent memory (L0~L4)
  global_mem.txt           # L2 — long-lived facts the agent has confirmed
  global_mem_insight.txt   # L1 — "fixed structure" insights / axioms
  *_sop.md                 # L3 — agent-authored SOPs (autonomous, plan, verify, …)
  L4_raw_sessions/         # L4 — compressed transcripts
  skill_search/            # skill index
  subagent.md              # subagent dispatch contract

assets/             # static prompt + tool schemas + bridges
  sys_prompt.txt / sys_prompt_en.txt
  tools_schema.json / tools_schema_cn.json   # _cn variant for GLM/Minimax/Kimi
  tool_usable_history.json                   # bootstrap tool examples
  tmwd_cdp_bridge/                           # injected CDP scripts
  global_mem_insight_template*.txt           # initial L1 seed

reflect/            # autonomous reflection loops
  autonomous.py     # self-driving idle behavior
  scheduler.py      # cron-like task runner (via launch.pyw --sched)

plugins/            # opt-in integrations
  langfuse_tracing.py

docs/mint/          # Mintlify documentation site
temp/               # runtime scratch (auto-created)
  model_responses/  # per-pid LLM request/response logs
  reflect_logs/     # reflect script output logs
```

## Key Backend API (used by every frontend)

```python
from agentmain import GeneraticAgent
agent = GeneraticAgent()           # initializes from mykey.py; agent.llmclient is None if unconfigured
threading.Thread(target=agent.run, daemon=True).start()

dq = agent.put_task(prompt, source="user")   # → queue.Queue
while True:
    item = dq.get(timeout=1)       # {'next': partial_text} stream, then {'done': final}

agent.abort()                      # interrupt current turn
agent.list_llms() / agent.next_llm(n) / agent.get_llm_name()
agent.history                      # rolling [USER]/[AGENT] log
```

Slash commands are *not* dispatched by the backend — each frontend wires them. `frontends/chatapp_common.py:handle_command` is the canonical implementation (used by all bot frontends + `gatui.py`); the Streamlit frontend (`stapp.py`) only handles `/new` and `/continue` directly.

## Run / Develop

```bash
# install minimal core, then add extras as needed (do NOT install all)
pip install -e .             # core
pip install -e .[ui]         # streamlit + pywebview
pip install -e .[all-frontends]  # bots

cp mykey_template.py mykey.py    # then fill in API keys

python launch.pyw            # default Streamlit + webview (port auto-selected)
python launch.pyw --sched    # + reflect/scheduler.py for cron tasks
python launch.pyw --tg --fs  # + Telegram + Feishu bots
python gatui.py              # terminal CLI, no GUI deps  #260429-21
streamlit run frontends/stapp2.py
python frontends/qtapp.py
```

Language env: `GA_LANG=en` forces English prompts/insights (default auto-detects from locale → `zh` if Chinese, else `en`). Tool schema variant `_cn` is loaded automatically when LLM model name contains `glm`/`minimax`/`kimi`.

## Logs

| Path | What |
|------|------|
| `temp/model_responses/model_responses_<pid>.txt` | raw LLM request/response (llmcore.py:_write_llm_log) |
| `temp/reflect_logs/<script>_<YYYY-MM-DD>.log` | reflect script results |
| `<task_dir>/stdout.log` / `stderr.log` | per-subprocess capture (agentmain.py:193) |
| `memory/L4_raw_sessions/` | compressed full-session transcripts |

No top-level app log file — frontends print to their own console.

## Conventions

- **Atomic tools, not task-specific tools.** Add capability via memory/SOPs first; only extend `assets/tools_schema.json` when truly novel.
- **Memory writes are append-mostly.** Older insights stay; the loop self-prunes via `memory_cleanup_sop.md`.
- **System prompt is assembled, not static.** `get_system_prompt()` concatenates `sys_prompt*.txt` + today's date + global memory each turn — this is intentional, do not cache.
- **mykey.py is git-ignored.** Configs are dict-keyed by name containing `api`/`config`/`cookie`; key substrings (`claude`, `oai`, `mixin`, `native`) drive session class selection (agentmain.py:load_llm_sessions).
- **Streaming convention.** Backend yields *cumulative* text on each `next` — frontends should diff against previously-printed length, not concatenate.
- **`<thinking>` and `<summary>` tags** are convention markers; CLI (`gatui.py`) strips them, GUI frontends fold them into expanders.

## Gotchas

- `launch.pyw` reads `os.name == 'nt'` for Win32 window placement; non-Windows fall through harmlessly.
- `_install_continue` (continue_cmd) **monkey-patches** `GeneraticAgent`; importing `chatapp_common` is required for `/continue` and `/new` history reset to work — `gatui.py` and bot frontends import it for this side effect.
- `MixinSession` requires base sessions of consistent native-vs-classic type; bad config raises at first `next_llm()`.
- Tool schema `_cn` variant exists because some Chinese models reject English-only tool descriptions; do not edit `_cn` from `en`-only assumptions.

## Related

- `~/clawd/projs/GenericAgent-why.md` — Why DK is exploring this repo (value card)
- `docs/mint/` — Mintlify site source
- `memory/self-gen-agent` skill — pattern reference (also installed as a Claude Code skill)

#260429-21 추가
