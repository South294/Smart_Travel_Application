from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

def validate_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

def serialize_doc(doc: dict) -> dict:
    if doc is None:
        return None
    doc["id"] = str(doc.pop("_id"))
    doc.pop("password_hash", None)
    return doc

def serialize_user(doc: dict) -> dict:
    if doc is None:
        return None
    result = doc.copy()
    result["id"] = str(result.pop("_id", ""))
    result.pop("password_hash", None)
    return result

def serialize_tour(doc: dict) -> dict:
    return serialize_doc(doc)

def serialize_booking(doc: dict) -> dict:
    return serialize_doc(doc)

def serialize_voucher(doc: dict) -> dict:
    return serialize_doc(doc)

def serialize_guide(doc: dict) -> dict:
    return serialize_doc(doc)
