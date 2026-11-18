import type {Listing} from '@/types';
import {documents} from './public-values';
import labels from '@/data/publisher-labels.json';
export function sheetOf(l:Listing){const p=documents.get(l.id);const names:Record<string,string>=labels[l.kind];return {known:Object.entries(p?.fields||{}).map(([k,v])=>({label:names[k]||k,ok:typeof v==='object'&&!Array.isArray(v)&&v!==null?'status' in v&&v.status==='known':Array.isArray(v)?v.length>0:v!==null&&v!==undefined&&v!==''&&v!=='unknown'&&v!=='not_applicable'}))};}
