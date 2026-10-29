#!/usr/bin/env python3
"""Rebuild all 13 supplied configuration files; original artwork is absent."""
import argparse,hashlib,json,platform,sys,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from dat_codec import encode,decode
from audit import inspect
PREFIX='Mods/FHD_MODS/FHD_FON/'
def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(data):return hashlib.sha256(data).hexdigest()
def compile_source(root=ROOT):
    files={};configs={};texts={}
    for p in sorted((root/'source').rglob('*.json')):
        name=p.relative_to(root/'source').with_suffix('.dat').as_posix();tree=load(p);data=encode(tree)
        assert decode(data,tree['format'])==tree
        files[name]=data;configs[name]=tree
    for item in load(root/'text-encodings.json'):
        name=item['path'];text=(root/'source'/name).read_bytes().decode(item['source_encoding']);texts[name]=text;files[name]=text.encode(item['runtime_encoding'])
    return files,configs,texts

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--strict-original',action='store_true');p.add_argument('--require-complete',action='store_true');p.add_argument('--output-dir',type=Path,default=ROOT/'dist');a=p.parse_args()
    files,configs,texts=compile_source();expected=load(ROOT/'original-file-sha256.json');assert set(files)==set(expected),'Runtime file list changed'
    actual={name:sha(data) for name,data in files.items()};changed=[name for name in actual if actual[name]!=expected[name]]
    if a.strict_original and changed:raise SystemExit('Original hash mismatch: '+repr(changed))
    audit=inspect(configs,texts)
    report={'status':'PASS: original configuration/code snapshot rebuilt; artwork missing from input','configuration_build_passed':True,'full_mod_complete':False,'runtime_files':len(files),'dat_files':len(configs),'byte_identical_files':len(files)-len(changed),'different_files':changed,'prebuilt_runtime_inputs_used':False,'live_game_executed':False,'sha256':actual,'python':platform.python_version(),'zlib':zlib.ZLIB_RUNTIME_VERSION,'resource_audit':audit}
    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    (out/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if a.require_complete:raise SystemExit('Incomplete original upload: no background artwork / PKG files. See build-report.json. No complete mod ZIP produced.')
    target=out/'FHD_FON_CONFIGS_ONLY_FROM_SOURCE.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(PREFIX+name,(2026,10,29,0,0,0));info.external_attr=0o100644<<16;z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    print(json.dumps({'configuration_build':'PASS','files':len(files),'identical':len(files)-len(changed),'full_mod_complete':False,'asset_aliases':audit['background_alias_count'],'unique_asset_paths':audit['unique_background_paths'],'missing_exact_local_aliases':len(audit['local_missing_exact_alias_references']),'dependency_cycle':audit['module_dependency_cycle'],'output':str(target)}))
if __name__=='__main__':main()
