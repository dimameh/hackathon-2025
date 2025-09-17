from openai import OpenAI
import mimetypes
import json
import os
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv
from pdf2image import convert_from_path  # pyright: ignore[reportUnknownVariableType]


from openai.types.responses import Response, ResponseInputParam
from openai.types.responses.response_input_message_content_list_param import (
    ResponseInputMessageContentListParam,
)
from openai.types.responses.response_input_text_param import ResponseInputTextParam
from openai.types.responses.response_input_image_param import ResponseInputImageParam

# Load environment variables from the .env file
load_dotenv()

client = OpenAI()  # waits for the key in the environment variable OPENAI_API_KEY

def parse_doc(file_paths: list[str], instruction: str | None = None) -> dict[str, Any]:
    """
    Loads multiple PDFs/images and returns combined parsed data (JSON).
    - file_paths: list of paths to files (.pdf, .png, .jpg, .jpeg, .webp, .tiff and etc.)
    - instruction: what to extract (optional)
    """
    content_items: list[ResponseInputMessageContentListParam] = []
    temp_files: list[str] = []  # для хранения путей к временным файлам
    openai_file_ids: list[str] = []  # для хранения ID файлов OpenAI
    
    try:
        for file_path in file_paths:
            p = Path(file_path)
            if not p.is_file():
                raise FileNotFoundError(file_path)

            mime, _ = mimetypes.guess_type(p.name)
            if not mime:
                if p.suffix.lower() == ".pdf":
                    mime = "application/pdf"
                else:
                    mime = "image/png"

            if mime == "application/pdf":
                images = transform_pdf_to_images(p.as_posix())
                temp_files.extend(images)  # сохраняем пути к временным файлам
                for image in images:
                    with open(image, "rb") as f:
                        up = client.files.create(file=f, purpose="vision")
                        openai_file_ids.append(up.id)  # сохраняем ID файла
                        content_items.append([
                            cast(ResponseInputImageParam, {
                                "type": "input_image", "file_id": up.id, "detail": "auto"},
                        )])
            else:
                with open(p, "rb") as f:
                    up = client.files.create(file=f, purpose="vision")
                    openai_file_ids.append(up.id)  # сохраняем ID файла
                    content_items.append([
                        cast(
                            ResponseInputImageParam,
                            {"type": "input_image", "file_id": up.id, "detail": "auto"},
                        ),
                    ])

        base_instruction = (
            "Extract key information from ALL provided documents and return ONE combined strict JSON with fields: "
            "title (use first document's title), date (use first document's date), "
            "parties_or_patient (combine unique names), diagnoses_or_topics (combine unique items), "
            "medications_or_items (combine unique items into array) add everything that is related to medications, form, dosage, duration, instructions, "
            "recommendations (combine all recommendations into one string) and full_text (combine all texts). "
            "If a field is unknown, use null or []. Try to get as much information as possible. "
            "Because in future you will be asked to explain this information for a person who doesn't know anything about the document and he is not a doctor. "
            "You will be guiding the user on how to use the information and what to do with it. be very precise and detailed. "
        )
        if instruction:
            base_instruction = instruction + "\n\n" + base_instruction

        content: ResponseInputMessageContentListParam = [
            cast(ResponseInputTextParam, {"type": "input_text", "text": base_instruction}),
            *[item for sublist in content_items for item in sublist],
        ]

        input_items: ResponseInputParam = [
            {"type": "message", "role": "user", "content": content}
        ]
        resp: Response = client.responses.create(
            model="gpt-5",
            input=input_items,
            text={"format": {"type": "json_object"}},
        )

        text = resp.output_text

        if not text:
            raise RuntimeError("Empty response from the model")

        return json.loads(text)

    finally:
        # Clean up all temporary files and OpenAI files
        cleanup_local_files(temp_files)
        cleanup_openai_files(openai_file_ids)


def cleanup_openai_files(file_ids: list[str]) -> None:
    """
    Deletes files from OpenAI by their ID
    - file_ids: list of file IDs to delete
    """
    for file_id in file_ids:
        try:
            client.files.delete(file_id)
        except Exception as e:
            print(f"Error deleting file {file_id} from OpenAI: {e}")

def cleanup_local_files(file_paths: list[str]) -> None:
    """
    Deletes local files
    - file_paths: list of file paths to delete
    """
    for path in file_paths:
        try:
            os.remove(path)
        except Exception as e:
            print(f"Error deleting local file {path}: {e}")

def transform_pdf_to_images(file_path: str) -> list[str]:
    """
    Transforms a PDF file to a list of images.
    - file_path: path to the PDF file
    Returns: list of paths to generated image files
    """
    images = convert_from_path(file_path)
    base_path = Path(file_path).stem
    paths: list[str] = []
    for i, image in enumerate(images):
        out_path = f"{base_path}_page_{i+1}.jpg"
        image.save(out_path, "JPEG")
        paths.append(out_path)
    return paths