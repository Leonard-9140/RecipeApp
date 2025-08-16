import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import database
import ollama
import threading
from datetime import datetime, timedelta # 導入日期時間處理模組

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        database.initialize_db()

        self.title("我的食材庫存與食譜管家")
        self.geometry("950x800")

        # --- 設定 Treeview 的顏色標籤 ---
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

    def populate_treeview(self):
        """從資料庫讀取資料，檢查日期並用顏色標示，最後顯示在列表上。"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        ingredients_list = database.get_all_ingredients()
        
        today = datetime.now().date()
        seven_days_later = today + timedelta(days=7)

        for item in ingredients_list:
            expiry_date_str = item[4]
            tag_to_use = ""

            try:
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                if expiry_date < today:
                    tag_to_use = "Expired"
                elif expiry_date <= seven_days_later:
                    tag_to_use = "ExpiringSoon"
            except ValueError:
                pass

            self.tree.insert("", tk.END, values=item, tags=(tag_to_use,))
    
    def start_recipe_generation_thread(self):
        self.generate_button.config(state="disabled")
        self.recipe_display.config(state="normal")
        self.recipe_display.delete("1.0", tk.END)
        self.recipe_display.insert(tk.END, "正在與 AI 廚師溝通中，請稍候...")
        self.recipe_display.config(state="disabled")
        thread = threading.Thread(target=self.generate_recipe)
        thread.start()

    def generate_recipe(self):
        """使用 gemma:2b 模型並優化 Prompt 來生成食譜。"""
        try:
            ingredients_list = database.get_all_ingredients()
            if not ingredients_list:
                self.after(0, self.update_recipe_display, "庫存是空的，請先新增一些食材！")
                return

            formatted_ingredients = "、".join([f"{item[1]} ({item[2]})" for item in ingredients_list])
            
            prompt = (
                f"你是一位專業且精通多國語言的廚師。請嚴格使用「標準的繁體中文 (Traditional Chinese, zh-TW)」進行回覆，確保沒有任何亂碼或無法辨識的字元。"
                f"根據以下我擁有的食材，設計一到兩道適合廚房新手的家常料理食譜。"
                f"請為每道菜提供清晰的【食材清單】和【步驟說明】。\n\n"
                f"我擁有的食材清單：{formatted_ingredients}"
            )
            
            response = ollama.chat(
                model='gemma:2b',
                messages=[{'role': 'user', 'content': prompt}]
            )
            recipe_text = response['message']['content']
            
            self.after(0, self.update_recipe_display, recipe_text)

        except Exception as e:
            error_message = f"生成食譜時發生錯誤：\n{e}\n\n請確認 Ollama 服務正在本機端正常執行。"
            self.after(0, self.update_recipe_display, error_message)
        finally:
            self.after(0, lambda: self.generate_button.config(state="normal"))

    def update_recipe_display(self, text):
        self.recipe_display.config(state="normal")
        self.recipe_display.delete("1.0", tk.END)
        self.recipe_display.insert(tk.END, text)
        self.recipe_display.config(state="disabled")

    def add_new_ingredient(self):
        name = self.name_entry.get()
        quantity = self.quantity_entry.get()
        p_date = self.purchase_date_entry.get()
        e_date = self.expiry_date_entry.get()
        if not name:
            messagebox.showwarning("輸入錯誤", "請至少輸入食材名稱！")
            return
        database.add_ingredient(name, quantity, p_date, e_date)
        self.clear_entries()
        self.populate_treeview()
        
    def update_selected_ingredient(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("選取錯誤", "請先在列表中選取一個食材！")
            return
        item_values = self.tree.item(selected_item, "values")
        selected_id = item_values[0]
        database.update_ingredient(selected_id, self.name_entry.get(), self.quantity_entry.get(), self.purchase_date_entry.get(), self.expiry_date_entry.get())
        self.clear_entries()
        self.populate_treeview()
        
    def delete_selected_ingredient(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("選取錯誤", "請先在列表中選取一個食材！")
            return
            
        item_values = self.tree.item(selected_item, "values")
        selected_id = item_values[0]

        if messagebox.askyesno("確認刪除", f"確定要刪除食材 '{item_values[1]}' 嗎？"):
            database.delete_ingredient(selected_id)
            self.clear_entries()
            self.populate_treeview()
            
    def on_item_select(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            return
        item_values = self.tree.item(selected_item, "values")
        self.clear_entries()
        self.name_entry.insert(0, item_values[1])
        self.quantity_entry.insert(0, item_values[2])
        self.purchase_date_entry.insert(0, item_values[3])
        self.expiry_date_entry.insert(0, item_values[4])
        
    def clear_entries(self):
        self.name_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.purchase_date_entry.delete(0, tk.END)
        self.expiry_date_entry.delete(0, tk.END)

if __name__ == "__main__":
    app = App()
    app.mainloop()