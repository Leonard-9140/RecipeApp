import git
import os

# 食譜 Repo 的網址
REPO_URL = "https://github.com/Anduin2017/HowToCook.git"
# 要儲存的本地路徑
LOCAL_REPO_PATH = "HowToCook_repo"

def clone_repo():
    """
    如果本地資料夾不存在，就從 GitHub clone 食譜 Repo。
    """
    if os.path.exists(LOCAL_REPO_PATH):
        print(f"'{LOCAL_REPO_PATH}' 資料夾已存在，跳過下載步驟。")
        print("如果需要更新食譜，請先手動刪除此資料夾。")
    else:
        print(f"正在從 {REPO_URL} 下載食譜庫...")
        try:
            git.Repo.clone_from(REPO_URL, LOCAL_REPO_PATH, branch='master')
            print("食譜庫下載完成！")
        except git.GitCommandError as e:
            print(f"下載失敗：{e}")
            print("請確認你已安裝 Git，並且網路連線正常。")

if __name__ == "__main__":
    clone_repo()