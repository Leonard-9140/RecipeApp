# 🍲 AI食材庫存與食譜管家

這是一個使用 Python Tkinter 開發的桌面應用程式，旨在幫助使用者管理家中的食材庫存，並利用在本機端運行的 AI 語言模型，根據現有食材提供食譜建議。

## ✨ 功能特色

* **圖形化介面**：使用 Tkinter 打造，簡單明瞭。
* **完整的庫存管理**：可新增、查詢、更新、刪除食材資料（名稱、數量、購買日期、有效日期）。
* **智慧過期提醒**：自動用顏色標示已過期（標示為紅色）和即將過期（7天內，標示為橘色）的食材。
* **本機 AI 食譜生成**：整合 [Ollama](https://ollama.com/) 在使用者自己的電腦上運行 AI 模型 (本專案預設使用`gemma:2b`)，無需網路連線或 API 金鑰，保障隱私。
* **資料持久化**：使用 SQLite 資料庫儲存所有食材資料，關閉程式後資料不遺失。

## 🛠️ 技術內容 

* **程式語言**: Python 3
* **GUI 框架**: Tkinter (Python 標準函式庫)
* **資料庫**: SQLite 3 (Python 標準函式庫)
* **AI 模型運行**: [Ollama](https://ollama.com/)
* **AI 模型**: `gemma:2b`

## 🚀 安裝與設定 (Installation & Setup)

請依照以下步驟來設定並執行本專案：

1.  **Clone 專案**
    ```bash
    git clone [https://github.com/你的使用者名稱/Recipe-AI-Manager.git](https://github.com/你的使用者名稱/Recipe-AI-Manager.git)
    cd Recipe-AI-Manager
    ```

2.  **安裝 Python**
    請確保你的電腦已安裝 Python 3.10 或以上版本。(本專案使用python 3.13.7 windows版開發)

3.  **設定 Ollama**
    * 前往 [Ollama 官網](https://ollama.com/) 下載並安裝。
    * 安裝完成後，執行以下指令來下載本專案使用的 AI 模型：
      ```bash
      ollama pull gemma:2b
      ```

4.  **安裝 Python 依賴套件**
    本專案使用 `ollama` Python 套件與 AI 模型溝通。
    ```bash
    python -m pip install ollama
    ```

## 📖 如何使用 (Usage)

1.  **啟動 AI 伺服器**
    在一個獨立的終端機視窗中，執行以下指令來啟動 Ollama 背景服務：
    ```bash
    ollama serve
    ```
    **注意**：此視窗在程式運行期間必須保持開啟。

2.  **執行主程式**
    在專案目錄下，打開另一個終端機視窗，執行：
    ```bash
    python main.py
    ```

3.  **操作應用程式**
    * 在左側區域輸入食材資訊，並使用「新增」、「更新」、「刪除」按鈕來管理庫存。
    * 點擊「根據現有食材，生成食譜！」按鈕，AI 將在下方區域顯示建議的食譜。