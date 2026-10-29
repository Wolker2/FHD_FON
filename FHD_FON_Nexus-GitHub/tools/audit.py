"""Audit original background references without changing the mod."""
def parameters(block,path=''):
    for entry in block['entries']:
        name=path+'.'+entry['name'] if path else entry['name']
        if entry['kind']=='block':yield from parameters(entry['value'],name)
        else:yield name,entry['value']

def inspect(configs,texts):
    aliases={}
    for name,tree in configs.items():
        if name.endswith('CacheData.dat'):
            for key,value in parameters(tree['root']):aliases.setdefault(key,[]).append({'module':name.split('/')[0],'value':value})
    references=[]
    for name,tree in configs.items():
        if not name.endswith('Main.dat'):continue
        for parent in tree['root']['entries']:
            if parent['kind']!='block' or parent['name']!='FHDDynamicBG':continue
            for record in parent['value']['entries']:
                if record['kind']!='block':continue
                values=dict(parameters(record['value']));requirement=values.get('requirement','')
                for field,value in values.items():
                    if value.startswith('Bm.'):
                        exact=value in aliases
                        references.append({'module':name.split('/')[0],'record':record['name'],'field':field,'requirement':requirement,'alias':value,'exact_in_supplied_cache':exact,'case_insensitive_in_supplied_cache':value.casefold() in {k.casefold() for k in aliases}})
    assets=[]
    for name,tree in configs.items():
        if name.endswith('CacheData.dat'):
            for alias,value in parameters(tree['root']):
                if value.lower().endswith(('.gi','.gai','.png','.jpg')):assets.append({'module':name.split('/')[0],'alias':alias,'path':value,'expected_provider':'optional_external_mod' if value.startswith('Mods\\') and not value.startswith('Mods\\FHD_MODS\\FHD_FON\\') else 'this_mod','present_in_upload':False})
    local_requirements={'','FHD_MODSFHD_FONFHDBG','FHD_MODSFHD_FONFHDNightBG','FHD_MODSFHD_FONFHDDynamicBG'}
    metadata={}
    for name,text in texts.items():
        if name.endswith('ModuleInfo.txt'):metadata[name.split('/')[0]]={line.partition('=')[0]:line.partition('=')[2] for line in text.splitlines() if line.startswith(('Name=','Dependence='))}
    dependency_cycle=metadata.get('FHDBG',{}).get('Dependence')=='FHDDynamicBG' and metadata.get('FHDDynamicBG',{}).get('Dependence')=='FHDBG'
    absent=[r for r in references if not r['exact_in_supplied_cache']]
    return {'runtime_assets_complete':False,'background_alias_count':len(assets),'unique_background_paths':len({r['path'].replace('\\','/').casefold() for r in assets}),'missing_own_unique_asset_paths':len({r['path'].replace('\\','/').casefold() for r in assets if r['expected_provider']=='this_mod'}),'external_asset_alias_count':sum(r['expected_provider']=='optional_external_mod' for r in assets),'assets':assets,'main_background_references':len(references),'missing_exact_alias_references':absent,'local_missing_exact_alias_references':[r for r in absent if r['requirement'] in local_requirements],'optional_external_alias_references':[r for r in references if r['requirement'] not in local_requirements],'module_dependency_cycle':dependency_cycle,'cycle':['FHDBG','FHDDynamicBG','FHDBG'] if dependency_cycle else [],'notes':['Missing exact references are original findings, not introduced by source recovery.','Case-insensitive comparison is diagnostic only; game resolution was not executed.','Optional third-party background packs are not included in this upload.']}
