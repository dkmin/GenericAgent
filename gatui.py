"""Terminal CLI frontend for GenericAgent.

Usage: python gatui.py [--llm_no N]

Slash commands: /help /status /stop /new /restore /continue [n] /llm [n] /quit
During streaming, Ctrl-C aborts the current task without exiting.
"""
import os, sys, re, time, queue, threading, argparse, signal, codecs

try: import termios, tty, select; _RAW_OK = sys.stdin.isatty()
except Exception: _RAW_OK = False

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
sys.path.insert(0, os.path.join(script_dir, 'frontends'))

from agentmain import GeneraticAgent
import chatapp_common  # installs /continue + reset_conversation patches
from chatapp_common import HELP_TEXT, format_restore
from continue_cmd import handle_frontend_command, reset_conversation

USE_COLOR = sys.stdout.isatty() and os.environ.get('NO_COLOR') is None
def c(code, s): return f"\033[{code}m{s}\033[0m" if USE_COLOR else s
DIM, BOLD, CYAN, GREEN, YELLOW, RED, MAGENTA = '2', '1', '36', '32', '33', '31', '35'

# Strip thinking/summary tags and turn markers for cleaner CLI output.
TURN_RE = re.compile(r'\**LLM Running \(Turn \d+\) \.\.\.\*\**')
THINK_RE = re.compile(r'<thinking>.*?</thinking>', re.DOTALL)
SUMMARY_RE = re.compile(r'<summary>.*?</summary>', re.DOTALL)

def clean(text):
    text = THINK_RE.sub('', text)
    text = SUMMARY_RE.sub('', text)
    text = TURN_RE.sub(c(DIM, '─── turn ───'), text)
    return text

def print_banner(agent):
    print(c(BOLD, "GenericAgent TUI"))
    llm = agent.get_llm_name() if agent.llmclient else "(none)"
    print(c(DIM, f"LLM [{agent.llm_no}] {llm}   /help for commands, /quit to exit"))
    print()

def cmd_status(agent):
    state = '🔴 running' if agent.is_running else '🟢 idle'
    llm = agent.get_llm_name() if agent.llmclient else '미설정'
    return f"상태: {state}\nLLM: [{agent.llm_no}] {llm}"

def cmd_llm(agent, parts):
    if not agent.llmclient: return "❌ 사용 가능한 LLM 설정이 없습니다"
    if len(parts) > 1:
        try:
            agent.next_llm(int(parts[1]))
            return f"✅ [{agent.llm_no}] {agent.get_llm_name()} 로 전환했습니다"
        except Exception:
            return f"사용법: /llm <0-{len(agent.list_llms()) - 1}>"
    return "LLMs:\n" + "\n".join(f"{'→' if cur else '  '} [{i}] {name}"
                                  for i, name, cur in agent.list_llms())

def cmd_restore(agent):
    try:
        info, err = format_restore()
        if err: return err
        restored, fname, count = info
        agent.abort()
        agent.history.extend(restored)
        return f"✅ {count}턴의 대화를 복원했습니다\n출처: {fname}"
    except Exception as e:
        return f"❌ 복원 실패: {e}"

def handle_slash(agent, line):
    parts = line.split()
    op = parts[0].lower()
    if op in ('/quit', '/exit'): return 'QUIT'
    if op == '/help':    return HELP_TEXT
    if op == '/status':  return cmd_status(agent)
    if op == '/stop':    agent.abort(); return "⏹️ 중지 요청을 보냈습니다"
    if op == '/new':     return reset_conversation(agent)
    if op == '/restore': return cmd_restore(agent)
    if op == '/continue':return handle_frontend_command(agent, line)
    if op == '/llm':     return cmd_llm(agent, parts)
    return None  # not a slash command we handle

