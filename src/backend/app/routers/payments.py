import hashlib
import hmac
from datetime import datetime
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.db.mongodb import get_db
from app.routers.deps import get_current_user
from app.routers.helpers import validate_object_id
from app.schemas.payment import PaymentCreateRequest, PaymentCreateResponse

router = APIRouter()


def _build_signature(params: dict) -> str:
    query = urlencode(sorted(params.items()))
    return hmac.new(
        settings.VNPAY_HASH_SECRET.encode("utf-8"),
        query.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()


def _has_vnpay_config() -> bool:
    return bool(settings.VNPAY_TMN_CODE and settings.VNPAY_HASH_SECRET and settings.VNPAY_RETURN_URL)


@router.post("/vnpay/create", response_model=PaymentCreateResponse)
async def create_vnpay_payment(
    payload: PaymentCreateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    if not _has_vnpay_config():
        raise HTTPException(
            status_code=503,
            detail="Chưa cấu hình VNPay Sandbox. Hãy điền VNPAY_TMN_CODE và VNPAY_HASH_SECRET trong backend/.env.",
        )

    db = get_db()
    booking_oid = validate_object_id(payload.booking_id)
    booking = await db.bookings.find_one({"_id": booking_oid, "user_id": current_user["id"]})
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy booking của bạn")
    if booking.get("payment_status") == "paid":
        raise HTTPException(status_code=400, detail="Booking này đã được thanh toán")

    txn_ref = f"ST{str(booking_oid)}{int(datetime.utcnow().timestamp())}"
    params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.VNPAY_TMN_CODE,
        "vnp_Amount": str(int(round(float(booking.get("total_amount", 0)) * 100))),
        "vnp_CreateDate": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        "vnp_CurrCode": "VND",
        "vnp_IpAddr": request.client.host if request.client else "127.0.0.1",
        "vnp_Locale": "vn",
        "vnp_OrderInfo": f"Thanh toan booking {payload.booking_id}",
        "vnp_OrderType": "other",
        "vnp_ReturnUrl": settings.VNPAY_RETURN_URL,
        "vnp_TxnRef": txn_ref,
    }
    params["vnp_SecureHash"] = _build_signature(params)
    payment_url = f"{settings.VNPAY_PAYMENT_URL}?{urlencode(params)}"

    await db.bookings.update_one(
        {"_id": booking_oid},
        {"$set": {"payment_status": "pending", "payment_provider": "vnpay", "payment_reference": txn_ref}},
    )
    return PaymentCreateResponse(mode="vnpay_sandbox", payment_url=payment_url, booking_id=payload.booking_id)


@router.get("/vnpay/return")
async def vnpay_return(request: Request):
    params = dict(request.query_params)
    received_hash = params.pop("vnp_SecureHash", "")
    params.pop("vnp_SecureHashType", None)
    if not received_hash or not _has_vnpay_config() or not hmac.compare_digest(received_hash, _build_signature(params)):
        return RedirectResponse(f"{settings.PAYMENT_FRONTEND_URL}?payment=invalid")

    txn_ref = params.get("vnp_TxnRef", "")
    response_code = params.get("vnp_ResponseCode", "99")
    db = get_db()
    booking = await db.bookings.find_one({"payment_reference": txn_ref})
    if not booking:
        return RedirectResponse(f"{settings.PAYMENT_FRONTEND_URL}?payment=missing")

    paid = response_code == "00"
    await db.bookings.update_one(
        {"_id": booking["_id"]},
        {"$set": {
            "payment_status": "paid" if paid else "failed",
            "status": "confirmed" if paid else "pending",
            "payment_response_code": response_code,
            "paid_at": datetime.utcnow().isoformat() if paid else None,
        }},
    )
    result = "success" if paid else "failed"
    return RedirectResponse(
        f"{settings.PAYMENT_FRONTEND_URL}?payment={result}&booking_id={booking['_id']}"
    )
