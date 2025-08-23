import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import database
# import ollama # 我們不再直接使用這個來建立 LLM 物件，LangChain會處理
import threading
from datetime import datetime, timedelta

# --- 導入 LangChain 和 ChromaDB 相關模組 ---
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
# --- 【修正第一處】導入 LangChain 提供的 Ollama 類別 ---
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ChromaDB 資料庫路徑
CHROMA_DB_PATH = "chroma_db"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        database.initialize_db()
        self.title("我的食材庫存與食譜管家")
        self.geometry("950x800")
        
        # --- 初始化 RAG 相關元件 ---
        self.rag_chain = self.setup_rag_chain()

        # (介面設定程式碼和之前一樣，折疊起來)
        style = ttk.Style()
        style.configure("Expired.Treeview", foreground="red")
        style.configure("ExpiringSoon.Treeview", foreground="orange")
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="both", expand=True)
        bottom_frame = ttk.LabelFrame(main_frame, text="AI 食譜建議", padding="10")
        bottom_frame.pack(fill="both", expand=True, pady=(10, 0))
        controls_frame = ttk.LabelFrame(top_frame, text="食材資料", padding="10")
        controls_frame.pack(side="left", fill="y", padx=(0, 10), pady=5)
        ttk.Label(controls_frame, text="食材名稱:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ttk.Entry(controls_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(controls_frame, text="數量:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.quantity_entry = ttk.Entry(controls_frame)
        self.quantity_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(controls_frame, text="購入日期 (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.purchase_date_entry = ttk.Entry(controls_frame)
        self.purchase_date_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(controls_frame, text="有效日期 (YYYY-MM-DD):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.expiry_date_entry = ttk.Entry(controls_frame)
        self.expiry_date_entry.grid(row=3, column=1, padx=5, pady=5)
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=10)
        self.add_button = ttk.Button(buttons_frame, text="新增食材", command=self.add_new_ingredient)
        self.add_button.pack(side="left", padx=5)
        self.update_button = ttk.Button(buttons_frame, text="更新選取", command=self.update_selected_ingredient)
        self.update_button.pack(side="left", padx=5)
        self.delete_button = ttk.Button(buttons_frame, text="刪除選取", command=self.delete_selected_ingredient)
        self.delete_button.pack(side="left", padx=5)
        display_frame = ttk.LabelFrame(top_frame, text="現有庫存", padding="10")
        display_frame.pack(side="right", fill="both", expand=True, pady=5)
        columns = ("id", "name", "quantity", "purchase_date", "expiry_date")
        self.tree = ttk.Treeview(display_frame, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="食材名稱")
        self.tree.heading("quantity", text="數量")
        self.tree.heading("purchase_date", text="購入日期")
        self.tree.heading("expiry_date", text="有效日期")
        self.tree.column("id", width=40, stretch=tk.NO) 
        self.tree.column("name", width=150)
        self.tree.column("quantity", width=80)
        self.tree.column("purchase_date", width=120)
        self.tree.column("expiry_date", width=120)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.generate_button = ttk.Button(bottom_frame, text="根據現有食材，生成食譜！", command=self.start_recipe_generation_thread)
        self.generate_button.pack(pady=5)
        self.recipe_display = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD, height=15)
        self.recipe_display.pack(fill="both", expand=True, pady=5)
        self.recipe_display.insert(tk.END, "點擊上方按鈕，AI 將會在此顯示建議的食譜...")
        self.recipe_display.config(state="disabled")
        self.populate_treeview()

    def setup_rag_chain(self):
        try:
            embeddings = OllamaEmbeddings(model="gemma:2b")
            vectorstore = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

            template = """
            你是一位專業的家常菜廚師。請嚴格根據我提供的【參考食譜】來回答問題。
            請整合參考食譜中的資訊，並根據使用者擁有的【現有食材】，設計一道料理的詳細食譜。
            如果參考食譜中的資訊不足，請基於你的專業知識做補充，但主要內容必須來自參考食譜。
            請用標準的繁體中文回答。

            【參考食譜】
            {context}

            【現有食材】
            {question}

            請根據以上資訊，提供一道菜的完整食譜（包含菜名、所需材料、詳細步驟）：
            """
            prompt = PromptTemplate.from_template(template)

            # --- 【修正第二處】使用從 langchain_community 導入的 Ollama 類別 ---
            llm = Ollama(model="gemma:2b")

            rag_chain = (
                {"context": retriever, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
            print("RAG chain 設定完成！")
            return rag_chain
        except Exception as e:
            print(f"設定 RAG chain 時發生錯誤: {e}")
            messagebox.showerror("啟動錯誤", f"無法初始化 AI 功能模組。\n請確認 '{CHROMA_DB_PATH}' 資料庫已成功建立。\n錯誤訊息: {e}")
            return None

    def generate_recipe(self):
        if not self.rag_chain:
            self.after(0, self.update_recipe_display, "AI 功能模組未成功初始化，無法生成食譜。")
            return

        try:
            ingredients_list = database.get_all_ingredients()
            if not ingredients_list:
                self.after(0, self.update_recipe_display, "庫存是空的，請先新增一些食材！")
                return

            question = "、".join([item[1] for item in ingredients_list])
            recipe_text = self.rag_chain.invoke(question)
            
            self.after(0, self.update_recipe_display, recipe_text)

        except Exception as e:
            error_message = f"生成食譜時發生錯誤：\n{e}\n\n請確認 Ollama 服務正在本機端正常執行。"
            self.after(0, self.update_recipe_display, error_message)
        finally:
            self.after(0, lambda: self.generate_button.config(state="normal"))

    # (其他所有函式都和之前一樣，無需修改，折疊起來)
    def start_recipe_generation_thread(self):
        self.generate_button.config(state="disabled")
        self.recipe_display.config(state="normal")
        self.recipe_display.delete("1.0", tk.END)
        self.recipe_display.insert(tk.END, "正在我們的專業食譜庫中搜尋靈感，請稍候...")
        self.recipe_display.config(state="disabled")
        thread = threading.Thread(target=self.generate_recipe)
        thread.start()
    def update_recipe_display(self, text):
        self.recipe_display.config(state="normal")
        self.recipe_display.delete("1.0", tk.END)
        self.recipe_display.insert(tk.END, text)
        self.recipe_display.config(state="disabled")
    def populate_treeview(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        ingredients_list = database.get_all_ingredients()
        today, seven_days_later = datetime.now().date(), datetime.now().date() + timedelta(days=7)
        for item in ingredients_list:
            expiry_date_str, tag_to_use = item[4], ""
            try:
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                if expiry_date < today: tag_to_use = "Expired"
                elif expiry_date <= seven_days_later: tag_to_use = "ExpiringSoon"
            except ValueError: pass
            self.tree.insert("", tk.END, values=item, tags=(tag_to_use,))
    def add_new_ingredient(self):
        name = self.name_entry.get()
        if not name: messagebox.showwarning("輸入錯誤", "請至少輸入食材名稱！"); return
        database.add_ingredient(name, self.quantity_entry.get(), self.purchase_date_entry.get(), self.expiry_date_entry.get())
        self.clear_entries(); self.populate_treeview()
    def update_selected_ingredient(self):
        selected_item = self.tree.focus()
        if not selected_item: messagebox.showwarning("選取錯誤", "請先在列表中選取一個食材！"); return
        item_values = self.tree.item(selected_item, "values")
        database.update_ingredient(item_values[0], self.name_entry.get(), self.quantity_entry.get(), self.purchase_date_entry.get(), self.expiry_date_entry.get())
        self.clear_entries(); self.populate_treeview()
    def delete_selected_ingredient(self):
        selected_item = self.tree.focus()
        if not selected_item: messagebox.showwarning("選取錯誤", "請先在列表中選取一個食材！"); return
        item_values = self.tree.item(selected_item, "values")
        if messagebox.askyesno("確認刪除", f"確定要刪除食材 '{item_values[1]}' 嗎？"):
            database.delete_ingredient(item_values[0]); self.clear_entries(); self.populate_treeview()
    def on_item_select(self, event):
        selected_item = self.tree.focus()
        if not selected_item: return
        item_values = self.tree.item(selected_item, "values")
        self.clear_entries()
        self.name_entry.insert(0, item_values[1]); self.quantity_entry.insert(0, item_values[2])
        self.purchase_date_entry.insert(0, item_values[3]); self.expiry_date_entry.insert(0, item_values[4])
    def clear_entries(self):
        self.name_entry.delete(0, tk.END); self.quantity_entry.delete(0, tk.END)
        self.purchase_date_entry.delete(0, tk.END); self.expiry_date_entry.delete(0, tk.END)

if __name__ == "__main__":
    app = App()
    app.mainloop()