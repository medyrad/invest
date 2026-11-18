import {listings} from '@/lib/listings';
import type {Listing,Opportunity} from '@/types';
export const COMPARE_MAX=4;
export const COMPARE_MIN=2;
export const SERIES=['#1e40af','#0d9488','#7c3aed','#db2777'] as const;
export const compareListings=listings;
export const oppOf=(l:Listing)=>l.raw as Opportunity;

export type CompareGroup = {id:'money'|'time'|'risk'|'project';title:string;note:string;keys:string[]};
// Order and project titles: reference src/lib/compare.ts groups/rows.
// Extra fields stay in their semantic group; no fabricated time group for sale.
export function comparisonGroups(kind:Listing['kind']):CompareGroup[]{
 const money={id:'money',title:'پول',note:'چقدر لازم است و درآمد چطور می‌رسد',keys:[]} as CompareGroup;
 const time={id:'time',title:'زمان',note:'کی درآمد شروع می‌شود و کی سرمایه برمی‌گردد',keys:[]} as CompareGroup;
 const risk={id:'risk',title:'ریسک و حقوق',note:'چه چیزی هنوز باید بررسی شود',keys:[]} as CompareGroup;
 const project={id:'project',title:'پروژه و محل',note:'پروژه چیست و کجاست',keys:[]} as CompareGroup;
 if(kind==='project'){
  money.keys=['min_capital','budget','irr','income','repay','finance','working_capital_min','purchase_price','deposit','monthly_rent','lump_rent','partner_share','government_share','partnership_settlements','contractor_settlements','sale_payments','lease_payments','heritage_returns','heritage_payments'];
  time.keys=['first_income_months','lockup_months','payback_years','payback_downside_years','execution_months','duration_years','operator_work_period','heritage_years'];
  risk.keys=['risk','legal_status','ownership','sector','caution','checks','accepted_guarantees','transfer_rights','rights_subject','rights_title_parties','rights_holder','rights_original_lease','rights_regime','rights_assignment','rights_key_money','rights_valuation','rights_permitted_use','rights_renewal','rights_claims','rights_registration','rights_costs','rights_occupancy','general_conditions','special_conditions'];
  project.keys=['group','subtype','phase','stage','model','model_id','routes','province','county','city','title','description','usage','metric_label','metric_quantity','revenues','interventions','lease_types','heritage_uses','steps'];
 } else if(kind==='fund'){
  money.keys=['minimum_investment','forecast_type','forecast','forecast_irr','forecast_simple_rate','forecast_effective_rate','payout','finance','repay'];
  time.note='مدت طرح و شرایط خروج';time.keys=['duration_months','exit'];
  risk.keys=['risk','bank_exists','bank_principal','bank_profit','bank_description','ownership','caution'];
  project.title='صندوق و طرح';project.note='نوع ابزار و موضوع سرمایه‌گذاری';project.keys=['fund_kind','fund_type','asset_sector','title','description','stage','model','steps'];
 }else{
  money.note='قیمت کل یا هر واحد و مقدار مبنای قیمت';money.keys=['price','price_mode','price_quantity','finance','repay'];
  risk.keys=['ownership','caution'];
  project.title='دارایی و محل';project.note='موضوع فروش چیست و کجاست';project.keys=['category','building_type','scrap_type','subject','usage','area','land_area','quantity','quantity_source','province','county','city','neighborhood','title','description','stage','model','steps'];
 }
 return (kind==='sale'?[money,risk,project]:[money,time,risk,project]);
}

export const projectCompareLabels:Record<string,string>={
 min_capital:'حداقل مبلغ ورود',budget:'نیاز مالی کل طرح',irr:'بازده داخلی پیش‌بینی‌شده',
 income:'نوع دریافت درآمد',repay:'منبع بازگشت پول',first_income_months:'اولین درآمد',
 lockup_months:'قفل سرمایه',payback_years:'بازگشت کامل سرمایه',
 payback_downside_years:'بازگشت در حالت بدبینانه',execution_months:'مدت اجرا',
 duration_years:'مدت قرارداد',risk:'سطح ریسک',legal_status:'وضعیت حقوقی',
 ownership:'مالکیت و انتقال',sector:'صاحب پروژه',caution:'نکته احتیاط',
 phase:'مرحله',model:'مدل همکاری',routes:'راه‌های ورود',
};
