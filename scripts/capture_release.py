#!/usr/bin/env python3
"""Compare public production bytes with reviewed local static artifacts."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
KIT=Path.home()/'.claude/harness/site/public'
def fetch(pair):
    url,path=pair
    with urlopen(Request(url,headers={'User-Agent':'AI-PMS-release-check'}),timeout=25) as response:
        data=response.read();headers={k:response.headers.get(k) for k in ['Content-Security-Policy','X-Content-Type-Options','X-Frame-Options']}
    expected=path.read_bytes();assert data==expected,'Production bytes differ: '+url
    assert headers['X-Content-Type-Options']=='nosniff',url
    return {'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes_equal':True,'security_headers':headers}
def main():
    manifest=json.loads((KIT/'manifest.json').read_text());pairs=[('https://harness-kit.vercel.app/'+name,KIT/name) for name in list(manifest['routes'])+['manifest.json','implementation.zip','reference-ko.zip','reference-en.zip']]
    public=ROOT/'apps/dashboard/public'
    pairs += [('https://ai-pms-dashboard.vercel.app/'+('' if name=='index.html' else name),public/name) for name in ['index.html','empty.html','report.html','snapshot.json']]
    with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(fetch,pairs))
    for result in results:
        if result['url'].endswith(('.html','vercel.app/')):assert result['security_headers']['Content-Security-Policy'],result['url']
    try:
        with urlopen(Request('https://ai-pms-dashboard.vercel.app/.env.local',method='HEAD'),timeout=15) as r:status=r.status
    except HTTPError as e:status=e.code
    assert status==404,'Unexpected env file route status'
    proof={'production_bytes':results,'env_route_status':status,'evidence_mode':'synthetic','personal_logs_uploaded':False}
    (ROOT/'specs/ai-pms-connectivity/public-bytes.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('PASS:',len(results),'production pages/bundles exactly match; env route404')
if __name__=='__main__':main()
