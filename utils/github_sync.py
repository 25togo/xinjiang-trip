"""GitHub API wrapper — 編輯 UI 把改動 commit 回 repo。

設定（Streamlit Cloud → app → Settings → Secrets）：

    github_token = "ghp_xxx"     # Personal Access Token (scope: repo)
    github_owner = "25togo"
    github_repo  = "xinjiang-trip"

設定後 Streamlit Cloud 會自動 reboot app。
"""
import base64
import requests
import streamlit as st

GITHUB_API = "https://api.github.com"


def _get_config():
    token = st.secrets.get("github_token") if hasattr(st, "secrets") else None
    owner = st.secrets.get("github_owner", "25togo") if hasattr(st, "secrets") else "25togo"
    repo = st.secrets.get("github_repo", "xinjiang-trip") if hasattr(st, "secrets") else "xinjiang-trip"
    return token, owner, repo


def is_configured() -> bool:
    token, _, _ = _get_config()
    return bool(token)


def _headers():
    token, _, _ = _get_config()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def show_setup_instructions():
    st.error("⚠️ 編輯功能需要 GitHub Token 才能用")
    st.markdown(
        """
        ### 設定 GitHub Token（一次性，5 分鐘）

        1. **產生 Token**
           - 打開 https://github.com/settings/tokens?type=beta
           - 點 **Generate new token (fine-grained)**
           - **Token name**：`xinjiang-trip-editor`
           - **Expiration**：1 year
           - **Repository access** → **Only select repositories** → 選 `25togo/xinjiang-trip`
           - **Repository permissions** → **Contents** → **Read and write**
           - 按 **Generate token** → 複製出來的字串（`github_pat_...`）

        2. **設到 Streamlit Cloud**
           - 打開 https://share.streamlit.io/
           - 點你的 app（`wendy-xinjiang-trip`）
           - 右下 **⋯** → **Settings** → 左側 **Secrets**
           - 貼上：
             ```toml
             github_token = "github_pat_xxxxxxx"
             github_owner = "25togo"
             github_repo  = "xinjiang-trip"
             ```
           - 按 **Save** → app 會自動 reboot
           - 約 30 秒後重整這頁，就可以開始編輯了
        """
    )


def get_file(path: str) -> tuple[str, str]:
    """讀 repo 內檔案。回傳 (內容字串, sha)。"""
    _, owner, repo = _get_config()
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(url, headers=_headers(), timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"讀檔失敗 {path}: {r.status_code} {r.text[:200]}")
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def update_file(path: str, content_str: str, message: str, sha: str) -> str:
    """覆寫 repo 內檔案。回傳 commit URL。"""
    _, owner, repo = _get_config()
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    payload = {
        "message": message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("ascii"),
        "sha": sha,
    }
    r = requests.put(url, headers=_headers(), json=payload, timeout=20)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"寫檔失敗 {path}: {r.status_code} {r.text[:200]}")
    return r.json().get("commit", {}).get("html_url", "")


def upload_image(file_bytes: bytes, filename: str, message: str = "feat: 上傳景點圖") -> str:
    """上傳圖到 repo images/places/，回傳 raw URL（可直接放 image_url）。"""
    _, owner, repo = _get_config()
    path = f"images/places/{filename}"
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"

    # 檢查同名檔是否已存在
    sha = None
    r = requests.get(url, headers=_headers(), timeout=10)
    if r.status_code == 200:
        sha = r.json()["sha"]

    payload = {
        "message": f"{message}: {filename}",
        "content": base64.b64encode(file_bytes).decode("ascii"),
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=_headers(), json=payload, timeout=30)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"上傳失敗 {filename}: {r.status_code} {r.text[:200]}")

    # cache-bust 用 commit sha 當 query string
    commit_sha = r.json().get("commit", {}).get("sha", "")[:7]
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
    return f"{raw_url}?v={commit_sha}" if commit_sha else raw_url
