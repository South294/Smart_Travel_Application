from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_db
from app.schemas.voucher import VoucherCreate, VoucherResponse
from app.routers.deps import get_current_user, get_current_admin_user
from app.routers.helpers import validate_object_id, serialize_voucher
from app.routers.helpers import validate_object_id
from typing import List

router = APIRouter()

@router.post("", response_model=VoucherResponse)
async def create_voucher(voucher: VoucherCreate, admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    existing = await db.vouchers.find_one({"code": voucher.code})
    if existing:
        raise HTTPException(status_code=400, detail="Mã voucher đã tồn tại")
    voucher_dict = voucher.model_dump()
    result = await db.vouchers.insert_one(voucher_dict)
    voucher_dict["id"] = str(result.inserted_id)
    return voucher_dict

@router.get("", response_model=List[VoucherResponse])
async def get_vouchers():
    db = get_db()
    cursor = db.vouchers.find({"is_active": True})
    vouchers = []
    async for doc in cursor:
        vouchers.append(serialize_voucher(doc))
    return vouchers

@router.post("/{code}/claim")
async def claim_voucher(code: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    voucher = await db.vouchers.find_one({"code": code, "is_active": True})
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher không tồn tại hoặc đã hết hạn")

    user_oid = validate_object_id(current_user["id"])
    user = await db.users.find_one({"_id": user_oid})
    saved_vouchers = user.get("saved_vouchers", [])

    if code in saved_vouchers:
        raise HTTPException(status_code=400, detail="Bạn đã nhận voucher này rồi")

    saved_vouchers.append(code)
    await db.users.update_one({"_id": user_oid}, {"$set": {"saved_vouchers": saved_vouchers}})
    return {"message": "Nhận voucher thành công"}

@router.get("/me", response_model=List[VoucherResponse])
async def get_my_vouchers(current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_oid = validate_object_id(current_user["id"])
    user = await db.users.find_one({"_id": user_oid})
    saved_vouchers = user.get("saved_vouchers", [])

    if not saved_vouchers:
        return []

    cursor = db.vouchers.find({"code": {"$in": saved_vouchers}})
    vouchers = []
    async for doc in cursor:
        vouchers.append(serialize_voucher(doc))
    return vouchers