def stream_response(agent, prompt):
    """Print rolling response incrementally; on Ctrl-C abort the turn."""
    dq = agent.put_task(prompt, source="user")
    printed = 0
    last = ''
    print(c(CYAN, "assistant▌"), flush=True)
    try:
        while True:
            try: item = dq.get(timeout=1)
            except queue.Empty: continue
            if 'next' in item:
                last = clean(item['next'])
                if len(last) > printed:
                    sys.stdout.write(last[printed:]); sys.stdout.flush()
                    printed = len(last)
            if 'done' in item:
                final = clean(item['done'])
                # Re-render only if final differs after cleaning (rare).
                if final != last:
                    if len(final) > printed:
                        sys.stdout.write(final[printed:])
                break
    except KeyboardInterrupt:
        agent.abort()
        print(c(YELLOW, "\n[aborted]"))
        # Drain queue briefly so next turn starts clean.
        deadline = time.time() + 2
        while time.time() < deadline:
            try: dq.get(timeout=0.1)
            except queue.Empty: break
            except Exception: break
        return
    print()  # trailing newline

def _read_line_raw(prompt_str):
    """Raw-mode line reader. ESC clears the buffer; Enter submits; Ctrl-D on empty → None.
    Ignores arrow keys / other escape sequences. Decodes UTF-8 incrementally for CJK."""
    sys.stdout.write(prompt_str); sys.stdout.flush()
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
    chars = []
    def redraw():
        sys.stdout.write('\r\033[2K' + prompt_str + ''.join(chars)); sys.stdout.flush()
    try:
        tty.setcbreak(fd)
        while True:
            b = os.read(fd, 1)
            if not b: return None
            if b == b'\x03': raise KeyboardInterrupt
            if b == b'\x04' and not chars:
                sys.stdout.write('\n'); return None
            if b in (b'\r', b'\n'):
                sys.stdout.write('\n'); sys.stdout.flush()
                return ''.join(chars)
            if b in (b'\x7f', b'\x08'):
                if chars: chars.pop(); redraw()
                continue
            if b == b'\x1b':
                r, _, _ = select.select([fd], [], [], 0.05)
                if r:
                    os.read(fd, 16)  # consume & ignore escape sequence
                    continue
                if chars:
                    chars.clear()
                    decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
                    redraw()
                continue
            ch = decoder.decode(b)
            if not ch: continue
            if ord(ch[0]) < 0x20: continue
            chars.append(ch)
            sys.stdout.write(ch); sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def read_multiline():
    """Read one logical input. Trailing backslash continues onto next line.
    ESC (when supported) clears the current line buffer."""
    prompt_main = c(GREEN, "you▶ ")
    prompt_cont = c(DIM, ".... ")
    reader = _read_line_raw if _RAW_OK else (lambda p: input(p))
    try: first = reader(prompt_main)
    except EOFError: return None
    if first is None: return None
    if not first.endswith('\\'): return first
    buf = [first[:-1]]
    while True:
        try: nxt = reader(prompt_cont)
        except EOFError: break
        if nxt is None: break
        if nxt.endswith('\\'): buf.append(nxt[:-1])
        else: buf.append(nxt); break
    return '\n'.join(buf)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--llm_no', type=int, default=0)
    args = parser.parse_args()

    agent = GeneraticAgent()
    if agent.llmclient is None:
        print(c(RED, "⚠️  사용 가능한 LLM 연결이 없습니다. mykey.py를 설정해주세요."))
        sys.exit(1)
    if args.llm_no:
        try: agent.next_llm(args.llm_no)
        except Exception as e: print(c(YELLOW, f"--llm_no {args.llm_no} 적용 실패: {e}"))
    threading.Thread(target=agent.run, daemon=True).start()
    print_banner(agent)

    while True:
        line = read_multiline()
        if line is None:
            print(); break
        line = line.strip()
        if not line: continue

        if line.startswith('/'):
            result = handle_slash(agent, line)
            if result == 'QUIT': break
            if result is not None:
                print(c(MAGENTA, result)); print()
                continue
            # Unknown /command falls through to LLM as a regular prompt.

        try:
            stream_response(agent, line)
        except KeyboardInterrupt:
            agent.abort()
            print(c(YELLOW, "\n[aborted]"))

    agent.abort()
    print(c(DIM, "bye."))

if __name__ == '__main__':
    main()
