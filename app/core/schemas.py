"""
Pydantic Schemas & Strict Mode JSON Schema Converter for Duolingo Speak
Single source of truth for structured LLM response validation across all providers.
"""

import copy
from typing import Any, Literal

from pydantic import BaseModel, Field


class UserFeedbackSchema(BaseModel):
    grammar_status: str = Field(
        description="Trạng thái ngữ pháp ngắn gọn (vd: 'Clean & Clear' hoặc ghi chú lỗi nhỏ)"
    )
    corrected_text: str = Field(
        description="Câu của học viên đã được sửa lỗi ngữ pháp, bảo toàn 100% ý định ban đầu"
    )
    native_phrasing: str = Field(
        description="Cách diễn đạt tự nhiên chuẩn bản xứ của câu nói đó"
    )
    duo_reaction: Literal["celebrate", "happy", "encouraging"] = Field(
        default="happy",
        description="Cảm xúc của nhân vật đại diện Duo"
    )
    grammar_explanation: str | None = Field(
        default=None,
        description="Giải thích ngắn gọn bằng tiếng Việt về lỗi ngữ pháp hoặc phát âm"
    )


class RoleplayTurnResponseSchema(BaseModel):
    natural_draft: str = Field(
        description="Suy nghĩ nháp súc tích tối đa 20 từ trước khi phản hồi"
    )
    vocab_check: str = Field(
        description="Tự kiểm tra trần từ vựng CEFR Level tối đa 20 từ"
    )
    final_response: str = Field(
        description="Câu thoại tiếng Anh chuẩn 100% của nhân vật, kết thúc bằng 1 câu hỏi mở gợi chuyện"
    )
    user_feedback: UserFeedbackSchema


class GreetingResponseSchema(BaseModel):
    natural_draft: str = Field(description="Ý tưởng mở đầu tình huống (max 20 words)")
    vocab_check: str = Field(description="Kiểm tra cấp độ CEFR (max 20 words)")
    final_response: str = Field(description="Lời mở đầu chào hỏi và câu hỏi gợi mở đầu tiên")


class QuickTranslationSchema(BaseModel):
    vietnamese_translation: str = Field(
        description="Bản dịch tiếng Việt tự nhiên, trực tiếp, không chứa văn bản râu ria"
    )


def to_strict_json_schema(model_cls: type[BaseModel]) -> dict[str, Any]:
    """
    Recursively converts a Pydantic BaseModel's JSON schema to comply with 
    OpenAI / Groq Strict Mode JSON Schema specifications.
    
    Rules enforced:
    1. additionalProperties = False on all object schemas (root & $defs / definitions).
    2. required = list(properties.keys()) covering 100% of keys on all object schemas.
    3. Transforms nullable fields with default=None to include anyOf: [..., {"type": "null"}].
    """
    schema = copy.deepcopy(model_cls.model_json_schema())

    def _transform_node(node: Any) -> Any:
        if not isinstance(node, dict):
            return node

        # Process $defs / definitions recursively
        if "$defs" in node and isinstance(node["$defs"], dict):
            for def_key, def_schema in list(node["$defs"].items()):
                node["$defs"][def_key] = _transform_node(def_schema)
        if "definitions" in node and isinstance(node["definitions"], dict):
            for def_key, def_schema in list(node["definitions"].items()):
                node["definitions"][def_key] = _transform_node(def_schema)

        # Process object node (properties or type == "object")
        if "properties" in node or node.get("type") == "object":
            node["type"] = "object"
            node["additionalProperties"] = False

            props = node.get("properties", {})
            node["required"] = list(props.keys())

            for prop_name, prop_schema in list(props.items()):
                if isinstance(prop_schema, dict) and prop_schema.get("default") is None and "default" in prop_schema:
                    if "anyOf" in prop_schema and isinstance(prop_schema["anyOf"], list):
                        has_null = any(
                            isinstance(item, dict) and item.get("type") == "null"
                            for item in prop_schema["anyOf"]
                        )
                        if not has_null:
                            prop_schema["anyOf"].append({"type": "null"})
                    elif "type" in prop_schema and prop_schema["type"] != "null":
                        old_type = prop_schema.pop("type")
                        prop_schema["anyOf"] = [{"type": old_type}, {"type": "null"}]

                props[prop_name] = _transform_node(prop_schema)

        # Process anyOf / allOf / oneOf
        for key in ("anyOf", "allOf", "oneOf"):
            if key in node and isinstance(node[key], list):
                node[key] = [_transform_node(item) for item in node[key]]

        # Process items (arrays)
        if "items" in node:
            if isinstance(node["items"], dict):
                node["items"] = _transform_node(node["items"])
            elif isinstance(node["items"], list):
                node["items"] = [_transform_node(item) for item in node["items"]]

        return node

    return _transform_node(schema)
