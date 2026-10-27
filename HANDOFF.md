# 交接：大聯盟盲標對決

給下一個聊天室看的。開新對話時，請它先讀這個檔案，再讀 `README.md` 和 `source/README.md`。

更新日期：2026-10-25（下午）

## 專案是什麼

一個雙人棒球選秀遊戲（MLB 或中職都能選），做成單一個 HTML 網頁：

1. 球員一個一個隨機抽出，事先不知道會抽到誰。兩名玩家用各自的預算競標，不加價的那方就放棄。
2. 選秀後可以交換球員 3 次。
3. 接著模擬比賽，有文字轉播，最後才公布勝負。

玩法有三種：單人對電腦、同一台輪流玩、線上對戰（Firebase）。

## 檔案位置

- 主資料夾：`/Users/simba/Downloads/mlb-auction-site`（Git 專案，分支 `main`）
- 單機版網站：`/Users/simba/Downloads/mlb-auction-單機版/index.html`（由 build.py 產生，不在 Git 裡）
- claude.ai 版：https://claude.ai/artifact/6LHQgeVKQTbXF9LFseiNrE（db + user capabilities）
- 舊版資料夾：`Downloads` 裡的 `mlb-auction-site 2/3/4` 和 `mlb-auction-site.zip`，都已過時，不要用

## 最重要的規則

**只改 `source/template.html`（或 pool 檔），改完執行 `python3 source/build.py`。**

`index.html`、`大聯盟盲標對決單機.html`、`source/claude-artifact.html`、`../mlb-auction-單機版/index.html` 都是產生出來的檔案，直接改的話下次重建會被蓋掉。

建置旗標：
- 多人版：`window.STANDALONE=true`，並載入 `firebase-config.js`
- 單機版：再加上 `window.OFFLINE=true`。首頁會顯示「線上對戰・敬請期待」

## 目前狀態

- 網站：GitHub Pages，從 `main` 根目錄發布，網址是 https://simba0812.github.io/MLB/ （英超版在 `/epl/`）。Firebase 的已授權網域要有 `simba0812.github.io`。
- GitHub：`simba0812/mlb`。2026-10-25 起 repo 根目錄就是 `mlb-auction-site` 的內容（原本根目錄只有單機版 `index.html`，`source/` 曾被刪掉，已從使用者上傳的檔案還原）。
- `source/build.py` 原本的檔案遺失，以 Git 歷史版本為底補上「產生 `../mlb-auction-單機版/index.html`」那幾行；四個產生的網頁都和使用者手上的版本逐位元相同。
- Firebase 專案 `mlbb-e98d2`，設定已填進 `firebase-config.js`。apiKey 是公開識別碼，不是密碼。
- `firestore.rules`（2026-10-26 版）：只有入座的玩家能改遊戲；其他人只能坐上空的 B 座位（只改 `seats.1`、時間戳記和 `lease`）或拿 `lease`；欄位限定在已知的那幾個，`state` 小於 200 KB。規則沒在模擬器測過（雲端環境不允許執行模擬器），是逐一對照程式裡每個寫入點確認的。
- 使用者還要自己做的事：
  - 在 Firebase 重新發布 `firestore.rules`（如果還是舊規則）
  - 把 `mlb-auction-site` 拖到 Netlify，再用 `mlb-auction-單機版` 另外建一個 Netlify 網站
  - 可以順便刪掉舊資料夾

## NBA 盲標對決（nba/）

- 2026-10-27 新增，中英文都有，玩法有單人、同一台輪流玩、線上對戰。說明在 `nba/source/README.md`。
- 以棒球版 template 為底組成（選秀、交易、線上房間都沿用），籃球的部分另外寫。之後如果棒球版的線上程式修了 bug，NBA 版也要一起改。
- 數據：NBA.com 會擋 GitHub 的主機，所以用 Basketball Reference，透過 `.github/workflows/fetch-nba.yml` 抓取。
- 線上對戰：房間放在同一個 `rooms` 集合，用 `cfg.game='nba'` 區分。節間決定存成 `dec[key]["節次:隊伍"]`，兩隊可以同時決定。
- 測試：jsdom 跑過中英文、單人／同一台、單場／三戰兩勝／七戰四勝；也用模擬的 Firestore 開兩個分頁，跑完一輪三戰兩勝的線上對戰，兩邊結果一致。

