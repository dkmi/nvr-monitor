"""Explicit browser check: pip install playwright; playwright install chromium."""
import sys,tempfile,threading
from pathlib import Path
from unittest.mock import patch
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.server import create_app

def main():
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  try:
   for case in ('same','new','none','failure','viewer'):
    with tempfile.TemporaryDirectory() as tmp:
     root=Path(tmp);release={'tag':'v1.4.1' if case=='new' else 'v1.4.0','revision':('a' if case=='none' else 'b')*40,'notes':'Test release'}
     with patch('app.updates.installed_revision',return_value='a'*40),patch('app.updates.latest_release',side_effect=RuntimeError('offline') if case=='failure' else None,return_value=release) as latest:
      app=create_app(root/'data',root/'recordings',root/'cache',start_engine=False);store=app.extensions['store'];store.save_user({'username':'notice-admin','password':'synthetic-notice-password','role':'admin'})
      if case=='viewer':store.save_user({'username':'notice-viewer','password':'synthetic-notice-password','role':'full'})
      server=make_server('127.0.0.1',0,app,threaded=True);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();context=browser.new_context();page=context.new_page();errors=[];requests=[]
      page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append((r.method,r.url)))
      try:
       page.goto(f'http://127.0.0.1:{server.server_port}');page.locator('#authUsername').fill('notice-viewer' if case=='viewer' else 'notice-admin');page.locator('#authPassword').fill('synthetic-notice-password');page.locator('#authForm button.primary').click();page.locator('#shell').wait_for(state='visible')
       if case in ('same','new'):
        page.locator('#updateNotice').wait_for(state='visible');assert ('updated build' if case=='same' else 'new version') in page.locator('#updateNoticeText').inner_text()
        page.locator('#toggleSidebar').click();assert page.locator('#sidebar').is_hidden() and page.locator('#updateNotice').is_visible()
        page.locator('#reviewUpdate').click();page.locator('#updatesDialog').wait_for(state='visible');page.locator('#closeUpdates').click();page.locator('#dismissUpdateNotice').click();assert page.locator('#updateNotice').is_hidden()
        page.reload();page.locator('#updateNotice').wait_for(state='visible');page.locator('#toggleSidebar').click();page.locator('aside [data-lang="bg"]').click();assert '1.4.' in page.locator('#updateNoticeText').inner_text();assert 'available' not in page.locator('#updateNoticeText').inner_text()
       else:
        if case!='viewer':page.wait_for_function('()=>performance.getEntriesByType("resource").some(e=>e.name.includes("/api/updates?check=1"))')
        page.wait_for_timeout(150);assert page.locator('#updateNotice').is_hidden()
       assert not [r for r in requests if r[0]=='POST' and '/api/updates' in r[1]],'Automatic installation attempted'
       if case=='viewer':assert latest.call_count==0 and not [r for r in requests if '/api/updates' in r[1]]
       else:assert latest.call_count>=1
       assert not errors,errors
       print('PASS automatic notice:',case,flush=True)
      finally:context.close();server.shutdown();thread.join()
  finally:browser.close()
if __name__=='__main__':main()
