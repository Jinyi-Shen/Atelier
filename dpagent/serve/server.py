from fastapi import FastAPI
from langserve import add_routes

from dpagent.serve.search import search_code_runnable, search_doc_runnable


app = FastAPI()


add_routes(app, search_code_runnable, path="/search_code")
add_routes(app, search_doc_runnable, path="/search_doc")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
