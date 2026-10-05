#!/usr/bin/env python3
"""Build a public static sample only. No personal logs or remote receiver."""
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
DASH=ROOT/'specs/ai-pms-dashboard'
spec=importlib.util.spec_from_file_location('portfolio',DASH/'portfolio.py')
portfolio=importlib.util.module_from_spec(spec);spec.loader.exec_module(portfolio)
def embedded(body, name, value):
    payload=json.dumps(value,ensure_ascii=False).replace('<','\\u003c')
    return body.replace('</head>','<script type="application/json" id="'+name+'">'+payload+'</script></head>')

def public_adoption():
    fixture=portfolio.read_json(ROOT/'specs/ai-pms-adoption-release/sample-documentary.json')
    store={'version':1,'sources':{}}
    for project in fixture['catalog']['projects']:
        for ref in project['source_refs']:
            store['sources'][portfolio.central.source_key(ref)]=dict(ref,label='가상 도입 예시 · 활동 미관측',evidence_mode='synthetic',events={})
    model=portfolio.build_model(store,fixture['catalog'],now='2026-10-05T00:00:00Z')
    assert model['evidence_mode']=='synthetic'
    assert all(not p['runs'] and not p['sessions'] and p['status']!='complete' for p in model['projects'])
    body=embedded(portfolio.render_html(model),'documentary-data',fixture['documentary'])
    body=embedded(body,'human-annotations',fixture['annotations'])
    # Reuse the private document-first UI while labelling public fictional provenance.
    body=body.replace('실제 프로젝트 · 기존 문서 기준','가상 프로젝트 · 문서 기반 도입 예시')
    notice='<aside class="notice" id="sampleBoundary">'+html.escape(fixture['boundary'])+' <a href="recorded-example.html">합성 실행 기록 예시 보기 →</a> · <a href="adoption-snapshot.json" download>수집 모델 JSON · 문서 작업 제외</a> · <a href="sample-documentary.json" download>전체 가상 문서 입력 JSON</a><p>수집 모델은 현재 관측 상태만 담습니다. 문서 작업과 출처는 전체 가상 문서 입력에 있으며, 이 입력은 빌더용 자료입니다. 스냅샷 가져오기만으로 문서 작업 화면이 재현되지는 않습니다.</p></aside>'
    body=body.replace('<main>','<main>'+notice,1)
    pages={'index.html':body}
    for sid,source in fixture['documentary']['sources'].items():
        assert re.fullmatch(r'[-a-zA-Z0-9_]+',sid)
        pages['source-'+sid+'.html']='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>가상 문서 발췌</title><main><h1>'+html.escape(source['path'])+'</h1><p>'+html.escape(fixture['boundary'])+'</p><pre>'+html.escape(source['excerpt'])+'</pre><a href="index.html#project='+source['project']+'">프로젝트로 돌아가기</a></main></html>'
    return pages,model

def main():
    out=ROOT/'apps/dashboard/public';out.mkdir(parents=True,exist_ok=True)
    live=ROOT/'specs/ai-pms-live/sample'
    use_live=(live/'operations.json').is_file()
    catalog=portfolio.read_json(live/'catalog.json' if use_live else ROOT/'specs/ai-pms-work-management/sample/catalog-work.json')
    store=portfolio.read_json(live/'central.json' if use_live else DASH/'sample/central.json')
    operations=portfolio.read_json(live/'operations.json') if use_live else None
    # New fictional participant environments have zero events; never fabricate hook observations.
    for project in catalog['projects']:
        for ref in project['source_refs']:
            key=portfolio.central.source_key(ref)
            if key not in store['sources']:
                store['sources'][key]=dict(ref,label='합성 예시 · 활동 미관측',evidence_mode='synthetic',events={})
    instant='2026-10-02T12:00:00Z' if use_live else '2026-10-01T12:00:00Z'
    model=portfolio.build_model(store,catalog,now=instant,**({'operations':operations} if use_live else {}))
    assert model['evidence_mode']=='synthetic'
    if use_live: assert model['operations']['version']==1
    pages={'recorded-example.html':portfolio.render_html(model),'empty.html':portfolio.render_html(portfolio.build_model(now='2026-10-01T12:00:00Z'))}
    # Authored synthetic phase descriptions affect presentation only, never completion.
    annotations=json.loads((ROOT/'specs/ai-pms-human-projection/sample-human-annotations.json').read_text())
    pages['recorded-example.html']=embedded(pages['recorded-example.html'],'human-annotations',annotations)
    # Authored fictional planning dates belong to the public demo view, never hook telemetry.
    schedule=json.loads((ROOT/'specs/ai-pms-wbs-timeline/sample-schedule.json').read_text())
    pages['recorded-example.html']=embedded(pages['recorded-example.html'],'sampleSchedule',schedule)
    recorded_notice='<aside class="notice" id="recordedBoundary">합성 실행 기록 예시 · 검사 통과·실패·재검증·승인 대기를 설명하는 가상 기록입니다. 실제 프로젝트 도입, 앱 훅 전달 또는 제공자 실행 성공의 증거가 아닙니다. <a href="index.html">문서 기반 도입 예시로 돌아가기 →</a> · <a href="snapshot.json" download>합성 실행 기록 JSON 다운로드</a></aside>'
    pages['recorded-example.html']=pages['recorded-example.html'].replace('<main>','<main>'+recorded_notice,1)
    adoption_pages,adoption_model=public_adoption()
    pages.update(adoption_pages)
    report=(ROOT/'reports/ai-pms-eli20/index.html').read_text()
    report=re.sub(r'href="../../specs/ai-pms-dashboard/evidence/dashboard.html"','href="/"',report)
    report=re.sub(r'href="../../([^"#]+)"',lambda m:'href="https://github.com/heejunyoo/ai-pms/blob/main/'+m[1]+'"',report)
    pages['report.html']=report
    overview=ROOT/'reports/harness-pms-eli20/index.html'
    if overview.exists():pages['overview.html']=overview.read_text()
    headers=[]
    for name,body in pages.items():
        body=body.replace('<head>', '<head><link rel="icon" href="data:,">', 1)
        (out/name).write_text(body)
        hashes=["'sha256-"+__import__('base64').b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',body,re.S)]
        csp="default-src 'none'; script-src "+' '.join(hashes)+"; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'"
        route='/' if name=='index.html' else '/'+name
        headers.append({'source':route,'headers':[{'key':'Content-Security-Policy','value':csp}]})
        if name=='index.html':headers.append({'source':'/index.html','headers':[{'key':'Content-Security-Policy','value':csp}]})
    (out/'snapshot.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n')
    (out/'adoption-snapshot.json').write_text(json.dumps(adoption_model,ensure_ascii=False,indent=2)+'\n')
    (out/'sample-documentary.json').write_bytes((ROOT/'specs/ai-pms-adoption-release/sample-documentary.json').read_bytes())
    (out/'robots.txt').write_text('User-agent: *\nAllow: /\n')
    headers.append({'source':'/(.*)','headers':[{'key':'X-Content-Type-Options','value':'nosniff'},{'key':'X-Frame-Options','value':'DENY'},{'key':'Referrer-Policy','value':'strict-origin-when-cross-origin'}]})
    config={'$schema':'https://openapi.vercel.sh/vercel.json','version':2,'framework':None,'outputDirectory':'public','cleanUrls':False,'headers':headers}
    (ROOT/'apps/dashboard/vercel.json').write_text(json.dumps(config,indent=2)+'\n')
    print('Built fictional document-first adoption, separate recorded synthetic example, empty state, reports and CSP headers')
if __name__=='__main__':main()
