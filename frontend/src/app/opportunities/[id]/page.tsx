import ReferenceShell from '@/components/core/reference-shell';
import {Detail} from '@/components/listing/detail';
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <ReferenceShell id={id}><Detail id={id}/></ReferenceShell>}
