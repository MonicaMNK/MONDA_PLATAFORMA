import { useEffect, useState } from 'react';
import { api, patch, post, type Course } from './lib/api';

type ManagedUser = { id?: string; nombre: string; correo: string; rol: string; estado: string; version?: number; password?: string };
const blank = (): ManagedUser => ({nombre:'',correo:'',rol:'estudiante',estado:'activo',password:''});

export function AdminManagement({courses, onCoursesChanged, section}: {courses: Course[]; onCoursesChanged: ()=>Promise<void>; section: 'courses'|'users'}) {
  const [users,setUsers] = useState<ManagedUser[]>([]);
  const [draft,setDraft] = useState<ManagedUser>(blank);
  const [course,setCourse] = useState({id:'',nombre:'',docenteId:'',descripcion:'',estado:'activo'});
  const [message,setMessage] = useState('');
  const [busy,setBusy] = useState(false);
  const [enrollment,setEnrollment] = useState({courseId:'',studentId:''});
  async function enroll(e: React.FormEvent) {
    e.preventDefault();setBusy(true);
    try { await post(`/api/courses/${enrollment.courseId}/enrollments`,{estudianteId:enrollment.studentId});setMessage('Estudiante matriculado.'); } catch(e) {setMessage(e instanceof Error?e.message:'Error al matricular');} finally {setBusy(false);}
  }
  async function reload() {
    const items: ManagedUser[] = [];
    let page = 1, total = 0;
    do { const result = await api<{items:ManagedUser[];total:number}>(`/api/admin/users?limit=100&page=${page++}`); items.push(...result.items); total=result.total; } while(items.length<total);
    setUsers(items);
  }
  useEffect(()=>{reload().catch(e=>setMessage(e.message));},[]);
  async function saveUser(e: React.FormEvent) {
    e.preventDefault(); setBusy(true);
    try {
      if(draft.id) await patch(`/api/admin/users/${draft.id}`,{nombre:draft.nombre,correo:draft.correo,rol:draft.rol,estado:draft.estado,version:draft.version});
      else await post('/api/admin/users',draft);
      setDraft(blank()); await reload(); setMessage('Usuario guardado.');
    } catch(e) {setMessage(e instanceof Error?e.message:'Error al guardar');} finally {setBusy(false);}
  }
  async function saveCourse(e: React.FormEvent) {
    e.preventDefault(); setBusy(true);
    try {
      if(course.id) await patch(`/api/courses/${course.id}`,{nombre:course.nombre,descripcion:course.descripcion,docenteId:course.docenteId,estado:course.estado});
      else await post('/api/courses',{nombre:course.nombre,descripcion:course.descripcion,docenteId:course.docenteId});
      setCourse({id:'',nombre:'',docenteId:'',descripcion:'',estado:'activo'}); await onCoursesChanged(); setMessage('Curso guardado.');
    } catch(e) {setMessage(e instanceof Error?e.message:'Error al guardar');} finally {setBusy(false);}
  }
  return <div className="panel">
    {message&&<div role="status" className="alert">{message}</div>}
    {section==='users'?<>
      <h3>{draft.id?'Editar usuario':'Crear usuario'}</h3>
      <form className="config-grid" onSubmit={saveUser}>
        <label>Nombre<input required minLength={2} value={draft.nombre} onChange={e=>setDraft({...draft,nombre:e.target.value})}/></label>
        <label>Correo<input required type="email" value={draft.correo} onChange={e=>setDraft({...draft,correo:e.target.value})}/></label>
        <label>Rol<select value={draft.rol} onChange={e=>setDraft({...draft,rol:e.target.value})}>{['administrador','docente','estudiante'].map(x=><option key={x}>{x}</option>)}</select></label>
        <label>Estado<select value={draft.estado} onChange={e=>setDraft({...draft,estado:e.target.value})}>{['activo','inactivo','pendiente'].map(x=><option key={x}>{x}</option>)}</select></label>
        {!draft.id&&<label>Contraseña inicial<input required type="password" minLength={8} maxLength={72} autoComplete="new-password" value={draft.password||''} onChange={e=>setDraft({...draft,password:e.target.value})}/></label>}
        <button disabled={busy} className="button primary">Guardar usuario</button>
        {draft.id&&<button type="button" className="button subtle" onClick={()=>setDraft(blank())}>Cancelar</button>}
      </form>
      <div className="table-wrap"><table><thead><tr><th>Nombre</th><th>Correo</th><th>Rol</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{users.map(u=><tr key={u.id}><td>{u.nombre}</td><td>{u.correo}</td><td>{u.rol}</td><td>{u.estado}</td><td><button className="button subtle" onClick={()=>setDraft({...u})}>Editar</button></td></tr>)}</tbody></table></div>
    </>:<>
      <h3>{course.id?'Editar curso y asignar docente':'Crear curso'}</h3>
      <form className="config-grid" onSubmit={saveCourse}>
        <label>Nombre<input required minLength={2} value={course.nombre} onChange={e=>setCourse({...course,nombre:e.target.value})}/></label>
        <label className="wide">Descripción del curso<textarea rows={3} value={course.descripcion} onChange={e=>setCourse({...course,descripcion:e.target.value})}/></label><label>Docente responsable<select required value={course.docenteId} onChange={e=>setCourse({...course,docenteId:e.target.value})}><option value="">Selecciona docente</option>{users.filter(u=>u.rol==='docente'&&u.estado==='activo').map(u=><option key={u.id} value={u.id}>{u.nombre} · {u.correo}</option>)}</select></label>
        {course.id&&<label>Estado<select value={course.estado} onChange={e=>setCourse({...course,estado:e.target.value})}><option>activo</option><option>archivado</option></select></label>}
        <button disabled={busy} className="button primary">Guardar curso</button>
        {course.id&&<button type="button" className="button subtle" onClick={()=>setCourse({id:'',nombre:'',docenteId:'',descripcion:'',estado:'activo'})}>Cancelar</button>}
      </form>
      {courses.map(c=><div key={c.id} className="section-title"><span>{c.nombre} · {users.find(u=>u.id===c.docenteId)?.nombre||'Docente'}</span><button className="button subtle" onClick={()=>setCourse({id:c.id,nombre:c.nombre,estado:c.estado,docenteId:c.docenteId||'',descripcion:c.descripcion||''})}>Editar / asignar</button></div>)}
      <h3>Matricular estudiante</h3><form className="config-grid" onSubmit={enroll}>
        <label>Curso<select required value={enrollment.courseId} onChange={e=>setEnrollment({...enrollment,courseId:e.target.value})}><option value="">Selecciona curso</option>{courses.filter(c=>c.estado==='activo').map(c=><option key={c.id} value={c.id}>{c.nombre}</option>)}</select></label>
        <label>Estudiante<select required value={enrollment.studentId} onChange={e=>setEnrollment({...enrollment,studentId:e.target.value})}><option value="">Selecciona estudiante</option>{users.filter(u=>u.rol==='estudiante'&&u.estado==='activo').map(u=><option key={u.id} value={u.id}>{u.nombre} · {u.correo}</option>)}</select></label>
        <button disabled={busy} className="button primary">Matricular</button>
      </form>
    </>}
  </div>;
}
