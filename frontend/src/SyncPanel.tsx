import { useEffect, useState } from 'react';
import { post } from './lib/api';

type QueuedDraft = {
  actionId: string;
  tipo: 'borrador_personal';
  version: number;
  payload: { courseId: string; text: string };
};

const prefix = 'monda-sync:';

function readQueue(key: string): QueuedDraft[] {
  try {
    const value = JSON.parse(localStorage.getItem(key) || '[]');
    return Array.isArray(value) ? value.filter((item): item is QueuedDraft =>
      item && typeof item.actionId === 'string' && item.tipo === 'borrador_personal' &&
      typeof item.payload?.text === 'string') : [];
  } catch {
    return [];
  }
}

function saveQueue(key: string, items: QueuedDraft[]) {
  if (items.length) localStorage.setItem(key, JSON.stringify(items));
  else localStorage.removeItem(key);
}

export function clearLocalDrafts(userId: string) {
  const scope = `${prefix}${userId}:`;
  for (let i = localStorage.length - 1; i >= 0; i--) {
    const key = localStorage.key(i);
    if (key?.startsWith(scope)) localStorage.removeItem(key);
  }
}

export function SyncPanel({ userId, courseId, online }: { userId: string; courseId: string; online: boolean }) {
  const key = `${prefix}${userId}:${courseId}`;
  const [text, setText] = useState('');
  const [queue, setQueue] = useState<QueuedDraft[]>(() => readQueue(key));
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');

  useEffect(() => { setQueue(readQueue(key)); setText(''); setNotice(''); }, [key]);

  async function synchronize() {
    if (!online || busy) return;
    const pending = readQueue(key);
    if (!pending.length) return;
    setBusy(true);
    try {
      const result = await post<{ results: { actionId: string; status: string; result?: { code?: string } }[] }>(
        '/api/sync', { actions: pending });
      const statuses = new Map(result.results.map(item => [item.actionId, item]));
      const remaining = pending.filter(item => !['applied', 'repeated'].includes(statuses.get(item.actionId)?.status || ''));
      saveQueue(key, remaining);
      setQueue(remaining);
      const applied = pending.length - remaining.length;
      setNotice(remaining.length
        ? `${applied} borrador(es) sincronizados; ${remaining.length} requieren revisión.`
        : `${applied} borrador(es) sincronizados sin duplicados.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'No se pudo sincronizar. El borrador sigue pendiente.');
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (online && readQueue(key).length) void synchronize();
    // Reintentar al recuperar conexión o al cambiar de usuario/curso.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [online, key]);

  function addDraft() {
    if (!courseId || !text.trim()) return;
    const draft: QueuedDraft = {
      actionId: crypto.randomUUID(), tipo: 'borrador_personal', version: 1,
      payload: { courseId, text: text.trim() },
    };
    const next = [...readQueue(key), draft];
    saveQueue(key, next);
    setQueue(next);
    setText('');
    setNotice(online ? 'Borrador guardado. Pulsa Sincronizar.' : 'Borrador guardado en este navegador; se enviará al reconectar.');
  }

  function removeDraft(actionId: string) {
    const next = readQueue(key).filter(item => item.actionId !== actionId);
    saveQueue(key, next);
    setQueue(next);
  }

  return <section className="panel sync-panel" aria-label="Sincronización de borradores">
    <div className="page-heading"><div><h1>Sincronización</h1><p>Guarda una nota personal para el curso y envíala al recuperar la conexión.</p></div></div>
    <p><strong>Estado:</strong> {online ? 'En línea' : 'Sin conexión'} · {queue.length} borrador(es) pendientes</p>
    <label>Nota personal del curso<textarea value={text} onChange={event => setText(event.target.value)} rows={4} placeholder="Escribe una nota sin datos personales" /></label>
    <div className="actions">
      <button className="button primary" onClick={addDraft} disabled={!courseId || !text.trim()}>Guardar borrador local</button>
      <button className="button subtle" onClick={() => void synchronize()} disabled={!online || busy || !queue.length}>{busy ? 'Sincronizando…' : 'Sincronizar pendientes'}</button>
    </div>
    {notice && <p role="status">{notice}</p>}
    {queue.length > 0 && <div className="table-wrap"><table><thead><tr><th>Borrador pendiente</th><th>ActionId</th><th>Acción</th></tr></thead><tbody>
      {queue.map(item => <tr key={item.actionId}><td>{item.payload.text}</td><td>{item.actionId.slice(0, 8)}</td><td><button className="button subtle" onClick={() => removeDraft(item.actionId)}>Quitar</button></td></tr>)}
    </tbody></table></div>}
    <p className="muted">Solo se sincronizan borradores personales. Las evaluaciones no se envían sin conexión. Al cerrar sesión se eliminan las notas locales de esta cuenta.</p>
  </section>;
}
