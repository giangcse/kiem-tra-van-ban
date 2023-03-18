import uvicorn
import json

from fastapi import FastAPI, Form
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Union

from elastic_search import search_bm25, search_simcse

app = FastAPI()
app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*']
        )

@app.get('/search')
def _search(request: Request, query: str, index: str, option: str):
    try:
        if(option == "simcse"):
            result = search_simcse(query, index)
        elif(option == "bm25"):
            result = search_bm25(query, index)
        return JSONResponse(status_code=200, content={'result': json.loads(result)})
    except Exception as e:
        return JSONResponse(status_code=401, content={'result': e})

if __name__=='__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=80)