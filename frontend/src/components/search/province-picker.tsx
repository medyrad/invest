"use client";
import type {RouteId} from '@/types';
import {GeographyFields} from './geography-fields';
export function CityPicker({route}:{route:RouteId;provinces:string[]}){return <div data-route={route}><GeographyFields cityOnly/></div>;}
export function LocationFields({route}:{route:RouteId;value:string[];onChange:(v:string[])=>void}){return <div data-route={route}><GeographyFields/></div>;}
