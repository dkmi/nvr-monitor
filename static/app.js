'use strict';
const dict={bg:{setupToken:'Код за първоначална настройка',masterPassword:'Главна парола',setupHelp:'Задай парола с поне 12 знака. Кодът за настройка се намира на сървъра в data/setup-token.',unlock:'Отключи',setupTitle:'Първо стартиране — създай главна парола',loginTitle:'Влез в системата за видеонаблюдение',live:'На живо',playback:'Playback',cameras:'Камери',addCamera:'+ Добави камера',backgroundHint:'Наблюдението и записването продължават при заключен интерфейс или затворен браузър.',changePassword:'Смени главната парола',lock:'Заключи',layout:'Изглед',noCameras:'Няма добавени камери',addHint:'Добави IP адреса и данните за вход на първата камера.',camera:'Камера',date:'Дата',refresh:'Обнови',timelineHint:'Натисни върху запис във времевата линия, за да го възпроизведеш. Часовете са по местното време на браузъра.',download:'Изтегли MP4',cameraSettings:'Настройки на камерата',name:'Име',host:'IP адрес / хост',username:'Потребител',cameraPassword:'Парола за камерата',port:'RTSP порт',channel:'Канал',stream:'Поток',mainStream:'Основен поток',subStream:'Допълнителен поток',enabled:'Камерата е включена',motionEnabled:'Запис при движение',sensitivity:'Чувствителност',buffer:'Буфер преди движението (сек.)',tail:'Запис след движението (сек.)',folder:'Подпапка в /recordings',maxDays:'Пази записи до (дни)',maxGB:'Лимит за камерата (GB)',bufferHelp:'Буфер: 0–30 секунди. Потокът се обработва в постоянен временен дисков кеш. MP4 се появява след края на събитието; дългите събития се разделят на части около 60 секунди.',zone:'Зона за засичане',zoneHelp:'Провлачи правоъгълник или въведи проценти. Прегледът е наличен след запазване на камерата. Зоната следва целия кадър.',width:'Ширина',height:'Височина',fullZone:'Целият кадър',deleteCamera:'Изтрий камерата',save:'Запази',oldPassword:'Текуща парола',newPassword:'Нова парола (поне 12 знака)',confirmPassword:'Повтори новата парола',passwordHelp:'Паролите за камерите се запазват. Всички други браузърни сесии се прекратяват.',cancel:'Отказ',soundOn:'Включи звук',soundOff:'Изключи звук',expand:'Разгъни',settings:'Настройки',buffering:'Пълнене на буфера · около 30 сек.',connecting:'Свързване…',watching:'Наблюдение за движение',recording:'● Запис при движение',offline:'Няма връзка — повторен опит',disabled:'Изключена',allCameras:'Всички камери',noClips:'Няма записи за избраната дата.',duration:'Продължителност',seconds:'сек.',clips:'записа',cameraCount:'камери',saved:'Настройките са запазени.',error:'Неуспешна заявка',invalidLogin:'Невалидна парола или код. След поредица опити изчакай една минута.',deleteConfirm:'Да изтрия ли камерата? Записите ще останат.',leavePassword:'Остави празно, за да запазиш текущата парола',zoneError:'Зоната трябва да е в границите на кадъра.',passwordMismatch:'Паролите не съвпадат.',passwordChanged:'Главната парола е сменена.',previewUnavailable:'Потокът се зарежда…',playError:'Записът не може да се отвори или вече е изтрит.'},en:{setupToken:'Initial setup code',masterPassword:'Master password',setupHelp:'Choose at least 12 characters. Find the setup code on the server in data/setup-token.',unlock:'Unlock',setupTitle:'First launch — create a master password',loginTitle:'Sign in to video surveillance',live:'Live',playback:'Playback',cameras:'Cameras',addCamera:'+ Add camera',backgroundHint:'Monitoring and recording continue when the interface is locked or the browser is closed.',changePassword:'Change master password',lock:'Lock',layout:'Layout',noCameras:'No cameras added',addHint:'Add the IP address and credentials of your first camera.',camera:'Camera',date:'Date',refresh:'Refresh',timelineHint:'Click a recording on the timeline to play it. Times use your browser’s local timezone.',download:'Download MP4',cameraSettings:'Camera settings',name:'Name',host:'IP address / host',username:'Username',cameraPassword:'Camera password',port:'RTSP port',channel:'Channel',stream:'Stream',mainStream:'Main stream',subStream:'Substream',enabled:'Camera enabled',motionEnabled:'Record on motion',sensitivity:'Sensitivity',buffer:'Pre-motion buffer (seconds)',tail:'Post-motion recording (seconds)',folder:'Subfolder under /recordings',maxDays:'Keep recordings for (days)',maxGB:'Camera storage limit (GB)',bufferHelp:'Buffer: 0–30 seconds. The stream uses a continuous temporary disk cache. MP4 appears after the event ends; long events are split near 60 seconds.',zone:'Detection zone',zoneHelp:'Drag a rectangle or enter percentages. Preview is available after saving the camera. The zone follows the entire frame.',width:'Width',height:'Height',fullZone:'Full frame',deleteCamera:'Delete camera',save:'Save',oldPassword:'Current password',newPassword:'New password (at least 12 characters)',confirmPassword:'Repeat new password',passwordHelp:'Camera credentials are retained. All other browser sessions are signed out.',cancel:'Cancel',soundOn:'Enable sound',soundOff:'Mute',expand:'Expand',settings:'Settings',buffering:'Filling buffer · about 30 sec',connecting:'Connecting…',watching:'Watching for motion',recording:'● Motion recording',offline:'Disconnected — retrying',disabled:'Disabled',allCameras:'All cameras',noClips:'No recordings for this date.',duration:'Duration',seconds:'sec',clips:'recordings',cameraCount:'cameras',saved:'Settings saved.',error:'Request failed',invalidLogin:'Invalid password or setup code. After repeated attempts, wait one minute.',deleteConfirm:'Delete this camera? Recordings will be retained.',leavePassword:'Leave blank to keep the current password',zoneError:'The zone must stay inside the frame.',passwordMismatch:'Passwords do not match.',passwordChanged:'Master password changed.',previewUnavailable:'Loading stream…',playError:'Recording is unavailable or has been deleted.'}};
Object.assign(dict.bg,{users:'Потребители',newUser:'+ Нов потребител',password:'Парола (поне 12 знака)',role:'Права',roleAdmin:'Администратор',roleFull:'Пълен достъп: камери и записи',roleLimited:'Ограничен: избрани камери и записи',rolePlayback:'Само преглед на записи',userEnabled:'Активен потребител',allCameraAccess:'Всички камери, включително бъдещи',roleHelp:'Администраторът управлява всичко. Останалите профили нямат достъп до настройки и пароли за камерите. Прегледът на записи не дава Live достъп.',deleteUser:'Изтрий потребителя',deleteUserConfirm:'Да изтрия ли потребителя?',userSaved:'Потребителят е запазен.',masterPassword:'Парола',changePassword:'Смени паролата',setupTitle:'Първо стартиране — създай администратор',setupHelp:'Избери потребителско име и парола с поне 12 знака.',invalidLogin:'Невалидно потребителско име или парола. След поредица опити изчакай една минута.',leavePassword:'Остави празно за запазване на паролата'});
Object.assign(dict.en,{users:'Users',newUser:'+ New user',password:'Password (at least 12 characters)',role:'Permissions',roleAdmin:'Administrator',roleFull:'Full: all cameras and recordings',roleLimited:'Limited: selected cameras and recordings',rolePlayback:'Recordings only',userEnabled:'Enabled user',allCameraAccess:'All cameras, including future cameras',roleHelp:'Administrators manage everything. Other roles cannot access settings or camera credentials. Recordings-only users cannot watch Live.',deleteUser:'Delete user',deleteUserConfirm:'Delete this user?',userSaved:'User saved.',masterPassword:'Password',changePassword:'Change password',setupTitle:'First launch — create an administrator',setupHelp:'Choose a username and a password with at least 12 characters.',invalidLogin:'Invalid username or password. After repeated attempts, wait one minute.'});
Object.assign(dict.bg,{viewingBuffer:'Буфер за гледане',buffering:'Пълнене на буфера…',delayHelp:'0 изключва умишленото забавяне. Остава техническото HLS закъснение. Записът и предзаписът при движение не се променят.',passwordChanged:'Паролата е сменена.',passwordHelp:'Останалите сесии на твоя профил ще бъдат прекратени.'});
Object.assign(dict.en,{viewingBuffer:'Viewing buffer',buffering:'Filling buffer…',delayHelp:'0 disables intentional delay. Technical HLS latency remains. Motion recording and pre-roll are unchanged.',passwordChanged:'Password changed.',passwordHelp:'Other sessions of your account will be signed out.'});
Object.assign(dict.bg,{motionMethod:'Засичане на движение',rtspDetection:'RTSP — анализ от сървъра',onvifDetection:'ONVIF — събития от камерата',onvifPort:'ONVIF HTTP порт',soapVersion:'Версия на ONVIF SOAP',automatic:'Автоматично',onvifFallback:'Резервен RTSP анализ при проблем с ONVIF',onvifSameCredentials:'Същите данни за вход като за видеото',onvifUsername:'ONVIF потребител',onvifPassword:'ONVIF парола',motionMethodHelp:'Видеото и звукът използват RTSP и в двата режима. При ONVIF движението, зоната и чувствителността се настройват в самата камера. Сървърните настройки са запазени за RTSP анализа; предзаписът, опашката и лимитите важат и за двата режима.',onvif_offline:'Видеото работи · няма ONVIF събития',rtsp_fallback:'RTSP — резервен анализ',onvif_connecting:'ONVIF — свързване'});
Object.assign(dict.en,{motionMethod:'Motion detection',rtspDetection:'RTSP — server analysis',onvifDetection:'ONVIF — camera events',onvifPort:'ONVIF HTTP port',soapVersion:'ONVIF SOAP version',automatic:'Automatic',onvifFallback:'Use RTSP analysis if ONVIF fails',onvifSameCredentials:'Use the same credentials as the video',onvifUsername:'ONVIF username',onvifPassword:'ONVIF password',motionMethodHelp:'Video and audio use RTSP in both modes. ONVIF uses motion, zones and sensitivity configured on the camera. Server settings are retained for RTSP analysis; pre-roll, tail and retention apply in both modes.',onvif_offline:'Video available · ONVIF events unavailable',rtsp_fallback:'RTSP — fallback analysis',onvif_connecting:'ONVIF — connecting'});
Object.assign(dict.bg,{videoCopy:'H.264 · Директно',videoTranscode:'Преобразуване на видео'});
Object.assign(dict.en,{videoCopy:'H.264 · Direct',videoTranscode:'Video transcoding'});
let dragCameraId=null,orderSaving=false;
let me=null,users=[],noticeRelease=null,authCheckGeneration=0;
let lang=localStorage.getItem('dm-lang')||'en',csrf='',configured=false,cameras=[],clips=[],photos=[],photoCursor=null,photoRequest=0,selectedPhoto=-1,editing=null,mode='live',selectedClip=null,zonePlayer=null;
const $=id=>document.getElementById(id),players=new Map();
const t=k=>dict[lang][k]||k;
function node(tag,cls,text){const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=text;return el;}
function language(value){lang=value;localStorage.setItem('dm-lang',lang);document.documentElement.lang=lang;document.querySelectorAll('[data-t]').forEach(el=>el.textContent=t(el.dataset.t));document.querySelectorAll('[data-lang]').forEach(el=>el.classList.toggle('selected',el.dataset.lang===lang));$('authTitle').textContent=t(configured?'loginTitle':'setupTitle');$('viewTitle').textContent=t(mode==='photos'?'photos':mode==='live'?'live':'playback');renderCameraList();if($('playCamera').options.length)$('playCamera').options[0].textContent=t('allCameras');if(mode==='playback')renderClips();if(mode==='photos')renderPhotos();for(const option of $('photoCamera').options){if(option.dataset.t)option.textContent=t(option.dataset.t);}updateTileLabels();renderUpdateNotice();renderUpdateProgress();syncCameraPositions();}
async function api(path,body,signal){const response=await fetch(path,{signal,method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:body===undefined?undefined:JSON.stringify(body)});if(!response.ok){if(response.status===401&&path!='/api/login')showAuth();const detail=await response.json().catch(()=>({}));throw new Error(`${detail.error||t('error')} (${response.status})`);}return response.json();}
function toast(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,6000);}
function showAuth(){authCheckGeneration++;clearCameraDrag();noticeRelease=null;renderUpdateNotice();players.forEach(p=>p.destroy());players.clear();if(zonePlayer)zonePlayer.destroy();zonePlayer=null;document.querySelectorAll('dialog[open]').forEach(d=>d.close());$('playPlayer').pause();$('playPlayer').removeAttribute('src');playbackRequest++;$('playCameraTiles').replaceChildren();$('grid').replaceChildren();me=null;$('cameraList').replaceChildren();cameras=[];clips=[];photos=[];photoCursor=null;photoRequest++;$('photoCamera').value='dashboard';$('photoDashboard').replaceChildren();$('photoGallery').replaceChildren();$('photoFull').removeAttribute('src');csrf='';$('shell').hidden=true;$('auth').hidden=false;renderUpdateProgress();}
async function boot(){try{const state=await api('/api/state');configured=state.configured;emailRecovery=Boolean(state.email_recovery);$('forgotPassword').hidden=!configured;csrf=state.csrf||'';me=state.user||null;$('tokenLabel').hidden=true;$('setupHelp').hidden=configured;$('authPassword').minLength=configured?1:12;language(lang);if(state.authenticated){$('auth').hidden=true;$('shell').hidden=false;applyPermissions();resumeUpdate();checkAdminUpdates();await loadCameras(me.role!=='playback');if(me.role==='playback')switchMode('playback');}}catch(e){$('authError').textContent=e.message;}}
$('authForm').onsubmit=async e=>{e.preventDefault();const button=e.submitter;button.disabled=true;try{const result=await api(configured?'/api/login':'/api/setup',{username:$('authUsername').value,password:$('authPassword').value,token:$('setupToken').value});csrf=result.csrf;configured=true;$('authPassword').value='';$('setupToken').value='';$('authError').textContent='';await boot();}catch(e){$('authError').textContent=t('invalidLogin');}finally{button.disabled=false;}};
function attach(video,id,delay=0){
 let hls=null,retry=null,nativeTimer=null,closed=false;const url=`/live/${id}/live.m3u8`;
 async function connect(){
  if(closed)return;let segmentSize=2;
  try{const response=await fetch(url);if(!response.ok)throw new Error('not ready');const text=await response.text();const durations=[...text.matchAll(/#EXTINF:([\d.]+)/g)].map(m=>Number(m[1]));segmentSize=Math.max(2,...durations);const required=delay>0?delay+segmentSize:2*segmentSize;if(durations.reduce((a,b)=>a+b,0)<required){retry=setTimeout(connect,2000);return;}}
  catch(_){if(!closed)retry=setTimeout(connect,3000);return;}
  if(closed)return;
  const target=delay>0?delay:2*segmentSize,maxLatency=Math.max(target+45,target*2);
  if(window.Hls&&Hls.isSupported()){
   const latency=delay>0?{liveSyncDuration:delay,liveMaxLatencyDuration:maxLatency}:{liveSyncDurationCount:2,liveMaxLatencyDurationCount:8};
   hls=new Hls({maxBufferLength:Math.max(30,delay+30),maxMaxBufferLength:Math.max(60,delay+60),backBufferLength:15,...latency,maxLiveSyncPlaybackRate:1,lowLatencyMode:false,enableWorker:true});hls.loadSource(url);hls.attachMedia(video);hls.on(Hls.Events.MANIFEST_PARSED,()=>video.play().catch(()=>{}));hls.on(Hls.Events.ERROR,(_,data)=>{if(data.fatal){hls.destroy();hls=null;retry=setTimeout(connect,5000);}});
  }else if(video.canPlayType('application/vnd.apple.mpegurl')){
   video.src=url;let positioned=false;video.play().catch(()=>{});nativeTimer=setInterval(()=>{if(!video.seekable.length)return;const end=video.seekable.end(video.seekable.length-1),start=video.seekable.start(0);if(!positioned&&end-start>=target){video.currentTime=Math.max(start,end-target);positioned=true;}else if(positioned&&end-video.currentTime>maxLatency)video.currentTime=Math.max(start,end-target);},1000);
  }else toast('HLS / MediaSource is not supported by this browser.');
 }
 video.autoplay=false;video.muted=true;connect();return{destroy(){closed=true;clearTimeout(retry);clearInterval(nativeTimer);if(hls)hls.destroy();video.pause();video.removeAttribute('src');video.load();}};
}
async function loadCameras(rebuild=false){const next=await api('/api/cameras');if(orderSaving||dragCameraId)return;const delayChanged=next.some(c=>c.live_delay!==(cameras.find(previous=>previous.id===c.id)?.live_delay??0));cameras=next;renderCameraList();if(rebuild||(delayChanged&&mode==='live'))renderGrid();else{updateTileLabels();syncCameraPositions();}const previous=$('playCamera').value;$('playCamera').replaceChildren(new Option(t('allCameras'),''));cameras.forEach(c=>$('playCamera').add(new Option(c.name,c.id)));$('playCamera').value=cameras.some(c=>c.id===previous)?previous:'';if(mode==='playback'&&syncPlaybackCameraTiles())loadClips().catch(e=>toast(e.message));const photoSelect=$('photoCamera'),photoPrevious=photoSelect.value;
 photoSelect.options.length=2;
 cameras.forEach(c=>photoSelect.add(new Option(c.name,c.id)));
 photoSelect.value=[...photoSelect.options].some(option=>option.value===photoPrevious)?photoPrevious:'dashboard';
 if(mode==='photos'&&photoSelect.value!==photoPrevious)loadPhotos().catch(e=>toast(e.message));}
function renderCameraList(){$('cameraList').replaceChildren();cameras.forEach(c=>{const row=node('div','cameraRow');row.dataset.id=c.id;if(me?.role==='admin'){row.append(cameraDragHandle(c.id));cameraDropTarget(row,c.id);}row.append(node('b','',c.name),node('small',c.status==='recording'?'recording':'',`${c.host?c.host+' · ':''}${t(c.status)}${detectionLabel(c)?' · '+detectionLabel(c):''}${videoLabel(c)?' · '+videoLabel(c):''}`));row.onclick=()=>{if(me?.role==='admin')editCamera(c);else if(me?.role==='playback'){$('playCamera').value=c.id;loadClips().catch(e=>toast(e.message));}};$('cameraList').append(row);});$('summary').textContent=`${cameras.length} ${t('cameraCount')}`;}
function renderGrid(){players.forEach(p=>p.destroy());players.clear();$('grid').replaceChildren();$('empty').hidden=cameras.length>0;for(const c of cameras){const tile=node('article','tile');tile.dataset.id=c.id;tile.setAttribute('role','listitem');if(me?.role==='admin')cameraDropTarget(tile,c.id);const video=node('video');video.autoplay=true;video.playsInline=true;video.controls=true;video.muted=true;video.ondblclick=()=>tile.classList.toggle('expanded');const status=node('span','liveStatus',t(c.status));const bar=node('div','tilebar');if(me?.role==='admin')bar.append(cameraDragHandle(c.id));bar.append(node('div','tileName',c.name));const buttons=node('div');const sound=node('button','sound',t('soundOn'));sound.onclick=()=>{video.muted=!video.muted;sound.textContent=t(video.muted?'soundOn':'soundOff');if(!video.muted)video.play().catch(()=>{});};const expand=node('button','', '⛶');expand.title=t('expand');expand.onclick=()=>tile.classList.toggle('expanded');const settings=node('button','','⚙');settings.title=t('settings');settings.onclick=()=>editCamera(c);buttons.append(sound,expand);if(me?.role==='admin')buttons.append(settings);bar.append(buttons);tile.append(video,status,bar);$('grid').append(tile);if(c.enabled)players.set(c.id,attach(video,c.id,c.live_delay));}syncCameraPositions();}
function updateTileLabels(){document.querySelectorAll('.tile').forEach(tile=>{const c=cameras.find(c=>c.id===tile.dataset.id);if(c){tile.querySelector('.liveStatus').textContent=t(c.enabled&&tile.querySelector('video').readyState<2&&c.status!=='offline'?'buffering':c.status)+(detectionLabel(c)?' · '+detectionLabel(c):'')+(videoLabel(c)?' · '+videoLabel(c):'');tile.querySelector('.liveStatus').classList.toggle('recording',c.status==='recording');tile.querySelector('.sound').textContent=t(tile.querySelector('video').muted?'soundOn':'soundOff');}});}
function switchMode(value){if(value==='live'&&me?.role==='playback')value='playback';mode=value;for(const [name,view,tab]of [['live','liveView','liveTab'],['playback','playView','playTab'],['photos','photosView','photosTab']]){$(view).hidden=mode!==name;$(tab).classList.toggle('active',mode===name);}$('viewTitle').textContent=t(mode==='photos'?'photos':mode==='live'?'live':'playback');if(mode!=='playback'){playbackRequest++;$('playCameraTiles').replaceChildren();}if(mode!=='live'){players.forEach(p=>p.destroy());players.clear();$('playPlayer').pause();if(mode==='playback')loadClips().catch(e=>toast(e.message));else loadPhotos().catch(e=>toast(e.message));}else{$('playPlayer').pause();renderGrid();}}
$('liveTab').onclick=()=>switchMode('live');$('playTab').onclick=()=>switchMode('playback');$('photosTab').onclick=()=>switchMode('photos');$('layout').onchange=()=>{$('grid').style.gridTemplateColumns=`repeat(${$('layout').value}, minmax(0,1fr))`;};
Object.assign(dict.en,{
 streamSource:'Camera manufacturer or stream type',streamDahua:'Dahua / compatible',streamCustom:'Custom (full RTSP URL)',
 rtspURL:'RTSP URL',rtspURLHelp:'Include the username and password if required. Encode special characters in the credentials.',
 keepRTSPURL:'Leave blank to keep the saved URL'
});
Object.assign(dict.bg,{
 streamSource:'Производител или вид на потока',streamDahua:'Dahua / съвместими',streamCustom:'Ръчно (пълен RTSP URL)',
 rtspURL:'RTSP адрес',rtspURLHelp:'Включи потребител и парола, ако са нужни. Кодирай специалните знаци в данните за вход.',
 keepRTSPURL:'Остави празно, за да запазиш текущия адрес'
});
const form=$('cameraForm'),field=name=>form.elements.namedItem(name);
function streamSourceChanged(){
 const source=field('stream_source').value;
 for(const label of form.querySelectorAll('[data-stream-fields]')){
  const active=(source==='custom'?label.dataset.streamFields==='custom':label.dataset.streamFields==='preset')
   && (source!=='tp_link'||label.id!=='streamChannel');
  label.hidden=!active;
  label.querySelector('input,select').disabled=!active;
 }
 field('rtsp_url').required=source==='custom'&&!editing?.has_rtsp_url;
 field('password').required=source!=='custom'&&!editing;
}
field('stream_source').onchange=streamSourceChanged;

function editCamera(c=null){if(me?.role!=='admin')return;editing=c;form.reset();$('formError').textContent='';for(const [key,value]of Object.entries(c||{})){const el=field(key);if(el&&!['password','onvif_password','rtsp_url'].includes(key)){if(el.type==='checkbox')el.checked=value;else el.value=value;}}field('username').value=c?.username||'admin';field('password').value='';field('password').placeholder=c?t('leavePassword'):'';field('stream_source').value=c?.has_rtsp_url?'custom':(c?.rtsp_preset||'dahua');field('rtsp_url').placeholder=c?.has_rtsp_url?t('keepRTSPURL'):'rtsp://user:password@192.0.2.20:554/stream1';streamSourceChanged();field('onvif_password').value='';field('onvif_password').placeholder=c?.has_onvif_password?t('leavePassword'):'';motionMethodChanged();const z=c?.zone||[0,0,1,1];['zx','zy','zw','zh'].forEach((k,i)=>field(k).value=Math.round(z[i]*100));$('sensValue').value=field('sensitivity').value;$('deleteCamera').hidden=!c;$('cameraDialog').showModal();drawZone();if(zonePlayer)zonePlayer.destroy();zonePlayer=c?.enabled?attach($('zoneVideo'),c.id):null;}
$('addCamera').onclick=()=>editCamera();$('emptyAdd').onclick=()=>editCamera();$('closeCamera').onclick=()=>$('cameraDialog').close();$('cameraDialog').addEventListener('close',()=>{field('rtsp_url').value='';if(zonePlayer)zonePlayer.destroy();zonePlayer=null;});
field('sensitivity').oninput=()=>{$('sensValue').value=field('sensitivity').value;};
form.onsubmit=async e=>{e.preventDefault();const value={};for(const el of form.elements){if(!el.name||['stream_source','zx','zy','zw','zh'].includes(el.name)||(el.disabled&&el.closest('[data-stream-fields]')))continue;value[el.name]=el.type==='checkbox'?el.checked:(el.type==='number'||el.type==='range'?Number(el.value):el.value);}const source=field('stream_source').value;
 if(source!=='custom'){value.rtsp_url='';value.rtsp_preset=source;}
 else if(!value.rtsp_url.trim()&&editing?.has_rtsp_url)delete value.rtsp_url;
 else value.rtsp_url=value.rtsp_url.trim();
 value.zone=['zx','zy','zw','zh'].map(k=>Number(field(k).value)/100);if(editing){value.id=editing.id;if(!value.password)delete value.password;if(!value.onvif_password)delete value.onvif_password;}const[x,y,w,h]=value.zone;if(x+w>1.001||y+h>1.001){$('formError').textContent=t('zoneError');return;}e.submitter.disabled=true;try{await api('/api/cameras',value);$('cameraDialog').close();await loadCameras(mode==='live');toast(t('saved'));}catch(e){$('formError').textContent=e.message;}finally{e.submitter.disabled=false;}};
$('deleteCamera').onclick=async()=>{if(editing&&confirm(t('deleteConfirm'))){try{await api(`/api/cameras/${editing.id}/delete`,{});$('cameraDialog').close();await loadCameras(mode==='live');}catch(e){$('formError').textContent=e.message;}}};
const canvas=$('zoneCanvas'),ctx=canvas.getContext('2d');let drag=null;
function drawZone(){const[x,y,w,h]=['zx','zy','zw','zh'].map(k=>Number(field(k).value)/100);ctx.clearRect(0,0,640,360);ctx.fillStyle='#32d2cc33';ctx.fillRect(x*640,y*360,w*640,h*360);ctx.strokeStyle='#54eeea';ctx.lineWidth=3;ctx.strokeRect(x*640,y*360,w*640,h*360);}
function point(e){const r=canvas.getBoundingClientRect();return[Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))];}
canvas.onpointerdown=e=>{drag=point(e);canvas.setPointerCapture(e.pointerId);};canvas.onpointermove=e=>{if(!drag)return;const p=point(e),v=[Math.min(p[0],drag[0]),Math.min(p[1],drag[1]),Math.abs(p[0]-drag[0]),Math.abs(p[1]-drag[1])];['zx','zy','zw','zh'].forEach((k,i)=>field(k).value=Math.round(v[i]*100));drawZone();};canvas.onpointerup=()=>{drag=null;['zw','zh'].forEach(k=>field(k).value=Math.max(2,Number(field(k).value)));drawZone();};['zx','zy','zw','zh'].forEach(k=>field(k).oninput=drawZone);$('resetZone').onclick=()=>{['zx','zy','zw','zh'].forEach((k,i)=>field(k).value=i<2?0:100);drawZone();};
function dateBounds(){const start=new Date($('playDate').value+'T00:00:00');const end=new Date(start);end.setDate(end.getDate()+1);return[start.getTime()/1000,end.getTime()/1000];}
let playbackRequest=0;
function syncPlaybackCameraTiles(){
 const grid=$('playCameraTiles'),selected=$('playCamera').value;
 const existing=new Map([...grid.children].map(tile=>[tile.dataset.camera,tile]));
 const tiles=cameras.map(camera=>{
  const tile=existing.get(camera.id)||node('button','camera-preview-tile');
  if(!tile.dataset.camera){
   tile.type='button';
   tile.dataset.camera=camera.id;
   const preview=node('span','camera-preview-frame','▣');
   preview.setAttribute('aria-hidden','true');
   tile.append(preview,node('span','camera-preview-name'));
   tile.onclick=()=>{
    $('playCamera').value=camera.id;
    $('playCamera').onchange();
   };
  }
  tile.lastElementChild.textContent=camera.name;
  tile.setAttribute('aria-pressed',String(camera.id===selected));
  return tile;
 });
 const changed=tiles.length!==grid.children.length||tiles.some((tile,i)=>tile!==grid.children[i]);
 if(changed)grid.replaceChildren(...tiles);
 grid.hidden=!tiles.length;
 return changed;
}
async function loadClips(){
 const request=++playbackRequest;
 syncPlaybackCameraTiles();
 const [start,end]=dateBounds();
 if(!Number.isFinite(start))return;
 const query=new URLSearchParams({from:start,to:end,previews:'1'});
 if($('playCamera').value)query.set('camera',$('playCamera').value);
 const result=await api('/api/recordings?'+query);
 if(request!==playbackRequest)return;
 for(const tile of $('playCameraTiles').children){
  const clip=result.previews[tile.dataset.camera]||'';
  if(clip===(tile.dataset.clip||''))continue;
  tile.dataset.clip=clip;
  const preview=tile.firstElementChild;
  preview.textContent='▣';
  if(!clip)continue;
  const video=node('video');
  video.muted=true;
  video.playsInline=true;
  video.preload='metadata';
  video.src=`/recordings/${clip}.mp4#t=0.1`;
  video.addEventListener('loadeddata',()=>video.classList.add('ready'),{once:true});
  video.addEventListener('error',()=>video.remove(),{once:true});
  preview.append(video);
 }
 if(selectedClip&&!result.clips.some(c=>c.id===selectedClip)){
  selectedClip=null;
  const player=$('playPlayer');
  player.pause();
  player.onloadedmetadata=null;
  player.onerror=null;
  player.removeAttribute('src');
  player.load();
  $('clipInfo').textContent='';
  $('download').hidden=true;
 }
 clips=result.clips;
 renderClips();
}
function formatTime(epoch){return new Date(epoch*1000).toLocaleTimeString(lang==='bg'?'bg-BG':'en-GB',{hour12:false});}
function renderClips(){$('clipList').replaceChildren();$('timeline').replaceChildren();$('clipCount').textContent=`${clips.length} ${t('clips')}`;if(!clips.length)$('clipList').append(node('p','muted',t('noClips')));const[start,end]=dateBounds();for(const c of clips){const el=node('button','clip'+(selectedClip===c.id?' selected':''));el.append(node('strong','',`${formatTime(c.start)} · ${Math.round(c.duration)} ${t('seconds')}`),node('small','',`${c.camera_name} · ${(c.bytes/1048576).toFixed(1)} MB`));el.onclick=()=>playClip(c,0);$('clipList').append(el);const mark=node('button',selectedClip===c.id?'selected':'');const left=Math.max(start,c.start),right=Math.min(end,c.start+c.duration);mark.style.left=`${100*(left-start)/(end-start)}%`;mark.style.width=`${Math.max(.12,100*(right-left)/(end-start))}%`;mark.title=`${c.camera_name} · ${formatTime(c.start)} · ${Math.round(c.duration)} ${t('seconds')}`;mark.onclick=e=>{const bounds=mark.getBoundingClientRect();playClip(c,Math.max(0,left-c.start)+(right-left)*(e.clientX-bounds.left)/bounds.width);};$('timeline').append(mark);}}
function playClip(c,offset=0){selectedClip=c.id;const player=$('playPlayer');player.src=`/recordings/${c.id}.mp4`;player.onloadedmetadata=()=>{player.currentTime=Math.min(offset,Math.max(0,player.duration-.1));player.play().catch(()=>{});};player.onerror=()=>toast(t('playError'));$('clipInfo').textContent=`${c.camera_name} · ${new Date(c.start*1000).toLocaleString(lang==='bg'?'bg-BG':'en-GB')} · ${t('duration')}: ${Math.round(c.duration)} ${t('seconds')}`;$('download').hidden=false;$('download').href=`/recordings/${c.id}.mp4?download=1`;renderClips();}
$('refreshClips').onclick=()=>loadClips().catch(e=>toast(e.message));$('playCamera').onchange=$('refreshClips').onclick;$('playDate').onchange=$('refreshClips').onclick;
$('lock').onclick=async()=>{try{await api('/api/logout',{});showAuth();await boot();}catch(e){toast(e.message);}};
$('changePassword').onclick=()=>{$('passwordForm').reset();$('passwordError').textContent='';$('passwordDialog').showModal();};$('cancelPassword').onclick=()=>$('passwordDialog').close();$('passwordForm').onsubmit=async e=>{e.preventDefault();const f=e.target;if(f.elements.password.value!==f.elements.confirm.value){$('passwordError').textContent=t('passwordMismatch');return;}try{const result=await api('/api/password',{old:f.elements.old.value,password:f.elements.password.value});csrf=result.csrf;$('passwordDialog').close();toast(t('passwordChanged'));}catch(e){$('passwordError').textContent=e.message;}};
document.querySelectorAll('[data-lang]').forEach(el=>el.onclick=()=>language(el.dataset.lang));document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.tile.expanded').forEach(el=>el.classList.remove('expanded'));});
const today=new Date();$('playDate').value=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;$('photoDate').value=$('playDate').value;setInterval(()=>$('clock').textContent=new Date().toLocaleString(lang==='bg'?'bg-BG':'en-GB'),1000);setInterval(()=>{if(!$('shell').hidden)loadCameras(false).catch(()=>{});},5000);setInterval(()=>{if(!$('shell').hidden&&mode==='playback')loadClips().catch(()=>{});},15000);boot();
function applyPermissions(){const admin=me?.role==='admin';$('addCamera').hidden=!admin;$('emptyAdd').hidden=!admin;$('manageUsers').hidden=!admin;$('manageSMTP').hidden=!admin;$('manageUpdates').hidden=!admin;$('cameraOrderHint').hidden=!admin;renderUpdateNotice();$('liveTab').hidden=me?.role==='playback';$('signedInAs').textContent=me?me.username:'';}
const userForm=$('userForm'),uf=name=>userForm.elements.namedItem(name);
function renderUsers(){$('userList').replaceChildren();users.forEach(u=>{const button=node('button','clip',`${u.username} · ${t({admin:'roleAdmin',full:'roleFull',limited:'roleLimited',playback:'rolePlayback'}[u.role])}${u.enabled?'':' · ⏸'}`);button.onclick=()=>editUser(u);$('userList').append(button);});}
function editUser(user=null){userForm.reset();uf('id').value=user?.id||'';uf('username').value=user?.username||'';uf('password').required=!user;uf('password').placeholder=user?t('leavePassword'):'';uf('role').value=user?.role||'limited';uf('enabled').checked=user?.enabled??true;uf('all_cameras').checked=user?.all_cameras||false;$('userError').textContent='';$('deleteUser').hidden=!user||user.id===me.id;const ids=new Set([...cameras.map(c=>c.id),...(user?.cameras||[])]);$('userCameras').replaceChildren();for(const id of ids){const label=node('label','check');const box=node('input');box.type='checkbox';box.value=id;box.checked=user?.cameras?.includes(id)||false;label.append(box,node('span','',cameras.find(c=>c.id===id)?.name||id));$('userCameras').append(label);}roleChanged();}
function roleChanged(){const role=uf('role').value;if(role==='admin'||role==='full')uf('all_cameras').checked=true;if(role==='limited')uf('all_cameras').checked=false;uf('all_cameras').disabled=role!=='playback';$('userCameras').hidden=uf('all_cameras').checked;}
uf('role').onchange=roleChanged;uf('all_cameras').onchange=roleChanged;
$('manageUsers').onclick=async()=>{try{users=await api('/api/users');renderUsers();editUser();$('usersDialog').showModal();}catch(e){toast(e.message);}};$('closeUsers').onclick=()=>$('usersDialog').close();$('newUser').onclick=()=>editUser();
userForm.onsubmit=async e=>{e.preventDefault();const value={username:uf('username').value,role:uf('role').value,enabled:uf('enabled').checked,all_cameras:uf('all_cameras').checked,cameras:[...$('userCameras').querySelectorAll('input:checked')].map(c=>c.value)};if(uf('id').value)value.id=uf('id').value;if(uf('password').value)value.password=uf('password').value;e.submitter.disabled=true;try{const result=await api('/api/users',value);if(result.csrf){csrf=result.csrf;me=result.user;applyPermissions();if(me.role!=='admin'){$('usersDialog').close();await loadCameras(true);return;}}users=await api('/api/users');renderUsers();editUser(result.user);toast(t('userSaved'));}catch(e){$('userError').textContent=e.message;}finally{e.submitter.disabled=false;}};
$('deleteUser').onclick=async()=>{if(!uf('id').value||!confirm(t('deleteUserConfirm')))return;try{await api(`/api/users/${uf('id').value}/delete`,{});users=await api('/api/users');renderUsers();editUser();}catch(e){$('userError').textContent=e.message;}};

function detectionLabel(c){return c.detection_mode==='onvif'?'ONVIF':c.detection_mode==='rtsp_fallback'?t('rtsp_fallback'):c.detection_mode==='onvif_connecting'?t('onvif_connecting'):c.detection_mode==='rtsp'?'RTSP':'';}
function motionMethodChanged(){const on=field('motion_source').value==='onvif',reuse=field('onvif_use_camera_credentials').checked;for(const name of ['onvif_port','onvif_soap','onvif_fallback','onvif_use_camera_credentials'])field(name).disabled=!on;for(const name of ['onvif_username','onvif_password'])field(name).disabled=!on||reuse;field('onvif_username').required=on&&!reuse;field('onvif_password').required=on&&!reuse&&!editing?.has_onvif_password;field('sensitivity').disabled=on;['zx','zy','zw','zh'].forEach(k=>field(k).disabled=on);$('zoneCanvas').style.pointerEvents=on?'none':'auto';$('zoneCanvas').style.opacity=on?'.4':'1';$('resetZone').disabled=on;}
field('motion_source').onchange=motionMethodChanged;field('onvif_use_camera_credentials').onchange=motionMethodChanged;

function videoLabel(c){if(c.video_mode==='copy'){const v=c.source_video||{};return t('videoCopy')+(v.width&&v.height?` · ${v.width}×${v.height}`:'');}return c.video_mode==='transcode'?t('videoTranscode'):'';}
Object.assign(dict.en,{updates:'Updates',checkUpdates:'Check for updates',installUpdate:'Install update',updateHelp:'Install official stable GitHub releases. Cameras, accounts and recordings are preserved. Recording pauses during restart; sign in again afterwards. Configuration is backed up before installation.',updateConfirm:'Install this release? Recording will pause during restart. A failed health check restores the previous version and configuration.',updaterMissing:'Host updater is unavailable. See README: Updates.',githubUnavailable:'GitHub is unavailable. Try again later.',updateCurrent:'Installed',updateLatest:'Latest',upToDate:'Up to date.',updateIdle:'Ready',queued:'Queued',building:'Building image',backing_up:'Backing up configuration',installing:'Installing',checking:'Checking health',rolling_back:'Restoring previous version',succeeded:'Update completed',rolled_back:'Update failed; previous version restored',failed:'Update failed; see host updater log'});
Object.assign(dict.bg,{"updates":"Обновяване","checkUpdates":"Провери за обновявания","installUpdate":"Инсталирай версията","updateHelp":"Камерите, потребителите и записите се запазват. Записването спира при рестарта; след това влез отново. Конфигурацията се архивира преди обновяване.","updateConfirm":"Да инсталирам тази версия? Записването ще спре при рестарта. При неуспешна проверка се възстановяват предишните версия и конфигурация.","updaterMissing":"Хост услугата за обновяване е недостъпна. Виж README: Updates.","githubUnavailable":"Няма връзка с GitHub. Опитай по-късно.","updateCurrent":"Инсталирана","updateLatest":"Последна","upToDate":"Версията е актуална.","updateIdle":"В готовност","queued":"В опашката","building":"Подготовка на образа","backing_up":"Архивиране","installing":"Инсталиране","checking":"Проверка","rolling_back":"Възстановяване","succeeded":"Обновяването приключи","rolled_back":"Предишната версия е възстановена","failed":"Неуспешно обновяване; провери лога"});
Object.assign(dict.en,{
 updateSubmitting:'Requesting update…',
 updateReconnecting:'Waiting for the server to respond. This page will retry automatically.',
 updateSignIn:'Sign in again to see the update result.'
});
Object.assign(dict.bg,{
 updateSubmitting:'Изпращане на заявката за обновяване…',
 updateReconnecting:'Изчакване на сървъра. Страницата ще опита отново автоматично.',
 updateSignIn:'Влез отново, за да видиш резултата от обновяването.'
});

const updateStages=['queued','building','backing_up','installing','checking'];
const updateResults=['succeeded','rolled_back','failed'];
let updateInfo=null, updateRequest=null, updateStage=null, updateMessage=null, updateError=null;
let updateRefreshing=false, updateSubmitting=false;

function renderUpdateProgress(){
 const progress=$('updateProgress');
 const stage=updateStages.indexOf(updateStage);
 progress.hidden=!updateRequest&&updateStage!=='succeeded';
 if(!updateMessage&&(stage>=0||updateStage==='succeeded')){
  progress.value=updateStage==='succeeded'?updateStages.length:stage;
 }else{
  progress.removeAttribute('value');
 }
 const status=updateMessage?t(updateMessage):updateError||(updateStage?t(updateStage):'');
 if($('updateStatus').textContent!==status)$('updateStatus').textContent=status;
 $('authUpdateStatus').hidden=!(updateRequest&&!me);
 $('authUpdateStatus').textContent=updateRequest&&!me?t('updateSignIn'):'';
 $('checkUpdates').disabled=updateRefreshing||updateSubmitting||!!updateRequest;
 $('installUpdate').disabled=updateRefreshing||updateSubmitting||!!updateRequest||
  !updateInfo?.updater_available||!updateInfo?.update_available;
}

async function refreshUpdates(check=false){
 if(updateRefreshing||updateSubmitting||me?.role!=='admin')return;
 const user=me;
 if(check)updateError=null;
 updateRefreshing=true;
 renderUpdateProgress();
 try{
  const info=await api('/api/updates'+(check?'?check=1':''),undefined,AbortSignal.timeout(25000));
  if(me!==user)return;
  updateInfo=info;
  const r=info.latest;
  $('updateVersions').textContent=`${t('updateCurrent')}: ${info.current}${info.current_revision?' ('+info.current_revision.slice(0,7)+')':''} | ${t('updateLatest')}: ${r?.tag||'--'}${r?.revision?' ('+r.revision.slice(0,7)+')':''}`;
  $('updateNotes').textContent=r?.notes||'';
  const {state,tag,finished_at:finishedAt}=info.job||{};
  updateMessage=null;
  if(info.updater_available&&(updateStages.includes(state)||state==='rolling_back')){
   updateError=null;
   updateRequest??={tag,previousFinish:null};
   updateStage=state;
  }else if(updateResults.includes(state)&&
           (!updateRequest||(tag===updateRequest.tag&&finishedAt!==updateRequest.previousFinish))){
   updateRequest=null;
   updateStage=state;
  }else if(!info.updater_available){
   updateMessage='updaterMissing';
  }else if(!updateRequest){
   updateStage=info.error?'githubUnavailable':info.update_available?'updateIdle':'upToDate';
  }
 }catch(e){
  if(updateRequest){
   updateMessage='updateReconnecting';
  }else if(me===user){
   updateStage=null;
   updateMessage='error';
  }
 }finally{
  updateRefreshing=false;
  renderUpdateProgress();
 }
}

function resumeUpdate(){
 if(me?.role!=='admin'){
  updateRequest=null;
  updateStage=null;
  updateMessage=null;
  updateInfo=null;
  updateError=null;
 }else if(updateRequest){
  if(!$('updatesDialog').open)$('updatesDialog').showModal();
  refreshUpdates();
 }
 renderUpdateProgress();
}

$('manageUpdates').onclick=()=>{
 if(me?.role!=='admin')return;
 $('updatesDialog').showModal();
 refreshUpdates(!updateRequest);
};
$('closeUpdates').onclick=()=>$('updatesDialog').close();
$('checkUpdates').onclick=()=>refreshUpdates(true);
setInterval(()=>{
 if(updateRequest||$('updatesDialog').open)refreshUpdates();
},2000);

$('installUpdate').onclick=async()=>{
 if(!updateInfo?.latest||updateSubmitting||updateRefreshing||updateRequest||!confirm(t('updateConfirm')))return;
 const {tag,revision}=updateInfo.latest;
 updateSubmitting=true;
 updateError=null;
 updateRequest={tag,previousFinish:updateInfo.job?.finished_at};
 updateStage=null;
 updateMessage='updateSubmitting';
 renderUpdateProgress();
 try{
  await api('/api/updates',{tag,revision});
  updateStage='queued';
  updateMessage=null;
 }catch(e){
  updateRequest=null;
  updateMessage=null;
  updateStage=null;
  updateError=e.message;
 }finally{
  updateSubmitting=false;
  renderUpdateProgress();
  if(updateRequest)refreshUpdates();
 }
};

function setSidebar(collapsed){$('shell').classList.toggle('sidebar-collapsed',collapsed);$('sidebar').inert=collapsed;$('toggleSidebar').textContent=collapsed?'>>>':'<<<';$('toggleSidebar').setAttribute('aria-expanded',String(!collapsed));$('toggleSidebar').setAttribute('aria-label',collapsed?'Show sidebar':'Hide sidebar');localStorage.setItem('nvr-sidebar-collapsed',collapsed?'1':'0');}
$('toggleSidebar').onclick=()=>setSidebar(!$('shell').classList.contains('sidebar-collapsed'));
setSidebar(localStorage.getItem('nvr-sidebar-collapsed')==='1');

Object.assign(dict.en,{updateNoticeNew:'A new version is available',updateNoticeChanged:'An updated build of this version is available',updateNoticeManual:'Installation starts only when you confirm it.',reviewUpdate:'Review update',dismissUpdateNotice:'Dismiss'});
async function checkAdminUpdates(){const generation=++authCheckGeneration,userId=me?.id;noticeRelease=null;renderUpdateNotice();if(me?.role!=='admin')return;try{const info=await api('/api/updates?check=1');if(generation!==authCheckGeneration||me?.id!==userId||me?.role!=='admin'||$('shell').hidden)return;if(info.update_available&&info.latest){noticeRelease={...info.latest,sameVersion:info.latest.tag.replace(/^v/,'')===info.current.replace(/^v/,'')};renderUpdateNotice();}}catch(_){/* A failed optional check must not interrupt monitoring or login. */}}
Object.assign(dict.bg,{"updateNoticeNew":"Има нова версия","updateNoticeChanged":"Има обновен код на текущата версия","updateNoticeManual":"Инсталацията започва само след твое потвърждение.","reviewUpdate":"Преглед на обновяването","dismissUpdateNotice":"Скрий"});
function renderUpdateNotice(){const show=me?.role==='admin'&&noticeRelease&&!$('shell').hidden;$('updateNotice').hidden=!show;if(show)$('updateNoticeText').textContent=`${t(noticeRelease.sameVersion?'updateNoticeChanged':'updateNoticeNew')}: ${noticeRelease.tag}${noticeRelease.revision?' ('+noticeRelease.revision.slice(0,7)+')':''}. ${t('updateNoticeManual')}`;}
$('reviewUpdate').onclick=()=>$('manageUpdates').click();$('dismissUpdateNotice').onclick=()=>{noticeRelease=null;renderUpdateNotice();};

Object.assign(dict.en,{photos:'Motion photos',photoSettings:'Motion photos',photoEnabled:'Save photos during motion',photoInterval:'Photo interval (seconds)',photoDays:'Keep photos for (days)',photoMB:'Photo storage limit per camera (MB)',photoSettingsHelp:'Independent of MP4 recording. Uses the motion detection method selected below. ONVIF zones are configured on the camera. Photos and thumbnails have separate retention limits from video; existing cameras start with photos disabled.',photosHelp:'Photos are captured only during detected motion. Times and date filters use your browser time zone.',noPhotos:'No photos for this camera and date.',morePhotos:'Load more photos',photoItems:'photos',previousPhoto:'Previous',nextPhoto:'Next',downloadPhoto:'Download JPEG'});
function photoURL(p,thumb=false){return `/recordings/timelapse/${p.camera_id}/${p.day}/${p.id}.jpg${thumb?'?thumb=1':''}`;}
Object.assign(dict.bg,{"photos":"Снимки при движение","photoSettings":"Снимки при движение","photoEnabled":"Запазвай снимки при движение","photoInterval":"Интервал между снимките (сек.)","photoDays":"Пази снимки до (дни)","photoMB":"Лимит за снимки на камера (MB)","photoSettingsHelp":"Независимо от MP4 записването. Използва избраното по-долу засичане на движение. При ONVIF зоната се задава в камерата. Снимките имат отделни лимити; за съществуващите камери функцията първоначално е изключена.","photosHelp":"Снимките се правят само при засечено движение. Часовете и филтърът по дата са по часовата зона на браузъра.","noPhotos":"Няма снимки за тази камера и дата.","morePhotos":"Зареди още снимки","photoItems":"снимки","previousPhoto":"Предишна","nextPhoto":"Следваща","downloadPhoto":"Изтегли JPEG"});
Object.assign(dict.en,{photoDashboard:'Dashboard'});
Object.assign(dict.bg,{photoDashboard:'Табло'});

function renderPhotoDashboard(cameras){
 const tiles=cameras.map(camera=>{
  const tile=node('button','camera-preview-tile');
  tile.type='button';
  const frame=node('span','camera-preview-frame','▣');
  frame.setAttribute('aria-hidden','true');
  if(camera.preview){
   const image=node('img');
   image.alt='';
   image.loading='lazy';
   image.src=photoURL(camera.preview,true);
   image.addEventListener('error',()=>image.remove(),{once:true});
   frame.append(image);
  }
  tile.append(frame,node('span','camera-preview-name',camera.name));
  tile.onclick=()=>{
   const select=$('photoCamera');
   if(![...select.options].some(option=>option.value===camera.id))select.add(new Option(camera.name,camera.id));
   select.value=camera.id;
   select.onchange();
  };
  return tile;
 });
 $('photoDashboard').replaceChildren(...tiles);
}

async function loadPhotos(append=false){
 const generation=++photoRequest,selection=$('photoCamera').value,dashboard=selection==='dashboard';
 $('photoDashboard').hidden=!dashboard;
 $('photoGallery').hidden=dashboard;
 for(const id of ['photoDateFilter','photosHelp','photoCount'])$(id).hidden=dashboard;
 if(!append){
  photos=[];
  photoCursor=null;
  $('photoGallery').replaceChildren();
  $('photoCount').textContent='';
  $('morePhotos').hidden=true;
 }
 if(dashboard){
  const cameras=await api('/api/timelapse/dashboard');
  if(generation===photoRequest)renderPhotoDashboard(cameras);
  return;
 }
 const start=new Date($('photoDate').value+'T00:00:00'),end=new Date(start);
 end.setDate(end.getDate()+1);
 if(!Number.isFinite(start.getTime()))return;
 const query=new URLSearchParams({from:start.getTime()/1000,to:end.getTime()/1000,limit:100});
 if(selection)query.set('camera',selection);
 if(append&&photoCursor)query.set('before',photoCursor);
 const result=await api('/api/timelapse?'+query);
 if(generation!==photoRequest)return;
 photos=append?[...photos,...result.photos]:result.photos;
 photoCursor=result.next_cursor;
 renderPhotos();
}
function renderPhotos(){if($('photoCamera').value==='dashboard')return;$('photoGallery').replaceChildren();$('photoCount').textContent=`${photos.length} ${t('photoItems')}`;$('morePhotos').hidden=!photoCursor;if(!photos.length)$('photoGallery').append(node('p','muted',t('noPhotos')));photos.forEach((p,i)=>{const button=node('button','photo-card');const image=node('img');image.loading='lazy';image.decoding='async';image.src=photoURL(p,true);image.alt=`${p.camera_name} ${formatTime(p.start)}`;button.append(image,node('strong','',p.camera_name),node('span','muted',`${formatTime(p.start)} · ${(p.bytes/1024).toFixed(0)} KB`));button.onclick=()=>showPhoto(i);$('photoGallery').append(button);});}
function showPhoto(index){selectedPhoto=index;const p=photos[index];if(!p)return;$('photoFull').src=photoURL(p);$('photoFull').alt=p.camera_name;$('photoInfo').textContent=`${p.camera_name} · ${new Date(p.start*1000).toLocaleString(lang==='bg'?'bg-BG':'en-GB')}`;$('downloadPhoto').href=photoURL(p)+'?download=1';$('previousPhoto').disabled=index===0;$('nextPhoto').disabled=index===photos.length-1;if(!$('photoDialog').open)$('photoDialog').showModal();}
$('refreshPhotos').onclick=()=>loadPhotos().catch(e=>toast(e.message));$('photoCamera').onchange=$('refreshPhotos').onclick;$('photoDate').onchange=$('refreshPhotos').onclick;$('morePhotos').onclick=()=>loadPhotos(true).catch(e=>toast(e.message));$('closePhoto').onclick=()=>$('photoDialog').close();$('photoDialog').addEventListener('close',()=>$('photoFull').removeAttribute('src'));$('previousPhoto').onclick=()=>showPhoto(selectedPhoto-1);$('nextPhoto').onclick=()=>showPhoto(selectedPhoto+1);

Object.assign(dict.en,{cameraDrag:'Drag to reorder cameras. Alt + arrow keys also move a camera.',cameraOrderSaved:'Camera order saved.',cameraOrderHint:'Drag the dotted handle to reorder cameras. The order is shared by all users.'});
function cameraDragHandle(id){const handle=node('button','camera-drag','⋮⋮');handle.type='button';handle.draggable=true;handle.title=t('cameraDrag');handle.setAttribute('aria-label',t('cameraDrag'));handle.onclick=e=>e.stopPropagation();handle.ondragstart=e=>{if(orderSaving||me?.role!=='admin'){e.preventDefault();return;}dragCameraId=id;e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/x-nvr-camera',id);document.body.classList.add('camera-dragging');};handle.ondragend=clearCameraDrag;handle.onkeydown=e=>{if(e.altKey&&['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();const index=cameras.findIndex(c=>c.id===id),next=index+(['ArrowLeft','ArrowUp'].includes(e.key)?-1:1);if(cameras[next])moveCamera(id,cameras[next].id);}};return handle;}
Object.assign(dict.bg,{"cameraDrag":"Влачи за подреждане. Може и с Alt + стрелките.","cameraOrderSaved":"Подредбата на камерите е запазена.","cameraOrderHint":"Влачи дръжката с точки, за да подредиш камерите. Редът е общ за всички потребители."});
function clearCameraDrag(){dragCameraId=null;document.body.classList.remove('camera-dragging');document.querySelectorAll('.camera-drop-target').forEach(el=>el.classList.remove('camera-drop-target'));}
function cameraDropTarget(element,id){element.ondragover=e=>{if(dragCameraId&&dragCameraId!==id&&!orderSaving){e.preventDefault();e.dataTransfer.dropEffect='move';element.classList.add('camera-drop-target');}};element.ondragleave=e=>{if(!element.contains(e.relatedTarget))element.classList.remove('camera-drop-target');};element.ondrop=e=>{e.preventDefault();e.stopPropagation();const from=dragCameraId;clearCameraDrag();if(from)moveCamera(from,id);};}
function syncCameraPositions(){document.querySelectorAll('.camera-drag').forEach(h=>{h.title=t('cameraDrag');h.setAttribute('aria-label',t('cameraDrag'));});$('grid').setAttribute('role','list');const positions=new Map(cameras.map((c,i)=>[c.id,i]));document.querySelectorAll('#grid>.tile').forEach(tile=>{const position=positions.get(tile.dataset.id);if(position!==undefined){tile.style.order=position;tile.setAttribute('aria-posinset',position+1);tile.setAttribute('aria-setsize',cameras.length);}});}
async function moveCamera(from,to){if(orderSaving||me?.role!=='admin'||from===to)return;const ids=cameras.map(c=>c.id),source=ids.indexOf(from),target=ids.indexOf(to);if(source<0||target<0)return;ids.splice(source,1);ids.splice(target,0,from);const userId=me.id,generation=authCheckGeneration;orderSaving=true;try{await api('/api/cameras/order',{ids});if(me?.id!==userId||generation!==authCheckGeneration||$('shell').hidden)return;const byId=new Map(cameras.map(c=>[c.id,c]));cameras=ids.map(id=>byId.get(id));renderCameraList();syncCameraPositions();toast(t('cameraOrderSaved'));}catch(e){toast(e.message);}finally{orderSaving=false;if(me&&!$('shell').hidden)loadCameras(false).catch(()=>{});}}

