from backend.domain.sources import trusted_source
from backend.config import VERSION

class LibraryService:
    def __init__(self, operations, settings):
        self.operations=operations; self.settings=settings

    def list_sources(self, request_id):
        docs=self.operations.list_knowledge(request_id)
        docs=[d for d in docs if trusted_source(d.get('source_url'))]
        return {'items':[{'title':d['title'],'text':d['text'],'url':d['source_url'],
                          'category':d['category'],'year':d['year'],'retrieved_at':d['retrieved_at']} for d in docs],
                'count':len(docs),'mode':self.settings.data_mode}

    def health(self, request_id):
        docs=self.operations.list_knowledge(request_id)
        docs=[d for d in docs if trusted_source(d.get('source_url'))]
        return {'status':'ok' if docs else 'empty','name':'Mambot','version':VERSION,'records':len(docs),
                'data_mode':self.settings.data_mode,'dense_search':self.settings.vector_enabled,
                'generation_configured':bool(self.settings.llm_key and self.settings.llm_model),
                'snapshot_date':min((d['retrieved_at'][:10] for d in docs if d['retrieved_at']),default=None),
                'authority':'verified','latest_verified':False}
