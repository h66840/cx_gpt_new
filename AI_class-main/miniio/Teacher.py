import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
import webbrowser # 用于打开浏览器预览文件
from Test import create_minio_client,list_objects_in_bucket,LOCAL_DOWNLOAD_DIR,BUCKET_NAME, download_word_file,generate_presigned_url


# 确保 MinIO 客户端在全局或类中可用
minio_client_global_teacher = create_minio_client()

class TeacherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("教师实验报告管理端")
        self.root.geometry("800x600") # 设置窗口大小
        # 顶部信息区域
        self.top_frame = tk.Frame(root, pady=10)
        self.top_frame.pack(fill=tk.X)

        tk.Label(self.top_frame, text="实验报告概览", font=("Arial", 16, "bold")).pack()
        self.report_count_label = tk.Label(self.top_frame, text="已提交 0 份报告", font=("Arial", 12))
        self.report_count_label.pack(pady=5)

        tk.Button(self.top_frame, text="刷新并查看报告", command=self.refresh_reports, font=("Arial", 12), bg="lightgreen", padx=15, pady=8).pack(pady=10)

        # --- 分隔线 ---
        tk.Frame(root, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, padx=5, pady=5)

        # 报告列表区域
        self.report_list_frame = tk.LabelFrame(root, text="已提交的实验报告列表", font=("Arial", 12, "bold"), padx=10, pady=10)
        self.report_list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.canvas = tk.Canvas(self.report_list_frame)
        self.scrollbar = tk.Scrollbar(self.report_list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 状态信息
        self.status_label = tk.Label(root, text="", fg="blue")
        self.status_label.pack(pady=5)

        # 初始加载报告
        self.refresh_reports()

    def refresh_reports(self):
        """刷新并显示MinIO桶中的报告列表"""
        if not minio_client_global_teacher:
            messagebox.showerror("错误", "MinIO客户端未初始化，请检查配置。")
            self.report_count_label.config(text="MinIO 连接失败")
            return

        self.status_label.config(text="正在刷新报告列表...", fg="orange")
        self.root.update_idletasks()

        # 清空之前的列表
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            object_names = list_objects_in_bucket(minio_client_global_teacher, BUCKET_NAME)
            self.report_count_label.config(text=f"已提交 {len(object_names)} 份报告")

            if not object_names:
                tk.Label(self.scrollable_frame, text="目前没有提交任何实验报告。").pack(pady=20)
            else:
                tk.Label(self.scrollable_frame, text="文件名", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=2, sticky="w")
                tk.Label(self.scrollable_frame, text="操作", font=("Arial", 10, "bold")).grid(row=0, column=1, columnspan=2, padx=5, pady=2, sticky="w")

                for i, obj_name in enumerate(object_names):
                    row_num = i + 1
                    tk.Label(self.scrollable_frame, text=obj_name, anchor="w").grid(row=row_num, column=0, padx=5, pady=2, sticky="w")

                    # 下载按钮
                    tk.Button(self.scrollable_frame, text="下载",
                              command=lambda name=obj_name: self.download_selected_report(name)).grid(row=row_num, column=1, padx=5, pady=2)

                    # 预览按钮
                    tk.Button(self.scrollable_frame, text="预览",
                              command=lambda name=obj_name: self.preview_selected_report(name)).grid(row=row_num, column=2, padx=5, pady=2)
            self.status_label.config(text="报告列表刷新完成。", fg="green")
        except Exception as e:
            self.status_label.config(text=f"刷新报告列表失败: {e}", fg="red")
            messagebox.showerror("刷新错误", f"获取报告列表失败: {e}")

    def download_selected_report(self, object_name):
        """下载选定的报告文件"""
        if not minio_client_global_teacher:
            messagebox.showerror("错误", "MinIO客户端未初始化。")
            return

        # 确保下载目录存在
        os.makedirs(LOCAL_DOWNLOAD_DIR, exist_ok=True)
        local_file_path = os.path.join(LOCAL_DOWNLOAD_DIR, object_name)

        self.status_label.config(text=f"正在下载 '{object_name}'...", fg="orange")
        self.root.update_idletasks()

        try:
            download_word_file(minio_client_global_teacher, BUCKET_NAME, object_name, local_file_path)
            if os.path.exists(local_file_path): # 只有文件存在才算成功
                self.status_label.config(text=f"文件 '{object_name}' 已下载到 '{local_file_path}'。", fg="green")
                messagebox.showinfo("下载成功", f"文件 '{object_name}' 已成功下载到:\n{local_file_path}")
            else:
                self.status_label.config(text=f"下载 '{object_name}' 失败，请检查MinIO日志。", fg="red")
        except Exception as e:
            self.status_label.config(text=f"下载 '{object_name}' 失败: {e}", fg="red")
            messagebox.showerror("下载错误", f"下载文件 '{object_name}' 失败: {e}")

    def preview_selected_report(self, object_name):
        """生成预签名URL并在浏览器中预览报告"""
        if not minio_client_global_teacher:
            messagebox.showerror("错误", "MinIO客户端未初始化。")
            return

        self.status_label.config(text=f"正在为 '{object_name}' 生成预览链接...", fg="orange")
        self.root.update_idletasks()

        try:
            # 预签名URL有效期设置为1小时 (3600秒)
            presigned_url = generate_presigned_url(minio_client_global_teacher, BUCKET_NAME, object_name, expiry_seconds=3600)
            if presigned_url:
                webbrowser.open(presigned_url)
                self.status_label.config(text=f"已在浏览器中打开 '{object_name}' 的预览。", fg="green")
            else:
                self.status_label.config(text=f"生成 '{object_name}' 预览链接失败。", fg="red")
                messagebox.showerror("预览错误", f"无法生成文件 '{object_name}' 的预览链接。")
        except Exception as e:
            self.status_label.config(text=f"预览 '{object_name}' 失败: {e}", fg="red")
            messagebox.showerror("预览错误", f"预览文件 '{object_name}' 失败: {e}")

if __name__ == "__main__":
    # 在运行前，请确保将所有的 MinIO 配置和函数（包括你原始的以及上面新添加的）
    # 都粘贴到本脚本顶部，确保 MinIO 客户端能够被正确创建。
    # 教师端和学生端可以同时运行在不同的窗口中，但它们都需要独立的 Tkinter root 实例。

    teacher_root = tk.Tk()
    app = TeacherApp(teacher_root)
    teacher_root.mainloop()