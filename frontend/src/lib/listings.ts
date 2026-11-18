import type {Listing} from '@/types';
import {documents} from './public-values';
export const listings:Listing[]=[];
export const listingById=(id:string)=>listings.find(l=>l.id===id);
export const payoutLabel:Record<string,string>={monthly:'ماهانه',quarterly:'سه‌ماهه',semiannual:'شش‌ماهه',annual:'سالانه',maturity:'سررسید',growth:'رشد ارزش'};
export const isNew=(l:Listing,since?:string)=>new Date(l.publishedAt).getTime()>= (since?new Date(since).getTime():Date.now()-7*86400000);
export function galleryOf(l:Listing){const p=documents.get(l.id);return (p?.images.length?p.images:[l.image]).map(src=>({src,caption:p?.images.length?'مشتق تصویر با تأیید بازبین':'تصویر برند؛ تصویر دارایی نیست'}));}
