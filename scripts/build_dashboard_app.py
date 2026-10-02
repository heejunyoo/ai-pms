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
    model=portfolio.build_model(portfolio.read_json(DASH/'sample/central.json'),portfolio.read_json(ROOT/'specs/ai-pms-management/sample/catalog-v3.json'),now='2026-10-01T12:00:00Z')
    assert model['evidence_mode']=='synthetic'
    pages={'index.html':portfolio.render_html(model),'empty.html':portfolio.render_html(portfolio.build_model(now='2026-10-01T12:00:00Z'))}
    report=(ROOT/'reports/ai-pms-eli20/index.html').read_text()
    report=re.sub(r'href="../../specs/ai-pms-dashboard/evidence/dashboard.html"','href="/"',report)
    report=re.sub(r'href="../../([^"#]+)"',lambda m:'href="https://github.com/heejunyoo/ai-pms/blob/main/'+m[1]+'"',report)
    pages['report.html']=report
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
