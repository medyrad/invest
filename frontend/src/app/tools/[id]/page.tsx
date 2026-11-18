import {notFound,redirect} from 'next/navigation';
import {ToolView} from '@/components/tools/tools';
import {toolById} from '@/data/tools';
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;if(id==='library'||id==='drafts')redirect('/'+id);if(!toolById(id))notFound();return <ToolView id={id}/>}
