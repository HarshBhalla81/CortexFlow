from pathlib import Path

from pypdf import PdfReader

from workers.base_worker import BaseWorker
from workers.document_worker import DocumentWorker


class PDFWorker(BaseWorker):

    def __init__(self):
        self.document_worker = DocumentWorker()

    def execute(self, payload):

        file_path = payload["file_path"]

        reader = PdfReader(file_path)

        full_text = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                full_text.append(text)

        document_text = "\n".join(full_text)

        document_id = Path(file_path).stem

        return self.document_worker.execute(
            {
                "id": document_id,
                "text": document_text,
                "source": file_path,
                "metadata": {
                    "file_type": "pdf",
                    "pages": len(reader.pages)
                }
            }
        )