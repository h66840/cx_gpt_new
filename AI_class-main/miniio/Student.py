import tkinter as tk
from tkinter import filedialog, messagebox
import os
import webbrowser # 用于打开浏览器预览文件
from Test import upload_word_file,create_minio_client, BUCKET_NAME
# 假设你的 MinIO 配置和上传函数都在这里
# ... (粘贴你原始的 MinIO 配置、create_minio_client 和 upload_word_file 函数到这里) ...

# 确保 MinIO 客户端在全局或类中可用
minio_client_global = create_minio_client()

class StudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("学生实验报告提交端")
        self.root.geometry("600x300") # 设置窗口大小

        self.selected_file_path = tk.StringVar()

        # 界面元素
        tk.Label(root, text="实验报告提交", font=("Arial", 16, "bold")).pack(pady=20)

        # 文件选择区域
        self.frame_file = tk.Frame(root)
        self.frame_file.pack(pady=10)

        tk.Label(self.frame_file, text="选择报告文件:").pack(side=tk.LEFT, padx=5)
        tk.Entry(self.frame_file, textvariable=self.selected_file_path, width=50, state='readonly').pack(side=tk.LEFT, padx=5)
        tk.Button(self.frame_file, text="浏览...", command=self.browse_file).pack(side=tk.LEFT, padx=5)

        # 上传按钮
        tk.Button(root, text="上传实验报告", command=self.upload_report, font=("Arial", 12), bg="lightblue", padx=20, pady=10).pack(pady=20)

        # 状态信息
        self.status_label = tk.Label(root, text="", fg="blue")
        self.status_label.pack(pady=5)

    def browse_file(self):
        """打开文件选择对话框，允许选择 .docx 文件"""
        file_path = filedialog.askopenfilename(
            title="选择实验报告文件",
            filetypes=[("Word Documents", "*.docx"), ("All files", "*.*")]
        )
        if file_path:
            self.selected_file_path.set(file_path)
            self.status_label.config(text="")

    def upload_report(self):
        """执行文件上传操作"""
        file_path = self.selected_file_path.get()
        if not file_path:
            messagebox.showwarning("警告", "请先选择一个文件！")
            return

        if not minio_client_global:
            messagebox.showerror("错误", "MinIO客户端未初始化，请检查配置。")
            return

        # 假设我们用文件名作为MinIO中的对象名
        # 为了区分不同学生，可以添加学号或用户名作为前缀
        object_name = os.path.basename(file_path) # 简单使用文件名
        # 实际应用中可能需要更复杂的命名规则，例如：
        # student_id = "S12345" # 假设的学生ID
        # object_name = f"{student_id}_{os.path.basename(file_path)}"

        self.status_label.config(text="正在上传中，请稍候...", fg="orange")
        self.root.update_idletasks() # 强制更新UI

        try:
            # 调用你的 MinIO 上传函数
            upload_word_file(minio_client_global, BUCKET_NAME, file_path, object_name)
            self.status_label.config(text=f"文件 '{os.path.basename(file_path)}' 上传成功！", fg="green")
        except Exception as e:
            self.status_label.config(text=f"上传失败: {e}", fg="red")
            messagebox.showerror("上传错误", f"上传过程中发生错误: {e}")

if __name__ == "__main__":
    # 请确保你的 MinIO 服务器正在运行，并且配置正确
    # 在运行前，请将上述 MinIO 配置和函数粘贴到本脚本顶部
    # 如果MinIO客户端未成功创建，学生端会提示错误。

    student_root = tk.Tk()
    app = StudentApp(student_root)
    student_root.mainloop()