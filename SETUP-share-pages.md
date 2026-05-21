# 技能分享預覽頁設定指南

讓 LINE / FB / IG / Threads / X / WhatsApp 等平台分享單一服務時，預覽卡顯示「**該服務**」的標題、提供者、介紹，而不是整個公會的通用介紹。

---

## 這套機制怎麼運作（30 秒理解）

```
       Google Sheet「上架清單」                                
                  ↓                                            
   GitHub Action（每 5 分鐘自動跑 ─ 急用可手動觸發）                              
                  ↓                                            
        generate-skill-pages.py                                
                  ↓                                            
    skill/<服務名>.html × N 個檔                                 
        （每個有專屬 OG meta）                                    
                  ↓                                            
   commit & push 回 GitHub Pages                              
                  ↓                                            
       LINE 抓到 → 顯示專屬預覽                                   
       使用者點到 → JS 自動轉到首頁打開 modal                       
```

---

## 一次性設定（只要做這 3 步）

### Step 1. 把 3 個檔案推上 GitHub

把妳資料夾裡這 3 個檔上傳到 `hannahchen6134/skillmarket` repo 的根目錄（保持資料夾結構）：

- `index.html`（已改好分享按鈕邏輯）
- `generate-skill-pages.py`（生成腳本）
- `.github/workflows/generate-pages.yml`（GitHub Action 設定）

**上傳方式**：到 https://github.com/hannahchen6134/skillmarket → Add file → Upload files → 拖檔進去 → Commit。

> ⚠️ `.github/workflows/` 是 GitHub 規定的特殊路徑，**結構必須正確**。如果網頁上傳會把資料夾壓平，可用：拖檔時把 `.github` 整個資料夾拉進去（Chrome / Edge 支援），或在 GitHub 網頁先建立 `.github/workflows/generate-pages.yml` 路徑再貼內容。

### Step 2. 開啟 Action 寫入權限

到 https://github.com/hannahchen6134/skillmarket/settings/actions

往下找到 **Workflow permissions** → 選 **「Read and write permissions」** → 按 Save。

不開這個的話 GitHub Action 沒辦法把生成的檔案 commit 回 repo。

### Step 3. 第一次手動觸發

到 https://github.com/hannahchen6134/skillmarket/actions/workflows/generate-pages.yml

→ 右邊 **Run workflow** → 選 `main` → 綠色 **Run workflow** 按鈕。

大概 30 秒~ 1 分鐘後跑完，回到 Actions 頁面會看到綠勾。這時 `skill/` 資料夾就有所有服務的 HTML 檔了。

---

## 平常怎麼運作

1. 妳上架新服務 → 整理到「上架清單」分頁 → L 欄打勾 ✅
2. **妳網站上的卡片清單立刻顯示**（這一直都是即時的，沒有變）
3. 給 LINE / FB / IG 抓 OG 用的分享預覽頁，大約 **5–15 分鐘內**自動生成
4. 之後分享該服務連結，預覽卡就會顯示專屬內容

**剛上架想馬上分享？** 到 Actions 頁面手動 Run workflow，1–2 分鐘內生效（比等排程快）。

> ⚠️ GitHub 對 schedule 排程有「整點附近會延遲」的特性，所以雖然設定每 5 分鐘一次，實際延遲可能 5–15 分鐘。要立刻看到效果就用手動觸發。

---

## 怎麼確認有生效

1. 上架一筆新服務後，跑完 Action
2. 在瀏覽器網址列直接打：`https://hannahchen6134.github.io/skillmarket/skill/`（後面接 slug，或先 git pull 看檔名）
3. 該頁應該會立刻自動跳回首頁打開 modal — 代表轉跳邏輯正確
4. 用 LINE / FB 的「分享」貼上 `skill/xxx.html` 網址，預覽卡標題應該變成「服務名 · by 提供者」

最快的測試方式：**用 Facebook 偵錯工具**
👉 https://developers.facebook.com/tools/debug/
貼 `https://hannahchen6134.github.io/skillmarket/skill/<slug>.html` 進去 → 看 og:title、og:description 是不是該服務的

---

## 常見問題

**Q: GitHub Action 跑失敗顯示紅 X 怎麼辦？**

點進去看 log。最常見原因：
- 步驟 2 沒開 Read and write permissions
- 試算表的「共用」沒設成「知道連結的任何人可檢視」

**Q: 我改了標題，舊的分享連結會壞嗎？**

會。標題變了 → slug 變了 → 舊 URL 變成 404。腳本會自動清掉沒在試算表裡的舊頁面。如果妳已經把舊 URL 分享到很多地方了，**不要改標題**。

**Q: 預覽圖（縮圖）也要客製化怎麼辦？**

目前所有服務共用 `starry-hall.jpg`。如果想要每個服務有自己的預覽圖，回頭跟我說一聲，我會幫妳加 Phase 2（用 Pillow 自動生成羊皮紙風格的服務卡圖片）。

**Q: 想停掉這套機制？**

把 `.github/workflows/generate-pages.yml` 刪掉就好。`skill/` 資料夾的 HTML 也可以一起刪掉。`index.html` 的分享按鈕 URL 改回 `#s/<title>` 即可。
