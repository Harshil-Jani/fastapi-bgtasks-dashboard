from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from fastapi.responses import HTMLResponse
import threading, json, asyncio
from .core import (
    _ws_lock,
    _ws_connections,
    _broadcast_update,
    _tasks,
    _tasks_lock,
    _wrap_task,
    _registered_funcs,
)
from .utils import _dt
from . import __version__

router = APIRouter()


@router.get("/dashboard")
def dashboard_html():
    html = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <title>FastAPI Background Tasks Dashboard</title>
        <style>
          body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#fafafa;color:#333;display:flex;flex-direction:column;min-height:100vh;overflow-x:hidden;}
          header{background:#009688;color:white;padding:1rem 2rem;}
          header h1{margin:0;font-size:1.5rem;}
          #status{margin:1rem 0;font-weight:bold;}
          #top-row{display:flex;justify-content:space-between;align-items:center;margin:0 2rem;}
          #filter-box{margin:1rem 2rem;display:flex;gap:1rem;align-items:center;flex-wrap:wrap;}
          input[type=text]{padding:0.5rem;border:1px solid #ccc;border-radius:4px;width:200px;}
          select{padding:0.5rem;border-radius:4px;border:1px solid #ccc;}
          button{padding:0.5rem 1rem;background:#F44336;color:white;border:none;border-radius:4px;cursor:pointer;position:relative;}
          button:hover{opacity:0.85;}
          table{width:100%;max-width:100vw;table-layout:fixed;margin:0 auto 2rem auto;border-collapse:collapse;background:white;border-radius:6px;overflow:hidden;}
          th, td{word-wrap:break-word;overflow-wrap:break-word;white-space:normal;}
          th{text-align:center;padding:0.75rem;font-size:0.95rem;color:#555;border-bottom:2px solid #ddd;cursor:pointer;user-select:none;}
          th.sort-asc::after{content:" ▲";font-size:0.75rem;}
          th.sort-desc::after{content:" ▼";font-size:0.75rem;}
          td{text-align:center;padding:0.75rem;border-bottom:1px solid #eee;font-size:0.9rem;vertical-align:middle;}
          td pre.param-preview, td pre.param-full{background:#f9f9f9;padding:0.5rem;border-radius:4px;font-family:monospace;font-size:0.8rem;margin:0;overflow:hidden;white-space:pre-wrap;word-break:break-word;text-align:left;max-width:95vw;}
          td pre.param-preview{max-height:3em;}
          .param-expand{display:inline-block;margin-top:0.25rem;color:#009688;cursor:pointer;font-size:0.75rem;font-weight:bold;}
          #empty{text-align:center;margin:2rem;color:#777;font-style:italic;}
          footer{margin-top:auto;background:#f0f0f0;text-align:center;padding:1rem;font-size:0.85rem;color:#555;}
          footer a{color:#009688;text-decoration:none;font-weight:bold;}
          tr:hover{border:1px solid #009688;border-radius:4px;}
          #status.connected{color:#4CAF50;font-weight:bold;background:#E8F5E9;padding:0.5rem 1rem;border-radius:4px;display:inline-block;}
          #status.disconnected{color:#F44336;font-weight:bold;background:#FFEBEE;padding:0.5rem 1rem;border-radius:4px;display:inline-block;}
          .tooltip { position: relative; display: inline-block; }
          .tooltip .tooltiptext {
            visibility: hidden;
            width: 200px;
            background-color: #555;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 0.5rem;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.75rem;
          }
          .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
          #pagination{display:flex;justify-content:center;gap:0.5rem;margin-bottom:2rem;flex-wrap:wrap;}
          #pagination button{padding:0.3rem 0.6rem;border:none;border-radius:4px;cursor:pointer;}
        </style>
      </head>
      <body>
        <header><h1>FastAPI Background Tasks Dashboard</h1></header>
        <div id="top-row">
          <div id="status">Connecting...</div>
          <div class="tooltip">
            <button id="clear-tasks">Clear Tasks</button>
            <span class="tooltiptext">Clear all in-memory background tasks</span>
          </div>
        </div>
        <div id="filter-box">
          <label for="filter">Filter by function:</label>
          <input type="text" id="filter" placeholder="Enter function name..." />
          <label for="status-filter">Filter by status:</label>
          <select id="status-filter">
            <option value="">All</option>
            <option value="QUEUED">Queued</option>
            <option value="RUNNING">Running</option>
            <option value="FINISHED">Finished</option>
            <option value="FAILED">Failed</option>
          </select>
          <label for="duration-unit">Duration unit:</label>
          <select id="duration-unit">
            <option value="ms">ms</option>
            <option value="s" selected>s</option>
            <option value="m">m</option>
            <option value="h">h</option>
          </select>
        </div>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th data-sort="func">Function</th>
              <th data-sort="status">Status</th>
              <th data-sort="started_at" class="sort-desc">Started</th>
              <th data-sort="ended_at">Ended</th>
              <th data-sort="duration">Duration</th>
              <th>Params</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="tbody"></tbody>
        </table>
        <div id="empty" style="display:none;">No background tasks yet</div>
        <div id="pagination"></div>
        <footer>
          Made with ❤️ for open-source community by 
          <a href="https://github.com/Harshil-Jani" target="_blank">Harshil-Jani</a>
          <br/>
          <small>fastapi-bgtasks-dashboard v{{VERSION}}</small>
        </footer>
        <script>
          const ws = new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/dashboard/ws');
          const tbody=document.getElementById('tbody');
          const statusEl=document.getElementById('status');
          const empty=document.getElementById('empty');
          const filterInput=document.getElementById('filter');
          const statusFilter=document.getElementById('status-filter');
          const durationSelect=document.getElementById('duration-unit');
          const clearBtn=document.getElementById('clear-tasks');
          const pagination=document.getElementById('pagination');

          let allTasks=[],sortField="started_at",sortDir=-1; // default newest first
          let currentPage=1, pageSize=100;

          ws.onopen=()=>{statusEl.className='connected';statusEl.innerText='Connected';};
          ws.onclose=()=>{statusEl.className='disconnected';statusEl.innerText='Disconnected';};
          ws.onmessage=ev=>{allTasks=JSON.parse(ev.data).tasks||[];currentPage=1;renderTasks();};
          filterInput.addEventListener('input',()=>{currentPage=1;renderTasks();});
          statusFilter.addEventListener('change',()=>{currentPage=1;renderTasks();});
          durationSelect.addEventListener('change',renderTasks);

          function computeDuration(start,end){
            if(!start||!end) return "–";
            const ms=new Date(end)-new Date(start);
            const unit=durationSelect.value;
            if(unit==="s") return (ms/1000).toFixed(2)+" s";
            if(unit==="m") return (ms/60000).toFixed(2)+" m";
            if(unit==="h") return (ms/3600000).toFixed(2)+" h";
            return ms+" ms";
          }

          function statusColor(status){
            const s=status.toUpperCase();
            if(s.includes('RUNNING')) return '#FFF9C4';
            if(s.includes('FINISHED')) return '#C8E6C9';
            if(s.includes('FAILED')) return '#FFCDD2';
            return '#ffffff';
          }

          function renderTasks(){
            const filter=filterInput.value.trim().toLowerCase();
            const statusVal=statusFilter.value;
            let tasks=allTasks.slice();
            if(filter) tasks=tasks.filter(t=>t.func.toLowerCase().includes(filter));
            if(statusVal) tasks=tasks.filter(t=>t.status.toUpperCase().includes(statusVal));

            if(sortField){
              tasks.sort((a,b)=>{
                let va=a[sortField],vb=b[sortField];
                if(sortField==='duration'){
                  va=parseFloat(computeDuration(a.started_at,a.ended_at));
                  vb=parseFloat(computeDuration(b.started_at,b.ended_at));
                }
                if(va<vb) return -1*sortDir;
                if(va>vb) return 1*sortDir;
                return 0;
              });
            }

            const totalPages=Math.ceil(tasks.length/pageSize);
            if(currentPage>totalPages) currentPage=totalPages||1;
            const start=(currentPage-1)*pageSize;
            const paginated=tasks.slice(start,start+pageSize);

            tbody.innerHTML='';
            if(paginated.length===0){ empty.style.display='block'; } 
            else { empty.style.display='none'; }

            paginated.forEach(t=>{
              const tr=document.createElement('tr');
              tr.style.backgroundColor=statusColor(t.status);
              const statusText=t.status.toUpperCase();
              const paramsStr=JSON.stringify(t.params,null,2)||'';
              const preview=paramsStr.length>200?paramsStr.slice(0,200)+"...":paramsStr;
              tr.innerHTML=`
                <td>${t.id}</td>
                <td>${t.func}</td>
                <td class="status">${statusText}</td>
                <td>${t.started_at||''}</td>
                <td>${t.ended_at||''}</td>
                <td>${computeDuration(t.started_at,t.ended_at)}</td>
                <td>
                  <pre class="param-preview">${preview}</pre>
                  ${paramsStr.length>200?'<div class="param-expand">Show more</div>':''}
                  <pre class="param-full" style="display:none;">${paramsStr}</pre>
                </td>
                <td><button class="run-btn" data-func="${t.func}" data-params='${JSON.stringify(t.params)}'>Run Again</button></td>
              `;
              tbody.appendChild(tr);
              const expandBtn=tr.querySelector('.param-expand');
              if(expandBtn) expandBtn.addEventListener('click',()=>{
                const full=tr.querySelector('.param-full');
                const previewBox=tr.querySelector('.param-preview');
                if(full.style.display==='none'){ full.style.display='block'; previewBox.style.display='none'; expandBtn.innerText='Show less'; }
                else { full.style.display='none'; previewBox.style.display='block'; expandBtn.innerText='Show more'; }
              });
            });

            document.querySelectorAll(".run-btn").forEach(b=>{
              b.addEventListener('click',async ()=>{
                const func=b.getAttribute('data-func');
                const params=JSON.parse(b.getAttribute('data-params'));
                try{
                  await fetch('/dashboard/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({func_name:func,params:params})});
                }catch(e){alert('Failed to trigger function');}
              });
            });

            // pagination controls
            pagination.innerHTML='';
            if(totalPages>1){
              for(let i=1;i<=totalPages;i++){
                const btn=document.createElement('button');
                btn.innerText=i;
                btn.style.background=(i===currentPage)?'#009688':'#ccc';
                btn.style.color='white';
                btn.addEventListener('click',()=>{currentPage=i;renderTasks();});
                pagination.appendChild(btn);
              }
            }
          }

          document.querySelectorAll("th[data-sort]").forEach(th=>{
            th.addEventListener('click',()=>{
              const field=th.getAttribute('data-sort');
              if(sortField===field) sortDir*=-1; else {sortField=field; sortDir=1;}
              document.querySelectorAll("th").forEach(x=>x.classList.remove('sort-asc','sort-desc'));
              th.classList.add(sortDir===1?'sort-asc':'sort-desc');
              renderTasks();
            });
          });

          clearBtn.addEventListener('click',async ()=>{
            try{
              await fetch('/dashboard/clear',{method:'POST'});
              allTasks=[];
              renderTasks();
            }catch(e){alert('Failed to clear tasks');}
          });
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html.replace("{{VERSION}}", __version__))


# WebSocket endpoint
@router.websocket("/dashboard/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    with _ws_lock:
        _ws_connections.add(websocket)
    try:
        # send initial snapshot
        with _tasks_lock:
            payload = {
                "tasks": [
                    {
                        "id": tid,
                        "func": data["func_name"],
                        "status": data["status"],
                        "started_at": _dt(data.get("started_at")),
                        "ended_at": _dt(data.get("ended_at")),
                        "params": data.get("params", {}),
                    }
                    for tid, data in _tasks.items()
                ]
            }
        await websocket.send_text(json.dumps(payload))
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:
                await asyncio.sleep(0.1)
    finally:
        with _ws_lock:
            _ws_connections.discard(websocket)


# Clear tasks endpoint
@router.post("/dashboard/clear")
async def clear_tasks():
    with _tasks_lock:
        _tasks.clear()
    _broadcast_update()
    return {"ok": True}


# Rerun task endpoint
@router.post("/dashboard/run")
async def run_task(data: dict):
    func_name = data.get("func_name")
    params = data.get("params", {})
    func = _registered_funcs.get(func_name)
    if not func:
        return {"ok": False, "error": "Function not found"}
    runner = _wrap_task(func, **params)
    threading.Thread(target=runner).start()
    return {"ok": True}
