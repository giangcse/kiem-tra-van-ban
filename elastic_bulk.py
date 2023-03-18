import os
import dotenv
import warnings
import time

from sentence_transformers import SentenceTransformer
from pyvi.ViTokenizer import tokenize
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

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

def bulk_data(data: list, index: str):
    '''
    BULK DATA INTO ELASTICSEARCH
    -------------------
    - data: danh sach du lieu can bulk
    - index: index can bulk
    '''
    try:
        mappings = {
            "dynamic": "true",
            "_source": {
                "enabled": "true"
            },
            "properties": {
                "filename": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "timestamp": {
                    "type": "text"
                },
                "sentence_num": {
                    "type": "float"
                },
                "type": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "sentence": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "sentence_vector": {
                    "type": "dense_vector",
                    "dims": 768
                }
            }
        }
        es.indices.create(index=index, mappings=mappings)
        bulkData = []
        count = 0
        timestamp = time.time()
        for i in data:
            bulkData.append(
                {
                    "_index": index,
                    "_source": {
                        "filename": str(i['filename']),
                        "timestamp": timestamp,
                        "sentence_num": int(count),
                        "type": str(i['type']),
                        "sentence": str(i['sentence']),
                        "sentence_vector": embed_text(i['sentence'])
                    }
                }
            )
            count += 1
        bulk(es, bulkData)
        return True
    except Exception as e:
        return False
