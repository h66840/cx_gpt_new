import os
from minio import Minio
from minio.error import S3Error

# --- MinIO 配置 ---
MINIO_ENDPOINT = "localhost:9000"  # 你的MinIO服务器地址和端口
MINIO_ACCESS_KEY = "minioadmin"     # 你的MinIO访问密钥
MINIO_SECRET_KEY = "minioadmin"     # 你的MinIO秘密密钥
MINIO_SECURE = False               # 如果你使用HTTPS，设置为True

# --- 文件和目录配置 ---
BUCKET_NAME = "labclass"  # MinIO中用于存储Word文件的桶名称
LOCAL_UPLOAD_DIR = "E:\\31276\\MIniotestData" # 本地要上传的Word文件所在的目录 (请替换为你的实际路径)
LOCAL_DOWNLOAD_DIR = "E:\\31276\\MIniodownload" # 本地下载文件保存的目录 (请替换为你的实际路径)

# --- 待上传的Word文件 ---
# 确保这个文件存在于 LOCAL_UPLOAD_DIR 路径下
UPLOAD_FILE_NAME = "agent.docx" # 你想上传的Word文件名称
OBJECT_NAME_ON_MINIO = "my_uploaded_doc.docx" # 在MinIO中存储的对象名称 (可以和本地文件名不同)

# --- 待下载的Word文件 ---
# 假设这个文件已经存在于MinIO的 BUCKET_NAME 中
DOWNLOAD_OBJECT_NAME = "my_uploaded_doc.docx" # MinIO中要下载的对象名称
LOCAL_DOWNLOADED_FILE_NAME = "downloaded_example_document.docx" # 下载到本地后的文件名称

def create_minio_client():
    """创建并返回MinIO客户端实例"""
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        print("MinIO客户端连接成功！")
        return client
    except Exception as e:
        print(f"连接MinIO失败: {e}")
        return None

def upload_word_file(client, bucket_name, local_file_path, object_name):
    """
    上传本地Word文件到MinIO桶中。
    :param client: MinIO客户端实例
    :param bucket_name: 目标桶名称
    :param local_file_path: 本地Word文件的完整路径
    :param object_name: 在MinIO中存储的对象名称
    """
    if not client:
        return

    # 检查桶是否存在，如果不存在则创建
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"桶 '{bucket_name}' 不存在，已创建。")
        else:
            print(f"桶 '{bucket_name}' 已存在。")
    except S3Error as e:
        print(f"检查/创建桶 '{bucket_name}' 失败: {e}")
        return

    # 检查本地文件是否存在
    if not os.path.exists(local_file_path):
        print(f"错误：本地文件 '{local_file_path}' 不存在。请检查路径和文件名。")
        return

    try:
        # 上传文件
        client.fput_object(
            bucket_name,
            object_name,
            local_file_path,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document" # Word文档的MIME类型
        )
        print(f"文件 '{local_file_path}' 已成功上传到 MinIO 为 '{object_name}'。")
    except S3Error as e:
        print(f"上传文件 '{local_file_path}' 失败: {e}")
    except FileNotFoundError:
        print(f"错误: 找不到文件 '{local_file_path}'。")
    except Exception as e:
        print(f"上传过程中发生未知错误: {e}")
# ... (你的 MinIO 配置和现有函数保持不变) ...

def list_objects_in_bucket(client, bucket_name):
    """
    列出MinIO桶中的所有对象。
    :param client: MinIO客户端实例
    :param bucket_name: 桶名称
    :return: 包含对象名称的列表
    """
    if not client:
        return []
    try:
        if not client.bucket_exists(bucket_name):
            print(f"桶 '{bucket_name}' 不存在。无法列出对象。")
            return []
        objects = client.list_objects(bucket_name, recursive=True)
        return [obj.object_name for obj in objects]
    except S3Error as e:
        print(f"列出桶 '{bucket_name}' 中的对象失败: {e}")
        return []
    except Exception as e:
        print(f"列出对象过程中发生未知错误: {e}")
        return []

def generate_presigned_url(client, bucket_name, object_name, expiry_seconds=3600):
    """
    为MinIO对象生成一个可访问的预签名URL。
    :param client: MinIO客户端实例
    :param bucket_name: 桶名称
    :param object_name: 对象名称
    :param expiry_seconds: URL的有效期（秒）
    :return: 预签名URL字符串
    """
    if not client:
        return None
    try:
        url = client.presigned_get_object(bucket_name, object_name, expires=expiry_seconds)
        return url
    except S3Error as e:
        print(f"生成预签名URL失败: {e}")
        return None
    except Exception as e:
        print(f"生成URL过程中发生未知错误: {e}")
        return None
def download_word_file(client, bucket_name, object_name, local_download_path):
    """
    从MinIO桶中下载Word文件到本地。
    :param client: MinIO客户端实例
    :param bucket_name: 源桶名称
    :param object_name: MinIO中要下载的对象名称
    :param local_download_path: 下载到本地后的完整文件路径
    """
    if not client:
        return

    # 检查桶是否存在
    try:
        if not client.bucket_exists(bucket_name):
            print(f"错误：桶 '{bucket_name}' 不存在。无法下载。")
            return
    except S3Error as e:
        print(f"检查桶 '{bucket_name}' 失败: {e}")
        return

    # 确保本地下载目录存在
    os.makedirs(os.path.dirname(local_download_path), exist_ok=True)

    try:
        # 下载文件
        client.fget_object(
            bucket_name,
            object_name,
            local_download_path,
        )
        print(f"文件 '{object_name}' 已成功从 MinIO 下载到 '{local_download_path}'。")
    except S3Error as e:
        if e.code == 'NoSuchKey':
            print(f"错误：MinIO中不存在对象 '{object_name}'。")
        else:
            print(f"下载文件 '{object_name}' 失败: {e}")
    except Exception as e:
        print(f"下载过程中发生未知错误: {e}")

if __name__ == "__main__":
    minio_client = create_minio_client()

    if minio_client:
        print("\n--- 开始上传文件 ---")
        local_upload_file_path = os.path.join(LOCAL_UPLOAD_DIR, UPLOAD_FILE_NAME)
        upload_word_file(minio_client, BUCKET_NAME, local_upload_file_path, OBJECT_NAME_ON_MINIO)

        print("\n--- 开始下载文件 ---")
        local_download_file_path = os.path.join(LOCAL_DOWNLOAD_DIR, LOCAL_DOWNLOADED_FILE_NAME)
        download_word_file(minio_client, BUCKET_NAME, DOWNLOAD_OBJECT_NAME, local_download_file_path)

        print("\n操作完成。")