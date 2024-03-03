import os
import json
import requests
import tempfile
from typing import List, Optional
import requests
from langchain.docstore.document import Document
from langchain.document_loaders import PyPDFLoader, UnstructuredFileLoader
from langchain.document_loaders.base import BaseLoader


class S3FileLoader(BaseLoader):
    """Loading logic for loading documents from s3."""

    def __init__(self, file_data: dict):
        """Initialize with bucket and key name."""
        self.storage_conf = json.loads(os.environ['app'])['aws']
        self.bucket = self.storage_conf['bucket']
        self.file_name = file_data["name"]
        self.file_data = file_data

    def load(self) -> List[Document]:
        """Load documents."""

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = f"{temp_dir}/{self.file_name}"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path,'wb') as tmp_file:
                print(self.storage_conf['internal'] + self.bucket + f'/{self.file_data["datastore_id"]}/' + self.file_name)
                respose = requests.get(self.storage_conf['internal'] + self.bucket + f'/{self.file_data["datastore_id"]}/' + self.file_name)
                respose.raise_for_status()
                tmp_file.write(respose.content)
            
            
            try:
                loader = CustomLoader(file_path)
                load = loader.load()
            
            except Exception:
                print('in excpetion trying custom')
                if self.file_data["mime_type"] == "application/pdf":
                    loader = PyPDFLoader(file_path)
                    load = loader.load()
                else:
                    loader = UnstructuredFileLoader(file_path)
                    load = loader.load()
            return load


class CustomLoader(BaseLoader):
    """Load text files."""

    def __init__(self, file_path: str, encoding: Optional[str] = None):
        """Initialize with file path."""
        self.file_path = file_path
        self.encoding = encoding

    def load(self) -> List[Document]:
        """Load from file path."""
        ayfie_conf = json.loads(os.environ['app'])['ayfie']
        headers = {"X-API-KEY": ayfie_conf['key']}
        metadata = {"source": self.file_path}

        with open(self.file_path, "rb") as file:
            files = {"file": file}
            r = requests.post(
                ayfie_conf['url'],
                files=files,
                headers=headers,
            )
            
            text = " ".join(r.json()["text"])
            return [Document(page_content=text, metadata=metadata)]
