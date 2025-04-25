import io
import json
from typing import List
from utils.logger import logger
from unstructured.partition.pdf import partition_pdf
from itertools import groupby

async def parse_document(file_content: bytes, file_name: str) -> List[dict]:
    """
    Parses a PDF by semantic elements (tables, titles, narrative text) rather than pages,
    preserving table continuity across page breaks and ensuring LLM readability.
    Each chunk includes file name and document title metadata.
    """
    try:
        logger.debug(f"Starting parsing for file: {file_name}. Content size: {len(file_content)} bytes.")
        
        # Create file-like object and parse directly
        file_like = io.BytesIO(file_content)
        file_like.name = file_name
        file_like.seek(0)
        elements = [el.to_dict() for el in partition_pdf(
            file=file_like,
            strategy="hi_res",
            infer_table_structure=True,
            extract_tables=True,
        )]

        if not elements:
            raise Exception("No content extracted.")

        doc_title = next(
            (e.get("text", "").strip() for e in elements if e.get("type") == "Title"),
            "Untitled Document"
        )

        # Group elements into semantic chunks
        semantic_chunks = []
        for elem_type, group in groupby(elements, key=lambda e: e.get("type", "")):
            items = list(group)
            pages = [it.get("metadata", {}).get("page_number", "unknown") for it in items]
            texts = []
            for it, p in zip(items, pages):
                txt = it.get("text", "").strip()
                if not txt:
                    continue
                if elem_type == "Table":
                    texts.append(f"[TABLE (Page {p})]\n{txt}\n[/TABLE]")
                else:
                    texts.append(txt)
            if texts:
                semantic_chunks.append({
                    "pdf_file": file_name,
                    "document_title": doc_title,
                    "element_type": elem_type or "Unknown",
                    "start_page": pages[0],
                    "end_page": pages[-1],
                    "text": f"File: {file_name}\nTitle: {doc_title}\n\n" + "\n\n".join(texts)
                })

        # Fallback for empty results
        if not semantic_chunks:
            all_text = "\n\n".join(elem.get("text", "").strip() 
                                 for elem in elements 
                                 if elem.get("text", "").strip())
            semantic_chunks.append({
                "pdf_file": file_name,
                "document_title": doc_title,
                "element_type": "Unknown",
                "start_page": "unknown",
                "end_page": "unknown",
                "text": f"File: {file_name}\nTitle: {doc_title}\n\n{all_text}"
            })

        # Debug output
        try:
            with open("/tmp/elements_grouped.json", "w") as f:
                json.dump(semantic_chunks, f, indent=2)
        except Exception as json_err:
            logger.error(f"Failed to write grouped data: {json_err}")

        return semantic_chunks

    except Exception as e:
        logger.error(f"Error parsing document '{file_name}': {e}")
        raise Exception(f"Failed to parse document '{file_name}': {e}")