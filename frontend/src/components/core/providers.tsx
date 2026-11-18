'use client';
import {Direction} from 'radix-ui';
import LoginShell from '@/components/auth/login-dialog';
import {useEffect,useState} from 'react';
function Notices(){const [notice,setNotice]=useState('');useEffect(()=>{const on=(e:Event)=>setNotice((e as CustomEvent<string>).detail);window.addEventListener('invest-notice',on);return()=>window.removeEventListener('invest-notice',on)},[]);return notice?<p role="status" className="surface fixed bottom-5 left-5 z-50 max-w-[calc(100vw-2rem)] rounded-2xl p-5">{notice}</p>:null;}
export default function Providers({children}:{children:React.ReactNode}){return <Direction.Provider dir="rtl"><LoginShell><Notices/>{children}</LoginShell></Direction.Provider>}
