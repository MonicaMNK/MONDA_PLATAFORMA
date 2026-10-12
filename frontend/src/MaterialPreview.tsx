import { useEffect,useRef,useState } from 'react';
import { renderAsync } from 'docx-preview';
import { X,Download,FileText } from './Icons';
import { raw } from './lib/api';
export async function downloadMaterial(id:string,name:string) {
  const response=await raw(`/api/contents/${id}/download`),url=URL.createObjectURL(await response.blob());
  const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export function MaterialPreview({id,onClose}:{id:string;onClose:()=>void}) {
  const [blob,setBlob]=useState<Blob>(),[pdf,setPdf]=useState(''),[name,setName]=useState('Documento'),[error,setError]=useState('');
  const frame=useRef<HTMLIFrameElement>(null);
  async function draw(){if(!blob||!frame.current?.contentDocument)return;try{const doc=frame.current.contentDocument;doc.body.innerHTML='';await renderAsync(blob,doc.body,doc.head,{inWrapper:true,breakPages:true,ignoreLastRenderedPageBreak:false,renderAltChunks:false,useBase64URL:true});}catch{setError('No se pudo mostrar este DOCX. Descarga el archivo original para abrirlo en Word.');}}
  useEffect(()=>{let active=true,url='';raw(`/api/contents/${id}/download`).then(async r=>{const b=await r.blob();if(!active)return;const header=r.headers.get('content-disposition')||'';const utf=header.match(/filename\*=UTF-8''([^;]+)/i),plain=header.match(/filename="?([^";]+)"?/);setName(utf?decodeURIComponent(utf[1]):plain?plain[1]:'Documento');if(b.type.includes('pdf')){url=URL.createObjectURL(b);setPdf(url)}else setBlob(b);}).catch(e=>{if(active)setError(e.message)});const key=(e:KeyboardEvent)=>{if(e.key==='Escape')onClose()};window.addEventListener('keydown',key);return()=>{active=false;if(url)URL.revokeObjectURL(url);window.removeEventListener('keydown',key)};},[id]);
  useEffect(()=>{draw()},[blob]);
  return <div className="modal-backdrop" onClick={onClose}><section className="document-modal original-document" role="dialog" aria-modal="true" aria-label="Documento original" onClick={e=>e.stopPropagation()}><header><div className="file-symbol"><FileText/></div><div><small>DOCUMENTO DEL CURSO</small><h3>{name}</h3></div><button className="icon-button" aria-label="Cerrar" onClick={onClose}><X/></button></header>{error?<div className="alert error">{error}</div>:pdf?<iframe title={name} className="original-frame" src={pdf+'#toolbar=1'}/>:<><iframe title="Documento Word" ref={frame} className="original-frame" sandbox="allow-same-origin" srcDoc="<!doctype html><html><head><meta charset='utf-8'><style>body{margin:0;background:#e2e8f0}.docx-wrapper{padding:20px!important}.docx{margin-bottom:20px!important}</style></head><body></body></html>" onLoad={()=>draw()}/>{!blob&&<div className="loading-state">Abriendo el archivo original…</div>}</>}<footer><span>{pdf?'PDF original':'DOCX: páginas, tablas, imágenes y estilos. La paginación puede variar respecto de Word.'}</span><button className="button primary" onClick={()=>downloadMaterial(id,name).catch(e=>setError(e.message))}><Download/> Descargar original</button></footer></section></div>;
}
