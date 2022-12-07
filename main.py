import uvicorn
from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi import WebSocket
from starlette.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from apps.jwt import get_current_user_email
from connection import ConnectionManager

from apps.api import api_app
from apps.auth import auth_app

from collections import defaultdict
from starlette.websockets import WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware


app = FastAPI()
app.mount('/auth', auth_app)
app.mount('/api', api_app)



app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get('/')
async def root():
    return HTMLResponse('''
        <body><a href="/auth/login">Log In</a></body>
    ''')

manager = ConnectionManager()


@app.get("/{room_name}/{user_name}")
async def get(request: Request, room_name, user_name):
    return templates.TemplateResponse(
        "chat-room.html",
        {"request": request, "room_name": room_name, "user_name": user_name},
    )


@app.websocket("/ws/{room_name}")
async def websocket_endpoint(
    websocket: WebSocket, room_name, background_tasks: BackgroundTasks
):
    await manager.connect(websocket, room_name)
    print(websocket, room_name)
    try:
        while True:
            data = await websocket.receive_text()

            room_members = (
                manager.get_members(room_name)
                if manager.get_members(room_name) is not None
                else []
            )
            if websocket not in room_members:
                print("SENDER NOT IN ROOM MEMBERS: RECONNECTING")
                await manager.connect(websocket, room_name)

            await manager.send_private_message(f"{data}", room_name)
    except WebSocketDisconnect:
        manager.remove(websocket, room_name)



@app.get('/token')
async def token(request: Request):
    return HTMLResponse('''
    <div>
                <script>
                function send(){
                    var req = new XMLHttpRequest();
                    console.log(req);
                    req.onreadystatechange = function() {
                        if (req.readyState === 4) {
                            console.log(req.response);
                            if (req.response["result"] === true) {
                                window.localStorage.setItem('jwt', req.response["access_token"]);
                                window.localStorage.setItem('refresh', req.response["refresh_token"]);
                            }
                        }
                    }
                    req.withCredentials = true;
                    req.responseType = 'json';
                    req.jwt=window.localStorage.getItem('jwt');
                    req.open("get", "/auth/token?"+window.location.search.substr(1), true);
                    req.send("");

                }
                </script>
                <button onClick="send()">Get FastAPI JWT Token</button>

                <button onClick='fetch("http://localhost:7000/api/").then(
                    (r)=>r.json()).then((msg)=>{console.log(msg)});'>
                Call Unprotected API
                </button>
                <button onClick='fetch("http://localhost:7000/api/protected").then(
                    (r)=>r.json()).then((msg)=>{console.log(msg)});'>
                Call Protected API without JWT
                </button>
                <button onClick='fetch("http://localhost:7000/api/protected",{
                    headers:{
                        "Authorization": "Bearer " + window.localStorage.getItem("jwt")
                    },
                }).then((r)=>r.json()).then((msg)=>{console.log(msg)});'>
                Call Protected API wit JWT
                </button>
                <button onClick='fetch("http://localhost:7000/auth/refresh",{
            method: "POST",
            headers:{
                "Authorization": "Bearer " + window.localStorage.getItem("jwt")
        },
            body:JSON.stringify({
                  grant_type:\"refresh_token\",
                 refresh_token:window.localStorage.getItem(\"refresh\")
                })
            }).then((r)=>r.json()).then((msg)=>{
            console.log(msg);
            if (msg["result"] === true) {
                  window.localStorage.setItem("jwt", msg["access_token"]);
            }
        });'>
Refresh
</button> 
            </div>
                
            ''')

@app.exception_handler(404)
async def custom_404_handler(_, __):
    return 'Page Not found'

if __name__ == '__main__':
    uvicorn.run(app, port=7000)

