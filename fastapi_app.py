from fastapi import FastAPI, Query
from github_utils import read_token, show_latest_commits, get_repos, show_commits_range
import uvicorn

app = FastAPI()

@app.get("/latest-commits")
def latest_commits_endpoint():
    return show_latest_commits(read_token(file_path='github_token.txt'))

@app.get("/repos")
def repos_endpoint():
    return get_repos(read_token(file_path='github_token.txt'))

@app.get("/commits-range")
def commits_range_endpoint(owner: str = Query(...), repo: str = Query(...), start: int = Query(...), end: int = Query(...)):
    token = read_token('github_token.txt')
    return show_commits_range(token, owner, repo, start, end)

if __name__ == "__main__":
    uvicorn.run("fastapi_app:app", host="127.0.0.1", port=8000)
