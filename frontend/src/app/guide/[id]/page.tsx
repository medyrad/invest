import ReferenceShell from '@/components/core/reference-shell';
import {GuideView} from '@/components/guide/guide-view';
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <ReferenceShell id={id}><GuideView id={id}/></ReferenceShell>}