Object.assign(dict.en,{
 close:'Close', forgotPassword:'Forgot password?', recoverySettings:'Password recovery', recoveryMethod:'Recovery method',
 emailLink:'Email link', recoveryKey:'Recovery key', sendResetLink:'Send reset link',
 resetPassword:'Set new password', resetRequested:'If recovery by email is available for this account, a link will be sent.',
 resetComplete:'Password changed. Sign in with your new password.',
 invalidRecovery:'This link or key is invalid or expired.',
 recoveryEmail:'Recovery email', sendVerification:'Send confirmation link', removeEmail:'Remove email',
 verifyRecovery:'Confirm recovery email', verifiedRecovery:'Recovery email confirmed.',
 recoveryEmailVerified:'Verified email', recoveryEmailPending:'Awaiting confirmation',
 recoveryEmailDisabled:'Email recovery is disabled. A recovery key can still be used.',
 verificationSent:'Confirmation link sent. Open it within 30 minutes.',
 generateRecoveryKey:'Generate new key', removeKey:'Remove key', recoveryKeyExists:'A recovery key is active.',
 recoveryKeyMissing:'No recovery key is active.',
 saveRecoveryKey:'Save this one-time key now. A new key replaces the old one. Changing your password clears the key.',
 recoverySaved:'Recovery settings saved.', smtpSettings:'SMTP settings', enableEmailRecovery:'Enable email recovery',
 gmailPreset:'Use Gmail settings', gmailHelp:'For Gmail, enter your full Gmail address and a Google App Password.',
 smtpHost:'SMTP server', smtpPort:'Port', smtpSecurity:'Encryption', smtpPassword:'SMTP password',
 smtpSender:'Sender address', publicUrl:'Public HTTPS address', testRecipient:'Test recipient',
 sendTestEmail:'Send test email', smtpSaved:'SMTP settings saved.', smtpTestSent:'Test email sent.',
 smtpStoredPassword:'Leave empty to keep the saved password'
});
Object.assign(dict.bg,{
 close:'Затвори', forgotPassword:'Забравена парола?', recoverySettings:'Възстановяване на парола', recoveryMethod:'Метод за възстановяване',
 emailLink:'Линк по имейл', recoveryKey:'Ключ за възстановяване', sendResetLink:'Изпрати линк',
 resetPassword:'Задай нова парола', resetRequested:'Ако профилът има настроено възстановяване по имейл, ще получиш линк.',
 resetComplete:'Паролата е сменена. Влез с новата парола.',
 invalidRecovery:'Линкът или ключът е невалиден или е изтекъл.',
 recoveryEmail:'Имейл за възстановяване', sendVerification:'Изпрати линк за потвърждение', removeEmail:'Премахни имейла',
 verifyRecovery:'Потвърди имейла', verifiedRecovery:'Имейлът за възстановяване е потвърден.',
 recoveryEmailVerified:'Потвърден имейл', recoveryEmailPending:'Очаква потвърждение',
 recoveryEmailDisabled:'Възстановяването по имейл е изключено. Можеш да използваш ключ.',
 verificationSent:'Изпратихме линк за потвърждение. Отвори го до 30 минути.',
 generateRecoveryKey:'Генерирай нов ключ', removeKey:'Премахни ключа', recoveryKeyExists:'Има активен ключ за възстановяване.',
 recoveryKeyMissing:'Няма активен ключ за възстановяване.',
 saveRecoveryKey:'Запази еднократния ключ сега. Новият ключ заменя стария. Смяната на паролата обезсилва ключа.',
 recoverySaved:'Настройките са запазени.', smtpSettings:'SMTP настройки', enableEmailRecovery:'Включи възстановяване по имейл',
 gmailPreset:'Използвай настройки за Gmail', gmailHelp:'За Gmail въведи пълния си адрес и парола за приложение от Google.',
 smtpHost:'SMTP сървър', smtpPort:'Порт', smtpSecurity:'Криптиране', smtpPassword:'SMTP парола',
 smtpSender:'Адрес на подателя', publicUrl:'Публичен HTTPS адрес', testRecipient:'Получател на тестовия имейл',
 sendTestEmail:'Изпрати тестов имейл', smtpSaved:'SMTP настройките са запазени.', smtpTestSent:'Тестовият имейл е изпратен.',
 smtpStoredPassword:'Остави празно, за да запазиш текущата парола'
});

