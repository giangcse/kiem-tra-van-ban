import os
import dotenv
import json
import warnings

from sentence_transformers import SentenceTransformer
from pyvi.ViTokenizer import tokenize
from elasticsearch import Elasticsearch
from underthesea import sent_tokenize, text_normalize

# Model convert
model_embedding = SentenceTransformer('VoVanPhuc/sup-SimCSE-VietNamese-phobert-base')
# Load .env
dotenv.load_dotenv()
# Hide warnings
warnings.filterwarnings('ignore')
# Elasticsearch
es = Elasticsearch(
    hosts=['https://'+str(os.getenv('ES_HOST'))+':'+str(os.getenv('ES_PORT'))],
    http_auth=(str(os.getenv('ES_USER')), str(os.getenv('ES_PASS'))),
    verify_certs=False
)

def embed_text(batch_text):
    batch_embedding = model_embedding.encode(batch_text)
    return [vector.tolist() for vector in batch_embedding]

def search_simcse(text: str, index: str):
    '''
    SEARCH DOCUMENT SIMCSE
    -------
    - text: Văn bản đầu vào (câu, đoạn văn)
    - index: Tên index trong elasticsearch (thường là tên file, văn bản)
    '''
    tokenize_text = sent_tokenize(text_normalize(text))
    for sentence in tokenize_text:
        query_vector = embed_text([tokenize(sentence)])[0]
        script_query = {
            "script_score": {
                "query": {
                    "match_all": {}
                },
                "script": {
                    "source": "cosineSimilarity(params['query_vector'], 'sentence_vector') + 1.0",
                    "params": {"query_vector": query_vector}
                }
            }
        }
        response = es.search(
            index=index,
            body={
                "size": 20,
                "query": script_query,
                "_source": {
                    "includes": ["filename", "timestamp", "sentence_num", "sentence", "type"]
                },
            },
            ignore=[400]
        )

        # result = []
        # for hit in response["hits"]["hits"]:
        #     result.append(hit["_source"]['title'])
    return json.dumps(dict(response), indent=4, ensure_ascii=True)

def search_bm25(text: str, index: str):
    '''
    SEARCH DOCUMENT BM25
    -------
    - text: Văn bản đầu vào (câu, đoạn văn)
    - index: Tên index trong elasticsearch (thường là tên file, văn bản)
    '''
    tokenize_text = sent_tokenize(text_normalize(text))
    for sentence in tokenize_text:
        query_vector = embed_text([tokenize(sentence)])[0]
        script_query = {
            "match": {
                "sentence":{
                    "query": sentence,
                    "fuzziness": "AUTO"
                }
            }
        }
        response = es.search(
            index=index,
            body={
                "size": 20,
                "query": script_query,
                "_source": {
                    "includes": ["filename", "timestamp", "sentence_num", "sentence", "type"]
                },
            },
            ignore=[400]
        )

        # result = []
        # for hit in response["hits"]["hits"]:
        #     result.append(hit["_source"]['title'])
    return json.dumps(dict(response), indent=4, ensure_ascii=True)
