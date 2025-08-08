import * as React from "react"; import { clsx } from "clsx";
export function Button({className,variant="default",size="md",...props}:{className?:string,variant?:"default"|"outline"|"ghost","size"?:'sm'|'md'|'lg'}&React.ButtonHTMLAttributes<HTMLButtonElement>){
 const base="inline-flex items-center justify-center rounded-2xl font-medium transition disabled:opacity-50";
 const variants={default:"bg-black text-white hover:opacity-90",outline:"border border-gray-300 hover:bg-gray-50",ghost:"hover:bg-gray-100"};
 const sizes={sm:"px-3 py-1.5 text-sm",md:"px-4 py-2 text-sm",lg:"px-5 py-3"};
 return <button className={clsx(base,variants[variant],sizes[size],className)} {...props}/>;}