const resetForm=$('resetForm'), resetField=name=>resetForm.elements.namedItem(name);
let emailRecovery=false, recoveryLink=null;
function configureReset(){
 const verifying=recoveryLink?.action==='verify';
 const byKey=!recoveryLink&&resetField('method').value==='key';
 const password=byKey||recoveryLink?.action==='reset';
 $('recoveryMethodLabel').hidden=!!recoveryLink;
 $('resetUsernameLabel').hidden=!!recoveryLink;
 $('resetKeyLabel').hidden=!byKey;
 $('resetPasswordFields').hidden=!password;
 resetField('username').required=!recoveryLink;
 resetField('key').required=byKey;
 resetField('password').required=!!password;
 resetField('confirm').required=!!password;
 const submit=$('submitReset');
 submit.dataset.t=verifying?'verifyRecovery':password?'resetPassword':'sendResetLink';
 submit.textContent=t(submit.dataset.t);
}

function openReset(link=null){
 recoveryLink=link;
 resetForm.reset();
 resetField('method').options[0].disabled=!emailRecovery;
 resetField('method').value=emailRecovery?'email':'key';
 resetField('username').value=$('authUsername').value;
 $('resetStatus').textContent='';
 $('submitReset').hidden=false;
 configureReset();
 if(!$('resetDialog').open)$('resetDialog').showModal();
}

