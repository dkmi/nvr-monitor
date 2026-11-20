"""Explicit Chromium check for real drag/drop, persistence and stable video nodes."""
import sys,tempfile,threading
from pathlib import Path
from unittest.mock import patch
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.server import create_app
from app.engine import validate_camera

def main():
 with tempfile.TemporaryDirectory() as tmp,patch('app.updates.latest_release',return_value={'tag':'v1.4.0','revision':None}):
  r=Path(tmp);app=create_app(r/'data',r/'records',r/'cache',False);store=app.extensions['store'];store.save_user({'username':'order-admin','password':'synthetic-order-password','role':'admin'});store.save_user({'username':'order-viewer','password':'synthetic-order-password','role':'full'})
  cams=[validate_camera({'name':'Camera '+str(i+1),'host':'192.0.2.'+str(i+1),'username':'test-camera','password':'synthetic-camera-password','enabled':False,'motion':True,'timelapse':True,'timelapse_interval':17}) for i in range(3)];store.put('cameras',cams);ids=[c['id'] for c in cams]
  server=make_server('127.0.0.1',0,app,threaded=True);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   with sync_playwright() as p:
    b=p.chromium.launch(headless=True);page=b.new_page(viewport={'width':1500,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{server.server_port}');page.locator('#authUsername').fill('order-admin');page.locator('#authPassword').fill('synthetic-order-password');page.locator('#authForm button.primary').click();page.locator('.tile').first.wait_for();page.locator('video').evaluate_all('(vs)=>vs.forEach((v,i)=>v.dataset.original=String(i))')
    def order():return [c['id'] for c in store.cameras()]
    page.locator(f'.cameraRow[data-id="{ids[0]}"] .camera-drag').drag_to(page.locator(f'.cameraRow[data-id="{ids[2]}"]'))
    page.wait_for_function('()=>[...document.querySelectorAll("#grid>.tile")].sort((a,b)=>Number(a.style.order)-Number(b.style.order))[2].dataset.id===\"'+ids[0]+'\"');assert order()==[ids[1],ids[2],ids[0]]
    assert page.locator(f'.tile[data-id="{ids[0]}"] video').get_attribute('data-original')=='0'
    page.locator(f'.tile[data-id="{ids[0]}"] .camera-drag').drag_to(page.locator(f'.tile[data-id="{ids[1]}"]'))
    page.wait_for_function('()=>[...document.querySelectorAll("#grid>.tile")].sort((a,b)=>Number(a.style.order)-Number(b.style.order))[0].dataset.id===\"'+ids[0]+'\"');assert order()==ids
    page.locator(f'.tile[data-id="{ids[0]}"] .camera-drag').focus();page.keyboard.press('Alt+ArrowRight');page.wait_for_function('()=>Number(document.querySelector(\'.tile[data-id="'+ids[0]+'"]\').style.order)===1');expected=[ids[1],ids[0],ids[2]];assert order()==expected
    page.reload();page.locator('.tile').first.wait_for();assert page.locator('#grid>.tile').evaluate_all('(ts)=>ts.map(t=>t.dataset.id)')==expected
    page.locator('.cameraRow').first.click();page.locator('[name="name"]').fill('Edited in place');page.locator('#cameraForm button.primary').click();page.locator('#cameraDialog').wait_for(state='hidden');assert order()==expected;assert all(c['timelapse_interval']==17 and c['password']=='synthetic-camera-password' for c in store.cameras())
    page.locator('aside [data-lang="bg"]').click();assert 'Alt' in page.locator('.camera-drag').first.get_attribute('title');page.locator('#lock').click();page.locator('#auth').wait_for(state='visible');page.locator('#authUsername').fill('order-viewer');page.locator('#authPassword').fill('synthetic-order-password');page.locator('#authForm button.primary').click();page.locator('.tile').first.wait_for();assert page.locator('.camera-drag').count()==0;assert page.locator('#grid>.tile').evaluate_all('(ts)=>ts.map(t=>t.dataset.id)')==expected
    assert not errors,errors;b.close();print('PASS sidebar/grid native drag, keyboard ordering, stable video nodes, reload persistence, edit position/credentials, shared viewer order and no JS errors')
  finally:server.shutdown();thread.join()
if __name__=='__main__':main()
