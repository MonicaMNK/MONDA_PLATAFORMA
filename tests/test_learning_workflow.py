from datetime import datetime,timedelta,timezone
from fastapi.testclient import TestClient
from backend.app.db.seed import init_test_db
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models import Alert,Attempt,Config,Content,ContentFolder,Enrollment,Event,RAGFragment,User,uid


def login(c,role):
    email,password=('docente','Docente123!') if role=='teacher' else ('estudiante','Estudiante123!')
    d=c.post('/api/auth/login',json={'correo':email+'@monda.local','password':password}).json()
    return {'Authorization':'Bearer '+d['accessToken']}


def test_completed_delivery_hidden_grade_teacher_correction_and_release():
    init_test_db(True)
    with TestClient(app) as c:
        t=login(c,'teacher');s=login(c,'student');course=c.get('/api/courses',headers=t).json()['items'][0]['id']
        aid=c.post(f'/api/courses/{course}/assessments/generate',headers=t,json={'tema':'Sistemas','cantidad':2}).json()['assessmentId']
        detail=c.get(f'/api/assessments/{aid}',headers=t).json()
        for q in detail['questions']:
            assert c.patch('/api/questions/'+q['id']+'/review',headers=t,json={'estado':'aprobado','version':q['version']}).status_code==200
        detail=c.get(f'/api/assessments/{aid}',headers=t).json();now=datetime.now(timezone.utc)
        assert c.post(f'/api/assessments/{aid}/publish',headers=t,json={'fechaInicio':(now-timedelta(minutes=1)).isoformat(),'fechaFin':(now+timedelta(days=1)).isoformat(),'version':detail['version']}).status_code==200
        attempt=c.post(f'/api/assessments/{aid}/attempts',headers=s,json={'accion':'iniciar'}).json()
        answers={q['id']:'A' for q in detail['questions']}
        assert c.post(f'/api/assessments/{aid}/attempts',headers=s,json={'accion':'guardar','intentoId':attempt['attemptId'],'respuestas':answers}).json()['saved']
        closed=c.post(f'/api/assessments/{aid}/attempts',headers=s,json={'accion':'cerrar','intentoId':attempt['attemptId']}).json()
        assert closed['estado']=='cerrado' and closed['puntaje'] is None
        row=c.get(f'/api/courses/{course}/assessments',headers=s).json()['items'][0]
        assert row['miEstado']=='completada'
        assert c.get(f'/api/assessments/{aid}/results',headers=s).status_code==409
        assert c.get(f'/api/assessments/{aid}/submissions',headers=s).status_code==403
        q=c.get(f'/api/assessments/{aid}',headers=t).json()['questions'][0]
        corrected=c.patch('/api/questions/'+q['id']+'/review',headers=t,json={'estado':'aprobado','version':q['version'],'clave':'B','justificacion':'La clave fue corregida por el docente según la evidencia del material.'})
        assert corrected.status_code==200,corrected.text
        report=c.get(f'/api/assessments/{aid}/submissions',headers=t).json()
        assert report['completed']==1
        assert report['items'][0]['puntaje']==10
        assert report['items'][0]['fechaInicio'] and report['items'][0]['fechaCierre'] and report['items'][0]['duracionSegundos']>=0
        assert c.post(f'/api/assessments/{aid}/results/publish',headers=s,json={'version':1}).status_code==403
        detail=c.get(f'/api/assessments/{aid}',headers=t).json()
        assert c.post(f'/api/assessments/{aid}/results/publish',headers=t,json={'version':detail['version']}).status_code==200
        result=c.get(f'/api/assessments/{aid}/results',headers=s).json()
        assert result['puntaje']==10
        assert any(q['clave']=='B' and 'corregida' in q['justificacion'] for q in result['questions'])
        grades=c.get('/api/users/me/grades',headers=s).json()['items']
        assert grades[0]['intento']['puntaje']==10
        reopened=c.post(f'/api/assessments/{aid}/attempts',headers=s,json={'accion':'iniciar'}).json()
        assert reopened['estado']=='cerrado' and reopened['attemptId']==attempt['attemptId']
        assert c.patch('/api/questions/'+q['id']+'/review',headers=t,json={'estado':'aprobado','version':corrected.json()['version'],'clave':'A'}).status_code==409


def test_rag_scope_includes_subfolders_and_never_broadens_empty_selection():
    init_test_db(True)
    with SessionLocal() as db:
        base=db.query(Content).first();teacher=db.query(User).filter_by(rol='docente').first()
        folder=ContentFolder(curso_id=base.curso_id,nombre='Semana 1',creado_por=teacher.id);db.add(folder);db.flush()
        child=ContentFolder(curso_id=base.curso_id,nombre='Lecturas',padre_id=folder.id,creado_por=teacher.id);db.add(child);db.flush()
        special=Content(documento_id=uid(),curso_id=base.curso_id,nombre_original='unicornios.docx',s3_key='local/synthetic_unicorn.docx',hash_sha256='0'*64,autor_id=teacher.id,carpeta_id=child.id,activo=True,estado_indexacion='indexado',modelo_embedding='fallback-lexical-v1')
        db.add(special);db.flush()
        db.add(RAGFragment(contenido_id=special.id,curso_id=base.curso_id,ordinal=1,texto='Los unicornios representan el ejemplo único de la carpeta seleccionada.',embedding_provider='fallback',embedding_model='fallback-lexical-v1',hash_fragmento='1'*64))
        db.commit();fid=folder.id;cid=special.id;course=base.curso_id
    with TestClient(app) as c:
        s=login(c,'student')
        d=c.post(f'/api/courses/{course}/rag/query',headers=s,json={'question':'unicornios','folderId':fid}).json()
        assert d['sources'] and all(x['contentId']==cid for x in d['sources'])
        empty=c.post(f'/api/courses/{course}/rag/query',headers=s,json={'question':'sistema','contentIds':[]}).json()
        assert empty['sources']==[] and not empty['evidenceSufficient']
        mismatch=c.post(f'/api/courses/{course}/rag/query',headers=s,json={'question':'sistema','conversationId':d['conversationId']})
        assert mismatch.status_code==409
        restricted=c.post(f'/api/courses/{course}/rag/query',headers=s,json={'question':'sistema','contentIds':[cid]}).json()
        assert restricted['sources']==[]


def test_alerts_track_never_active_students_and_do_not_duplicate_reviewed():
    init_test_db(True)
    with SessionLocal() as db:
        enrollment=db.query(Enrollment).first();enrollment.creado_en=datetime.now(timezone.utc)-timedelta(days=12);course=enrollment.curso_id;db.commit()
    with TestClient(app) as c:
        t=login(c,'teacher');path=f'/api/courses/{course}/analytics'
        rows=c.get(path,headers=t).json()['alertas'];assert len(rows)==1
        assert rows[0]['regla']=='inactividad_7d' and rows[0]['estudiante']
        assert c.patch('/api/alerts/'+rows[0]['id'],headers=t,json={'estado':'revisada','comentario':'Contacto realizado.'}).status_code==200
        again=c.get(path,headers=t).json()['alertas'];assert len(again)==1 and again[0]['estado']=='revisada'
        with SessionLocal() as db:
            student=db.query(User).filter_by(rol='estudiante').first();db.add(Event(usuario_seudonimo=student.seudonimo,curso_id=course,tipo='rag_query'));db.commit()
        resolved=c.get(path,headers=t).json()['alertas'];assert resolved[0]['evidencia']['resuelta']
