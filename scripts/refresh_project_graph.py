#!/usr/bin/env python3
"""Refresh this project's local AST graph; never sends code to a model API."""
import collections
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / 'graphify-out'
    # extract keeps the explicit code-only boundary; update also discovers
    # fenced code in Markdown. AST's content cache still avoids unchanged work.
    command = ['graphify', 'extract', str(ROOT), '--code-only', '--no-cluster', '--force']
    subprocess.run(command, cwd=ROOT, check=True)
    path = out / 'graph.json'
    graph = json.loads(path.read_text())
    raw_nodes = graph['nodes']
    excluded_ids = {n['id'] for n in raw_nodes if n.get('file_type') == 'document' or Path(n.get('source_file', '')).suffix.lower() in {'.md', '.txt'}}
    nodes = graph['nodes'] = [n for n in raw_nodes if n['id'] not in excluded_ids]
    edge_key = 'edges' if 'edges' in graph else 'links'
    edges = graph[edge_key] = [e for e in graph[edge_key] if e['source'] not in excluded_ids and e['target'] not in excluded_ids]
    ids = {n['id'] for n in nodes}
    if len(ids) != len(nodes):
        raise ValueError('Duplicate AST node IDs')
    # Raw extraction can refer to external/unresolved call targets. Preserve
    # these as explicit unresolved references, never as implemented services.
    dangling = sorted({e[k] for e in edges for k in ('source', 'target')} - ids)
    nodes.extend(dict(id=id, label=id, file_type='unresolved-reference',
                      source_file='', source_location='', _origin='unresolved',
                      resolution='not_resolved_by_ast') for id in dangling)
    ids = {n['id'] for n in nodes}
    assert all(e['source'] in ids and e['target'] in ids for e in edges)
    graph['scope'] = {'mode': 'local-code-only-ast', 'semantic_model_calls': False, 'cached_document_nodes_removed': len(excluded_ids),
                      'unresolved_references': len(dangling),
                      'runtime_integration_proven': False}
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + '\n')
    counts = collections.Counter(n.get('source_file', '').split('/')[0]
                                 for n in nodes if n.get('source_file'))
    manifest = dict(mode='local-code-only-ast', nodes=len(nodes), edges=len(edges),
                    unresolved_references=len(dangling), endpoints_valid=True,
                    graph_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    node_groups=dict(counts), semantic_model_calls=False,
                    runtime_integration_proven=False, generated_copies_included=True)
    (out / 'validation.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (out / 'GRAPH_REPORT.md').write_text(
        '# AI PMS local code graph\n\n'
        f"{len(nodes)} nodes, {len(edges)} edges; {len(dangling)} unresolved references. "
        'All edge endpoints exist after explicit unresolved-reference normalization.\n\n'
        'AST extraction only. Docs, screenshots and JSONL telemetry are not semantically '
        'indexed. No model API call, runtime observation, clustering or integration proof. '
        'Generated/static copies and tests are included; node counts are not product size '
        'or implementation completion.\n\n'
        'Canonical roles and update/query instructions: ../docs/project-architecture.md. '
        'This graph and its cache are excluded from public export.\n')
    print(f"Graph PASS: {len(nodes)} nodes, {len(edges)} edges; "
          f"{len(dangling)} explicit unresolved references; local AST only")


if __name__ == '__main__':
    main()
