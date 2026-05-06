from pydantic import BaseModel, Field
from crewai.tools import tool, BaseTool
from typing import Type
from ultralytics import YOLO
import json

class ToolHelmetDetectionInput(BaseModel):
    image: str = Field(..., description="image_path")

class ToolHelmetDetection(BaseTool):
    name: str = "tools_deteksi_helmet"
    description: str = "Tools untuk deteksi yang tidak pakai helm"
    args_schema: Type[BaseModel] = ToolHelmetDetectionInput

    modelVision: YOLO = YOLO("src/pelatihanindoprima/tools/model-yolo.pt")

    def _run(self, image: str) -> str:
        result = self.modelVision(image)
        detected_objects = result[0].boxes.cls.tolist()
        class_names = result[0].names
        object_counts = {}
        person = 0
        helmet = 0
        head = 0

        for hasil in detected_objects:
            class_name = class_names[int(hasil)]
            if (class_name == "head"):
                head = head + 1
            elif (class_name == "helmet"):
                helmet = helmet + 1
            else:
                person = person + 1

        result_dict = {
        "result": f"Detected {person} person(s), {helmet} helmet(s), {head} head(s) without helmet",
        "head": head,
        "person": person,
        "helmet": helmet
        }
        return str(result_dict)