from fastapi import FastAPI
import uvicorn

duolingo = FastAPI(title="Mini Duolingo")



if __name__ == '__main__':
    uvicorn.run(duolingo, host="127.0.0.1", port=8000)