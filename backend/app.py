"""Single FastAPI composition root. Run with python run.py."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from backend.config import ROOT, VERSION, settings
from backend.errors import DomainError
from backend.operations.knowledge import KnowledgeOperations
from backend.services.chat import ChatService
from backend.services.library import LibraryService
from backend.routes.api import make_router
from backend.infrastructure.http_boundaries import HttpBoundaries, RateLimiter

operations = KnowledgeOperations(settings)
limiter = RateLimiter()
windows = limiter.windows

@asynccontextmanager
async def lifespan(app):
    try:
        yield
    finally:
        operations.close()

app = FastAPI(title='Mambot', version=VERSION, lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(HttpBoundaries, limiter=limiter)
router = make_router(ChatService(operations, settings), LibraryService(operations, settings))
app.include_router(router, prefix='/mambot')
app.include_router(router)  # Compatibility for clients of 1.0/1.1.

@app.exception_handler(DomainError)
async def safe_domain_error(request, error):
    return JSONResponse({'detail': str(error), 'request_id': request.state.request_id}, status_code=error.status)

@app.exception_handler(RequestValidationError)
async def safe_validation_error(request, error):
    return JSONResponse({'detail': 'Nội dung không hợp lệ: câu hỏi 1–800 ký tự, tối đa 10 lượt lịch sử.',
                         'request_id': request.state.request_id}, status_code=422)

@app.get('/')
@app.get('/mambot')
def canonical_index(request: Request):
    return RedirectResponse(request.scope.get('root_path', '').rstrip('/') + '/mambot/', status_code=307)

@app.get('/mambot/', name='index')
def index():
    return FileResponse(ROOT / 'static/index.html')

app.mount('/mambot/static', StaticFiles(directory=ROOT / 'static'), name='mambot-static')
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
