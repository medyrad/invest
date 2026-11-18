import {listings} from '@/lib/listings';
import type {Listing,Opportunity} from '@/types';
export const COMPARE_MAX=4;
export const COMPARE_MIN=2;
export const SERIES=['#1e40af','#0d9488','#7c3aed','#db2777'] as const;
export const compareListings=listings;
export const oppOf=(l:Listing)=>l.raw as Opportunity;
