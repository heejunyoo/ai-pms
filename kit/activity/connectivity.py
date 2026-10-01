"""Strict, offline connectivity allowlist; no raw tool payloads."""
import re
FIELDS = {'server','tool','status','duration_ms','operation','resources','artifact_refs'}
PRIVATE = re.compile(r'(?i)([a-z][a-z0-9+.-]*://|www\.|[/\\]|\bBearer\s|\b(?:sk|ghp|github_pat|xox[baprs])[-_][A-Za-z0-9_-]{8,}|\bAIza[A-Za-z0-9_-]{20,}|(?:password|secret|token|api[_ -]?key)\s*[:=]|\b(?:select|insert|update|delete)\s+.*\b(?:from|into|set)\b)')
def ident(v):
    return isinstance(v,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}',v) is not None and not PRIVATE.search(v)
def valid(c, configured=False):
    if not isinstance(c,dict) or set(c)!=FIELDS: return False
    if any(c[k] is not None and not ident(c[k]) for k in ('server','tool')): return False
    if c['status'] not in (('configured','unknown') if configured else ('requested','completed','failed','unknown')): return False
    if c['duration_ms'] is not None and (type(c['duration_ms']) is not int or not 0<=c['duration_ms']<=86400000): return False
    if c['operation'] not in ('read','write','delete','unknown'): return False
    for field in ('resources','artifact_refs'):
        if not isinstance(c[field],list) or len(c[field])>32: return False
        for r in c[field]:
            if not isinstance(r,dict): return False
            if field=='artifact_refs':
                if set(r)!={'id','version'} or not all(ident(r[k]) for k in r): return False
            else:
                if set(r)!={'id','kind','label','evidence'} or not ident(r['id']): return False
                if r['kind'] not in ('database','document','repository','api','file','unknown') or r['evidence'] not in ('declared','input','output'): return False
                if not isinstance(r['label'],str) or len(r['label'])>160 or PRIVATE.search(r['label']) or any(ord(ch)<32 for ch in r['label']): return False
    return True