$('forgotPassword').onclick=()=>openReset();
$('closeReset').onclick=()=>$('resetDialog').close();
$('resetDialog').addEventListener('close',()=>{
 recoveryLink=null;
 resetForm.reset();
});
resetField('method').onchange=configureReset;
resetForm.onsubmit=async e=>{
 e.preventDefault();
 const link=recoveryLink;
 const username=resetField('username').value;
 const password=resetField('password').value;
 const button=e.submitter;
 if(resetField('password').required&&password!==resetField('confirm').value){
  $('resetStatus').textContent=t('passwordMismatch');
  return;
 }
 button.disabled=true;
 try{
  if(link?.action==='verify'){
   await api('/api/recovery/verify',{token:link.token});
   recoveryLink=null;
   $('resetStatus').textContent=t('verifiedRecovery');
   button.hidden=true;
  }else if(!link&&resetField('method').value==='email'){
   await api('/api/recovery/request',{username});
   $('resetStatus').textContent=t('resetRequested');
  }else{
   await api('/api/recovery/reset',{method:link?'email':'key',token:link?.token||resetField('key').value,username,password});
   showAuth();
   $('authRecoveryStatus').textContent=t('resetComplete');
   $('authRecoveryStatus').hidden=false;
  }
 }catch(error){
  $('resetStatus').textContent=error.message.endsWith(' (400)')?t('invalidRecovery'):error.message;
 }finally{
  button.disabled=false;
 }
};

