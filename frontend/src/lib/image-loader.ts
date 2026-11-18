export default function imageLoader({ src, width }: { src: string; width: number }) { return `${src}?w=${width}`; }

export const withBase=(src:string)=>src;
