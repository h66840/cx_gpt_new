from dotenv import load_dotenv

load_dotenv(".env")

from concurrent.futures import ThreadPoolExecutor  # noqa: E402
executor = ThreadPoolExecutor()

from src.config import Config  # noqa: E402
config = Config()

# 註釋掉可能導致 CUDA 錯誤的模塊初始化
# from src.core import KnowledgeBase  # noqa: E402
# knowledge_base = KnowledgeBase()

# from src.core import GraphDatabase  # noqa: E402
# graph_base = GraphDatabase()

# from src.core.retriever import Retriever  # noqa: E402
# retriever = Retriever()

# 創建空的佔位符，避免導入錯誤
knowledge_base = None
graph_base = None
retriever = None
