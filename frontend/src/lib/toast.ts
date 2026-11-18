const show=(message:string,options?:{description?:string;action?:{label:string;onClick:()=>void}})=>{if(typeof window!=='undefined')window.dispatchEvent(new CustomEvent('invest-notice',{detail:message+(options?.description?' '+options.description:'')}));};
export const toast=Object.assign(show,{success:show,error:show});
