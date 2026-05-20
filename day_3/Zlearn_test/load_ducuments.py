import os
from typing import List

import dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

dotenv.load_dotenv()

documents: List = []
file_folder = 'D:\pythonFile\DeepLearning\day_3\data'
for filename in os.listdir(file_folder):
    file_path = os.path.join(file_folder, filename)
    print(file_path)

    loader = PyMuPDFLoader(file_path)
    documents.extend(loader.load())



text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = text_splitter.split_documents(documents)

texts: List = []
metadates : List = []
for chunk in chunks:
    texts.append(chunk.page_content)
    metadates.append(chunk.metadata)

embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(name = "llmops")

vector_store = PineconeVectorStore(embedding=embeddings, index=index)

vector_store.add_texts(texts, metadatas=metadates, namespace="ReID")
