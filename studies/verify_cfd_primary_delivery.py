"""Audit live dependencies and all declared native bytes before loading reducers."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def verify_files(base,files):
    # Normalize the declared root (macOS /var is an OS alias); child links remain forbidden.
    base=Path(base).resolve()
    for name,expected in files.items():
        relative=Path(name);path=base/relative
        if relative.is_absolute() or '..' in relative.parts or any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file():
            raise ValueError('missing/unsafe declared file: '+name)
        if digest(path)!=expected:raise ValueError('declared file changed: '+name)
    return len(files)


def verify(source,out):
    identity=json.loads((out/'identity.json').read_text())
    verify_files(ROOT,identity['source_hashes']);verify_files(out/'frozen-source',identity['source_hashes'])
    freeze=json.loads((out/'protocol-freeze.json').read_text())
    verify_files(out,{'protocol-freeze.json':identity['protocol_freeze_sha256'],
                      'legacy-verification-receipt.json':identity['legacy_verification_receipt_sha256']})
    verify_files(source,{'delivery-manifest.json':freeze['old_delivery_sha256'],'analysis.json':freeze['old_analysis_sha256']})
    manifest=json.loads((source/'delivery-manifest.json').read_text())
    legacy=verify_files(ROOT,manifest['files'])
    old=json.loads((source/'protocol.json').read_text())
    dependencies=verify_files(ROOT,old['source_hashes'])
    verify_files(source/'frozen-source',old['source_hashes'])
    # Manifest entry points are already bound by the unchanged legacy delivery.
    native=0
    for u,d in ((5,30),(10,30),(5,60),(10,60)):
        for scale in (1,2,4,8):
            work=source/f're200-u{u}-d{d}-g{scale}'
            entries=json.loads((work/'evidence.json').read_text())['files']
            native+=verify_files(work,{name:value['sha256'] for name,value in entries.items()})
    print(json.dumps({'live_dependency_files':dependencies,'legacy_delivery_files':legacy,
                      'direct_native_records':native,'stage':'hashes verified; recomputing 32 snapshots'}),flush=True)
    sys.path.insert(0,str(ROOT))
    from studies.reprocess_cfd_primary import analyze
    analyze(source,out,True)
    print(json.dumps({'passed':True,'verifier_sha256':digest(Path(__file__)),
                      'live_dependency_files':dependencies,'legacy_delivery_files':legacy,
                      'direct_native_records':native,'analysis_sha256':digest(out/'analysis.json')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    verify(a.source.resolve(),a.out.resolve())
