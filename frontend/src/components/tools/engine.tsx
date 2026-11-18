'use client';
import {ProfessionalForm} from '@/components/core/profile';
import {ServiceEditor} from './service-editor';
import {tools} from '@/data/tools';
export type ToolSection={title:string;fields:string[];optional?:boolean};
export function LegacyTool({opener}:{opener:string;root:string;sections?:ToolSection[]}){const tool=tools.find(t=>t.opener===opener);if(tool?.id==='ma-profile')return <ProfessionalForm/>;if(tool&& !['library','drafts'].includes(tool.id))return <ServiceEditor kind={tool.id}/>;return null}
