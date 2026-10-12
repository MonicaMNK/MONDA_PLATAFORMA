"""Prueba RAG real sobre el material demo de SQLite; conserva usuarios y cursos."""
import sys
import json
import os
from pathlib import Path
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT/'data'/'.gemini.env')
os.environ['DATABASE_URL']=f"sqlite:///{(ROOT/'data'/'gemini_smoke.db').as_posix()}"
os.environ['MONDA_DEMO']='1'
os.environ['STORAGE_MODE']='local'
from backend.app.db.seed import create_schema_for_tests, seed_demo_data
create_schema_for_tests(reset=False)
seed_demo_data()
from docx import Document
expected=[
    'Un sistema es un conjunto de componentes relacionados que interactúan entre sí para alcanzar un propósito u objetivo común.',
    'Los sistemas reciben entradas, realizan procesos y generan salidas. También pueden incorporar retroalimentación para ajustar su funcionamiento.',
    'En un sistema de información, personas, procesos, datos y tecnología colaboran para capturar, procesar, almacenar y distribuir información útil.',
    'La frontera de un sistema permite distinguirlo de su entorno, mientras que las interfaces permiten el intercambio entre componentes o sistemas.',
]
assert [p.text for p in Document(ROOT/'data'/'uploads'/'seed_sistemas.docx').paragraphs][1:]==expected, 'El material no coincide con la demo sintética.'

from backend.app.db.session import SessionLocal
from backend.app.models import Config, Content, User
from backend.app.services.content_service import index_content
from backend.app.services.rag_service import query_rag
from backend.app.core.config import settings

with SessionLocal() as db:
    teacher = db.query(User).filter_by(correo='docente@monda.local').first()
    content = db.query(Content).filter_by(s3_key='local/seed_sistemas.docx', activo=True).first()
    if content is None:
        content = db.query(Content).filter_by(s3_key='local/seed_sistemas.docx').first()
    cfg=db.get(Config,'rag')
    cfg.valor={**cfg.valor,'mode':'gemini','modelo':settings.gemini_llm_model}
    cfg.version+=1
    db.commit()
    job=index_content(db,teacher,content)
    print('Indexación:',json.dumps(job.resultado,ensure_ascii=True))
    result=query_rag(db,teacher,content.curso_id,'¿Qué es un sistema y cuáles son sus componentes?')
    print('Consulta:',json.dumps({k:result[k] for k in ['mode','evidenceSufficient','providerWarning']},ensure_ascii=True))
    print('Fuentes:',len(result['sources']))
    if result['mode']!='gemini' or result['providerWarning'] or not result['evidenceSufficient']:
        raise SystemExit(1)
    print('RAG Gemini verificado: embeddings, recuperación y generación.')
