"""Recheck saved release evidence; remote bytes were fetched after deployment."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    evidence = json.loads((HERE / 'release-evidence.json').read_text())
    assert evidence['public_url'] == 'https://harness-kit.vercel.app'
    assert evidence['deployment_url'].startswith('https://')
    assert evidence['checks'] and all(c['exit_code'] == 0 for c in evidence['checks'])
    for item in evidence['installed_files']:
        assert sha(item['installed']) == sha(item['staged']) == item['sha256'], item
    assert len(evidence['public_artifacts']) >= 5
    for item in evidence['public_artifacts']:
        assert item['url'].startswith(evidence['public_url'] + '/')
        assert sha(item['local']) == sha(item['downloaded']) == item['sha256'], item
    continuation = (HERE.parent.parent / 'NEXT_SESSION.md').read_text()
    assert '서로 다른 두 사용자 환경' in continuation
    assert '중앙 서비스' in continuation and '아직 구현되지 않았습니다' in continuation
    print('Installed guard, public HTML/ZIP byte evidence and central PMS continuation verified')

if __name__ == '__main__':
    main()
