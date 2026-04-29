"""One-shot CLI frontend for GenericAgent.

Usage:
    python gacli.py "your prompt"
    echo "your prompt" | python gacli.py
    python gacli.py --llm_no 1 --quiet "your prompt"

Runs a single turn (prompt -> response) and exits. For interactive chat use gatui.py.
"""
import os, sys, re, queue, threading, argparse

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
sys.path.insert(0, os.path.join(script_dir, 'frontends'))

from agentmain import GeneraticAgent

USE_COLOR = sys.stdout.isatty() and os.environ.get('NO_COLOR') is None
def c(code, s): return f"\033[{code}m{s}\033[0m" if USE_COLOR else s
DIM, BOLD, CYAN, YELLOW, RED = '2', '1', '36', '33', '31'

TURN_RE = re.compile(r'\**LLM Running \(Turn \d+\) \.\.\.\*\**')
THINK_RE = re.compile(r'<thinking>.*?</thinking>', re.DOTALL)
SUMMARY_RE = re.compile(r'<summary>.*?</summary>', re.DOTALL)

def clean(text):
    text = THINK_RE.sub('', text)
    text = SUMMARY_RE.sub('', text)
    text = TURN_RE.sub(c(DIM, '─── turn ───'), text)
    return text

def read_prompt(arg_prompt):
    if arg_prompt: return arg_prompt
    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data: return data
    return None

def run_once(agent, prompt, raw=False, stream=True):
    dq = agent.put_task(prompt, source="user")
    printed = 0
    last = ''
    final_text = ''
    try:
        while True:
            try: item = dq.get(timeout=1)
            except queue.Empty: continue
            if 'next' in item and stream:
                last = item['next'] if raw else clean(item['next'])
                if len(last) > printed:
                    sys.stdout.write(last[printed:]); sys.stdout.flush()
                    printed = len(last)
            if 'done' in item:
                final_text = item['done'] if raw else clean(item['done'])
                if stream:
                    if len(final_text) > printed:
                        sys.stdout.write(final_text[printed:])
                else:
                    sys.stdout.write(final_text)
                break
    except KeyboardInterrupt:
        agent.abort()
        sys.stderr.write(c(YELLOW, "\n[aborted]\n"))
        return 130
    sys.stdout.write('\n'); sys.stdout.flush()
    return 0

def main():
    parser = argparse.ArgumentParser(description="One-shot GenericAgent CLI.")
    parser.add_argument('prompt', nargs='?', help='Prompt text. If omitted, read from stdin.')
    parser.add_argument('--llm_no', type=int, default=0)
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress banner.')
    parser.add_argument('--raw', action='store_true', help='Do not strip <thinking>/<summary>/turn markers.')
    parser.add_argument('--no-stream', action='store_true', help='Print only the final response, not incremental output.')
    args = parser.parse_args()

    prompt = read_prompt(args.prompt)
    if not prompt:
        parser.error("no prompt given (pass as arg or pipe via stdin)")

    agent = GeneraticAgent()
    if agent.llmclient is None:
        sys.stderr.write(c(RED, "⚠️  사용 가능한 LLM 연결이 없습니다. mykey.py를 설정해주세요.\n"))
        sys.exit(1)
    if args.llm_no:
        try: agent.next_llm(args.llm_no)
        except Exception as e:
            sys.stderr.write(c(YELLOW, f"--llm_no {args.llm_no} 적용 실패: {e}\n"))

    if not args.quiet:
        llm = agent.get_llm_name() if agent.llmclient else "(none)"
        sys.stderr.write(c(DIM, f"[gacli] LLM [{agent.llm_no}] {llm}\n"))

    threading.Thread(target=agent.run, daemon=True).start()
    try:
        rc = run_once(agent, prompt, raw=args.raw, stream=not args.no_stream)
    finally:
        agent.abort()
    sys.exit(rc)

if __name__ == '__main__':
    main()
