from aiohttp import web
import aiohttp_jinja2
import jinja2
import json
import database  # твой модуль для работы с БД

connected_users = {}  # username -> WebSocketResponse

database.init_db1()

async def button_clicked(request):
    data = await request.post()
    username = data.get('login')
    password = data.get('password')
    if database.authenticate_user(username, password):
        response = web.Response(status=302, headers={'Location': f'/index/name={username}'})
        response.set_cookie('name', username, path='/')
        return response
    else:
        return web.Response(text='Неверный логин или пароль', status=401)

@aiohttp_jinja2.template('index.html')
async def index(request):
    return {}

@aiohttp_jinja2.template('main.html')
async def main_route(request):
    username = request.cookies.get('name')
    if not username:
        raise web.HTTPFound('/')
    img_data = database.image_get(username)

    if not img_data or not img_data[0] or not img_data[0][0]:
        image_path = '/static/defolt_avatar.png'
    else:
        image_path = img_data[0][0][0]

    friends_data = img_data[1][0] if len(img_data) > 1 and img_data[1] else []
    img = database.add_img_friend(friends_data)
    return {
        'user': username,
        'img': image_path,
        'frend': friends_data,
        'img_friends': img,
    }

async def send_message(request):
    data = await request.post()
    sender = request.cookies.get('name')
    receiver = data.get('receiver')
    message = data.get('message')

    if sender and receiver and message:
        database.add_message(sender, receiver, message)
        if receiver in connected_users:
            ws = connected_users[receiver]
            await ws.send_json({
                'type': 'chat',
                'sender': sender,
                'message': message
            })
        return web.json_response({'status': 'ok'})
    else:
        return web.json_response({'status': 'error', 'message': 'Invalid data'})

async def get_chat(request):
    sender = request.cookies.get('name')
    receiver = request.rel_url.query.get('user')
    if sender and receiver:
        chat_messages = database.get_chat_between_users(sender, receiver)
        return web.json_response({'messages': chat_messages})
    else:
        return web.json_response({'messages': []})

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    username = request.cookies.get('name')
    if not username:
        await ws.close()
        return ws

    connected_users[username] = ws
    print(f"{username} connected.")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)

                msg_type = data.get('type')

                if msg_type == 'chat':
                    receiver = data.get('receiver')
                    message = data.get('message')
                    if receiver and message:
                        database.add_message(username, receiver, message)
                        if receiver in connected_users:
                            await connected_users[receiver].send_json({
                                'type': 'chat',
                                'sender': username,
                                'message': message
                            })
                        # Эхо отправителю
                        await ws.send_json({
                            'type': 'chat',
                            'sender': username,
                            'message': message
                        })

                # УДАЛЕНА обработка WebRTC сигналов (offer, answer, candidate)
                # elif msg_type in ['offer', 'answer', 'candidate']:
                #     receiver = data.get('receiver')
                #     if receiver in connected_users:
                #         await connected_users[receiver].send_json({
                #             **data,
                #             'sender': username
                #         })

                # Обработка отклонения и завершения звонка (можно убрать, если не нужно)
                elif msg_type in ['decline', 'end_call']:
                    receiver = data.get('receiver')
                    if receiver in connected_users:
                        await connected_users[receiver].send_json({
                            'type': msg_type,
                            'sender': username
                        })

            elif msg.type == web.WSMsgType.ERROR:
                print(f'WS connection error: {ws.exception()}')

    finally:
        if username in connected_users:
            del connected_users[username]
        print(f"{username} disconnected.")

    return ws


app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))

app.router.add_static('/static/', path='static', name='static')
app.router.add_post('/send_message', send_message)
app.router.add_get('/get_chat', get_chat)
app.router.add_get('/ws', websocket_handler)
app.add_routes([web.get('/', index)])
app.add_routes([web.post('/login', button_clicked)])
app.add_routes([web.get('/index/name={name}', main_route)])

if __name__ == '__main__':
    web.run_app(app)