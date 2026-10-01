#!/usr/bin/env python3
"""핸드오프 계획 / 패킷 / 반환값 검증기.

    validate.py plan   <plan.json>
    validate.py packet <packet.json>
    validate.py result <result.json> [--plan <plan.json> | --packet <packet.json>]
    validate.py emit   <plan.json> <task_id>     # 디스패치용 프롬프트 블록 출력
    validate.py selftest                         # 설치 확인: 검출이 살아 있는지 스스로 검사

ERROR 가 하나라도 있으면 exit 1. WARN 은 exit 0 (읽고 사람이 판단한다).
의존성 없음 — 여기서 쓰는 JSON Schema 키워드만 직접 구현한다.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 종료 조건에 들어가면 판정이 불가능해지는 표현
VAGUE = [
    "적절히", "적당히", "최대한", "가능하면", "필요시", "필요하면", "충분히",
    "알아서", "등등", "기타 등", "properly", "appropriately", "as needed",
    "if possible", "reasonable", "make sure it works",
]
WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}
EXEC_TOOLS = {"Bash", "PowerShell"}

_SCHEMA_CACHE = {}


def schema(name):
    if name not in _SCHEMA_CACHE:
        _SCHEMA_CACHE[name] = json.loads((HERE / name).read_text(encoding="utf-8"))
    return _SCHEMA_CACHE[name]


# ---------------------------------------------------------------- schema 검사

def validate(node, sch, path, errs):
    """이 디렉터리의 스키마들이 쓰는 키워드만 검사한다."""
    if "$ref" in sch:
        validate(node, schema(sch["$ref"]), path, errs)
        return

    t = sch.get("type")
    if t and not _type_ok(node, t):
        errs.append(f"{path}: 타입이 {t} 여야 하는데 {type(node).__name__} 이다")
        return

    if "enum" in sch and node not in sch["enum"]:
        errs.append(f"{path}: {sch['enum']} 중 하나여야 하는데 {node!r} 이다")

    if isinstance(node, str):
        if len(node) < sch.get("minLength", 0):
            errs.append(f"{path}: 최소 {sch['minLength']}자 필요 (현재 {len(node)}자)")
        pat = sch.get("pattern")
        if pat and not re.match(pat, node):
            errs.append(f"{path}: 형식 위반 (pattern {pat})")

    if isinstance(node, (int, float)) and not isinstance(node, bool):
        if "minimum" in sch and node < sch["minimum"]:
            errs.append(f"{path}: {sch['minimum']} 이상이어야 한다 (현재 {node})")
        if "maximum" in sch and node > sch["maximum"]:
            errs.append(f"{path}: {sch['maximum']} 이하여야 한다 (현재 {node})")

    if isinstance(node, list):
        if len(node) < sch.get("minItems", 0):
            errs.append(f"{path}: 항목이 최소 {sch['minItems']}개 필요 (현재 {len(node)}개)")
        if "items" in sch:
            for i, item in enumerate(node):
                validate(item, sch["items"], f"{path}[{i}]", errs)

    if isinstance(node, dict):
        if len(node) < sch.get("minProperties", 0):
            errs.append(f"{path}: 비어 있으면 안 된다")
        for key in sch.get("required", []):
            if key not in node:
                errs.append(f"{path}.{key}: 필수 필드가 없다")
        props = sch.get("properties", {})
        if sch.get("additionalProperties") is False:
            for key in node:
                if key not in props:
                    errs.append(f"{path}.{key}: 스키마에 없는 필드다")
        for key, sub in props.items():
            if key in node:
                validate(node[key], sub, f"{path}.{key}", errs)


def _type_ok(node, t):
    return {
        "object": lambda n: isinstance(n, dict),
        "array": lambda n: isinstance(n, list),
        "string": lambda n: isinstance(n, str),
        "boolean": lambda n: isinstance(n, bool),
        "integer": lambda n: isinstance(n, int) and not isinstance(n, bool),
        "number": lambda n: isinstance(n, (int, float)) and not isinstance(n, bool),
    }.get(t, lambda n: True)(node)


# ---------------------------------------------------------------- 패킷 의미 검사

def _obj(node, key):
    """present-but-null 도 {} 로 다룬다 — .get(k, {}) 는 키가 **없을 때만** 기본값을 준다."""
    v = node.get(key)
    return v if isinstance(v, dict) else {}


def touched_files(p):
    paths = [e.get("path") for e in (p.get("edit_points") or []) if isinstance(e, dict)]
    return [x for x in paths + (p.get("files_to_create") or []) if isinstance(x, str)]


def haiku_gaps(p):
    """Haiku 에 넘기려면 채워야 할 것. 비어 있으면 적합."""
    gaps = []
    files = touched_files(p)
    if len(files) > 3:
        gaps.append(f"대상 파일 {len(files)}개 (3개 이하여야 함)")
    if p.get("kind") == "implement":
        pts = p.get("edit_points") or []
        if not pts and not p.get("files_to_create"):
            gaps.append("고칠 곳도 만들 파일도 지정되지 않음")
        elif any(not e.get("symbol") for e in pts if isinstance(e, dict)):
            gaps.append("심볼이 특정되지 않은 edit_point 있음")
    if not p.get("acceptance"):
        gaps.append("acceptance 없음 (기계 판정 불가)")
    if not p.get("reference_impl"):
        gaps.append("reference_impl 없음 (흉내낼 본보기가 없으면 자기 스타일로 쓴다)")
    return gaps


def check_packet(p, errs, warns, prefix="", in_plan=False):
    kind = p.get("kind")
    tid = p.get("task_id", "?")
    at = f"{prefix}{tid}"

    # 종류별 필수 — JSON Schema 로 표현하지 않고 여기서 본다(에러 메시지가 낫다)
    if kind in ("implement", "verify") and not p.get("acceptance"):
        errs.append(f"{at}: kind={kind} 인데 acceptance 가 없다 — 하위 모델이 성공을 스스로 선언하게 된다")
    if kind == "implement" and not (p.get("edit_points") or p.get("files_to_create")):
        errs.append(f"{at}: kind=implement 인데 edit_points/files_to_create 가 둘 다 없다 — 어디를 고칠지 모른다")
    if kind == "investigate" and not p.get("return_schema"):
        errs.append(f"{at}: kind=investigate 인데 return_schema 가 없다 — 산문이 돌아온다")
    if kind == "implement" and not (WRITE_TOOLS & set(p.get("tools_allowed") or [])):
        errs.append(f"{at}: kind=implement 인데 tools_allowed 에 쓰기 도구가 없다 — 실행 자체가 불가능하다")

    acc = p.get("acceptance") or {}
    if acc and EXEC_TOOLS.isdisjoint(p.get("tools_allowed") or []):
        errs.append(f"{at}: acceptance 명령이 있는데 tools_allowed 에 Bash/PowerShell 이 없다 — 돌릴 수 없다")

    # 모델 등급
    gaps = haiku_gaps(p)
    hint = p.get("model_hint")
    if hint == "haiku" and gaps:
        warns.append(f"{at}: haiku 에는 부족하다 — {', '.join(gaps)}. sonnet 으로 올리거나 태스크를 더 쪼개라")
    # Missing hints inherit the parent; packet completeness is not a model recommendation.

    # 소프트 신호
    for i, cond in enumerate(p.get("done_when") or []):
        hit = [v for v in VAGUE if isinstance(cond, str) and v in cond]
        if hit:
            warns.append(f"{at}.done_when[{i}]: 모호한 표현 {hit} — 참/거짓 판정이 되는 문장인지 확인")

    # 계획 안에서는 depends_on 과 context.excluded 가 같은 역할을 하므로 중복 경고하지 않는다
    if not in_plan and p.get("already_tried") == []:
        warns.append(f"{at}: already_tried 가 비었다 — 정말 아무것도 안 해봤는지 확인 (중복 실행 1위 실패모드)")

    if not _obj(p, "context").get("spec_ref"):
        warns.append(f"{at}: context.spec_ref 가 없다 — 근거 문서 없이 넘기면 하위 모델이 지어낸다")

    facts = _obj(p, "context").get("facts") or []
    total = sum(len(f) for f in facts if isinstance(f, str))
    if total > 4000:
        warns.append(f"{at}: context.facts 가 {total}자 — 파일 덤프에 가깝다. 경로로 바꿔라")

    obj = p.get("objective")
    if isinstance(obj, str) and (obj.count("\n") >= 2 or re.match(r"^\s*\d[.)]", obj)):
        warns.append(f"{at}: objective 가 절차처럼 보인다 — 목표 한 문장으로 줄여라")

    depth = _obj(p, "budget").get("max_spawn_depth")
    if isinstance(depth, int) and depth > 3:
        warns.append(
            f"{at}: max_spawn_depth={depth} — 기본 상한은 3계층이다. "
            "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH 를 올리지 않으면 상한에서 Agent 툴이 회수된다"
        )

    if (_obj(p, "on_failure").get("partial_ok") is False
            and _obj(p, "budget").get("max_turns", 99) < 5):
        warns.append(f"{at}: partial_ok=false 인데 max_turns 가 작다 — 예산 부족으로 전량 실패할 수 있다")


# ---------------------------------------------------------------- 계획 교차검사

def check_plan(plan, errs, warns):
    tasks = plan.get("tasks") or []
    ids = [t.get("task_id") for t in tasks if isinstance(t, dict)]
    phase_ids = {ph.get("id") for ph in (plan.get("phases") or []) if isinstance(ph, dict)}

    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errs.append(f"task_id 중복: {sorted(dupes)}")

    if plan.get("open_decisions") and any(t.get("kind") == "implement" for t in tasks):
        errs.append(
            f"open_decisions 가 {len(plan['open_decisions'])}건 남았는데 implement 태스크가 있다 — "
            "설계 판단은 상위 모델이 끝내고 넘긴다"
        )

    graph = {}
    for t in tasks:
        if not isinstance(t, dict):
            continue
        tid = t.get("task_id")
        ph = t.get("phase")
        if ph is not None and ph not in phase_ids:
            errs.append(f"{tid}: phase={ph!r} 가 phases 에 없다")
        deps = t.get("depends_on") or []
        for d in deps:
            if d not in ids:
                errs.append(f"{tid}: depends_on 의 {d!r} 가 존재하지 않는 태스크다")
        graph[tid] = [d for d in deps if d in ids]

    cycle = find_cycle(graph)
    if cycle:
        errs.append(f"depends_on 순환: {' -> '.join(cycle)}")

    # 같은 Phase 안에서 파일이 겹치면 병렬 실행이 불가능하다
    by_phase = {}
    for t in tasks:
        if isinstance(t, dict):
            by_phase.setdefault(t.get("phase"), []).append(t)
    for ph, group in by_phase.items():
        seen = {}
        for t in group:
            for f in touched_files(t):
                if f in seen and seen[f] not in (t.get("depends_on") or []):
                    warns.append(
                        f"phase={ph}: {seen[f]} 와 {t.get('task_id')} 가 같은 파일 {f} 를 만진다 — "
                        "병렬로 못 돌린다. 합치거나 depends_on 으로 순서를 주라"
                    )
                seen.setdefault(f, t.get("task_id"))

    for ph in plan.get("phases") or []:
        if isinstance(ph, dict) and not by_phase.get(ph.get("id")):
            warns.append(f"phase={ph.get('id')}: 소속 태스크가 없다")

    for t in tasks:
        if isinstance(t, dict):
            check_packet(t, errs, warns, prefix="task ", in_plan=True)


def find_cycle(graph):
    state, stack = {}, []

    def walk(n):
        if state.get(n) == 1:
            return stack[stack.index(n):] + [n]
        if state.get(n) == 2:
            return None
        state[n] = 1
        stack.append(n)
        for m in graph.get(n, []):
            hit = walk(m)
            if hit:
                return hit
        stack.pop()
        state[n] = 2
        return None

    for node in graph:
        hit = walk(node)
        if hit:
            return hit
    return None


# ---------------------------------------------------------------- 반환값 검사

def check_result(r, packet, errs, warns):
    status = r.get("status")
    checks = r.get("done_when_check") or []

    unmet = [c for c in checks if isinstance(c, dict) and c.get("met") is False]
    if status == "complete" and unmet:
        errs.append(f"status=complete 인데 done_when 미충족 {len(unmet)}건 — partial 이거나 failed 다")
    if status == "complete" and r.get("unmet_constraints"):
        errs.append("status=complete 인데 unmet_constraints 가 비어 있지 않다")
    if status == "partial" and not r.get("next_packet_hint"):
        warns.append("status=partial 인데 next_packet_hint 가 없다 — 남은 조각을 쪼갤 근거가 없다")

    evidence = sum(len(c.get("evidence") or "") for c in checks if isinstance(c, dict))
    conf = r.get("confidence")
    if isinstance(conf, (int, float)) and not isinstance(conf, bool) and conf >= 0.9 and evidence < 50:
        warns.append(f"confidence={conf} 인데 evidence 총량이 {evidence}자 — 근거 없는 자신감이다")

    if packet is None:
        warns.append("--plan / --packet 없이 검사했다 — task_id·개수·범위 대조를 건너뛰었다")
        return

    kind = packet.get("kind")
    if r.get("task_id") != packet.get("task_id"):
        errs.append(f"task_id 불일치: 패킷 {packet.get('task_id')!r} vs 반환 {r.get('task_id')!r}")

    expected = len(packet.get("done_when") or [])
    if expected and len(checks) != expected:
        errs.append(f"done_when_check 개수 불일치: 패킷 {expected}개 vs 반환 {len(checks)}개 — 1:1 대응해야 한다")

    if kind == "investigate" and status != "failed" and "payload" not in r:
        errs.append(f"payload: kind=investigate, status={status} 인데 산출물이 없다")

    acc = packet.get("acceptance") if isinstance(packet.get("acceptance"), dict) else None
    run = r.get("acceptance_run") if isinstance(r.get("acceptance_run"), dict) else None
    if acc and status == "complete":
        if not run:
            errs.append("acceptance 가 있는 패킷인데 acceptance_run 이 없다 — 돌리지 않고 complete 를 선언했다")
        else:
            want = acc.get("expect_exit_code")
            if run.get("exit_code") != want:
                errs.append(
                    f"acceptance_run.exit_code={run.get('exit_code')} 인데 기대값은 {want} 다 — complete 가 아니다"
                )
            tail = run.get("output_tail") or ""
            missing = [s for s in (acc.get("expect_contains") or []) if s not in tail]
            if missing:
                warns.append(f"acceptance 기대 문자열이 output_tail 에 없다: {missing} (잘렸을 수 있음)")

    allowed = set(touched_files(packet))
    if allowed:
        stray = [
            f.get("path") for f in (r.get("files_changed") or [])
            if isinstance(f, dict) and f.get("path") not in allowed
        ]
        if stray:
            errs.append(f"범위 이탈: 패킷에 없는 파일을 변경했다 — {stray}")


# ---------------------------------------------------------------- emit

RETURN_LINE = (
    "반드시 아래 JSON 하나만 출력한다(설명 금지). done_when_check 는 위 done_when 과 1:1 개수로 맞춘다. "
    "acceptance.command 를 실제로 실행하고 그 exit_code 와 마지막 출력을 acceptance_run 에 담는다. "
    "지키지 못한 제약은 unmet_constraints 에 적는다 — 비어 있다고 거짓말하지 않는다.\n"
    '{"task_id":"%s","status":"complete|partial|failed","files_changed":[{"path":"","action":"modified","summary":""}],'
    '"acceptance_run":{"command":"","exit_code":0,"output_tail":""},'
    '"done_when_check":[{"condition":"","met":true,"evidence":""}],'
    '"unmet_constraints":[],"confidence":0.0,"notes_for_orchestrator":""}'
)


def emit(plan, task_id):
    task = next((t for t in plan.get("tasks", []) if t.get("task_id") == task_id), None)
    if task is None:
        print(f"ERROR  {task_id!r} 가 계획에 없다. 있는 것: {[t.get('task_id') for t in plan.get('tasks', [])]}")
        return 1

    unfinished = [
        d for d in (task.get("depends_on") or [])
    ]
    print(f"# 작업 지시: {task_id}   (model_hint={task.get('model_hint') or 'inherit'})")
    if unfinished:
        print(f"# 선행 태스크가 끝났는지 먼저 확인: {unfinished}")
    print(f"# 목표(전체): {plan.get('goal')}")
    print(f"# 근거 문서: {plan.get('spec_ref')}  ← 필요한 부분만 읽는다")
    print()
    print("아래 패킷대로만 작업한다. 패킷 밖의 파일을 만들거나 고치지 않는다.")
    print()
    print("```json")
    print(json.dumps(task, ensure_ascii=False, indent=2))
    print("```")
    print()
    print(RETURN_LINE % task_id)
    return 0


# ---------------------------------------------------------------- 설치 확인

# (설명, 계획을 망가뜨리는 함수) — 각 항목이 ERROR 를 최소 1건 내야 검출이 살아 있는 것이다
MUTATIONS = [
    ("필수 필드 삭제", lambda p: p["tasks"][0].pop("objective")),
    ("implement 인데 acceptance 없음", lambda p: p["tasks"][0].pop("acceptance")),
    ("없는 Phase 참조", lambda p: p["tasks"][0].__setitem__("phase", "no-such-phase")),
    ("depends_on 순환", lambda p: p["tasks"][0].__setitem__(
        "depends_on", [p["tasks"][2]["task_id"]])),
    ("미해결 설계 판단 잔존", lambda p: p["open_decisions"].append("undecided")),
]


def selftest():
    """example 파일로 정상 통과와 결함 검출을 모두 확인한다. 배치 직후 1회 실행용."""
    import copy

    ok = True

    def line(label, passed, detail=""):
        nonlocal ok
        ok = ok and passed
        print(f"{'PASS' if passed else 'FAIL'}  {label}{'  — ' + detail if detail else ''}")

    errs = []
    plan = load(HERE / "example.plan.json", errs)
    result = load(HERE / "example.result.json", errs)
    if errs:
        for e in errs:
            print(f"FAIL  예시 파일 로드 — {e}")
        return 1

    e, w = [], []
    validate(plan, schema("plan.schema.json"), "plan", e)
    check_plan(plan, e, w)
    line("정상 계획 통과", not e, "; ".join(e))
    line("기본 예시 모델 상속", all(t.get("model_hint") == "inherit" for t in plan["tasks"]))

    e, w = [], []
    validate(result, schema("result.schema.json"), "result", e)
    packet = next((t for t in plan["tasks"] if t["task_id"] == result["task_id"]), None)
    check_result(result, packet, e, w)
    line("정상 반환 통과", not e, "; ".join(e))

    for label, mutate in MUTATIONS:
        broken = copy.deepcopy(plan)
        mutate(broken)
        e, w = [], []
        validate(broken, schema("plan.schema.json"), "plan", e)
        check_plan(broken, e, w)
        line(f"결함 검출: {label}", bool(e), "검출되지 않았다" if not e else "")

    print(f"\n{'ALL PASS — 스킬이 정상 배치되었다' if ok else 'FAIL — 배치가 불완전하다'}")
    return 0 if ok else 1


# ---------------------------------------------------------------- 진입점

def load(path, errs):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        errs.append(f"{path}: 파일이 없다")
    except json.JSONDecodeError as e:
        errs.append(f"{path}: JSON 파싱 실패 — {e}")
    return None


def main(argv):
    if len(argv) >= 2 and argv[1] == "selftest":
        return selftest()
    if len(argv) < 3 or argv[1] not in ("plan", "packet", "result", "emit"):
        print(__doc__.strip())
        return 2

    kind, target = argv[1], argv[2]
    errs, warns = [], []

    doc = load(target, errs)
    if doc is None:
        _report(kind, errs, warns)
        return 1

    if kind == "emit":
        if len(argv) < 4:
            print("emit 은 task_id 가 필요하다: validate.py emit <plan.json> <task_id>")
            return 2
        return emit(doc, argv[3])

    validate(doc, schema(f"{kind}.schema.json"), kind, errs)

    if kind == "plan":
        check_plan(doc, errs, warns)
    elif kind == "packet":
        check_packet(doc, errs, warns)
    else:
        packet = None
        for flag in ("--packet", "--plan"):
            if flag in argv and argv.index(flag) + 1 >= len(argv):
                print(__doc__.strip())
                return 2
        if "--packet" in argv:
            packet = load(argv[argv.index("--packet") + 1], errs)
        elif "--plan" in argv:
            plan = load(argv[argv.index("--plan") + 1], errs)
            if plan:
                packet = next(
                    (t for t in plan.get("tasks", []) if t.get("task_id") == doc.get("task_id")), None
                )
                if packet is None:
                    errs.append(f"반환값의 task_id {doc.get('task_id')!r} 가 계획에 없다")
        check_result(doc, packet, errs, warns)

    _report(kind, errs, warns)
    return 1 if errs else 0


def _report(kind, errs, warns):
    for e in errs:
        print(f"ERROR  {e}")
    for w in warns:
        print(f"WARN   {w}")
    if not errs and not warns:
        print("OK")
    elif not errs:
        print(f"\n통과 (WARN {len(warns)}건 — 읽고 판단한다)")
    else:
        todo = (
            "결과를 수용하지 않는다. 패킷을 고쳐 1회만 재발행한다"
            if kind == "result"
            else "디스패치하지 않는다"
        )
        print(f"\n실패 (ERROR {len(errs)}건) — {todo}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