const recoveryForm=$('recoveryForm'), recoveryField=name=>recoveryForm.elements.namedItem(name);
let recoverySaving=false;
async function refreshRecovery(){
 const info=await api('/api/recovery');
 const details=[];
 if(info.email)details.push(t('recoveryEmailVerified')+' — '+info.email);
 if(info.pending_email)details.push(t('recoveryEmailPending')+' — '+info.pending_email);
 if(!info.email_available)details.push(t('recoveryEmailDisabled'));
 $('recoveryEmailStatus').textContent=details.join(' · ');
 $('verifyRecoveryEmail').disabled=!info.email_available;
 $('removeRecoveryEmail').hidden=!(info.email||info.pending_email);
 $('recoveryKeyStatus').textContent=t(info.has_key?'recoveryKeyExists':'recoveryKeyMissing');
 $('removeRecoveryKey').hidden=!info.has_key;
}
$('manageRecovery').onclick=async()=>{
 try{
  recoveryForm.reset();
  $('recoveryStatus').textContent='';
  await refreshRecovery();
  $('recoveryDialog').showModal();
 }catch(error){toast(error.message);}
};
$('closeRecovery').onclick=()=>$('recoveryDialog').close();
$('recoveryDialog').addEventListener('close',()=>{
 recoveryForm.reset();
 $('generatedKey').value='';
 $('generatedKeyLabel').hidden=true;
});
recoveryForm.onsubmit=async e=>{
 e.preventDefault();
 if(recoverySaving)return;
 const user=me;
 const action=e.submitter.value;
 const password=recoveryField('password').value;
 const email=recoveryField('email').value;
 recoverySaving=true;
 e.submitter.disabled=true;
 try{
  const result=await api('/api/recovery',{action,password,email});
  if(me!==user||!$('recoveryDialog').open)return;
  recoveryField('password').value='';
  if(action==='create_key'||action==='remove_key'){
   $('generatedKey').value=result.key||'';
   $('generatedKeyLabel').hidden=!result.key;
  }
  $('recoveryStatus').textContent=t(action==='verify_email'?'verificationSent':'recoverySaved');
  await refreshRecovery();
 }catch(error){$('recoveryStatus').textContent=error.message;}
 finally{
  recoverySaving=false;
  e.submitter.disabled=false;
 }
};