## 動漫大亂鬥（anime/）

- 2026-10-25 新增，中英文都有，玩法有單人對電腦和同一台輪流玩。說明在 `anime/source/README.md`。
- 角色數值放在 `anime/source/roster.json`，是依原作自訂的。綜合評價會在開啟網頁時，用固定種子跑兩兩單挑，依勝率算出來。
- 不能用官方圖片：網站是公開的。

## 英超版（epl/）

- 2026-10-25 新增，英文介面，玩法只有單人對電腦和同一台輪流玩，沒有線上對戰。說明在 `epl/source/README.md`。
- 和棒球版一樣：只改 `epl/source/template.html`，改完執行 `python3 epl/source/build.py`。
- 數據是 2025-26 FPL 的整季數據，從 vaastav/Fantasy-Premier-League 的 GitHub 存檔抓取（雲端環境只連得到 GitHub）。
- 賽制：單場（淘汰賽，平手就踢延長賽、再踢 PK）、主客場兩回合（看總比分）、三戰兩勝。
- 每隊 13 人（11 名先發加 2 名替補），各位置人數自己決定，只要能排出合法先發就好（`canComplete`）。有五段戰術，比賽中切換時記錄在 `gm.tac` 的 `{t:分鐘序號, i:隊伍, v:戰術}`，重播時會從同一分鐘開始套用。比賽畫面有 SVG 球場和 xG 走勢圖。
- 測試：jsdom 跑過三種賽制的完整流程（選秀、交易、排陣容、換人決定、延長賽、PK），重播結果一致；Playwright 截過桌機和手機畫面，沒有出現橫向捲動。還沒在真的手機上測過。

## 已做好的功能

- **聯盟與名額**
  - MLB 668 人、中職 197 人，都是 2026 季數據。
  - 賽前可以選名額：先發 3–6（七戰四勝至少 4）、中繼 2–8、終結者 1–3、板凳打者 0–3。
  - 賽制：單場、三戰兩勝、七戰四勝。大約 50 支籤，預算 200。
- **數據分級**：傳統數據（含 OPS）和 Savant 數據都只分 PR90+ 金框、PR75+ 紅框、PR50 綠框三級。
- **總評**：按同類球員（打者 / 先發 / 中繼＋終結者）的排名換算成百分位，再套 `OVR_CURVE`。二刀流取兩者較高的再加 4。
- **守備**：有 OAA/UZR 和捕手框界值，`computeDef` 換算成同一個尺度。任何守位的打者都能放 DH。
- **多重守位**（2026-10-25）：pool 裡每位打者都有 `poss` 欄位，由 `source/fetch_positions.py` 產生。`poss` 是 `{守位: 出賽場數}`；中職另外有 `pinn`（`{守位: 局數}`），資料來自野球革命，因為中職官網只讓台灣連線。`setAlt` 會把主守位以外、MLB 滿 30 場或中職滿 150 局的守位列進 `p.alt`，作為副守位。資料由 GitHub Actions 的 `fetch-positions.yml` 抓取，改到 `fetch_positions.py` 並推上去就會自動重抓。`openSlotsFor` 會依序放：主守位 → 副守位 → DH → 板凳。副守位的守備值用 `pdef`，也就是那個守位本身的跑分。`computeDef` 會先把它拉回平均：乘上主守位場數，除以（副守位場數 + 60），再用和主守位相同的尺度換算，存進 `p.defAt`。抓不到數據時才退回：正的乘 0.7、負的不變；牽涉捕手或主守位是 DH 的，一律算 -2；沒有 `poss` 時，行為和以前完全相同（已用固定 seed 比對過）。**目前的 pool 還沒有 `poss`，因為雲端環境連不上 MLB 和中職官網，要在 Mac 上執行一次 `fetch_positions.py` 才會生效。**
- **投手**：
  - 有體力條，前三場的用球數會造成疲勞。
  - 先發輪值休息天數：`restN`。
  - 中繼優先上牛棚投手。
  - 有球速（中職沒有公開數據）。
