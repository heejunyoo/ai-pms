#!/usr/bin/env python3
"""Build a public static sample only. No personal logs or remote receiver."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
DASH=ROOT/'specs/ai-pms-dashboard'
spec=importlib.util.spec_from_file_location('portfolio',DASH/'portfolio.py')
portfolio=importlib.util.module_from_spec(spec);spec.loader.exec_module(portfolio)
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
    pages={'index.html':portfolio.render_html(model),'empty.html':portfolio.render_html(portfolio.build_model(now='2026-10-01T12:00:00Z'))}
    # Authored synthetic phase descriptions affect presentation only, never completion.
    annotations=json.loads((ROOT/'specs/ai-pms-human-projection/sample-human-annotations.json').read_text())
    annotation_json=json.dumps(annotations,ensure_ascii=False).replace('<','\\u003c')
    pages['index.html']=pages['index.html'].replace('</head>','<script type="application/json" id="human-annotations">'+annotation_json+'</script></head>')
    # Authored fictional planning dates belong to the public demo view, never hook telemetry.
    schedule=json.loads((ROOT/'specs/ai-pms-wbs-timeline/sample-schedule.json').read_text())
    schedule_json=json.dumps(schedule,ensure_ascii=False).replace('<','\\u003c')
    pages['index.html']=pages['index.html'].replace('</head>','<script type="application/json" id="sampleSchedule">'+schedule_json+'</script></head>')
    report=(ROOT/'reports/ai-pms-eli20/index.html').read_text()
    report=re.sub(r'href="../../specs/ai-pms-dashboard/evidence/dashboard.html"','href="/"',report)
    report=re.sub(r'href="../../([^"#]+)"',lambda m:'href="https://github.com/heejunyoo/ai-pms/blob/main/'+m[1]+'"',report)
    pages['report.html']=report
    overview=ROOT/'reports/harness-pms-eli20/index.html'
    if overview.exists():pages['overview.html']=overview.read_text()
    headers=[]
    for name,body in pages.items():
        (out/name).write_text(body)
        hashes=["'sha256-"+__import__('base64').b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',body,re.S)]
        csp="default-src 'none'; script-src "+' '.join(hashes)+"; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'"
        route='/' if name=='index.html' else '/'+name
        headers.append({'source':route,'headers':[{'key':'Content-Security-Policy','value':csp}]})
        if name=='index.html':headers.append({'source':'/index.html','headers':[{'key':'Content-Security-Policy','value':csp}]})
    (out/'snapshot.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n')
    (out/'robots.txt').write_text('User-agent: *\nAllow: /\n')
    headers.append({'source':'/(.*)','headers':[{'key':'X-Content-Type-Options','value':'nosniff'},{'key':'X-Frame-Options','value':'DENY'},{'key':'Referrer-Policy','value':'strict-origin-when-cross-origin'}]})
    config={'$schema':'https://openapi.vercel.sh/vercel.json','version':2,'framework':None,'outputDirectory':'public','cleanUrls':False,'headers':headers}
    (ROOT/'apps/dashboard/vercel.json').write_text(json.dumps(config,indent=2)+'\n')
    print('Built synthetic dashboard, empty state, ELI20 report and CSP headers')
if __name__=='__main__':main()
