from backend.db.gateway import RegisteredGateway
from backend.infrastructure.embedding import embed_question
from backend.errors import DomainError

class KnowledgeOperations:
    def __init__(self, settings):
        self.settings = settings
        self.gateway = RegisteredGateway(settings)

    def list_knowledge(self, request_id):
        try:
            return self.gateway.execute('knowledge.snapshot', {}, request_id)
        except Exception:
            raise DomainError() from None

    def close(self):
        self.gateway.close()

    def find_related_knowledge(self, question, request_id):
        if not self.settings.vector_enabled:
            return []
        if self.settings.data_mode != 'mongo':
            raise DomainError('Tìm kiếm ngữ nghĩa yêu cầu chế độ MongoDB.', 503)
        try:
            vector = embed_question(question)
            return self.gateway.execute('knowledge.semantic', {'QUERY_VECTOR': vector, 'TOP_K': 10}, request_id)
        except Exception:
            raise DomainError('Tìm kiếm ngữ nghĩa chưa sẵn sàng. Kiểm tra cấu hình máy chủ.', 503) from None