- **賽前**：排打序（點兩個棒次互換）、選先發。
- **比賽中**：關鍵時刻詢問是否換投、代打，也可以選「自動調度」。
- **系列賽**：累計打擊率、OPS、防禦率，最後選出 MVP。
- **線上對戰**：
  - 房號 4 碼。
  - 賽前調整陣容 3 分鐘，時間到自動確認。比賽中的決定 1 分鐘，時間到自動選擇。
  - 房間 3 天後過期，網站內建清除；也可以另外開 Firestore TTL（欄位 `expireAt`）。
- **語言**：中文／英文，存在 localStorage 的 `mlbLang`。線上兩人可以用不同語言，結果一樣。
- **介面**：
  - 手機和平板版面。
  - 同一台輪流玩時，選秀畫面分成五欄：名單｜競標｜球員卡｜競標｜名單。
  - 選秀畫面不用捲動就看得到競標區。

## 技術重點（改程式前要知道）

- **模擬**：log5 打席模型。打者對照 `LG`，投手對照 `LGP`。另外套用球場係數、疲勞、捕手框界值。守備會把安打變出局（d/260）或出局變安打（d/520）。
- **決定性**：比賽由 seed（mulberry32）加上玩家的決定重播，所有裝置結果相同。改模擬時要保持亂數的消耗順序一致。中英文的轉播文字也消耗相同的亂數。
- **手機效能**（2026-10-25）：`hydrate` 只有在聯盟改變時才呼叫 `setLeague`（重建數據表在手機上要花幾十毫秒）；`render()` 會把目前的畫面寫在 `.wrap` 的 class 上（`s-draft`、`s-pick`、`s-game`、`duo`），CSS 不再使用 `.wrap:has(...)`；`pick` 畫面只有在 picks 或 rev 改變時才重畫；Noto Sans TC 只載入 400 和 700 兩種字重。
- **暫停**：遇到需要玩家決定時，`simGame` 會丟出 `{pause, partial}`。`play()` 會先檢查決定是否已經到了；這是之前修好的手機卡死問題，不要拿掉。
- **線上資料**：
  - Firestore 的 `rooms/{code}` 有這些欄位：seats、setup、cfg、picks、dec、state（JSON 字串）、rev、deck0、exp。
  - 抽籤順序用 `deckDiff` / `deckFrom` 壓縮。寫入透過 `dbWrite` 排隊處理。
  - 回到前景（visibilitychange）時會重新同步。
- **翻譯**：用 `TR(zh,en)`。不要用 `L`，`L` 是 lot 變數。
- **中職 id**：是字串（前綴 `c`），所以要用 `pid()` 轉換，不要用 `+value`。
- **預期得分**：MLB 每隊每場約 4.6 分，中職約 4.1 分。調整後要重新測一下。

## 測試方式

- 用 jsdom 24.1.3 模擬瀏覽器，搭配假的 db / Firebase 資料。
- 也可以用內建瀏覽器預覽：暫時建立 `.claude/launch.json`，用 `python3 -m http.server 8765`。測完要刪掉這個檔（`.claude/` 已經在 `.gitignore` 裡）。
- 還沒在真的手機或平板上測過。

## 更新數據（新球季）

    python3 source/fetch_stats.py 2027
    python3 source/fetch_cpbl.py 2027
    python3 source/fetch_positions.py 2027
    python3 source/build.py

## 使用者偏好

- 用繁體中文溝通，遊戲介面同時有中英文。
- 雲端對話（claude.ai/code）：Claude 改完後 commit 並 push 到指定的 `claude/...` 分支，使用者在 GitHub 合併到 `main`，再用 GitHub Desktop 拉回 Mac。Claude 不直接動 `main`。
- 本機對話：使用者自己 commit 和 push（用 GitHub Desktop）。
- 不要動家目錄 `/Users/simba` 那個 Git 專案。
- 使用者說「先不要改，只是詢問」時，就只回答問題。
- 計費無法由我控制（使用者曾要求從 cloud session credit 扣款）。
