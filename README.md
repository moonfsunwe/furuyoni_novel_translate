# 散櫻亂武小說翻譯站

這是一個用於展示中日雙語網頁小說的網站。本網站支援中日文對照閱讀，並可根據需求切換單一語言模式。

## 版權聲明

- 原文連載網址：[桜降る代に小噺を](http://bfpblog.bakafire.main.jp/?eid=14)
- 日文原文版權所有 © 作 五十嵐月夜 / 原案 BakaFire / 插繪 TOKIAME
- 中文機械翻譯 SakuraLLM (14b-qwen2.5-v1.0-q6k) / ChatGPT 5.6 Luna
- 本網站內容僅供學習交流使用，嚴禁用於商業用途。若有侵權請聯繫刪除。

## 目錄結構

```
novels/
  sakura-no-kami/        # 第一部
    index.html           # 章節索引
    chapters/
      01-main/           # 第一章
        text/            # 文本檔案
          XX-zh.txt      # 中文文本
          XX-jp.txt      # 日文文本
        XX.html          # 內文頁面
        index.html       # 內文索引
```

## 如何新增章節內容

### 文本檔案

1. 在 `text` 資料夾中建立對應的中文和日文文本檔案：
   - 中文檔案命名為 `章節號-zh.txt`
   - 日文檔案命名為 `章節號-jp.txt`
   - 特別章節使用底線（如：`45_5-zh.txt`）

2. 文本格式規則：
   - 每個段落之間使用空行分隔
   - 不需要加入章節標題
   - 確保中日文本的段落數量一致

### 插入圖片

在 HTML 檔案中使用 `image-definitions` 區塊來定義圖片：

```html
<div id="image-definitions" style="display: none;">
    <div class="novel-image-def" data-insert-after-line="62">
        <figure class="novel-image">
            <img src="圖片網址">
        </figure>
    </div>
</div>
```

參數說明：
- `data-insert-after-line`：指定圖片要插入在第幾行文字之後
- `img src`：圖片的網址（支援外部連結）

JavaScript 會自動：
- 在指定的段落後插入圖片
- 處理圖片的載入和顯示
- 確保圖片在適當的位置正確顯示

## 閱讀模式

網站提供三種閱讀模式：
- 中日對照（預設）
- 僅中文
- 僅日文

可透過頁面上的設定面板切換閱讀模式。

## 瀏覽控制

- 使用頁面底部的導航按鈕切換章節
- 可透過麵包屑導航快速跳轉到目錄頁
- 支援鍵盤快捷鍵（方向鍵）控制章節切換

## 技術說明

- 使用 HTML5 和 CSS3 建構頁面
- 使用 JavaScript 實現：
  - 文本載入和解析
  - 圖片動態插入
  - 閱讀模式切換
  - 章節導航控制
- 使用 Google Fonts（Noto Sans TC/JP）顯示中日文字
- 支援響應式設計，適應不同裝置
- 純靜態網頁，可直接部署到網頁空間
