import os
import dotenv
import time
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

def index_document(text: str, index: str, filename: str, page_num: int, type: str):
    '''
    INGEST DOCUMENT
    -------
    - text: Văn bản đầu vào (câu, đoạn văn)
    - index: Tên index trong elasticsearch (thường là tên file, văn bản)
    - filename: Tên file so sánh để ghi log
    - page_num: Câu, đoạn văn thuộc trang số mấy
    - type: Loại (văn bản/bảng)
    '''
    sentences = [i for i in sent_tokenize(text_normalize(text))]
    for sentence in sentences:
        sentence = tokenize(sentence)
        sentence_vectors = embed_text(sentence)
        es.index(
            index=index,
            document={
                "filename": filename,
                "timestamp": time.time(),
                "page_num" : page_num,
                "type": type,
                "sentence": sentence,
                "sentence_vector": sentence_vectors
            }
        )
    es.indices.refresh(index=index)
    return None

def ingest(data: list, index: str):
    bulkData = []
    count = 0
    timestamp = time.time()
    for i in data:
        es.index(
            index=index,
            document={
                        "filename": str(i['filename']),
                        "timestamp": timestamp,
                        "sentence_num": int(count),
                        "sentence": str(i['sentence']),
                        "sentence_vector": embed_text(i['sentence']),
                        "type": str(i['type'])
                    }
        )
        count += 1
    es.indices.refresh(index=index)
    return True
# index_document("Sau 3 năm cưới nhau, tôi vẫn tự hào gọi vợ mình là em bé. Cụ thể là em bé bé cái mồm thôi.", "test001", "facebook", 1)