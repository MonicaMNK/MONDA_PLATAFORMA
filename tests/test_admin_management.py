from fastapi.testclient import TestClient
from backend.app.db.seed import init_test_db
from backend.app.main import app


def login(client, email, password):
    result=client.post('/api/auth/login',json={'correo':email,'password':password})
    assert result.status_code==200
    return {'Authorization':'Bearer '+result.json()['accessToken']}


def test_admin_creates_edits_users_and_assigns_courses():
    init_test_db(True)
    with TestClient(app) as client:
        admin=login(client,'admin@monda.local','Admin123!')
        teacher=login(client,'docente@monda.local','Docente123!')
        users=client.get('/api/admin/users',headers=admin).json()['items']
        original=next(u for u in users if u['rol']=='docente')
        student=next(u for u in users if u['rol']=='estudiante')
        created=client.post('/api/admin/users',headers=admin,json={'nombre':'Nuevo profesor','correo':'nuevo@monda.local','rol':'docente','estado':'activo','password':'Docente456!'})
        assert created.status_code==201,created.text
        new=created.json()
        login(client,'nuevo@monda.local','Docente456!')
        update={'nombre':'Profesor actualizado','correo':'profesor@monda.local','rol':'docente','estado':'activo','version':new['version']}
        edited=client.patch('/api/admin/users/'+new['id'],headers=admin,json=update)
        assert edited.status_code==200,edited.text
        assert edited.json()['nombre']=='Profesor actualizado'
        assert client.patch('/api/admin/users/'+new['id'],headers=admin,json=update).status_code==409
        course=client.post('/api/courses',headers=admin,json={'nombre':'Curso nuevo','docenteId':new['id']})
        assert course.status_code==201,course.text
        cid=course.json()['id']
        assert course.json()['docenteId']==new['id']
        assert client.post('/api/courses',headers=admin,json={'nombre':'Curso inválido','docenteId':student['id']}).status_code==422
        assert client.patch('/api/courses/'+cid,headers=teacher,json={'docenteId':original['id']}).status_code==403
        reassigned=client.patch('/api/courses/'+cid,headers=admin,json={'nombre':'Curso editado','docenteId':original['id']})
        assert reassigned.status_code==200,reassigned.text
        assert reassigned.json()['docenteId']==original['id']
        own_course=client.get('/api/courses',headers=teacher).json()['items'][0]
        assert client.patch('/api/courses/'+own_course['id'],headers=teacher,json={'docenteId':new['id']}).status_code==403
        last=next(u for u in users if u['rol']=='administrador')
        assert client.patch('/api/admin/users/'+last['id'],headers=admin,json={'estado':'pendiente','version':last['version']}).status_code==409
