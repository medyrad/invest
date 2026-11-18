import type {Listing,SearchCriteria,MatchResult} from '@/types';
export const WEIGHTS={amount:30,category:20,location:15,return:20,risk:15,terms:15};
export const ASSISTANT_MAX_RESULTS=10;
const cache=new Map<string,MatchResult[]>();
export const criteriaKey=(c:SearchCriteria)=>JSON.stringify(c);
export function acceptRanking(c:SearchCriteria,rows:MatchResult[]){cache.set(criteriaKey(c),rows)}
export const forRoute=(list:Listing[],route:string)=>list.filter(l=>l.routes.includes(route));
export function rank(list:Listing[],c:SearchCriteria,limit?:number){const allowed=new Set(list.map(l=>l.id));const result=(cache.get(criteriaKey(c))||[]).filter(r=>allowed.has(r.listing.id));return limit?result.slice(0,limit):result}
export function matchListing(l:Listing,c:SearchCriteria):MatchResult{return rank([l],c)[0]||{listing:l,score:0,reasons:[{label:'نتیجه سرور هنوز در دسترس نیست',status:'unknown'}]};}

export const clearRanking=()=>cache.clear();
