from functools import lru_cache
import threading

_lock = threading.Lock()

@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding
    return TextEmbedding('intfloat/multilingual-e5-large')

def embed_question(question):
    # Explicit opt-in: first use downloads the E5 model, never needed in local mode.
    with _lock:
        return list(_model().embed(['query: ' + question]))[0].tolist()
