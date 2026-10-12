import React from 'react';

export function readableAnswer(value: unknown): string {
  if(typeof value!=='string') {
    if(value&&typeof value==='object') {
      const obj=value as Record<string,unknown>;
      for(const key of ['answer','respuesta','text','texto','contenido','message']) if(obj[key]) return readableAnswer(obj[key]);
      return Object.entries(obj).filter(([k])=>!['sources','fuentes','metadata'].includes(k)).map(([k,v])=>`${k}: ${readableAnswer(v)}`).join('\n\n');
    }
    return String(value??'');
  }
  const candidate=value.trim().replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'');
  if(candidate.startsWith('{')||candidate.startsWith('[')) {
    try { const data=JSON.parse(candidate);return Array.isArray(data)?data.map(readableAnswer).join('\n\n'):readableAnswer(data); } catch {}
  }
  return value;
}

function inline(text:string):React.ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`|\[F\d+\])/g).map((part,i)=>part.startsWith('**')?<strong key={i}>{part.slice(2,-2)}</strong>:part.startsWith('`')?<code key={i}>{part.slice(1,-1)}</code>:/^\[F\d+\]$/.test(part)?<span className="citation" key={i}>{part}</span>:part);
}

export function MessageText({text}:{text:unknown}) {
  const blocks=readableAnswer(text).split(/\n\s*\n/);
  return <div className="message-prose">{blocks.map((block,i)=>{
    const lines=block.trim().split('\n');
    if(lines.every(l=>/^\s*[-*•]\s/.test(l))) return <ul key={i}>{lines.map((l,j)=><li key={j}>{inline(l.replace(/^\s*[-*•]\s/,''))}</li>)}</ul>;
    if(lines.every(l=>/^\s*\d+[.)]\s/.test(l))) return <ol key={i}>{lines.map((l,j)=><li key={j}>{inline(l.replace(/^\s*\d+[.)]\s/,''))}</li>)}</ol>;
    return <div key={i}>{lines.map((l,j)=>/^#{1,3}\s/.test(l)?<h4 key={j}>{inline(l.replace(/^#{1,3}\s/,''))}</h4>:<p key={j}>{inline(l)}</p>)}</div>;
  })}</div>;
}
