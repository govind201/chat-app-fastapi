import os

from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from fastapi import FastAPI
from fastapi import Request
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from apps.jwt import create_token
from apps.jwt import CREDENTIALS_EXCEPTION
from apps.jwt import valid_email_from_db
from apps.jwt import create_refresh_token
from apps.jwt import decode_token
from datetime import datetime
from fastapi.responses import RedirectResponse
from .jwt import FAKE_DB


# Create the auth app
auth_app = FastAPI()

# OAuth settings
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or None
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or None
if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_SECRET is None:
    raise BaseException('Missing env variables')

# Set up OAuth
config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# Set up the middleware to read the request session
SECRET_KEY = os.environ.get('SECRET_KEY') or None
if SECRET_KEY is None:
    raise 'Missing SECRET_KEY'
auth_app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Frontend URL:
FRONTEND_URL = os.environ.get('FRONTEND_URL') or 'http://localhost:7000/token'


@auth_app.route('/login')
async def login(request: Request):
    redirect_uri = FRONTEND_URL  # This creates the url for our /auth endpoint
    return await oauth.google.authorize_redirect(request, redirect_uri)


@auth_app.route('/token')
async def auth(request: Request):
    try:
        redirect_uri = 'http://localhost:7000/home'
        access_token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        raise CREDENTIALS_EXCEPTION
    user_data = await oauth.google.parse_id_token(request, access_token)
    
    # if not valid_email_from_db(user_data['email']):
    #     print(user_data.email)
    #     print('Not a valid email in fake db')
    #     raise CREDENTIALS_EXCEPTION
        
    return JSONResponse({
        'result': True,
        'access_token': create_token(user_data['email']),
        'refresh_token': create_refresh_token(user_data['email']),
    })
    # return JSONResponse({'result':'failed because not in db', 'google_data': user_data, })
    raise CREDENTIALS_EXCEPTION

@auth_app.post('/refresh')
async def refresh(request: Request):
    try:
        # Only accept post requests
        if request.method == 'POST':
            form = await request.json()
            if form.get('grant_type') == 'refresh_token':
                token = form.get('refresh_token')
                payload = decode_token(token)
                # Check if token is not expired
                if datetime.utcfromtimestamp(payload.get('exp')) > datetime.utcnow():
                    email = payload.get('sub')
                    # # Validate email
                    # if valid_email_from_db(email):
                        # Create and return token
                    return JSONResponse({'result': True, 'access_token': create_token(email)})

    except Exception:
        raise CREDENTIALS_EXCEPTION
    raise CREDENTIALS_EXCEPTION