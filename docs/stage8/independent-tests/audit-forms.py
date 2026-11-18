"""نگاشت کنترل‌ها؛ نتیجهٔ پیدا شدن کنترل جای آزمون معنای قاعده نیست."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
source=json.loads((ROOT/'specs/010-specialist-services/forms-source-map.json').read_text())
native=json.loads((ROOT/'backend/apps/services/schemas.json').read_text())
html=(ROOT/'.tools/reference/advisor/public/engine/advisor.html').read_text()
def ids(v):
    if isinstance(v,dict):return {v['id']} if 'id' in v else set().union(*(ids(x) for x in v.values()),set())
    if isinstance(v,list):return set().union(*(ids(x) for x in v),set())
    return set()
with (ROOT/'docs/stage8/independent-evidence/form-audit.csv').open('w') as f:
    out=csv.writer(f,lineterminator="\n");out.writerow(['service','reference_id','found_in_actual_html','native_keys','native_conditions','native_units','note'])
    for kind,config in source['services'].items():
        if kind not in native:continue
        for field in config['fields']:
            refids=ids(field.get('source'))|{field['id']}
            matches=[n for n in native[kind]['fields'] if ids(n.get('source'))&refids]
            if not matches:
                key={'lp-type':'types','fi-contribution':'contributions','fi-source-filter':'source_filter'}.get(field['id'],field['id'])
                matches=[n for n in native[kind]['fields'] if n['key']==key]
            note='تطبیق شناسه/مقصد؛ صحت معنایی از آزمون‌های نام‌برده در گزارش'
            if field['id']=='idea-files':note='پنل مشترک فایل خصوصی طبق D32؛ تفاوت مجاز قالب‌ها'
            elif field.get('type')=='heading':note='عنوان گروه منبع؛ حذف مشاهده‌شده S08-IT-004'
            elif field.get('ui_only'):note='فیلتر نمایشی کتابخانه؛ گزینه risk حذف شده S08-IT-005'
            elif not matches:note='نگاشت خودکار کامل نیست و قبولی مستقل ادعا نمی‌شود'
            out.writerow([kind,field['id'],field['id'] in html,','.join(n['key'] for n in matches),json.dumps([n.get('when') for n in matches],ensure_ascii=False),','.join(n.get('unit') or '' for n in matches),note])
