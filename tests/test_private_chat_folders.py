from io import BytesIO
from uuid import uuid4
import pytest
from docx import Document
from fastapi.testclient import TestClient
from backend.app.db.seed import init_test_db
from backend.app.main import app


@pytest.fixture
def client():
    init_test_db(True)
    with TestClient(app) as c:
        yield c


def login(client,role):
    names={'administrador':('admin','Admin123!'),'docente':('docente','Docente123!'),'estudiante':('estudiante','Estudiante123!')}
    name,password=names[role]
    response=client.post('/api/auth/login',json={'correo':name+'@monda.local','password':password})
    assert response.status_code==200
    return {'Authorization':'Bearer '+response.json()['accessToken']}


def docx_bytes():
    document=Document();document.add_paragraph('Material sintético de la semana uno: los sistemas tienen entradas, procesos y salidas.')
    buffer=BytesIO();document.save(buffer);return buffer.getvalue()


def test_conversations_are_private_for_every_role(client):
    headers={role:login(client,role) for role in ['administrador','docente','estudiante']}
    course=client.get('/api/courses',headers=headers['docente']).json()['items'][0]['id']
    chats={}
    for role,h in headers.items():
        response=client.post(f'/api/courses/{course}/rag/query',headers=h,json={'question':'¿Qué es un sistema?'})
        assert response.status_code==200,response.text
        chats[role]=response.json()
    assert len({c['conversationId'] for c in chats.values()})==3
    for role,h in headers.items():
        visible=client.get('/api/rag/conversations',params={'courseId':course},headers=h).json()['items']
        assert [c['id'] for c in visible]==[chats[role]['conversationId']]
        for owner,chat in chats.items():
            status=client.get('/api/rag/conversations/'+chat['conversationId']+'/messages',headers=h).status_code
            assert status==(200 if owner==role else 403)
            if owner!=role:
                assert client.post(f'/api/courses/{course}/rag/query',headers=h,json={'question':'Pregunta','conversationId':chat['conversationId']}).status_code==403


def test_week_folders_upload_preview_move_and_student_read_only(client):
    teacher=login(client,'docente');student=login(client,'estudiante')
    course=client.get('/api/courses',headers=teacher).json()['items'][0]['id']
    base=f'/api/courses/{course}'
    week=client.post(base+'/folders',headers=teacher,json={'nombre':'Semana 1'})
    assert week.status_code==201,week.text
    folder=week.json()['id']
    nested=client.post(base+'/folders',headers=teacher,json={'nombre':'Lecturas','parentId':folder})
    assert nested.status_code==201
    assert nested.json()['parentId']==folder
    assert client.post(base+'/folders',headers=teacher,json={'nombre':'semana 1'}).status_code==409
    assert client.post(base+'/folders',headers=student,json={'nombre':'No permitido'}).status_code==403
    assert client.patch('/api/folders/'+folder,headers=student,json={'nombre':'Otro'}).status_code==403
    assert len(client.get(base+'/folders',headers=student).json()['items'])==2
    upload=client.post(base+'/contents',headers=teacher,files={'file':('semana1.docx',docx_bytes())},data={'folderId':nested.json()['id']})
    assert upload.status_code==201,upload.text
    cid=upload.json()['contentId']
    files=client.get(base+'/contents',headers=student).json()['items']
    assert next(f for f in files if f['id']==cid)['folderId']==nested.json()['id']
    preview=client.get(f'/api/contents/{cid}/preview',headers=student)
    assert preview.status_code==200,preview.text
    assert 'semana uno' in preview.json()['text']
    assert client.get(f'/api/contents/{cid}/download',headers=student).status_code==200
    assert client.post(base+'/contents',headers=student,files={'file':('denied.docx',docx_bytes())}).status_code==403
    assert client.post(f'/api/contents/{cid}/index',headers=student).status_code==403
    assert client.patch(f'/api/contents/{cid}/folder',headers=student,json={'folderId':folder}).status_code==403
    assert client.patch(f'/api/contents/{cid}/folder',headers=teacher,json={'folderId':None}).json()['folderId'] is None
    renamed=client.patch('/api/folders/'+folder,headers=teacher,json={'nombre':'Semana 01'})
    assert renamed.status_code==200
    assert renamed.json()['nombre']=='Semana 01'


def test_folders_and_previews_cannot_cross_courses(client):
    teacher=login(client,'docente');student=login(client,'estudiante')
    course=client.get('/api/courses',headers=teacher).json()['items'][0]['id']
    other=client.post('/api/courses',headers=teacher,json={'nombre':'Curso ajeno al alumno'}).json()['id']
    folder=client.post(f'/api/courses/{other}/folders',headers=teacher,json={'nombre':'Privado'}).json()['id']
    assert client.get(f'/api/courses/{other}/folders',headers=student).status_code==403
    assert client.post(f'/api/courses/{course}/folders',headers=teacher,json={'nombre':'Cruce','parentId':folder}).status_code==403
    assert client.post(f'/api/courses/{course}/contents',headers=teacher,files={'file':('cross.docx',docx_bytes())},data={'folderId':folder}).status_code==403
    upload=client.post(f'/api/courses/{other}/contents',headers=teacher,files={'file':('privado.docx',docx_bytes())},data={'folderId':folder}).json()['contentId']
    assert client.get(f'/api/contents/{upload}/preview',headers=student).status_code==403
    own=client.get(f'/api/courses/{course}/contents',headers=teacher).json()['items'][0]['id']
    assert client.patch(f'/api/contents/{own}/folder',headers=teacher,json={'folderId':folder}).status_code==403


def test_provider_status_is_admin_only_and_checks_models(client,monkeypatch):
    from backend.app.api.v1.routers import admin
    class Response:
        def raise_for_status(self):pass
        def json(self):return {'models':[{'name':'llama3:latest'},{'name':'nomic-embed-text:latest'}]}
    monkeypatch.setattr(admin.requests,'get',lambda *args,**kw:Response())
    assert client.get('/api/admin/providers',headers=login(client,'estudiante')).status_code==403
    result=client.get('/api/admin/providers',headers=login(client,'administrador'))
    assert result.status_code==200
    assert result.json()['ollama']['available']
    assert result.json()['ollama']['llmReady']
    assert result.json()['ollama']['embeddingReady']


def test_sqlite_upgrade_preserves_existing_rows_and_is_idempotent(tmp_path,monkeypatch):
    from sqlalchemy import create_engine,inspect,text
    from backend.app.db import seed
    engine=create_engine(f"sqlite:///{tmp_path/'old.db'}")
    identifier=uuid4().hex
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE contenidos (id CHAR(32) PRIMARY KEY)'))
        conn.execute(text('INSERT INTO contenidos (id) VALUES (:id)'),{'id':identifier})
    monkeypatch.setattr(seed,'engine',engine)
    seed.create_schema_for_tests(reset=False)
    seed.create_schema_for_tests(reset=False)
    assert 'carpeta_id' in {c['name'] for c in inspect(engine).get_columns('contenidos')}
    with engine.connect() as conn:
        assert conn.execute(text('SELECT id FROM contenidos')).scalar()==identifier
    engine.dispose()
