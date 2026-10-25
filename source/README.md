# 原始檔

網站是由這裡的檔案產生的。要改遊戲內容，改這裡，再重新產生 `index.html`。

- `template.html`：遊戲的程式和版面，球員資料的位置留空
- `pool.json`：MLB 668 位球員的 2026 球季數據
- `pool_cpbl.json`：中職 197 位球員的 2026 球季數據
- `build.py`：把上面幾個合起來，產生上一層的 `index.html`（多人版）和 `大聯盟盲標對決單機.html`、再上一層的 `mlb-auction-單機版/index.html`（單機版網站），以及給 claude.ai 用的 `claude-artifact.html`
- `fetch_stats.py`：從 MLB.com 和 Baseball Savant 重新抓數據，更新 `pool.json`
- `fetch_cpbl.py`：從野球革命和中華職棒官網重新抓數據，更新 `pool_cpbl.json`
- `fetch_positions.py`：抓每位打者上季守過的所有守位，寫進兩個 pool 檔的 `poss` 欄位，其他數據不動。MLB 用官方 Stats API 的各守位出賽場數，中職用中職官網的各守位出賽場數；滿 30 場的守位算副守位

重新產生網站（在 `mlb-auction-site` 資料夾裡執行）：

    python3 source/build.py

換成新球季的數據：

    python3 source/fetch_stats.py 2027
    python3 source/fetch_cpbl.py 2027
    python3 source/fetch_positions.py 2027
    python3 source/build.py

`fetch_cpbl.py` 依賴野球革命目前公開的資料介面和中職官網的成績頁格式，網站改版的話可能要跟著調整。

這個資料夾跟著網站一起上傳到 Netlify 也沒關係，裡面沒有密碼或私人資料。