const smtpForm=$('smtpForm'), smtpField=name=>smtpForm.elements.namedItem(name);
function showSMTP(config){
 smtpField('enabled').checked=!!config.enabled;
 for(const name of ['host','username','sender','base_url'])smtpField(name).value=config[name]||'';
 smtpField('port').value=config.port||587;
 smtpField('security').value=config.security||'starttls';
 smtpField('password').value='';
 smtpField('password').placeholder=config.has_password?t('smtpStoredPassword'):'';
 $('smtpFields').disabled=!config.enabled;
 $('sendTestMail').disabled=!config.enabled;
}
smtpField('enabled').onchange=()=>{$('smtpFields').disabled=!smtpField('enabled').checked;};
$('gmailPreset').onclick=()=>{
 smtpField('host').value='smtp.gmail.com';
 smtpField('port').value=587;
 smtpField('security').value='starttls';
};
$('manageSMTP').onclick=async()=>{
 try{
  showSMTP(await api('/api/smtp'));
  $('smtpStatus').textContent='';
  $('smtpDialog').showModal();
 }catch(error){toast(error.message);}
};
$('closeSMTP').onclick=()=>$('smtpDialog').close();
$('smtpDialog').addEventListener('close',()=>{smtpField('password').value='';});
smtpForm.onsubmit=async e=>{
 e.preventDefault();
 const value={enabled:smtpField('enabled').checked,port:smtpField('port').valueAsNumber};
 for(const name of ['host','security','username','sender','base_url'])value[name]=smtpField(name).value.trim();
 const password=smtpField('password').value;
 if(password||!value.username)value.password=password;
 e.submitter.disabled=true;
 try{
  const saved=await api('/api/smtp',value);
  emailRecovery=saved.enabled;
  showSMTP(saved);
  $('smtpStatus').textContent=t('smtpSaved');
 }catch(error){$('smtpStatus').textContent=error.message;}
 finally{e.submitter.disabled=false;}
};
$('smtpTestForm').onsubmit=async e=>{
 e.preventDefault();
 e.submitter.disabled=true;
 try{
  await api('/api/smtp/test',{recipient:e.currentTarget.elements.namedItem('recipient').value});
  $('smtpStatus').textContent=t('smtpTestSent');
 }catch(error){$('smtpStatus').textContent=error.message;}
 finally{e.submitter.disabled=!smtpField('enabled').checked;}
};

function openRecoveryLink(){
 const recoveryFragment=location.hash.match(/^#(reset|verify)=([A-Za-z0-9_-]{43})$/);
 if(!recoveryFragment)return;
 history.replaceState(history.state,'',location.pathname+location.search);
 document.querySelectorAll('dialog[open]:not(#resetDialog)').forEach(dialog=>dialog.close());
 language(lang);
 openReset({action:recoveryFragment[1],token:recoveryFragment[2]});
}
window.addEventListener('hashchange',openRecoveryLink);
openRecoveryLink();
