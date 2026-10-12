(function(){
'use strict';
var h=React.createElement;

function Badge(props){return h('span',{className:'badge '+(props.type||'')},props.children)}
function Btn(props){return h('button',{className:'btn '+(props.secondary?'secondary ':'')+(props.danger?'danger':''),type:props.type||'button',onClick:props.onClick,disabled:props.disabled},props.children)}
function Card(props){return h('div',{className:'card '+(props.className||'')},props.children)}
function Notice(props){return h('div',{className:'notice '+(props.type||'')},props.children)}
function Field(label,child){return h('div',{className:'field'},h('label',null,label),child)}
function Header(id,title,subtitle){return h('div',null,h('div',{className:'eyebrow'},'DISEÑO PI7 · '+id),h('h1',{className:'title'},title),h('p',{className:'subtitle'},subtitle))}
function fmtRole(r){return r==='administrador'?'Administrador':r==='docente'?'Docente':'Estudiante'}

class App extends React.Component{
  constructor(props){
    super(props);
    var user=null;try{user=JSON.parse(sessionStorage.getItem('monda_user')||'null')}catch(e){}
    this.state={
      user:user,token:sessionStorage.getItem('monda_token')||'',page:'cursos',
      email:'docente@monda.local',password:'Docente123!',courses:[],course:null,
      contents:[],messages:[],conversationId:null,question:'¿Qué es un sistema?',
      assessments:[],detail:null,focusAssessment:null,attempt:null,answers:{},
      analytics:null,adminUsers:[],adminConfig:null,audit:[],msg:'',busy:false,
      gen:{tema:'Sistemas y componentes',bloom:'comprender',dificultad:'media',cantidad:5,tipo:'opcion_multiple'},
      uploadFile:null,documentId:'',contentVersion:1,studentId:'',offline:!navigator.onLine
      ,newCourseName:'',newTeacherId:'',editCourse:null,editUser:null,newUser:{nombre:'',correo:'',rol:'estudiante',estado:'activo',password:''}
    };
    this.api=this.api.bind(this);
  }
  componentDidMount(){
    window.addEventListener('online',()=>this.setState({offline:false}));
    window.addEventListener('offline',()=>this.setState({offline:true}));
    if(this.state.user)this.loadCourses();
  }
  api(path,opts){
    opts=opts||{};var headers=Object.assign({},opts.headers||{});var token=this.state.token||sessionStorage.getItem('monda_token');var self=this;
    if(token)headers.Authorization='Bearer '+token;
    if(opts.json!==undefined){headers['Content-Type']='application/json';opts.body=JSON.stringify(opts.json)}
    var requestOptions=Object.assign({},opts,{headers:headers,credentials:'same-origin'});
    return fetch(path,requestOptions).then(function(r){
      if(r.status!==401||path.indexOf('/api/auth/')===0)return r;
      var csrf='';document.cookie.split('; ').forEach(function(part){if(part.indexOf('monda_csrf=')===0)csrf=decodeURIComponent(part.substring('monda_csrf='.length))});
      if(!csrf)return r;
      return fetch('/api/auth/refresh',{method:'POST',credentials:'same-origin',headers:{'X-CSRF-Token':csrf}}).then(function(refreshResponse){
        if(!refreshResponse.ok)return r;
        return refreshResponse.json().then(function(data){sessionStorage.setItem('monda_token',data.accessToken);headers.Authorization='Bearer '+data.accessToken;self.setState({token:data.accessToken});return fetch(path,Object.assign({},opts,{headers:headers,credentials:'same-origin'}));});
      });
    }).then(function(r){
      if(r.status===204)return null;var ct=r.headers.get('content-type')||'';
      if(!r.ok)return (ct.indexOf('json')>=0?r.json():r.text().then(function(t){return {message:t}})).then(function(e){throw new Error(e.message||(e.detail&&e.detail.message)||'Error de solicitud')});
      return ct.indexOf('json')>=0?r.json():r;
    });
  }
  setMsg(msg){this.setState({msg:msg||''})}
  login(e){
    if(e)e.preventDefault();this.setState({busy:true,msg:''});
    this.api('/api/auth/login',{method:'POST',json:{correo:this.state.email,password:this.state.password}}).then((d)=>{
      sessionStorage.setItem('monda_token',d.accessToken);sessionStorage.setItem('monda_user',JSON.stringify(d.user));
      this.setState({user:d.user,token:d.accessToken,busy:false,page:'cursos',messages:[],conversationId:null,course:null,contents:[],adminUsers:[],adminConfig:null},()=>this.loadCourses());
    }).catch((e)=>this.setState({busy:false,msg:e.message}));
  }
  logout(){var headers={};document.cookie.split('; ').forEach(function(part){if(part.indexOf('monda_csrf=')===0)headers['X-CSRF-Token']=decodeURIComponent(part.substring('monda_csrf='.length))});this.api('/api/auth/logout',{method:'POST',headers:headers}).catch(function(){});sessionStorage.clear();this.setState({user:null,token:'',courses:[],course:null,msg:'',messages:[],conversationId:null,contents:[],adminUsers:[],adminConfig:null,audit:[]})}
  enrollStudent(){var c=this.state.course,id=this.state.studentId.trim();if(!c||!id)return this.setMsg('Selecciona un curso e introduce el UUID del estudiante.');this.api('/api/courses/'+c.id+'/enrollments',{method:'POST',json:{estudianteId:id}}).then(()=>this.setState({studentId:'',msg:'Matrícula registrada correctamente.'})).catch((e)=>this.setMsg(e.message))}
  loadCourses(){
    if(this.state.user.rol==='administrador')this.loadAdmin();
    this.api('/api/courses').then((d)=>this.setState({courses:d.items,course:this.state.course||d.items[0]||null})).catch((e)=>this.setMsg(e.message));
  }
  selectCourse(c){this.setState({course:c,msg:'',detail:null,analytics:null,messages:[],conversationId:null},()=>this.navigate(this.state.page))}
  createCourse(){var body={nombre:this.state.newCourseName};if(this.state.user.rol==='administrador'){if(!this.state.newTeacherId)return this.setMsg('Selecciona un docente activo.');body.docenteId=this.state.newTeacherId}this.api('/api/courses',{method:'POST',json:body}).then((c)=>this.setState({newCourseName:'',course:c,msg:'Curso creado.'},()=>this.loadCourses())).catch((e)=>this.setMsg(e.message))}
  saveCourse(){var c=this.state.editCourse;this.api('/api/courses/'+c.id,{method:'PATCH',json:{nombre:c.nombre,estado:c.estado,docenteId:c.docenteId}}).then((d)=>this.setState({editCourse:null,course:this.state.course&&this.state.course.id===d.id?d:this.state.course,msg:'Curso actualizado.'},()=>this.loadCourses())).catch((e)=>this.setMsg(e.message))}
  createUser(){this.api('/api/admin/users',{method:'POST',json:this.state.newUser}).then(()=>this.setState({newUser:{nombre:'',correo:'',rol:'estudiante',estado:'activo',password:''},msg:'Usuario creado.'},()=>this.loadAdmin())).catch((e)=>this.setMsg(e.message))}
  saveUser(){var u=this.state.editUser;this.api('/api/admin/users/'+u.id,{method:'PATCH',json:{nombre:u.nombre,correo:u.correo,rol:u.rol,estado:u.estado,version:u.version}}).then(()=>this.setState({editUser:null,msg:'Usuario actualizado.'},()=>this.loadAdmin())).catch((e)=>this.setMsg(e.message))}
  navigate(page){
    this.setState({page:page,msg:''},()=>{
      if(page==='contenidos')this.loadContents();
      if(page==='revision'||page==='resolver')this.loadAssessments();
      if(page==='seguimiento')this.loadAnalytics();
      if(page==='admin')this.loadAdmin();
    });
  }
  loadContents(){if(!this.state.course)return;this.api('/api/courses/'+this.state.course.id+'/contents').then((d)=>this.setState({contents:d.items})).catch((e)=>this.setMsg(e.message))}
  upload(){
    var f=this.state.uploadFile,c=this.state.course;if(!f||!c)return this.setMsg('Selecciona un PDF o DOCX.');
    var fd=new FormData();fd.append('file',f);fd.append('version',String(this.state.contentVersion));if(this.state.documentId)fd.append('documentoId',this.state.documentId);this.setState({busy:true,msg:''});
    fetch('/api/courses/'+c.id+'/contents',{method:'POST',headers:{Authorization:'Bearer '+this.state.token},body:fd}).then((r)=>r.json().then((d)=>({ok:r.ok,d:d}))).then((x)=>{
      if(!x.ok)throw new Error(x.d.message||'Error de carga');
      this.setState({documentId:x.d.documentoId||this.state.documentId,contentVersion:Number(x.d.version||this.state.contentVersion)+1});return this.api('/api/contents/'+x.d.contentId+'/index',{method:'POST',headers:{'Idempotency-Key':crypto.randomUUID()}});
    }).then((d)=>{this.setState({busy:false,msg:d.estado==='completado'?'Material cargado e indexado.':'Indexación: '+d.estado});this.loadContents()}).catch((e)=>this.setState({busy:false,msg:e.message}));
  }
  downloadContent(x){
    fetch('/api/contents/'+x.id+'/download',{headers:{Authorization:'Bearer '+this.state.token}}).then((r)=>{if(!r.ok)throw new Error('No se pudo descargar.');return r.blob()}).then((b)=>{var u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download=x.nombre;a.click();URL.revokeObjectURL(u)}).catch((e)=>this.setMsg(e.message));
  }
  ask(){
    var c=this.state.course,q=this.state.question.trim();if(!c||!q)return;
    var msgs=this.state.messages.concat([{autor:'usuario',contenido:q}]);this.setState({messages:msgs,busy:true,msg:''});
    this.api('/api/courses/'+c.id+'/rag/query',{method:'POST',json:{question:q,conversationId:this.state.conversationId}}).then((d)=>{
      this.setState({messages:this.state.messages.concat([{autor:'tutor',contenido:d.answer,fuentes:d.sources,messageId:d.messageId,evidence:d.evidenceSufficient}]),conversationId:d.conversationId,question:'',busy:false,msg:'Tutor: '+d.mode+(d.providerWarning?' · '+d.providerWarning:'')});
    }).catch((e)=>this.setState({busy:false,msg:e.message}));
  }
  rate(id,util){this.api('/api/rag/messages/'+id+'/rating',{method:'POST',json:{util:util}}).then(()=>this.setMsg('Valoración guardada.')).catch((e)=>this.setMsg(e.message))}
  generate(){
    if(!this.state.course)return this.setMsg('Selecciona un curso.');var g=this.state.gen;this.setState({busy:true,msg:''});
    this.api('/api/courses/'+this.state.course.id+'/assessments/generate',{method:'POST',json:{tema:g.tema,bloom:g.bloom,dificultad:g.dificultad,cantidad:Number(g.cantidad),tipo:g.tipo}}).then((d)=>{
      this.setState({busy:false,msg:'Borrador generado.',focusAssessment:d.assessmentId,page:'revision'},()=>this.loadAssessments(d.assessmentId));
    }).catch((e)=>this.setState({busy:false,msg:e.message}));
  }
  loadAssessments(preferred){
    if(!this.state.course)return;
    this.api('/api/courses/'+this.state.course.id+'/assessments').then((d)=>{
      this.setState({assessments:d.items});var id=preferred||this.state.focusAssessment||(d.items[0]&&d.items[0].id);if(id)this.openAssessment(id);
    }).catch((e)=>this.setMsg(e.message));
  }
  openAssessment(id){
    this.api('/api/assessments/'+id).then((d)=>{
      this.setState({detail:d,focusAssessment:id,answers:{},attempt:null});
      if(this.state.user.rol==='estudiante'){
        this.api('/api/assessments/'+id+'/attempts',{method:'POST',headers:{'Idempotency-Key':crypto.randomUUID()},json:{accion:'iniciar'}}).then((a)=>this.setState({attempt:a})).catch((e)=>this.setMsg(e.message));
      }
    }).catch((e)=>this.setMsg(e.message));
  }
  reviewQuestion(q,state){
    this.api('/api/questions/'+q.id+'/review',{method:'PATCH',json:{estado:state,version:q.version}}).then(()=>{this.setMsg('Revisión guardada.');this.openAssessment(this.state.detail.id)}).catch((e)=>this.setMsg(e.message));
  }
  publish(){
    var d=this.state.detail;if(!d)return;var start=new Date(Date.now()-60000).toISOString(),end=new Date(Date.now()+7*86400000).toISOString();
    this.api('/api/assessments/'+d.id+'/publish',{method:'POST',json:{fechaInicio:start,fechaFin:end,version:d.version}}).then(()=>{this.setMsg('Evaluación publicada.');this.openAssessment(d.id)}).catch((e)=>this.setMsg(e.message));
  }
  closeAttempt(){
    var d=this.state.detail;if(!d)return;
    this.api('/api/assessments/'+d.id+'/attempts',{method:'POST',headers:{'Idempotency-Key':crypto.randomUUID()},json:{accion:'cerrar',intentoId:this.state.attempt&&this.state.attempt.attemptId,respuestas:this.state.answers}}).then((r)=>this.setState({attempt:r,msg:'Intento cerrado. Puntaje: '+r.puntaje+'/20 ('+r.correctas+'/'+r.total+').'})).catch((e)=>this.setMsg(e.message));
  }
  loadAnalytics(){if(!this.state.course||this.state.user.rol==='estudiante')return;this.api('/api/courses/'+this.state.course.id+'/analytics').then((d)=>this.setState({analytics:d})).catch((e)=>this.setMsg(e.message))}
  reviewAlert(id){this.api('/api/alerts/'+id,{method:'PATCH',json:{estado:'revisada',comentario:'Revisada desde el panel local'}}).then(()=>this.loadAnalytics()).catch((e)=>this.setMsg(e.message))}
  exportCsv(){
    if(!this.state.course)return;fetch('/api/courses/'+this.state.course.id+'/reports/export?format=csv',{headers:{Authorization:'Bearer '+this.state.token}}).then((r)=>{if(!r.ok)throw new Error('No se pudo exportar.');return r.blob()}).then((b)=>{var u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download='reporte_monda.csv';a.click();URL.revokeObjectURL(u)}).catch((e)=>this.setMsg(e.message));
  }
  loadAdmin(){if(this.state.user.rol!=='administrador')return;Promise.all([this.api('/api/admin/users?limit=100'),this.api('/api/admin/config'),this.api('/api/admin/audit')]).then((x)=>this.setState({adminUsers:x[0].items,adminConfig:x[1],audit:x[2].items})).catch((e)=>this.setMsg(e.message))}
  saveConfig(){var c=this.state.adminConfig;if(!c)return;this.api('/api/admin/config',{method:'PATCH',json:{topK:Number(c.topK),umbral:Number(c.umbral),mode:c.mode||'auto',modelo:c.modelo,ollamaModel:c.ollamaModel,version:c.version}}).then((d)=>this.setState({adminConfig:d,msg:'Configuración guardada y auditada.'},()=>this.loadAdmin())).catch((e)=>this.setMsg(e.message))}
  sync(){
    if(this.state.offline)return this.setMsg('Conecta el equipo antes de sincronizar.');
    this.api('/api/sync',{method:'POST',json:{actions:[{actionId:crypto.randomUUID(),tipo:'draft',payload:{tipo:'nota_local',texto:'Borrador de demostración'},version:1}]}}).then((d)=>this.setMsg('Sincronización aplicada: '+d.results[0].status)).catch((e)=>this.setMsg(e.message));
  }
  renderLogin(){
    var cred=(name,email,pass)=>h('button',{className:'btn secondary',style:{marginRight:8,marginTop:8},onClick:()=>this.setState({email:email,password:pass})},name);
    return h('div',{className:'loginWrap'},
      h('section',{className:'hero'},h('div',null,h('div',{className:'eyebrow',style:{color:'#bcd4fa'}},'UNMSM · FISI · T6–T9'),h('h1',null,'Aprende, consulta y evalúa en un solo lugar.'),h('p',null,'Monda integra cursos, materiales versionados, tutor RAG con fuentes, evaluación con revisión docente y seguimiento académico.'))),
      h('section',{className:'login'},h('div',{className:'box'},h('div',{className:'brand',style:{marginBottom:28}},'monda',h('span',null,'Plataforma educativa')),h('h2',null,'Iniciar sesión'),h('p',{className:'muted'},'Entorno local funcional para validar PI7.'),
        h('form',{onSubmit:(e)=>this.login(e)},Field('Correo',h('input',{type:'email',required:true,value:this.state.email,onChange:(e)=>this.setState({email:e.target.value})})),Field('Contraseña',h('input',{type:'password',required:true,value:this.state.password,onChange:(e)=>this.setState({password:e.target.value})})),this.state.msg&&h(Notice,{type:'error'},this.state.msg),h(Btn,{type:'submit',disabled:this.state.busy},this.state.busy?'Ingresando…':'Ingresar')),
        h('div',{className:'demoCred'},h('strong',null,'Cuentas de demostración'),h('div',null,cred('Docente','docente@monda.local','Docente123!'),cred('Estudiante','estudiante@monda.local','Estudiante123!'),cred('Administrador','admin@monda.local','Admin123!')))
      ))
    );
  }
  renderCourses(){
    var admin=this.state.user.rol==='administrador',teachers=this.state.adminUsers.filter((u)=>u.rol==='docente'&&u.estado==='activo'),edit=this.state.editCourse;
    var teacherOptions=(value,onChange)=>h('select',{value:value||'',onChange:onChange},h('option',{value:''},'Selecciona docente'),teachers.map((u)=>h('option',{key:u.id,value:u.id},u.nombre+' · '+u.correo)));
    var management=this.state.user.rol!=='estudiante'&&h(Card,null,h('h3',null,'Crear curso'),Field('Nombre',h('input',{value:this.state.newCourseName,onChange:(e)=>this.setState({newCourseName:e.target.value})})),admin&&Field('Docente responsable',teacherOptions(this.state.newTeacherId,(e)=>this.setState({newTeacherId:e.target.value}))),h(Btn,{onClick:()=>this.createCourse(),disabled:this.state.newCourseName.trim().length<2},'Crear curso'),admin&&h('div',null,h('h3',null,'Editar y asignar cursos'),this.state.courses.map((c)=>h('div',{key:c.id,className:'actions'},h('span',null,c.nombre+' · '+((this.state.adminUsers.find((u)=>u.id===c.docenteId)||{}).nombre||'Docente')),h(Btn,{secondary:true,onClick:()=>this.setState({editCourse:Object.assign({},c)})},'Editar / asignar')))),edit&&h('div',null,Field('Nombre del curso',h('input',{value:edit.nombre,onChange:(e)=>this.setState({editCourse:Object.assign({},edit,{nombre:e.target.value})})})),Field('Docente',teacherOptions(edit.docenteId,(e)=>this.setState({editCourse:Object.assign({},edit,{docenteId:e.target.value})}))),Field('Estado',h('select',{value:edit.estado,onChange:(e)=>this.setState({editCourse:Object.assign({},edit,{estado:e.target.value})})},['activo','archivado'].map((s)=>h('option',{key:s,value:s},s)))),h(Btn,{onClick:()=>this.saveCourse()},'Guardar curso'),h(Btn,{secondary:true,onClick:()=>this.setState({editCourse:null})},'Cancelar')));
    var cards=this.state.courses.map((c)=>h(Card,{key:c.id},h('div',{className:'actions',style:{justifyContent:'space-between'}},h(Badge,{type:c.estado==='activo'?'':'gray'},c.estado),h('span',{className:'small muted'},c.id.slice(0,8))),h('h3',{style:{marginTop:18}},c.nombre),h('p',{className:'muted'},'Materiales, tutor, evaluaciones y analítica.'),h(Btn,{onClick:()=>this.selectCourse(c)},this.state.course&&this.state.course.id===c.id?'Seleccionado':'Abrir curso')));
    return h('div',null,Header('UI-02','Mis cursos','Selecciona el espacio académico sobre el que deseas trabajar.'),management,this.state.user.rol!=='estudiante'&&h(Card,null,h('h3',null,'Matricular estudiante'),h('p',{className:'muted'},'Curso seleccionado: '+(this.state.course?this.state.course.nombre:'ninguno')),Field('Estudiante',admin?h('select',{value:this.state.studentId,onChange:(e)=>this.setState({studentId:e.target.value})},h('option',{value:''},'Selecciona estudiante'),this.state.adminUsers.filter((u)=>u.rol==='estudiante'&&u.estado==='activo').map((u)=>h('option',{key:u.id,value:u.id},u.nombre+' · '+u.correo))):h('input',{value:this.state.studentId,onChange:(e)=>this.setState({studentId:e.target.value}),placeholder:'UUID de estudiante'})),h(Btn,{onClick:()=>this.enrollStudent(),disabled:!this.state.course||!this.state.studentId},'Registrar matrícula')),h('div',{className:'grid'},cards.length?cards:h('div',{className:'empty'},'No hay cursos.')));
  }
  renderContents(){
    var c=this.state.course;if(!c)return h(Notice,null,'Selecciona un curso primero.');var rows=this.state.contents.map((x)=>h('tr',{key:x.id},h('td',null,x.nombre),h('td',null,x.version),h('td',null,h(Badge,{type:x.estado==='indexado'?'':'warn'},x.estado)),h('td',null,h(Btn,{secondary:true,onClick:()=>this.downloadContent(x)},'Descargar'))));
    return h('div',null,Header('UI-03','Contenidos del curso',c.nombre+' · PDF/DOCX, versiones e indexación RAG'),this.state.user.rol!=='estudiante'&&h(Card,null,h('h3',null,'Cargar material'),h('p',{className:'muted'},'Archivos con texto extraíble, máximo 20 MiB.'),Field('Archivo',h('input',{type:'file',accept:'.pdf,.docx',onChange:(e)=>this.setState({uploadFile:e.target.files[0]})})),Field('ID lógico del documento (vacío para material nuevo)',h('input',{value:this.state.documentId,onChange:(e)=>this.setState({documentId:e.target.value}),placeholder:'Se genera al primer upload'})),Field('Versión',h('input',{type:'number',min:1,value:this.state.contentVersion,onChange:(e)=>this.setState({contentVersion:Number(e.target.value)})})),h(Btn,{onClick:()=>this.upload(),disabled:this.state.busy},this.state.busy?'Procesando…':'Cargar e indexar')),h(Card,null,h('h3',null,'Materiales'),rows.length?h('table',null,h('thead',null,h('tr',null,h('th',null,'Material'),h('th',null,'Versión'),h('th',null,'Estado'),h('th',null,'Acción'))),h('tbody',null,rows)):h('div',{className:'empty'},'Aún no hay materiales.')));
  }
  renderTutor(){
    if(!this.state.course)return h(Notice,null,'Selecciona un curso primero.');var bubbles=this.state.messages.map((m,i)=>h('div',{key:i,className:'bubble '+m.autor},h('div',null,m.contenido),m.fuentes&&m.fuentes.slice(0,3).map((s,j)=>h('span',{key:j,className:'source'},'Fuente '+(j+1)+' · fragmento '+s.ordinal+' · similitud '+s.score+': '+s.excerpt)),m.messageId&&h('div',{className:'actions',style:{marginTop:8}},h(Btn,{secondary:true,onClick:()=>this.rate(m.messageId,true)},'Útil'),h(Btn,{secondary:true,onClick:()=>this.rate(m.messageId,false)},'No útil'))));
    return h('div',null,Header('UI-04','Tutor del curso','Consulta solo materiales autorizados y revisa siempre las fuentes.'),h('div',{className:'grid',style:{gridTemplateColumns:'1.5fr .5fr'}},h(Card,null,h('div',{className:'chat'},bubbles.length?bubbles:h('div',{className:'empty'},'Escribe tu primera consulta.')),Field('Pregunta',h('textarea',{rows:3,value:this.state.question,onChange:(e)=>this.setState({question:e.target.value}),placeholder:'Pregunta sobre los materiales…'})),h(Btn,{onClick:()=>this.ask(),disabled:this.state.busy},this.state.busy?'Consultando…':'Consultar')),h(Card,null,h('h3',null,'Cómo responde'),h('p',{className:'muted'},'Recupera fragmentos con TF‑IDF/coseno. Si activas Ollama, redacta con el contexto recuperado.'),h(Notice,null,'Si no alcanza el umbral de evidencia, Monda se abstiene.'))));
  }
  renderGenerate(){
    if(this.state.user.rol==='estudiante')return h(Notice,null,'Esta pantalla corresponde al rol Docente.');if(!this.state.course)return h(Notice,null,'Selecciona un curso primero.');var g=this.state.gen,upd=(k,v)=>this.setState({gen:Object.assign({},g,{[k]:v})});
    return h('div',null,Header('UI-05','Generar evaluación','Los reactivos se crean como borradores y requieren revisión docente.'),h(Card,null,h('div',{className:'grid'},Field('Tema',h('input',{value:g.tema,onChange:(e)=>upd('tema',e.target.value)})),Field('Nivel de Bloom',h('select',{value:g.bloom,onChange:(e)=>upd('bloom',e.target.value)},['recordar','comprender','aplicar','analizar','evaluar','crear'].map((x)=>h('option',{key:x,value:x},x)))),Field('Dificultad',h('select',{value:g.dificultad,onChange:(e)=>upd('dificultad',e.target.value)},['baja','media','alta'].map((x)=>h('option',{key:x,value:x},x)))),Field('Cantidad',h('input',{type:'number',min:1,max:20,value:g.cantidad,onChange:(e)=>upd('cantidad',e.target.value)}))),h(Btn,{onClick:()=>this.generate(),disabled:this.state.busy},this.state.busy?'Generando…':'Generar borradores')));
  }
  renderReview(){
    if(this.state.user.rol==='estudiante')return h(Notice,null,'Esta pantalla corresponde al rol Docente.');var d=this.state.detail;
    var list=this.state.assessments.map((a)=>h('button',{key:a.id,className:'btn '+(d&&d.id===a.id?'':'secondary'),style:{display:'block',width:'100%',marginBottom:8},onClick:()=>this.openAssessment(a.id)},a.titulo+' · '+a.estado));
    var detail=d?h('div',null,h('div',{className:'actions',style:{justifyContent:'space-between'}},h('h3',null,d.titulo),h(Badge,{type:d.estado==='publicada'?'':'warn'},d.estado)),d.questions.map((q,i)=>h('div',{className:'questionBox',key:q.id},h('strong',null,(i+1)+'. '+q.enunciado),Object.keys(q.opciones).map((k)=>h('div',{key:k,className:'muted',style:{marginTop:6}},k+'. '+q.opciones[k])),h('p',{className:'small'},'Clave: '+q.clave+' · Fuente: '+String(q.fragmentoId||'').slice(0,8)),h('div',{className:'actions'},h(Badge,{type:q.estadoRevision==='aprobado'?'':q.estadoRevision==='rechazado'?'red':'gray'},q.estadoRevision),h(Btn,{secondary:true,onClick:()=>this.reviewQuestion(q,'aprobado')},'Aprobar'),h(Btn,{secondary:true,onClick:()=>this.reviewQuestion(q,'rechazado')},'Rechazar')))),h(Btn,{onClick:()=>this.publish(),disabled:d.estado==='publicada'},'Publicar por 7 días')):h('div',{className:'empty'},'Selecciona una evaluación.');
    return h('div',null,Header('UI-06','Revisar y publicar','La publicación exige que todos los reactivos estén aprobados.'),h('div',{className:'grid',style:{gridTemplateColumns:'.65fr 1.35fr'}},h(Card,null,h('h3',null,'Borradores'),list.length?list:h('div',{className:'empty'},'No hay evaluaciones.')),h(Card,null,detail)));
  }
  renderSolve(){
    if(this.state.user.rol!=='estudiante')return h('div',null,Header('UI-07','Resolver evaluación','Vista destinada al estudiante.'),h(Notice,null,'Inicia sesión como Estudiante para probar intento y calificación.'));
    var d=this.state.detail,list=this.state.assessments.map((a)=>h('button',{key:a.id,className:'btn secondary',style:{display:'block',width:'100%',marginBottom:8},onClick:()=>this.openAssessment(a.id)},a.titulo));
    var exam=d?h('div',null,h('h3',null,d.titulo),d.questions.map((q,i)=>h('div',{className:'questionBox',key:q.id},h('strong',null,(i+1)+'. '+q.enunciado),Object.keys(q.opciones).map((k)=>h('label',{className:'opt',key:k},h('input',{type:'radio',name:q.id,checked:this.state.answers[q.id]===k,onChange:()=>this.setState({answers:Object.assign({},this.state.answers,{[q.id]:k})})}),' '+k+'. '+q.opciones[k])))),h(Btn,{onClick:()=>this.closeAttempt(),disabled:this.state.attempt&&this.state.attempt.estado==='cerrado'},this.state.attempt&&this.state.attempt.estado==='cerrado'?'Intento cerrado':'Finalizar intento')):h('div',{className:'empty'},'Selecciona una evaluación.');
    return h('div',null,Header('UI-07','Resolver evaluación','Un intento por estudiante; el puntaje se calcula en el servidor.'),h('div',{className:'grid',style:{gridTemplateColumns:'.6fr 1.4fr'}},h(Card,null,h('h3',null,'Disponibles'),list.length?list:h('div',{className:'empty'},'No hay evaluaciones publicadas.')),h(Card,null,exam)));
  }
  renderAnalytics(){
    if(this.state.user.rol==='estudiante')return h(Notice,null,'El seguimiento agregado corresponde al docente.');if(!this.state.course)return h(Notice,null,'Selecciona un curso primero.');var d=this.state.analytics;
    var kpis=d?Object.keys(d.indicadores).map((k)=>h(Card,{key:k,className:'metric'},h('span',{className:'kpiTitle'},k.replace(/([A-Z])/g,' $1')),h('strong',null,d.indicadores[k]===null?'—':d.indicadores[k]))):[];
    var alerts=d&&d.alertas.length?h('table',null,h('thead',null,h('tr',null,h('th',null,'Estudiante'),h('th',null,'Regla'),h('th',null,'Evidencia'),h('th',null,'Estado'))),h('tbody',null,d.alertas.map((a)=>h('tr',{key:a.id},h('td',null,a.estudianteId.slice(0,8)),h('td',null,a.regla),h('td',null,JSON.stringify(a.evidencia)),h('td',null,a.estado==='abierta'?h(Btn,{secondary:true,onClick:()=>this.reviewAlert(a.id)},'Revisar'):h(Badge,null,'revisada')))))):h('div',{className:'empty'},'No hay alertas abiertas.');
    return h('div',null,Header('UI-08','Seguimiento académico','Indicadores descriptivos y alertas explicables; no toman decisiones automáticas.'),d?h('div',{className:'grid3'},kpis):h('div',null,'Cargando…'),d&&h(Card,null,h('div',{className:'actions',style:{justifyContent:'space-between'}},h('h3',null,'Alertas'),h(Btn,{secondary:true,onClick:()=>this.exportCsv()},'Exportar CSV')),alerts));
  }
  renderAdmin(){
    var form=(u,update,save,label)=>h(Card,null,h('h3',null,label),Field('Nombre',h('input',{value:u.nombre,onChange:(e)=>update('nombre',e.target.value)})),Field('Correo',h('input',{type:'email',value:u.correo,onChange:(e)=>update('correo',e.target.value)})),Field('Rol',h('select',{value:u.rol,onChange:(e)=>update('rol',e.target.value)},['administrador','docente','estudiante'].map((s)=>h('option',{key:s,value:s},fmtRole(s))))),Field('Estado',h('select',{value:u.estado,onChange:(e)=>update('estado',e.target.value)},['activo','inactivo','pendiente'].map((s)=>h('option',{key:s,value:s},s)))),!u.id&&Field('Contraseña inicial (mínimo 8 caracteres)',h('input',{type:'password',value:u.password,onChange:(e)=>update('password',e.target.value),autoComplete:'new-password'})),h(Btn,{onClick:save,disabled:!u.nombre||!u.correo||(!u.id&&u.password.length<8)},'Guardar usuario'),u.id&&h(Btn,{secondary:true,onClick:()=>this.setState({editUser:null})},'Cancelar'));
    var userForms=h('div',null,form(this.state.newUser,(k,v)=>this.setState({newUser:Object.assign({},this.state.newUser,{[k]:v})}),()=>this.createUser(),'Crear usuario'),this.state.editUser&&form(this.state.editUser,(k,v)=>this.setState({editUser:Object.assign({},this.state.editUser,{[k]:v})}),()=>this.saveUser(),'Editar usuario'),h(Card,null,h('h3',null,'Editar usuarios'),this.state.adminUsers.map((u)=>h('div',{key:u.id,className:'actions'},h('span',null,u.nombre+' · '+u.correo),h(Btn,{secondary:true,onClick:()=>this.setState({editUser:Object.assign({},u)})},'Editar')))));
    if(this.state.user.rol!=='administrador')return h(Notice,null,'Inicia sesión como Administrador para acceder.');var c=this.state.adminConfig,change=(k,v)=>this.setState({adminConfig:Object.assign({},c,{[k]:v})});
    var users=h('table',null,h('thead',null,h('tr',null,h('th',null,'Nombre'),h('th',null,'UUID'),h('th',null,'Rol'),h('th',null,'Estado'))),h('tbody',null,this.state.adminUsers.map((u)=>h('tr',{key:u.id},h('td',null,u.nombre),h('td',{className:'small'},u.id),h('td',null,u.rol),h('td',null,h(Badge,{type:u.estado==='activo'?'':'warn'},u.estado))))));
    var aud=this.state.audit.length?h('table',null,h('thead',null,h('tr',null,h('th',null,'Acción'),h('th',null,'Objeto'),h('th',null,'Resultado'))),h('tbody',null,this.state.audit.slice(0,10).map((a)=>h('tr',{key:a.id},h('td',null,a.accion),h('td',null,a.objeto),h('td',null,a.resultado))))):h('div',{className:'empty'},'Sin registros.');
    return h('div',null,Header('UI-09','Administración','Usuarios, configuración RAG y trazabilidad.'),userForms,h('div',{className:'grid'},h(Card,null,h('h3',null,'Configuración RAG'),c&&h('div',null,Field('Modo del tutor',h('select',{value:c.mode||'auto',onChange:(e)=>change('mode',e.target.value)},['auto','gemini','ollama','fallback'].map((s)=>h('option',{key:s,value:s},s)))),Field('Top K',h('input',{type:'number',value:c.topK,onChange:(e)=>change('topK',e.target.value)})),Field('Umbral',h('input',{type:'number',step:'.01',value:c.umbral,onChange:(e)=>change('umbral',e.target.value)})),Field('Modelo Gemini',h('input',{value:c.modelo,onChange:(e)=>change('modelo',e.target.value)})),Field('Modelo Ollama',h('input',{value:c.ollamaModel,onChange:(e)=>change('ollamaModel',e.target.value)})),h(Btn,{onClick:()=>this.saveConfig()},'Guardar'))),h(Card,null,h('h3',null,'Usuarios'),users)),h(Card,null,h('h3',null,'Auditoría reciente'),aud));
  }
  renderSync(){return h('div',null,Header('UI-10','Sincronización','Lectura y borradores locales con idempotencia al recuperar conexión.'),h(Card,null,h('div',{className:'actions',style:{justifyContent:'space-between'}},h('h3',null,'Estado de conexión'),h(Badge,{type:this.state.offline?'warn':''},this.state.offline?'Sin conexión':'En línea')),h('p',{className:'muted'},'Los borradores se reenvían con actionId para evitar duplicados.'),h(Btn,{onClick:()=>this.sync(),disabled:this.state.offline},'Probar sincronización')))}
  renderPage(){var p=this.state.page;if(p==='cursos')return this.renderCourses();if(p==='contenidos')return this.renderContents();if(p==='tutor')return this.renderTutor();if(p==='generar')return this.renderGenerate();if(p==='revision')return this.renderReview();if(p==='resolver')return this.renderSolve();if(p==='seguimiento')return this.renderAnalytics();if(p==='admin')return this.renderAdmin();return this.renderSync()}
  renderShell(){
    var u=this.state.user,c=this.state.course;var nav=[['cursos','◫','Mis cursos'],['contenidos','▤','Contenidos'],['tutor','✦','Tutor']];if(u.rol!=='estudiante'){nav.push(['generar','＋','Generar evaluación']);nav.push(['revision','✓','Revisar/publicar'])}nav.push(['resolver','◉','Resolver evaluación']);if(u.rol!=='estudiante')nav.push(['seguimiento','▥','Seguimiento']);if(u.rol==='administrador')nav.push(['admin','⚙','Administración']);nav.push(['sync','↻','Sincronización']);
    return h('div',{className:'app'},h('header',{className:'top'},h('div',{className:'brand'},'monda',h('span',null,'Plataforma educativa')),h('div',{className:'topright'},c&&h(Badge,{type:'gray'},c.nombre),h('div',{className:'muted small'},u.nombre,h('br'),fmtRole(u.rol)),h('div',{className:'avatar'},u.nombre.charAt(0).toUpperCase()),h(Btn,{secondary:true,onClick:()=>this.logout()},'Salir'))),h('div',{className:'layout'},h('aside',{className:'side'},h('div',{className:'mini'},'Navegación'),nav.map((n)=>h('button',{key:n[0],className:this.state.page===n[0]?'active':'',onClick:()=>this.navigate(n[0])},h('span',null,n[1]),n[2])),h('div',{className:'mini'},'Curso actual'),h('div',{className:'small muted',style:{padding:'8px 12px'}},c?c.nombre:'Ninguno seleccionado')),h('main',{className:'main'},this.renderPage(),this.state.msg&&h('div',{style:{marginTop:14}},h(Notice,{type:/guardad|publicad|generad|indexad|Puntaje|aplicada/i.test(this.state.msg)?'ok':'error'},this.state.msg)),h('div',{className:'footerNote'},'Monda local · Implementación técnica PI7 · Los datos de demostración no son resultados institucionales.'))));
  }
  render(){return this.state.user?this.renderShell():this.renderLogin()}
}

ReactDOM.render(h(App),document.getElementById('root'));
})();
