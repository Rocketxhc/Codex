#!/usr/bin/env python3
"""Exercise the cloud-installed browser and document workflow on local fixtures."""
import argparse
import http.server
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import zipfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--state',type=Path,default=Path(os.environ.get('CLOUD_SKILLS_STATE_DIR','/workspace/skill-platform')))
args=parser.parse_args()
repo=Path(__file__).resolve().parent.parent
state=args.state.resolve()
output=Path(tempfile.mkdtemp(prefix='cold-smoke-',dir=state/'validation'))
python=state/'documents-venv/bin/python'
content={'title':'云端技能恢复验证','subtitle':'Cloud-only workflow','sections':[{'heading':'中文文档','paragraphs':['此文件由仓库内安装流程恢复后生成。'],'table':[['项目','结果'],['文档','正常']]}],'slides':[{'title':'中文幻灯片','bullets':['可编辑文本','无需本地设备依赖']} ]}
data=output/'content.json'
data.write_text(json.dumps(content,ensure_ascii=False),encoding='utf-8')
for skill,script,name in [('document-creator','create_document.py','check.docx'),('presentation-creator','create_presentation.py','check.pptx')]:
    subprocess.run([str(python),str(repo/'.agents/skills'/skill/'scripts'/script),str(data),str(output/name)],check=True)
    with zipfile.ZipFile(output/name) as archive:
        assert archive.testzip() is None
    subprocess.run(['soffice','--headless','--convert-to','pdf','--outdir',str(output),str(output/name)],check=True)
    # Separate names avoid DOCX and PPTX both producing check.pdf.
    destination=output/(name+'.pdf')
    (output/'check.pdf').rename(destination)
    subprocess.run([str(python),'-c','from pypdf import PdfReader; import sys; r=PdfReader(sys.argv[1]); assert len(r.pages)==int(sys.argv[2]); assert "云端技能恢复验证" in "".join(p.extract_text() for p in r.pages)',str(destination),'1' if name.endswith('docx') else '2'],check=True)
    subprocess.run(['pdftoppm','-f','1','-singlefile','-r','90','-png',str(destination),str(output/name)],check=True)

class Fixture(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body=b'<title>Cloud skill recovery</title><input id="name"><button id="send" onclick="document.querySelector(\'#result\').textContent=\'Hello \'+document.querySelector(\'#name\').value">Apply</button><div id="result"></div>'
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(body)
    def log_message(self,*_):
        pass

server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Fixture)
thread=threading.Thread(target=server.serve_forever,daemon=True)
thread.start()
browser=[str(state/'bin/agent-browser'),'--session',f'cold-smoke-{os.getpid()}']
try:
    for command in [('open',f'http://127.0.0.1:{server.server_port}'),('fill','#name','Cloud Recovery'),('click','#send')]:
        subprocess.run([*browser,*command],check=True)
    result=subprocess.check_output([*browser,'get','text','#result'],text=True)
    assert 'Hello Cloud Recovery' in result,result
    subprocess.run([*browser,'screenshot',str(output/'browser.png')],check=True)
finally:
    subprocess.run([*browser,'close'],check=False)
    server.shutdown()
    server.server_close()
(output/'results.json').write_text(json.dumps({'documents':'passed','browser':'passed','repo':str(repo),'state':str(state)},indent=2)+'\n')
print(f'Cold runtime functional checks passed. Evidence: {output}')
