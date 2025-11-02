import pytest
from importlib import import_module

views = import_module("api.views")


def test_get_template_from_mongo_success(monkeypatch):
    # prepara documentos simulados na 'collection'
    docs = {
        "h2p": {"_id": "h2p", "model": "H2P", "extension": "xml", "template": "<t>h2p</t>"},
        "byext": {"_id": "any", "extension": "cfg", "template": "fallback-cfg"},
    }

    class MockColl:
        def find_one(self, query):
            # 1) buscar por model regex + extension
            if isinstance(query, dict) and "model" in query and "extension" in query:
                regex = query["model"].get("$regex", "")
                # tirar ^$
                pattern = regex.strip("^$")
                for d in docs.values():
                    if d.get("model") and d.get("model").lower() == pattern.lower() and d.get("extension") == query["extension"]:
                        return d
            # 2) buscar por _id
            if isinstance(query, dict) and "_id" in query:
                return docs.get(query["_id"])
            # 3) fallback por extension
            if isinstance(query, dict) and "extension" in query and len(query) == 1:
                for d in docs.values():
                    if d.get("extension") == query["extension"]:
                        return d
            return None

    class MockDB:
        def __init__(self):
            self.device_templates = MockColl()
        def get_collection(self, name):
            return self.device_templates

    monkeypatch.setattr("api.views.get_mongo_client", lambda: MockDB())

    # busca por model (case-insensitive) com ext xml -> encontra via model regex
    doc = views.get_template_from_mongo("H2P", "xml")
    assert doc and doc.get("template") == "<t>h2p</t>"

    # busca por model inexistente e ext cfg -> fallback por extensão
    doc2 = views.get_template_from_mongo("NoModel", "cfg")
    assert doc2 and doc2.get("template") == "fallback-cfg"