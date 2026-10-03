import json
import re
import asyncio
from typing import Any, Dict, List, Optional
from time import monotonic

import httpx
from fastapi import APIRouter, HTTPException, Query, Request

from app.core.config import settings
from app.db.mongodb import get_db
from app.schemas.ai import ChatRequest, ChatResponse, ItineraryDay, Recommendation, WeatherSnapshot

router = APIRouter()
_weather_cache: Dict[str, tuple] = {}
_chat_requests: Dict[str, List[float]] = {}
CHAT_LIMIT = 20
CHAT_WINDOW_SECONDS = 60
CHAT_HISTORY_LIMIT = 12

CITY_COORDINATES: Dict[str, tuple] = {
    "hà nội": (21.0285, 105.8542),
    "hải phòng": (20.8449, 106.6881),
    "quảng ninh": (20.9500, 107.0833),
    "hạ long": (20.9500, 107.0833),
    "bắc ninh": (21.1861, 106.0763),
    "hà nam": (20.5453, 105.9123),
    "hải dương": (20.9373, 106.3146),
    "hưng yên": (20.6464, 106.0511),
    "nam định": (20.4344, 106.1775),
    "thái bình": (20.4463, 106.3366),
    "ninh bình": (20.2506, 105.9745),
    "vĩnh phúc": (21.3089, 105.6049),
    "tam đảo": (21.4550, 105.6420),
    "phú thọ": (21.3917, 105.3211),
    "hà giang": (22.8233, 104.9839),
    "cao bằng": (22.6667, 106.2500),
    "bắc kạn": (22.1472, 105.8347),
    "tuyên quang": (21.8236, 105.2144),
    "lào cai": (22.4856, 103.9707),
    "sa pa": (22.3364, 103.8438),
    "sapa": (22.3364, 103.8438),
    "yên bái": (21.7167, 104.8667),
    "thái nguyên": (21.5942, 105.8481),
    "lạng sơn": (21.8536, 106.7628),
    "bắc giang": (21.2731, 106.1947),
    "điện biên": (21.3833, 103.0167),
    "lai châu": (22.3964, 103.4589),
    "sơn la": (21.3256, 103.9189),
    "mộc châu": (20.8439, 104.6473),
    "hòa bình": (20.8172, 105.3381),
    "mai châu": (20.6589, 105.0811),
    "thanh hóa": (19.8067, 105.7852),
    "nghệ an": (18.6734, 105.6813),
    "hà tĩnh": (18.3428, 105.9058),
    "quảng bình": (17.4689, 106.6225),
    "quảng trị": (16.7417, 107.1856),
    "thừa thiên huế": (16.4637, 107.5909),
    "huế": (16.4637, 107.5909),
    "đà nẵng": (16.0544, 108.2022),
    "quảng nam": (15.5667, 108.4833),
    "hội an": (15.8801, 108.3380),
    "quảng ngãi": (15.1206, 108.7922),
    "bình định": (13.7829, 109.2197),
    "quy nhơn": (13.7829, 109.2197),
    "phú yên": (13.0881, 109.3094),
    "khánh hòa": (12.2388, 109.1967),
    "nha trang": (12.2388, 109.1967),
    "ninh thuận": (11.5667, 108.9833),
    "bình thuận": (10.9274, 108.1018),
    "phan thiết": (10.9274, 108.1018),
    "mũi né": (10.9330, 108.2870),
    "kon tum": (14.3500, 108.0000),
    "măng đen": (14.6067, 108.2897),
    "gia lai": (13.9833, 108.0000),
    "đắk lắk": (12.6667, 108.0500),
    "buôn ma thuột": (12.6667, 108.0500),
    "đắk nông": (12.0000, 107.6833),
    "lâm đồng": (11.9404, 108.4583),
    "đà lạt": (11.9404, 108.4583),
    "bình phước": (11.7500, 106.9000),
    "tây ninh": (11.3000, 106.1000),
    "bình dương": (11.1667, 106.6667),
    "đồng nai": (10.9500, 106.8167),
    "bà rịa": (10.4967, 107.1683),
    "vũng tàu": (10.4114, 107.1362),
    "côn đảo": (8.6835, 106.6067),
    "hồ chí minh": (10.8231, 106.6297),
    "long an": (10.5333, 106.4000),
    "tiền giang": (10.3500, 106.3500),
    "bến tre": (10.2333, 106.3833),
    "trà vinh": (9.9333, 106.3333),
    "vĩnh long": (10.2500, 105.9667),
    "đồng tháp": (10.4667, 105.6333),
    "an giang": (10.3833, 105.4167),
    "châu đốc": (10.7000, 105.1167),
    "kiên giang": (10.0167, 105.0833),
    "phú quốc": (10.2899, 103.9840),
    "cần thơ": (10.0452, 105.7469),
    "hậu giang": (9.7833, 105.4667),
    "sóc trăng": (9.6000, 105.9667),
    "bạc liêu": (9.2833, 105.7167),
    "cà mau": (9.1833, 105.1500),
}

LOCATION_ALIASES: Dict[str, List[str]] = {
    "phú thọ": ["phú thọ", "phu tho", "đền hùng", "den hung", "nghĩa lĩnh", "long cốc", "long coc", "xuân sơn", "xuan son", "thanh thủy", "thanh thuy", "việt trì", "viet tri"],
    "đà lạt": ["đà lạt", "da lat", "dalat", "lâm đồng", "lam dong", "langbiang", "tuyền lâm", "cầu đất", "datanla", "puppy farm"],
    "sa pa": ["sa pa", "sapa", "lào cai", "lao cai", "fansipan", "cát cát", "mường hoa", "ô quy hồ", "tả van"],
    "sapa": ["sa pa", "sapa", "lào cai", "lao cai", "fansipan", "cát cát", "mường hoa", "ô quy hồ", "tả van"],
    "hà nội": ["hà nội", "ha noi", "hanoi", "thủ đô", "hoàn kiếm", "phố cổ", "ba đình", "tây hồ", "hồ gươm"],
    "quảng ninh": ["quảng ninh", "quang ninh", "hạ long", "ha long", "halong", "bãi cháy", "ti tốp", "tuần châu", "vân đồn", "cô tô", "cát bà", "yên tử"],
    "hạ long": ["hạ long", "ha long", "halong", "quảng ninh", "quang ninh", "bãi cháy", "ti tốp", "tuần châu", "lan hạ"],
    "hà giang": ["hà giang", "ha giang", "hagiang", "đồng văn", "lũng cú", "mã pí lèng", "nho quế", "mèo vạc", "quản bạ"],
    "cao bằng": ["cao bằng", "cao bang", "bản giốc", "ban gioc", "pác bó", "pac bo", "ngườm ngao", "trùng khánh"],
    "bắc kạn": ["bắc kạn", "bac kan", "hồ ba bể", "ba be"],
    "ninh bình": ["ninh bình", "ninh binh", "tràng an", "bái đính", "tam cốc", "hang múa", "hoa lư", "tuyệt tình cốc"],
    "đà nẵng": ["đà nẵng", "da nang", "danang", "bà nà", "bà nà hills", "sơn trà", "mỹ khê", "ngũ hành sơn", "cầu rồng"],
    "hội an": ["hội an", "hoi an", "hoian", "quảng nam", "quang nam", "rừng dừa bảy mẫu", "chùa cầu", "sông hoài", "mỹ sơn"],
    "quảng nam": ["quảng nam", "quang nam", "hội an", "hoi an", "mỹ sơn", "tam kỳ"],
    "huế": ["huế", "hue", "thừa thiên huế", "thua thien hue", "sông hương", "đại nội", "khải định", "thiên mụ", "lăng cô"],
    "thừa thiên huế": ["thừa thiên huế", "thua thien hue", "huế", "hue", "sông hương", "đại nội"],
    "nha trang": ["nha trang", "nhatrang", "khánh hòa", "khanh hoa", "hòn mun", "vinpearl", "vinwonders", "cam ranh", "tháp bà"],
    "khánh hòa": ["khánh hòa", "khanh hoa", "nha trang", "cam ranh", "vân phong"],
    "quy nhơn": ["quy nhơn", "quy nhon", "quynhon", "bình định", "binh dinh", "kỳ co", "eo gió", "ghềnh ráng"],
    "bình định": ["bình định", "binh dinh", "quy nhơn", "kỳ co", "eo gió"],
    "phú yên": ["phú yên", "phu yen", "ghềnh đá đĩa", "ghenh da dia", "mũi điện", "bãi môn", "tháp nghinh phong", "tuy hòa"],
    "phú quốc": ["phú quốc", "phu quoc", "phuquoc", "kiên giang", "kien giang", "hòn thơm", "grand world", "bãi sao", "an thới", "sunset sanato", "hà tiên"],
    "kiên giang": ["kiên giang", "kien giang", "phú quốc", "nam du", "hà tiên", "rạch giá"],
    "quảng bình": ["quảng bình", "quang binh", "phong nha", "kẻ bàng", "sơn đoòng", "thiên đường", "suối moọc", "đồng hới"],
    "quảng trị": ["quảng trị", "quang tri", "địa đạo vịnh mốc", "thành cổ", "đông hà"],
    "thanh hóa": ["thanh hóa", "thanh hoa", "sầm sơn", "sam son", "pù luông", "pu luong", "thành nhà hồ", "hải tiến"],
    "nghệ an": ["nghệ an", "nghe an", "cửa lò", "cua lo", "làng sen", "nam đàn", "vinh"],
    "hà tĩnh": ["hà tĩnh", "ha tinh", "thiên cầm", "ngã ba đồng lộc"],
    "quảng ngãi": ["quảng ngãi", "quang ngai", "lý sơn", "ly son"],
    "ninh thuận": ["ninh thuận", "ninh thuan", "vĩnh hy", "vinh hy", "hang rái", "tháp chàm", "phan rang"],
    "bình thuận": ["bình thuận", "binh thuan", "phan thiết", "phan thiet", "mũi né", "mui ne", "bàu trắng", "phú quý"],
    "phan thiết": ["phan thiết", "phan thiet", "mũi né", "mui ne", "bình thuận", "bàu trắng"],
    "mũi né": ["mũi né", "mui ne", "phan thiết", "bình thuận", "bàu trắng"],
    "kon tum": ["kon tum", "kontum", "măng đen", "mang den", "nhà thờ gỗ"],
    "măng đen": ["măng đen", "mang den", "mangden", "kon tum", "pa sỹ", "đắk ke"],
    "gia lai": ["gia lai", "gialai", "pleiku", "biển hồ", "chư đăng ya"],
    "đắk lắk": ["đắk lắk", "dak lak", "daklak", "buôn ma thuột", "buon ma thuot", "hồ lắk", "dray nur"],
    "đắk nông": ["đắk nông", "dak nong", "tà đùng", "ta dung"],
    "lâm đồng": ["lâm đồng", "lam dong", "đà lạt", "da lat", "bảo lộc", "bao loc"],
    "tây ninh": ["tây ninh", "tay ninh", "núi bà đen", "nui ba den", "tòa thánh"],
    "bà rịa": ["bà rịa", "ba ria", "vũng tàu", "vung tau", "côn đảo", "hồ tràm"],
    "vũng tàu": ["vũng tàu", "vung tau", "vungtau", "hải đăng", "kito", "bãi sau", "bà rịa"],
    "côn đảo": ["côn đảo", "con dao", "condao", "hàng dương", "đầm trầu"],
    "hồ chí minh": ["hồ chí minh", "ho chi minh", "sài gòn", "sai gon", "saigon", "tphcm", "bến thành", "củ chi", "landmark"],
    "an giang": ["an giang", "châu đốc", "chau doc", "trà sư", "tra su", "miếu bà chúa xứ", "núi sam"],
    "đồng tháp": ["đồng tháp", "dong thap", "tràm chim", "sa đéc", "xẻo quýt", "cao lãnh"],
    "tiền giang": ["tiền giang", "tien giang", "mỹ tho", "thới sơn", "cái bè"],
    "bến tre": ["bến tre", "ben tre", "xứ dừa", "cồn phụng"],
    "cần thơ": ["cần thơ", "can tho", "cantho", "miền tây", "cái răng", "chợ nổi", "ninh kiều"],
    "cà mau": ["cà mau", "ca mau", "đất mũi", "dat mui", "u minh hạ", "hòn khoai"],
    "sơn la": ["sơn la", "son la", "mộc châu", "moc chau", "tà xùa", "ta xua"],
    "mộc châu": ["mộc châu", "moc chau", "mocchau", "sơn la", "đồi chè trái tim", "dải yếm", "bạch long"],
    "hòa bình": ["hòa bình", "hoa binh", "mai châu", "mai chau", "thung nai"],
    "yên bái": ["yên bái", "yen bai", "mù cang chải", "mu cang chai", "tú lệ", "hồ thác bà"],
    "điện biên": ["điện biên", "dien bien", "mường thanh", "a1", "pha đin"],
    "hải phòng": ["hải phòng", "hai phong", "cát bà", "cat ba", "đồ sơn", "do son"],
    "vĩnh phúc": ["vĩnh phúc", "vinh phuc", "tam đảo", "tam dao", "tamdao", "tây thiên"],
    "tam đảo": ["tam đảo", "tam dao", "tamdao", "vĩnh phúc"],
    "bắc ninh": ["bắc ninh", "bac ninh", "chùa dâu", "chùa phật tích", "đền đô", "quan họ", "làng tranh đông hồ"],
    "bắc giang": ["bắc giang", "bac giang", "chùa vĩnh nghiêm", "tây yên tử", "lục ngạn", "suối mỡ"],
    "thái nguyên": ["thái nguyên", "thai nguyen", "tân cương", "hồ núi cốc", "atk định hóa"],
    "tuyên quang": ["tuyên quang", "tuyen quang", "na hang", "lâm bình", "tân trào", "suối khoáng mỹ lâm"],
    "lạng sơn": ["lạng sơn", "lang son", "ải chi lăng", "tam thanh", "nhị thanh", "mẫu sơn", "tân thanh"],
    "lai châu": ["lai châu", "lai chau", "đèo ô quy hồ", "cầu kính rồng mây", "sìn hồ", "bạch mộc lương tử"],
    "hà nam": ["hà nam", "ha nam", "chùa tam chúc", "tam chúc", "đền trúc", "bát cảnh sơn", "vũ đại"],
    "hải dương": ["hải dương", "hai duong", "côn sơn", "kiếp bạc", "côn sơn kiếp bạc", "đảo cò chi lăng nam"],
    "hưng yên": ["hưng yên", "hung yen", "phố hiến", "đền mẫu", "chùa chuông", "nhãn lồng"],
    "nam định": ["nam định", "nam dinh", "đền trần", "chùa cổ lễ", "nhà thờ đổ hải lý", "thành nam"],
    "thái bình": ["thái bình", "thai binh", "chùa keo", "biển đồng châu", "đền đồng bằng", "bánh cáy"],
    "bình phước": ["bình phước", "binh phuoc", "bù gia mập", "thác mơ", "bà rá"],
    "bình dương": ["bình dương", "binh duong", "lạc cảnh đại nam", "đại nam", "chùa bà thiên hậu", "lái thiêu"],
    "đồng nai": ["đồng nai", "dong nai", "vườn quốc gia cát tiên", "cát tiên", "bửu long", "thác đá hàn", "trị an"],
    "long an": ["long an", "làng nổi tân lập", "tân lập", "cần giuộc", "cánh đồng bất tận"],
    "trà vinh": ["trà vinh", "tra vinh", "ao bà om", "chùa hang", "chùa âng", "biển ba động"],
    "vĩnh long": ["vĩnh long", "vinh long", "cù lao an bình", "gốm mang thít", "mang thít"],
    "hậu giang": ["hậu giang", "hau giang", "chợ nổi ngã bảy", "ngã bảy", "lung ngọc hoàng"],
    "sóc trăng": ["sóc trăng", "soc trang", "chùa dơi", "chùa chén kiểu", "oóc om bóc", "bánh pía"],
    "bạc liêu": ["bạc liêu", "bac lieu", "công tử bạc liêu", "điện gió bạc liêu", "chùa xiêm cán", "dạ cổ hoài lang"],
}

CANONICAL_CITY_NAMES: Dict[str, str] = {
    "phú thọ": "Phú Thọ",
    "đà lạt": "Đà Lạt",
    "sa pa": "Sa Pa",
    "sapa": "Sa Pa",
    "hà nội": "Hà Nội",
    "hạ long": "Hạ Long",
    "quảng ninh": "Quảng Ninh",
    "hà giang": "Hà Giang",
    "cao bằng": "Cao Bằng",
    "bắc kạn": "Bắc Kạn",
    "ninh bình": "Ninh Bình",
    "đà nẵng": "Đà Nẵng",
    "hội an": "Hội An",
    "quảng nam": "Quảng Nam",
    "huế": "Huế",
    "thừa thiên huế": "Thừa Thiên Huế",
    "nha trang": "Nha Trang",
    "khánh hòa": "Khánh Hòa",
    "quy nhơn": "Quy Nhơn",
    "bình định": "Bình Định",
    "phú yên": "Phú Yên",
    "phú quốc": "Phú Quốc",
    "kiên giang": "Kiên Giang",
    "quảng bình": "Quảng Bình",
    "quảng trị": "Quảng Trị",
    "thanh hóa": "Thanh Hóa",
    "nghệ an": "Nghệ An",
    "hà tĩnh": "Hà Tĩnh",
    "quảng ngãi": "Quảng Ngãi",
    "ninh thuận": "Ninh Thuận",
    "bình thuận": "Bình Thuận",
    "phan thiết": "Phan Thiết",
    "mũi né": "Mũi Né",
    "kon tum": "Kon Tum",
    "măng đen": "Măng Đen",
    "gia lai": "Gia Lai",
    "đắk lắk": "Đắk Lắk",
    "buôn ma thuột": "Buôn Ma Thuột",
    "đắk nông": "Đắk Nông",
    "lâm đồng": "Lâm Đồng",
    "tây ninh": "Tây Ninh",
    "bà rịa": "Bà Rịa - Vũng Tàu",
    "bà rịa vũng tàu": "Bà Rịa - Vũng Tàu",
    "bà rịa - vũng tàu": "Bà Rịa - Vũng Tàu",
    "vũng tàu": "Vũng Tàu",
    "côn đảo": "Côn Đảo",
    "hồ chí minh": "Hồ Chí Minh",
    "sài gòn": "Hồ Chí Minh",
    "tphcm": "Hồ Chí Minh",
    "an giang": "An Giang",
    "đồng tháp": "Đồng Tháp",
    "tiền giang": "Tiền Giang",
    "bến tre": "Bến Tre",
    "cần thơ": "Cần Thơ",
    "cà mau": "Cà Mau",
    "sơn la": "Sơn La",
    "mộc châu": "Mộc Châu",
    "hòa bình": "Hòa Bình",
    "yên bái": "Yên Bái",
    "điện biên": "Điện Biên",
    "hải phòng": "Hải Phòng",
    "vĩnh phúc": "Vĩnh Phúc",
    "tam đảo": "Tam Đảo",
    "bắc ninh": "Bắc Ninh",
    "bắc giang": "Bắc Giang",
    "thái nguyên": "Thái Nguyên",
    "tuyên quang": "Tuyên Quang",
    "lạng sơn": "Lạng Sơn",
    "lai châu": "Lai Châu",
    "hà nam": "Hà Nam",
    "hải dương": "Hải Dương",
    "hưng yên": "Hưng Yên",
    "nam định": "Nam Định",
    "thái bình": "Thái Bình",
    "bình phước": "Bình Phước",
    "bình dương": "Bình Dương",
    "đồng nai": "Đồng Nai",
    "long an": "Long An",
    "trà vinh": "Trà Vinh",
    "vĩnh long": "Vĩnh Long",
    "hậu giang": "Hậu Giang",
    "sóc trăng": "Sóc Trăng",
    "bạc liêu": "Bạc Liêu",
}


CITY_HIGHLIGHTS: Dict[str, Dict[str, Any]] = {
    "phú thọ": {
        "title": "Phú Thọ - Vùng đất cội nguồn non sông & Không gian di sản Đền Hùng",
        "intro": "Phú Thọ là cái nôi của dân tộc Việt Nam, mảnh đất thiêng liêng lưu giữ nghìn năm lịch sử thời đại Hùng Vương dựng nước, nơi hội tụ cảnh sắc non nước hữu tình với những ốc đảo chè xanh ngát và di sản Hát Xoan được UNESCO vinh danh:",
        "spots": [
            "Khu di tích lịch sử Quốc gia đặc biệt Đền Hùng trên núi Nghĩa Lĩnh linh thiêng",
            "Đồi chè Long Cốc (Tân Sơn) - ốc đảo chè hình bát úp đẹp bậc nhất Việt Nam, điểm săn mây bình minh tuyệt tác",
            "Vườn quốc gia Xuân Sơn với hệ sinh thái rừng nguyên sinh, hang Lạng và thác nước hoang sơ",
            "Khu du lịch suối khoáng nóng Thanh Thủy thư giãn và phục hồi sức khỏe",
            "Đầm Ao Châu được ví như Vịnh Hạ Long trên cạn với 99 ngách nước trong xanh",
            "Thưởng thức đặc sản thịt chua Thanh Sơn, cá lăng sông Đà, cọ ỏm và bánh chưng bánh giầy làng Dòng"
        ],
        "itinerary": [
            {"day": 1, "title": "Hành Hương Về Đất Tổ Đền Hùng & Suối Khoáng Thanh Thủy", "activities": ["Viếng Đền Hạ, Đền Trung, Đền Thượng và Lăng Hùng Vương trên núi Nghĩa Lĩnh", "Dâng hương tại Đền Giếng và Bảo tàng Hùng Vương", "Thưởng thức đặc sản thịt chua Thanh Sơn và cá lăng sông Đà", "Chiều thư giãn tắm ngâm suối khoáng nóng Thanh Thủy"]},
            {"day": 2, "title": "Săn Mây Đồi Chè Long Cốc & Khám Phá Vườn Quốc Gia Xuân Sơn", "activities": ["Sáng sớm đón bình minh săn biển mây bồng bềnh tại Đồi chè Long Cốc", "Tham quan và chụp ảnh đồi chè bát úp xanh ngút ngàn", "Khám phá hang động và rừng cây nguyên sinh Vườn quốc gia Xuân Sơn", "Giao lưu văn hóa và nghe làn điệu Hát Xoan Phú Thọ"]}
        ]
    },
    "đà lạt": {
        "title": "Đà Lạt - Thiên đường sương mù, ngàn hoa và thung lũng tình yêu",
        "intro": "Đà Lạt là điểm đến hoàn hảo với khí hậu trong lành se lạnh quanh năm, rừng thông xanh ngát, thung lũng mờ ảo và ngàn hoa khoe sắc rực rỡ:",
        "spots": [
            "Quảng trường Lâm Viên & dạo bộ ven bờ Hồ Xuân Hương thơ mộng",
            "Đỉnh Langbiang huyền thoại ngắm trọn vẹn toàn cảnh cao nguyên Lâm Viên",
            "Máng trượt xuyên rừng thông và ngắm thác đổ hùng vĩ tại Thác Datanla",
            "Săn mây bình minh rực rỡ tại Đồi chè Cầu Đất",
            "Nông trại Cún Puppy Farm và trải nghiệm hái dâu tây chín mọng tại vườn",
            "Chợ đêm Đà Lạt thưởng thức bánh tráng nướng, sữa đậu nành nóng và dâu lắc"
        ],
        "itinerary": [
            {"day": 1, "title": "Check-in Biểu Tượng Thành Phố & Ẩm Thực Chợ Đêm", "activities": ["Chụp ảnh cùng búp hoa Atiso khổng lồ tại Quảng trường Lâm Viên", "Dạo quanh bờ Hồ Xuân Hương mát rượi", "Tham quan Ga cổ Đà Lạt công trình kiến trúc Pháp", "Khám phá ẩm thực chợ đêm Đà Lạt"]},
            {"day": 2, "title": "Săn Mây Đồi Chè Cầu Đất & Chinh Phục Langbiang", "activities": ["Khởi hành sáng sớm săn mây bình minh tại Đồi chè Cầu Đất", "Chinh phục đỉnh núi Langbiang bằng xe Jeep", "Trải nghiệm máng trượt uốn lượn tại Thác Datanla", "Tối thưởng thức lẩu gà lá é hoặc lẩu bò Ba Toa"]},
            {"day": 3, "title": "Nông Trại Cún Puppy Farm & Tự Hái Dâu Tây Vườn", "activities": ["Vui chơi cùng các chú cún tại Puppy Farm", "Tham quan vườn hoa cẩm tú cầu và vườn bí ngô khổng lồ", "Tự tay hái dâu tây chín đỏ tại vườn công nghệ cao", "Thư giãn cà phê view thung lũng trước khi trở về"]}
        ]
    },
    "sa pa": {
        "title": "Sa Pa - Thị trấn trong mây & Nóc nhà Đông Dương Fansipan",
        "intro": "Sa Pa mê hoặc du khách bởi vẻ đẹp kỳ vĩ của dãy Hoàng Liên Sơn, những thửa ruộng bậc thang uốn lượn và bản sắc văn hóa vùng cao mộc mạc:",
        "spots": [
            "Chinh phục đỉnh Fansipan 3.143m bằng tuyến cáp treo đạt kỷ lục thế giới",
            "Khám phá nét đẹp văn hóa người H'Mông tại Bản Cát Cát",
            "Chiêm ngưỡng thung lũng ruộng bậc thang tuyệt mỹ tại Thung lũng Mường Hoa",
            "Ngắm hoàng hôn ngoạn mục tại Cổng trời Đèo Ô Quy Hồ - tứ đại đỉnh đèo",
            "Thưởng thức đặc sản lẩu cá hồi, cá tầm nóng hổi và đồ nướng than hồng"
        ],
        "itinerary": [
            {"day": 1, "title": "Nhà Thờ Đá Cổ Kính & Khám Phá Bản Cát Cát", "activities": ["Dạo quanh Nhà thờ Đá và hồ Sa Pa trung tâm", "Trekking bản Cát Cát ngắm thác Tiên Sa và cối xay nước", "Thưởng thức đồ nướng than hồng phố núi"]},
            {"day": 2, "title": "Chinh Phục Đỉnh Fansipan 3.143m & Đèo Ô Quy Hồ", "activities": ["Đi cáp treo vượt thung lũng mây lên đỉnh Fansipan", "Chiêm bái Đại Tượng Phật trên đỉnh núi thiêng", "Ngắm hoàng hôn rực rỡ tại Cổng trời Đèo Ô Quy Hồ", "Thưởng thức lẩu cá tầm nghi ngút khói"]},
            {"day": 3, "title": "Thung Lũng Mường Hoa & Mua Sắm Đặc Sản Vùng Cao", "activities": ["Tham quan bãi đá cổ và ruộng bậc thang Mường Hoa", "Tìm hiểu làng nghề dệt thổ cẩm truyền thống", "Mua sắm hạt dẻ nóng, nấm hương rừng và thịt trâu gác bếp"]}
        ]
    },
    "đà nẵng": {
        "title": "Đà Nẵng - Thành phố biển hiện đại và đáng sống nhất Việt Nam",
        "intro": "Đà Nẵng sở hữu bãi cát trắng mịn trải dài tuyệt đẹp, những cây cầu kiến trúc độc đáo và khu du lịch Sun World Bà Nà Hills vang danh toàn cầu:",
        "spots": [
            "Check-in Cầu Vàng bàn tay khổng lồ nổi tiếng tại Sun World Bà Nà Hills",
            "Tắm biển thư giãn và trải nghiệm lướt sóng tại Bãi biển Mỹ Khê",
            "Viếng tượng Phật Bà khổng lồ Chùa Linh Ứng và ngắm toàn cảnh vịnh từ Bán đảo Sơn Trà",
            "Khám phá hệ thống hang động huyền bí tại Danh thắng Ngũ Hành Sơn",
            "Chiêm ngưỡng Cầu Rồng phun lửa và phun nước rực sáng cuối tuần"
        ],
        "itinerary": [
            {"day": 1, "title": "Bãi Biển Mỹ Khê & Bán Đảo Sơn Trà", "activities": ["Tắm biển tại Bãi biển Mỹ Khê", "Viếng Chùa Linh Ứng bán đảo Sơn Trà", "Thưởng thức bánh tráng cuốn thịt heo hai đầu da", "Xem Cầu Rồng phun lửa buổi tối"]},
            {"day": 2, "title": "Trọn Ngày Khám Phá Bà Nà Hills", "activities": ["Đi tuyến cáp treo đạt nhiều kỷ lục thế giới", "Check-in Cầu Vàng nổi tiếng", "Vui chơi tại Làng Pháp và Fantasy Park", "Thưởng thức buffet phong phú trên đỉnh núi"]},
            {"day": 3, "title": "Danh Thắng Ngũ Hành Sơn & Phố Cổ Hội An", "activities": ["Khám phá động Huyền Không tại Ngũ Hành Sơn", "Thăm làng đá mỹ nghệ Non Nước", "Di chuyển vào Phố cổ Hội An thả đèn hoa đăng lung linh"]}
        ]
    },
    "phú quốc": {
        "title": "Phú Quốc - Thiên đường nghỉ dưỡng Đảo Ngọc biển xanh cát trắng",
        "intro": "Phú Quốc níu giữ du khách bởi làn nước biển ngọc bích trong veo, bờ cát trắng êm mịn, cảnh hoàng hôn ngoạn mục và các đại đô thị giải trí không ngủ:",
        "spots": [
            "Tắm biển thư giãn tại Bãi Sao với dải cát trắng mịn màng như kem",
            "Đi cáp treo vượt biển 3 dây dài nhất thế giới sang Đảo Hòn Thơm",
            "Hòa mình vào không khí sôi động của thành phố không ngủ Grand World Phú Quốc",
            "Đi cano cao tốc lặn ngắm san hô tại quần đảo hoang sơ phía nam An Thới",
            "Ngắm hoàng hôn tuyệt đẹp bên những tác phẩm nghệ thuật tại Sunset Sanato",
            "Thưởng thức món bún quậy Kiến Xây tự pha nước chấm và gỏi cá trích đặc sản"
        ],
        "itinerary": [
            {"day": 1, "title": "Bãi Sao Cát Trắng & Hoàng Hôn Sunset Sanato", "activities": ["Tắm biển và chụp ảnh xích đu tại Bãi Sao", "Thưởng thức hải sản làng chài Hàm Ninh", "Chiêm ngưỡng hoàng hôn tại Sunset Sanato", "Dạo chợ đêm Phú Quốc ăn bún quậy"]},
            {"day": 2, "title": "Tour Cano 4 Đảo Hoang Sơ & Cáp Treo Hòn Thơm", "activities": ["Lên cano cao tốc khám phá Hòn Móng Tay, Hòn Gầm Ghì, Hòn Mây Rút", "Lặn ngắm san hô tự nhiên", "Đi cáp treo Hòn Thơm và chơi công viên nước Aquatopia"]},
            {"day": 3, "title": "Bắc Đảo Grand World & Tinh Hoa Việt Nam", "activities": ["Ngồi thuyền Gondola ngắm cảnh kênh đào Venice thu nhỏ tại Grand World", "Thăm Bảo tàng Gấu Teddy Bear", "Xem show diễn thực cảnh Tinh Hoa Việt Nam"]}
        ]
    },
    "nha trang": {
        "title": "Nha Trang - Thiên đường biển xanh ngọc bích và vịnh đảo thơ mộng",
        "intro": "Nha Trang làm say đắm lòng người với bờ cát trắng mịn thoai thoải, làn nước trong vắt cùng các tổ hợp vui chơi giải trí nghỉ dưỡng đẳng cấp quốc tế:",
        "spots": [
            "Lặn biển ngắm rạn san hô rực rỡ sắc màu tại Khu bảo tồn sinh thái Hòn Mun",
            "Vui chơi bất tận tại tổ hợp công viên giải trí VinWonders trên đảo Hòn Tre",
            "Khám phá di sản kiến trúc Chăm Pa cổ kính tại Tháp Bà Ponagar",
            "Trải nghiệm tắm bùn khoáng nóng thư giãn cơ thể và phục hồi năng lượng",
            "Thưởng thức nem nướng Ninh Hòa chuẩn vị, bún sứa thơm lừng và hải sản tươi sống"
        ],
        "itinerary": [
            {"day": 1, "title": "Du Ngoạn Vịnh Nha Trang & Lặn Ngắm San Hô Hòn Mun", "activities": ["Lên du thuyền tham quan các hòn đảo trong vịnh", "Lặn ống thở ngắm san hô tự nhiên tại Hòn Mun", "Thưởng thức bữa trưa hải sản tươi sống trên bè nổi Làng Chài"]},
            {"day": 2, "title": "Vui Chơi Đẳng Cấp Thế Giới Tại VinWonders", "activities": ["Đi cáp treo vượt biển chiêm ngưỡng vịnh ngọc từ trên cao", "Thử thách với các trò chơi cảm giác mạnh và công viên nước", "Khám phá Thủy cung hiện đại và xem show Tata Show"]},
            {"day": 3, "title": "Di Tích Tháp Bà Ponagar & Tắm Bùn Khoáng Nóng", "activities": ["Tham quan di tích lịch sử Tháp Bà Ponagar linh thiêng", "Trải nghiệm tắm bùn khoáng nóng phục hồi sức khỏe", "Thưởng thức nem nướng Ninh Hòa và mua mực một nắng làm quà"]}
        ]
    },
    "hạ long": {
        "title": "Hạ Long - Di sản thiên nhiên thế giới tráng lệ giữa biển Đông",
        "intro": "Vịnh Hạ Long sở hữu hàng nghìn đảo đá vôi kỳ vĩ muôn hình vạn trạng nhô lên từ làn nước biển xanh ngọc biếc tạo nên bức tranh thủy mặc tuyệt mỹ:",
        "spots": [
            "Du ngoạn du thuyền sang trọng thưởng ngoạn hàng nghìn hòn đảo đá vôi kỳ vĩ",
            "Thám hiểm Hang Sửng Sốt với những khối thạch nhũ lung linh huyền ảo",
            "Tự tay chèo thuyền kayak len lỏi qua vòm đá Hang Luồn tĩnh lặng",
            "Tắm biển và chinh phục đỉnh núi ngắm trọn toàn cảnh 360 độ tại Đảo Ti Tốp",
            "Trải nghiệm cáp treo Nữ Hoàng và vui chơi tại Sun World Hạ Long Park"
        ],
        "itinerary": [
            {"day": 1, "title": "Du Thuyền Thưởng Ngoạn Vịnh & Thám Hiểm Hang Sửng Sốt", "activities": ["Lên du thuyền xuất bến cảng Tuần Châu bắt đầu hành trình ngắm vịnh", "Khám phá vẻ đẹp kỳ vĩ của Hang Sửng Sốt", "Chèo thuyền kayak qua vòm đá Hang Luồn", "Tắm biển và leo đỉnh ngắm vịnh tại Đảo Ti Tốp"]},
            {"day": 2, "title": "Bình Minh Trên Boong Tàu & Phố Biển Bãi Cháy", "activities": ["Tập thái cực quyền đón bình minh trong lành trên boong tàu", "Thăm trang trại nuôi cấy ngọc trai truyền thống", "Vui chơi tại Sun World Bãi Cháy và mua chả mực giã tay"]}
        ]
    },
    "quảng ninh": {
        "title": "Quảng Ninh - Miền di sản thiên nhiên Vịnh Hạ Long & Thánh địa Yên Tử",
        "intro": "Quảng Ninh hội tụ kỳ quan thiên nhiên thế giới Vịnh Hạ Long, quần thể danh thắng tâm linh Yên Tử thanh tịnh và biển đảo Cô Tô, Quan Lạn hoang sơ tuyệt mỹ:",
        "spots": [
            "Chiêm ngưỡng hàng nghìn đảo đá vôi kỳ vĩ trên Vịnh Hạ Long và Vịnh Bái Tử Long",
            "Hành hương về chốn tổ Phật giáo Trúc Lâm Yên Tử thanh tịnh mây ngàn",
            "Thám hiểm Hang Sửng Sốt, Động Thiên Cung và chèo thuyền kayak Hang Luồn",
            "Nghỉ dưỡng biển đảo hoang sơ tại Đảo Cô Tô, Quan Lạn cát trắng mịn",
            "Thưởng thức đặc sản chả mực giã tay Hạ Long, ngán biển, sá sùng Quan Lạn"
        ],
        "itinerary": [
            {"day": 1, "title": "Khám Phá Vịnh Hạ Long & Chèo Thuyền Kayak", "activities": ["Lên du thuyền thưởng ngoạn kỳ quan thế giới", "Thăm Hang Sửng Sốt và ngắm toàn cảnh từ Đảo Ti Tốp", "Chèo thuyền kayak và tắm biển Bãi Cháy"]},
            {"day": 2, "title": "Hành Hương Yên Tử Chốn Tổ Thiền Phái", "activities": ["Đi cáp treo lên chùa Hoa Yên và Chùa Đồng đỉnh Yên Tử", "Thưởng ngoạn rừng trúc bạt ngàn và mua măng trúc Yên Tử"]}
        ]
    },
    "ninh bình": {
        "title": "Ninh Bình - Non nước hữu tình và Quần thể Di sản Tràng An",
        "intro": "Ninh Bình nức tiếng gần xa với cảnh quan núi đá vôi ngập nước kỳ vĩ, những hang động huyền ảo được UNESCO công nhận là Di sản kép thế giới:",
        "spots": [
            "Đi thuyền nan luồn lách qua các hang động kỳ thú tại Danh thắng Tràng An",
            "Chiêm bái Chùa Bái Đính - ngôi chùa sở hữu nhiều kỷ lục lớn nhất Đông Nam Á",
            "Chinh phục gần 500 bậc đá lên Đỉnh Hang Múa chiêm ngưỡng toàn cảnh Tam Cốc",
            "Khám phá Cố đô Hoa Lư - kinh đô đầu tiên của nước Đại Cồ Việt hào hùng",
            "Thưởng thức đặc sản thịt dê núi nướng tảng thơm lừng và cơm cháy giòn rụm"
        ],
        "itinerary": [
            {"day": 1, "title": "Hành Trình Thuyền Nan Tràng An & Đỉnh Hang Múa", "activities": ["Ngồi thuyền nan lướt nhẹ khám phá các hang động Tràng An", "Leo gần 500 bậc thang lên đỉnh Hang Múa ngắm sông Ngô Đồng", "Thưởng thức thịt dê núi cơm cháy"]},
            {"day": 2, "title": "Tâm Linh Chùa Bái Đính & Thăm Cố Đô Hoa Lư", "activities": ["Chiêm bái Điện Tam Thế, Tượng Phật Di Lặc bằng đồng tại Bái Đính", "Thăm đền thờ Vua Đinh Tiên Hoàng và Vua Lê Đại Hành tại Hoa Lư"]}
        ]
    },
    "hà giang": {
        "title": "Hà Giang - Miền đá nở hoa và những cung đèo huyền thoại",
        "intro": "Hà Giang làm mê đắm trái tim mọi du khách với những cung đèo uốn lượn ngoạn mục, dòng sông Nho Quế màu xanh ngọc bích và cao nguyên đá kỳ vĩ:",
        "spots": [
            "Chinh phục Đèo Mã Pí Lèng - một trong tứ đại đỉnh đèo hiểm trở nhất Việt Nam",
            "Đi thuyền trên dòng sông Nho Quế ngắm Hẻm vực Tu Sản sâu nhất Đông Nam Á",
            "Chạm tay vào Cột cờ Lũng Cú - điểm cực Bắc địa đầu thiêng liêng của Tổ quốc",
            "Khám phá Dinh thự Vua Mèo Vương Chính Đức và dạo bộ Phố cổ Đồng Văn",
            "Thưởng thức thắng cố, bánh tam giác mạch nướng thơm và cháo ấu tẩu nóng"
        ],
        "itinerary": [
            {"day": 1, "title": "Cổng Trời Quản Bạ Núi Đôi & Làng Lũng Cẩm", "activities": ["Vượt Dốc Bắc Sum quanh co ngoạn mục", "Ngắm toàn cảnh núi rừng tại Cổng trời Quản Bạ và Núi Đôi Cô Tiên", "Thăm Làng văn hóa Lũng Cẩm bối cảnh phim Chuyện của Pao"]},
            {"day": 2, "title": "Cực Bắc Lũng Cú & Đèo Mã Pí Lèng - Sông Nho Quế", "activities": ["Khám phá kiến trúc độc đáo Dinh thự họ Vương", "Chinh phục bậc thang lên Cột cờ Lũng Cú", "Chinh phục đèo Mã Pí Lèng và đi thuyền trên sông Nho Quế"]},
            {"day": 3, "title": "Phố Cổ Đồng Văn & Mua Sắm Đặc Sản Vùng Cao", "activities": ["Dạo quanh phiên chợ vùng cao Đồng Văn rực rỡ sắc màu", "Mua thịt trâu gác bếp, mật ong hoa bạc hà và trà Shan tuyết"]}
        ]
    },
    "cao bằng": {
        "title": "Cao Bằng - Non nước hữu tình, Thác Bản Giốc & Cội nguồn cách mạng Pác Bó",
        "intro": "Cao Bằng được thiên nhiên ban tặng thác nước tự nhiên lớn nhất Đông Nam Á cùng hệ thống hang động kỳ vĩ nằm trong Công viên Địa chất Toàn cầu UNESCO:",
        "spots": [
            "Chiêm ngưỡng vẻ đẹp tráng lệ kỳ vĩ của Thác Bản Giốc bên dòng sông Quây Sơn",
            "Thăm Khu di tích lịch sử Quốc gia đặc biệt Pác Bó, Suối Lê-nin trong xanh và Núi Các Mác",
            "Khám phá Động Ngườm Ngao thạch nhũ vàng óng lung linh huyền ảo",
            "Hồ Thang Hen thơ mộng nằm giữa thung lũng núi đá trùng điệp",
            "Thưởng thức đặc sản vịt quay 7 vị, bánh cuốn Cao Bằng chan nước canh xương và thạch đen Thạch An"
        ],
        "itinerary": [
            {"day": 1, "title": "Suối Lê-nin Pác Bó & Di Tích Lịch Sử", "activities": ["Thăm Khu di tích Pác Bó, ngắm làn nước xanh ngọc bích của suối Lê-nin", "Thăm Hang Cốc Bó và bàn đá lịch sử của Bác Hồ", "Thưởng thức bánh cuốn Cao Bằng nóng hổi"]},
            {"day": 2, "title": "Thác Bản Giốc Hùng Vĩ & Động Ngườm Ngao", "activities": ["Đi bè tre áp sát chân ngọn Thác Bản Giốc hùng tráng", "Khám phá mê cung thạch nhũ Động Ngườm Ngao", "Thưởng thức vịt quay 7 vị và hạt dẻ Trùng Khánh"]}
        ]
    },
    "mộc châu": {
        "title": "Mộc Châu - Cao nguyên mộng mơ xanh ngát đồi chè và thung lũng mận",
        "intro": "Mộc Châu làm say lòng người bởi những đồi chè xanh mướt mát trải dài ngút ngàn, không khí mát lành của thảo nguyên và những mùa hoa rực rỡ sắc màu:",
        "spots": [
            "Chụp ảnh tại Đồi chè Trái Tim xanh mướt ngát ngào hương chè non",
            "Chiêm ngưỡng dòng thác Dải Yếm trắng xóa mềm mại như dải lụa tiên",
            "Trải nghiệm bước đi trên không trung tại Cầu kính Bạch Long dài nhất thế giới",
            "Dạo bước ngắm hồ nước thơ mộng giữa Rừng thông Bản Áng",
            "Thưởng thức sữa tươi Mộc Châu, bê chao giòn rụm, cá suối chiên và ốc đá rừng"
        ],
        "itinerary": [
            {"day": 1, "title": "Đồi Chè Trái Tim & Rừng Thông Bản Áng", "activities": ["Check-in đồi chè Trái Tim xanh ngát", "Đạp xe dạo quanh hồ nước thơ mộng Rừng thông Bản Áng", "Thưởng thức món bê chao đặc sản Mộc Châu nóng hổi"]},
            {"day": 2, "title": "Thác Dải Yếm & Trải Nghiệm Cầu Kính Bạch Long", "activities": ["Chiêm ngưỡng dòng nước hùng vĩ tại Thác Dải Yếm", "Thử thách lòng dũng cảm trên Cầu kính Bạch Long vắt qua vách núi", "Thăm thung lũng mận Nà Ka và thưởng thức sữa tươi nguyên chất"]}
        ]
    },
    "quy nhơn": {
        "title": "Quy Nhơn - Kỳ Co Eo Gió thiên đường biển đảo hoang sơ tuyệt mỹ",
        "intro": "Quy Nhơn hấp dẫn du khách bằng làn nước biển trong vắt nhìn thấy đáy, bờ cát vàng óng ả nép mình dưới rặng đá hùng vĩ và hải sản thơm ngon bổ dưỡng:",
        "spots": [
            "Đắm mình vào làn nước xanh màu ngọc bích tại Bãi biển Kỳ Co",
            "Đi dạo trên con đường ven biển ngoạn mục ngắm sóng vỗ tại Eo Gió",
            "Tìm hiểu dấu tích kiến trúc cổ Chăm Pa tại Tháp Đôi huyền bí",
            "Thăm mộ thi sĩ Hàn Mặc Tử và Bãi tắm Hoàng Hậu tại Ghềnh Ráng Tiên Sa",
            "Thưởng thức bánh xèo tôm nhảy giòn rụm, bún chả cá và nem nướng chợ Huyện"
        ],
        "itinerary": [
            {"day": 1, "title": "Kỳ Co Biển Ngọc & Đi Dạo Con Đường Ven Biển Eo Gió", "activities": ["Đi cano cao tốc vượt biển sang Bãi tắm Kỳ Co", "Lặn ngắm san hô tự nhiên tại Bãi Dứa", "Dạo bước trên cung đường bậc thang đón gió tại Eo Gió", "Thưởng thức ốc biển và bánh xèo tôm nhảy"]},
            {"day": 2, "title": "Ghềnh Ráng Tiên Sa & Di Tích Tháp Đôi Chăm Pa", "activities": ["Thăm Bãi Trứng bãi tắm Hoàng Hậu Nam Phương và đồi thi nhân", "Khám phá kiến trúc độc đáo Tháp Đôi giữa lòng thành phố", "Thưởng thức bún chả cá Quy Nhơn đậm đà hương vị biển"]}
        ]
    },
    "hà nội": {
        "title": "Hà Nội - Thủ đô ngàn năm văn hiến cổ kính và thanh lịch",
        "intro": "Hà Nội mang nét đẹp lắng đọng hoài niệm với 36 phố phường rêu phong, những công trình kiến trúc thời Pháp cổ và nền ẩm thực đường phố tinh hoa nức tiếng:",
        "spots": [
            "Dạo bước quanh Hồ Hoàn Kiếm, Cầu Thê Húc đỏ son và Đền Ngọc Sơn cổ kính",
            "Khám phá 36 phố phường Hà Nội rêu phong bằng xe điện hoặc xích lô",
            "Viếng Lăng Chủ tịch Hồ Chí Minh, Khu di tích Phủ Chủ tịch và Chùa Một Cột",
            "Thăm Văn Miếu - Quốc Tử Giám ngôi trường đại học đầu tiên của Việt Nam",
            "Thưởng thức phở bò gia truyền, bún chả nướng than hoa và cà phê trứng phố cổ"
        ],
        "itinerary": [
            {"day": 1, "title": "Dấu Ấn Lịch Sử Nghìn Năm & Nét Đẹp Phố Cổ", "activities": ["Viếng Lăng Bác và chiêm ngưỡng Chùa Một Cột độc đáo", "Thăm Văn Miếu Quốc Tử Giám biểu tượng đạo học", "Dạo quanh bờ Hồ Gươm và check-in Cầu Thê Húc", "Thưởng thức bún chả nướng và ly cà phê trứng Giảng thơm béo"]},
            {"day": 2, "title": "Không Gian Văn Hóa & Hoàng Hôn Hồ Tây", "activities": ["Tham quan Bảo tàng Dân tộc học Việt Nam", "Viếng Chùa Trấn Quốc ngôi chùa cổ nhất Hà Nội bên Hồ Tây", "Ngắm hoàng hôn lãng mạn trên đường Thanh Niên và ăn kem Tràng Tiền"]}
        ]
    },
    "huế": {
        "title": "Huế - Cố đô thâm trầm, nguy nga di sản triều Nguyễn",
        "intro": "Cố đô Huế mang vẻ đẹp trầm mặc cổ kính với những cung điện lăng tẩm uy nghiêm tráng lệ nép mình bên dòng sông Hương êm đềm:",
        "spots": [
            "Khám phá Đại Nội Huế - Hoàng thành nguy nga của 13 vị vua triều Nguyễn",
            "Chiêm bái Chùa Thiên Mụ cổ tự linh thiêng soi bóng bên dòng sông Hương",
            "Chiêm ngưỡng kiệt tác kiến trúc Đông Tây tinh xảo tại Lăng Khải Định",
            "Đi thuyền rồng nghe ca Huế và thả hoa đăng ngắm Cầu Tràng Tiền đổi màu",
            "Thưởng thức bún bò Huế đậm đà chuẩn vị, các món bánh bèo, nậm, lọc và chè hẻm"
        ],
        "itinerary": [
            {"day": 1, "title": "Hoàng Thành Đại Nội & Thuyền Rồng Sông Hương", "activities": ["Tham quan Ngọ Môn, Điện Thái Hòa, Tử Cấm Thành trong Đại Nội", "Viếng Chùa Thiên Mụ tháp Phước Duyên cổ kính", "Đi thuyền rồng thưởng thức làn điệu Ca Huế trên dòng sông Hương"]},
            {"day": 2, "title": "Kiến Trúc Lăng Tẩm Triều Nguyễn & Ẩm Thực Cố Đô", "activities": ["Chiêm ngưỡng vẻ đẹp tinh hoa tráng lệ tại Lăng Khải Định", "Thăm Lăng Tự Đức với không gian thi ca thanh tịnh", "Thưởng thức bánh bèo chén, bánh nậm, bột lọc và chè bột lọc heo quay"]}
        ]
    },
    "hội an": {
        "title": "Hội An - Đô thị cổ kính hoài niệm rực rỡ ánh đèn lồng",
        "intro": "Phố cổ Hội An quyến rũ bởi những mái ngói rêu phong cổ kính, giàn hoa giấy rực rỡ bên hiên nhà gỗ, dòng sông Hoài thơ mộng và ẩm thực xứ Quảng thơm ngon:",
        "spots": [
            "Dạo bước phố cổ chiêm ngưỡng Chùa Cầu, nhà cổ Phùng Hưng, hội quán Phúc Kiến",
            "Đi thuyền gỗ thả đèn hoa đăng cầu bình an lung linh trên dòng sông Hoài",
            "Trải nghiệm cảm giác xoay tròn thích thú trên thuyền thúng Rừng dừa Bảy Mẫu",
            "Thưởng thức mì Quảng đậm đà, cao lầu sợi vàng óng, bánh mì Phượng và trà thảo mộc Mót"
        ],
        "itinerary": [
            {"day": 1, "title": "Khám Phá Di Sản Phố Cổ & Thả Hoa Đăng Sông Hoài", "activities": ["Thăm Chùa Cầu biểu tượng, nhà cổ Tấn Ký và hội quán Quảng Đông", "Nhâm nhi ly nước trà thảo mộc Mót thanh mát ven đường", "Đi thuyền gỗ ngắm hoàng hôn và thả đèn hoa đăng lung linh trên dòng sông Hoài", "Thưởng thức cao lầu và cơm gà bà Buội trứ danh"]},
            {"day": 2, "title": "Lắc Thúng Rừng Dừa Bảy Mẫu & Làng Gốm Thanh Hà", "activities": ["Trải nghiệm chèo thuyền thúng len lỏi qua các rặng dừa xanh mướt", "Xem nghệ nhân biểu diễn quăng chài và múa thúng điêu luyện", "Tự tay làm đồ gốm lưu niệm tại Làng gốm cổ Thanh Hà"]}
        ]
    },
    "cần thơ": {
        "title": "Cần Thơ - Thủ phủ miền Tây sông nước & Chợ nổi Cái Răng",
        "intro": "Cần Thơ mộc mạc và trù phú với nét văn hóa giao thương chợ nổi đặc sắc trên sông, những vườn cây ăn trái sum sê trĩu quả và người dân đôn hậu mến khách:",
        "spots": [
            "Khám phá nét sinh hoạt buôn bán độc đáo tại Chợ nổi Cái Răng sáng sớm",
            "Thưởng thức trái cây tươi ngon hái tận cành tại các Miệt vườn sinh thái",
            "Chiêm ngưỡng kiến trúc Đông Tây giao thoa tại Nhà cổ Bình Thủy",
            "Dạo bến Ninh Kiều lung linh về đêm và ngắm Cầu đi bộ Tình Yêu",
            "Thưởng thức hủ tiếu pizza, bánh xèo miền Tây, cá tai tượng chiên xù và lẩu mắm"
        ],
        "itinerary": [
            {"day": 1, "title": "Chợ Nổi Cái Răng & Miệt Vườn Sinh Thái", "activities": ["Đi thuyền sớm hòa mình vào Chợ nổi Cái Răng ăn tô bún nước lèo trên sông", "Tham quan lò hủ tiếu truyền thống và thưởng thức pizza hủ tiếu giòn tan", "Thăm vườn cây ăn quả tự tay hái sầu riêng, chôm chôm, măng cụt", "Dạo Bến Ninh Kiều và ngắm cầu Cần Thơ về đêm"]},
            {"day": 2, "title": "Nhà Cổ Bình Thủy & Chợ Đêm Tây Đô", "activities": ["Chiêm ngưỡng Nhà cổ Bình Thủy cổ kính hơn 140 năm tuổi", "Thăm Cồn Sơn trải nghiệm làm bánh dân gian Nam Bộ", "Thưởng thức đặc sản lẩu mắm miền Tây thơm lừng trước khi trở về"]}
        ]
    },
    "quảng bình": {
        "title": "Quảng Bình - Vương quốc hang động kỳ vĩ bậc nhất thế giới",
        "intro": "Quảng Bình là thủ phủ hang động của thế giới với Vườn quốc gia Phong Nha - Kẻ Bàng, những dòng sông ngầm kỳ bí và bãi biển Nhật Lệ thơ mộng:",
        "spots": [
            "Khám phá Động Phong Nha và Động Thiên Đường - hoàng cung trong lòng đất",
            "Tắm suối chèo kayak giữa làn nước xanh màu ngọc bích tại Suối Nước Moọc",
            "Trải nghiệm đu dây zipline và tắm bùn tự nhiên tại Hang Tối",
            "Chiêm ngưỡng cồn cát Quang Phú mênh mông sát bờ biển",
            "Thưởng thức cháo canh cá lóc, đẻn biển, lẩu cá khoai và bánh bột lọc Đồng Hới"
        ],
        "itinerary": [
            {"day": 1, "title": "Động Thiên Đường Hoàng Cung & Suối Nước Moọc", "activities": ["Khám phá hệ thống thạch nhũ tráng lệ tại Động Thiên Đường", "Tắm mát và chèo thuyền kayak tại Suối Moọc", "Thưởng thức gà nướng muối cheo bản địa"]},
            {"day": 2, "title": "Động Phong Nha Kỳ Bí & Biển Nhật Lệ", "activities": ["Ngồi thuyền ngược dòng sông Son khám phá Động Phong Nha", "Dạo biển Nhật Lệ ngắm hoàng hôn và thưởng thức hải sản"]}
        ]
    },
    "phú yên": {
        "title": "Phú Yên - Xứ sở hoa vàng trên cỏ xanh & Kỳ quan Ghềnh Đá Đĩa",
        "intro": "Phú Yên quyến rũ du khách bằng bờ biển hoang sơ tuyệt mỹ, những cột đá bazan hình lục lăng xếp chồng độc nhất vô nhị và ngọn hải đăng đón bình minh đầu tiên:",
        "spots": [
            "Chiêm ngưỡng tuyệt tác kiến trúc địa chất thiên nhiên tại Ghềnh Đá Đĩa",
            "Đón ánh bình minh đầu tiên trên đất liền Việt Nam tại Mũi Điện - Bãi Môn",
            "Check-in bãi cỏ xanh ngát sát vách biển tại Bãi Xép bối cảnh phim Tôi thấy hoa vàng trên cỏ xanh",
            "Chụp ảnh kiến trúc tháp Chăm hiện đại tại Tháp Nghinh Phong biểu tượng Tuy Hòa",
            "Thưởng thức mắt cá ngừ đại dương tiềm thuốc bắc, sò huyết đầm Ô Loan và bánh canh hẹ"
        ],
        "itinerary": [
            {"day": 1, "title": "Ghềnh Đá Đĩa Kỳ Vĩ & Bãi Xép Hoa Vàng", "activities": ["Khám phá kỳ quan tổ ong khổng lồ Ghềnh Đá Đĩa", "Check-in Bãi Xép ngắm biển từ vách đá phủ xương rồng", "Thưởng thức sò huyết đầm Ô Loan trứ danh"]},
            {"day": 2, "title": "Mũi Điện Đón Bình Minh & Tháp Nghinh Phong", "activities": ["Chinh phục ngọn Hải đăng Mũi Điện đón tia nắng bình minh đầu tiên", "Tắm biển Bãi Môn làn nước trong vắt", "Check-in Tháp Nghinh Phong lộng gió quảng trường biển Tuy Hòa"]}
        ]
    },
    "tây ninh": {
        "title": "Tây Ninh - Nóc nhà Nam Bộ Núi Bà Đen & Thánh địa Cao Đài",
        "intro": "Tây Ninh nổi bật với ngọn Núi Bà Đen hùng vĩ cao nhất Nam Bộ, quần thể tâm linh Đại Phật Tượng bằng đồng trên mây và văn hóa tôn giáo Cao Đài độc đáo:",
        "spots": [
            "Chinh phục đỉnh Núi Bà Đen 986m bằng tuyến cáp treo hiện đại săn mây bồng bềnh",
            "Chiêm bái Tượng Phật Bà Tây Bổ Đà Sơn bằng đồng cao nhất châu Á trên đỉnh núi",
            "Tham quan Tòa Thánh Tây Ninh công trình kiến trúc tôn giáo độc nhất vô nhị",
            "Thưởng thức bánh tráng phơi sương Trảng Bàng cuốn thịt luộc rau rừng và bò tơ Tây Ninh"
        ],
        "itinerary": [
            {"day": 1, "title": "Chinh Phục Đỉnh Núi Bà Đen & Tòa Thánh Cao Đài", "activities": ["Đi cáp treo Sun World lên đỉnh Núi Bà Đen ngắm biển mây", "Chiêm bái tượng Phật Bà và ngắm quảng trường hoa rực rỡ", "Thăm Tòa Thánh Tây Ninh xem lễ cúng trang nghiêm", "Thưởng thức bánh tráng phơi sương cuốn thịt luộc chấm mắm nêm"]}
        ]
    },
    "an giang": {
        "title": "An Giang - Miền Thất Sơn huyền bí, Rừng tràm Trà Sư & Miếu Bà Chúa Xứ",
        "intro": "An Giang mang vẻ đẹp kỳ bí của dãy Thất Sơn Bảy Núi, thảm bèo xanh mướt của rừng tràm Trà Sư và điểm hành hương linh thiêng bậc nhất phương Nam:",
        "spots": [
            "Viếng Miếu Bà Chúa Xứ Núi Sam Châu Đốc linh thiêng cầu bình an tài lộc",
            "Lướt tắc ráng xuyên qua thảm bèo xanh mướt tại Rừng tràm Trà Sư",
            "Khám phá nét văn hóa độc đáo của người Chăm tại Làng Chăm Châu Phong",
            "Thưởng thức bún cá Châu Đốc nước dùng ngải bún vàng óng, lẩu mắm và bánh bò thốt nốt"
        ],
        "itinerary": [
            {"day": 1, "title": "Tâm Linh Miếu Bà Núi Sam & Rừng Tràm Trà Sư", "activities": ["Viếng Miếu Bà Chúa Xứ Núi Sam và Chùa Hang", "Đi xuồng ba lá len lỏi trong Rừng tràm Trà Sư ngắm chim trời", "Thưởng thức bún cá Châu Đốc và nước thốt nốt ngọt thanh"]}
        ]
    },
    "cà mau": {
        "title": "Cà Mau - Điểm cực Nam Tổ quốc, rừng ngập mặn U Minh Hạ và Đất Mũi",
        "intro": "Cà Mau là vùng đất địa đầu cực Nam thiêng liêng nơi cuối trời Tổ quốc, nơi phù sa bồi đắp rừng đước bạt ngàn và ngắm trọn cả mặt trời mọc ở biển Đông lẫn lặn ở biển Tây:",
        "spots": [
            "Check-in Cột Mốc Tọa Độ Quốc Gia GPS 0001 tại Mũi Cà Mau",
            "Chinh phục Cột Cờ Hà Nội uy nghiêm tại Mũi Cà Mau",
            "Trải nghiệm đi vỏ lãi xuyên rừng đước nguyên sinh Vườn quốc gia Mũi Cà Mau",
            "Khám phá Rừng U Minh Hạ trải nghiệm gác kèo ong và nếm mật ong rừng tươi nguyên",
            "Thưởng thức cua Cà Mau chắc thịt ngọt lịm, cá thòi lòi nướng muối ớt và vọp nướng mỡ hành"
        ],
        "itinerary": [
            {"day": 1, "title": "Chạm Tay Điểm Cực Nam Đất Mũi Cà Mau", "activities": ["Đi cano cao tốc xuyên rừng ngập mặn ra Mũi Cà Mau", "Chụp ảnh tại Cột Mốc Tọa Độ GPS 0001 và biểu tượng con tàu hướng ra biển lớn", "Thưởng thức cua Cà Mau hấp và cá thòi lòi nướng muối ớt"]},
            {"day": 2, "title": "Rừng U Minh Hạ & Trải Nghiệm Gác Kèo Ong", "activities": ["Khám phá Rừng quốc gia U Minh Hạ", "Theo chân thợ rừng trải nghiệm gác kèo ong lấy mật", "Thưởng thức lẩu mắm cá đồng ăn kèm bông súng, rau muống đồng"]}
        ]
    },
    "măng đen": {
        "title": "Măng Đen - Nàng thơ đại ngàn Kon Tum & Khí hậu Đà Lạt thứ hai",
        "intro": "Măng Đen được ví như thiên đường sinh thái hoang sơ giữa đại ngàn Tây Nguyên với rừng thông bạt ngàn, hồ thác thơ mộng và không khí se lạnh quanh năm:",
        "spots": [
            "Chiêm ngưỡng dòng nước trắng xóa kỳ vĩ giữa rừng nguyên sinh tại Thác Pa Sỹ",
            "Thả hồn thư thái bên bờ Hồ Đắk Ke nước trong xanh in bóng thông reo",
            "Chiêm bái Tượng Đức Mẹ Măng Đen linh thiêng giữa rừng đại ngàn",
            "Trải nghiệm cắm trại săn mây bình minh trên đỉnh đồi thông",
            "Thưởng thức cơm lam gà nướng chấm muối é, lẩu lá khổ qua rừng và cá tầm Măng Đen"
        ],
        "itinerary": [
            {"day": 1, "title": "Hồ Đắk Ke & Thác Pa Sỹ Đại Ngàn", "activities": ["Dạo quanh bờ Hồ Đắk Ke ngắm hoa anh đào và liễu rủ", "Khám phá Khu du lịch sinh thái Thác Pa Sỹ", "Thưởng thức món gà nướng cơm lam thơm phức bên bếp lửa"]},
            {"day": 2, "title": "Tượng Đức Mẹ & Nông Trại Rau Sạch", "activities": ["Viếng Tượng Đức Mẹ Măng Đen cầu bình an", "Ghé thăm các nông trại rau hoa công nghệ cao", "Uống cà phê ngắm hoàng hôn buông xuống thung lũng thông reo"]}
        ]
    },
    "côn đảo": {
        "title": "Côn Đảo - Hòn đảo thiêng liêng, biển xanh hoang sơ và di tích lịch sử",
        "intro": "Côn Đảo là điểm đến đặc biệt kết hợp giữa dấu ấn lịch sử hào hùng, bãi biển trong vắt nhìn thấu đáy và hệ sinh thái rùa biển hiếm có:",
        "spots": [
            "Viếng Nghĩa trang Hàng Dương và thắp hương tại mộ nữ Anh hùng Võ Thị Sáu vào ban đêm",
            "Tìm hiểu lịch sử hào hùng bất khuất tại Di tích Nhà tù Côn Đảo - Chuồng cọp Pháp, Mỹ",
            "Tắm biển tại Bãi Đầm Trầu bãi biển cát vàng hình vầng trăng khuyết tuyệt đẹp",
            "Lặn ngắm san hô và thả rùa con về biển tại Vườn Quốc Gia Côn Đảo",
            "Thưởng thức mứt hạt bàng đặc sản, ốc vú nàng và cá thu một nắng"
        ],
        "itinerary": [
            {"day": 1, "title": "Dấu Ấn Lịch Sử Côn Đảo & Nghĩa Trang Hàng Dương", "activities": ["Tham quan Bảo tàng Côn Đảo và Trại Phú Hải", "Khám phá hệ thống Chuồng Cọp Pháp và Chuồng Cọp Mỹ", "Buổi tối viếng Nghĩa trang Hàng Dương thắp nén tâm hương tưởng niệm"]},
            {"day": 2, "title": "Bãi Đầm Trầu Biển Ngọc & Mũi Chim Chim", "activities": ["Tắm biển và check-in máy bay hạ cánh sát bãi biển Bãi Đầm Trầu", "Ngắm toàn cảnh biển đảo hùng vĩ tại Mũi Chim Chim", "Thưởng thức hải sản tươi sống tại chợ đêm Côn Đảo"]}
        ]
    },
    "vũng tàu": {
        "title": "Vũng Tàu - Thành phố biển ngập tràn nắng gió và ẩm thực phong phú",
        "intro": "Vũng Tàu là điểm hẹn nghỉ dưỡng biển lý tưởng ngay gần TP.HCM với bờ biển cát mịn, ngọn hải đăng cổ kính và những món hải sản tươi ngon:",
        "spots": [
            "Chinh phục gần 1.000 bậc đá lên Tượng Chúa Kito Vua trên đỉnh Núi Nhỏ",
            "Ngắm toàn cảnh thành phố biển từ Ngọn Hải Đăng cổ Vũng Tàu",
            "Tắm biển vui chơi lướt sóng tại Bãi Sau và đi dạo hoàng hôn Bãi Trước",
            "Thưởng thức bánh khọt Gốc Vú Sữa giòn rụm, lẩu cá đuối chua cay và gỏi cá mai"
        ],
        "itinerary": [
            {"day": 1, "title": "Tượng Chúa Kito & Bãi Sau Biển Xanh", "activities": ["Chinh phục đỉnh Núi Nhỏ ngắm vịnh biển từ cánh tay Tượng Chúa Kito", "Tắm biển và chơi thể thao bãi biển tại Bãi Sau", "Thưởng thức lẩu cá đuối măng chua và bánh bông lan trứng muối"]},
            {"day": 2, "title": "Ngọn Hải Đăng Cổ & Check-in Mũi Nghinh Phong", "activities": ["Lên Ngọn Hải Đăng Vũng Tàu ngắm toàn cảnh thành phố và uống cà phê", "Check-in Cổng trời Mũi Nghinh Phong lộng gió", "Thưởng thức bánh khọt tôm tươi vàng giòn"]}
        ]
    },
    "phan thiết": {
        "title": "Phan Thiết Mũi Né - Thủ phủ resort, đồi cát bay và biển xanh cát vàng",
        "intro": "Phan Thiết Mũi Né lôi cuốn du khách bằng những đồi cát mênh mông như sa mạc thu nhỏ, làn nước biển trong xanh và văn hóa làng chài ven biển mộc mạc:",
        "spots": [
            "Trượt cát và đi xe địa hình mạo hiểm trên Đồi Cát Bay và Đồi Cát Trắng Bàu Trắng",
            "Lội dòng nước mát lành ngắm nhũ đá đỏ kỳ vĩ tại Suối Tiên Mũi Né",
            "Ngắm cảnh bình minh tấp nập thuyền thúng về bờ tại Làng Chài Mũi Né",
            "Thưởng thức lẩu thả Mũi Né, bánh căn hải sản, răng mực nướng và nước mắm truyền thống"
        ],
        "itinerary": [
            {"day": 1, "title": "Bàu Trắng Sa Mạc Thu Nhỏ & Suối Tiên Huyền Ảo", "activities": ["Trải nghiệm xe Jeep leo đồi cát trắng Bàu Trắng ngắm hồ sen", "Dạo bước chân trần lội dòng nước mát tại Suối Tiên", "Tắm biển và nghỉ dưỡng tại các resort ven bờ biển Mũi Né"]},
            {"day": 2, "title": "Bình Minh Làng Chài & Tháp Chàm Poshanư", "activities": ["Đón bình minh tại Làng chài Mũi Né chụp ảnh hàng trăm thuyền thúng đầy màu sắc", "Tham quan di tích Tháp Chăm Poshanư cổ kính", "Thưởng thức đặc sản lẩu thả và bánh xèo Phan Thiết"]}
        ]
    },
    "mũi né": {
        "title": "Phan Thiết Mũi Né - Thủ phủ resort, đồi cát bay và biển xanh cát vàng",
        "intro": "Phan Thiết Mũi Né lôi cuốn du khách bằng những đồi cát mênh mông như sa mạc thu nhỏ, làn nước biển trong xanh và văn hóa làng chài ven biển mộc mạc:",
        "spots": [
            "Trượt cát và đi xe địa hình mạo hiểm trên Đồi Cát Bay và Đồi Cát Trắng Bàu Trắng",
            "Lội dòng nước mát lành ngắm nhũ đá đỏ kỳ vĩ tại Suối Tiên Mũi Né",
            "Ngắm cảnh bình minh tấp nập thuyền thúng về bờ tại Làng Chài Mũi Né",
            "Thưởng thức lẩu thả Mũi Né, bánh căn hải sản, răng mực nướng và nước mắm truyền thống"
        ],
        "itinerary": [
            {"day": 1, "title": "Bàu Trắng Sa Mạc Thu Nhỏ & Suối Tiên Huyền Ảo", "activities": ["Trải nghiệm xe Jeep leo đồi cát trắng Bàu Trắng ngắm hồ sen", "Dạo bước chân trần lội dòng nước mát tại Suối Tiên", "Tắm biển và nghỉ dưỡng tại các resort ven bờ biển Mũi Né"]},
            {"day": 2, "title": "Bình Minh Làng Chài & Tháp Chàm Poshanư", "activities": ["Đón bình minh tại Làng chài Mũi Né chụp ảnh hàng trăm thuyền thúng đầy màu sắc", "Tham quan di tích Tháp Chăm Poshanư cổ kính", "Thưởng thức đặc sản lẩu thả và bánh xèo Phan Thiết"]}
        ]
    },
    "hồ chí minh": {
        "title": "Hồ Chí Minh - Sài Gòn năng động, hoa lệ và nhịp sống bất tận",
        "intro": "Thành phố Hồ Chí Minh là trung tâm văn hóa kinh tế sôi động bậc nhất Việt Nam với những tòa nhà chọc trời hiện đại đan xen công trình kiến trúc lịch sử:",
        "spots": [
            "Chiêm ngưỡng kiến trúc Dinh Độc Lập, Bưu điện Trung tâm Thành phố và Nhà thờ Đức Bà",
            "Khám phá mạng lưới địa đạo huyền thoại tại Di tích Lịch sử Địa Đạo Củ Chi",
            "Dạo bước trên Phố đi bộ Nguyễn Huệ ngắm cảnh sông Sài Gòn và tòa nhà Landmark 81",
            "Trải nghiệm du thuyền ngắm hoàng hôn và dùng bữa tối lãng mạn trên sông Sài Gòn",
            "Thưởng thức cơm tấm sườn bì chả, hủ tiếu Nam Vang, bánh mì Sài Gòn và cà phê vợt"
        ],
        "itinerary": [
            {"day": 1, "title": "Biểu Tượng Sài Gòn & Du Thuyền Sông Sài Gòn", "activities": ["Tham quan Dinh Độc Lập và Nhà thờ Đức Bà", "Check-in Bưu điện Trung tâm TP.HCM và đường sách Nguyễn Văn Bình", "Lên đài quan sát Landmark 81 SkyView ngắm toàn cảnh thành phố", "Thưởng thức bữa tối du thuyền trên sông Sài Gòn lấp lánh ánh đèn"]}
        ]
    },
    "bắc ninh": {
        "title": "Bắc Ninh - Miền quan họ Kinh Bắc, di tích Chùa Dâu & Đền Đô",
        "intro": "Bắc Ninh là cái nôi của nền văn minh sông Hồng, nổi tiếng với di sản Dân ca Quan họ được UNESCO vinh danh cùng hàng trăm ngôi chùa và đền đài cổ kính:",
        "spots": [
            "Chùa Dâu - ngôi chùa cổ nhất Việt Nam với lịch sử khởi nguồn Phật giáo",
            "Chùa Phật Tích với pho tượng Phật A Di Đà bằng đá thời Lý tuyệt tác",
            "Khu di tích Đền Đô thờ 8 vị vua triều Lý linh thiêng",
            "Làng tranh dân gian Đông Hồ lưu giữ hồn tranh dân tộc",
            "Thưởng thức bánh phu thê Đình Bảng, nem bùi Ninh Xá, bánh tẻ làng Chờ"
        ],
        "itinerary": [
            {"day": 1, "title": "Hành Hương Chùa Cổ Kinh Bắc & Di Sản Đền Đô", "activities": ["Tham quan và chiêm bái Chùa Dâu và Chùa Phật Tích", "Dâng hương tại Đền Đô tìm hiểu lịch sử nhà Lý", "Khám phá nghệ thuật làm tranh khắc gỗ tại Làng tranh Đông Hồ", "Thưởng thức bánh phu thê Đình Bảng và nghe Dân ca Quan họ"]}
        ]
    },
    "bắc giang": {
        "title": "Bắc Giang - Vùng đất di tích Tây Yên Tử & Vải thiều Lục Ngạn",
        "intro": "Bắc Giang nổi bật với phong cảnh núi non hùng vĩ của sườn Tây Yên Tử, những rừng vải bạt ngàn và di tích lịch sử ghi dấu hào khí dân tộc:",
        "spots": [
            "Khu du lịch tâm linh - sinh thái Tây Yên Tử thanh tịnh",
            "Chùa Vĩnh Nghiêm lưu giữ mộc bản kinh Phật được UNESCO công nhận",
            "Vùng đồi vải thiều trù phú Lục Ngạn chín đỏ rực rỡ",
            "Khu du lịch sinh thái Suối Mỡ dòng nước trong lành",
            "Thưởng thức bánh đa Thổ Hà, vải thiều ngọt lịm và gà đồi Yên Thế"
        ],
        "itinerary": [
            {"day": 1, "title": "Tây Yên Tử Hùng Vĩ & Chùa Cổ Vĩnh Nghiêm", "activities": ["Đi cáp treo khám phá quần thể chùa tháp Tây Yên Tử", "Chiêm ngưỡng kho mộc bản quý giá tại Chùa Vĩnh Nghiêm", "Dạo chơi vãn cảnh Suối Mỡ mát rượi", "Thưởng thức gà đồi Yên Thế và bánh đa Kế"]}
        ]
    },
    "thái nguyên": {
        "title": "Thái Nguyên - Đệ nhất danh trà Tân Cương, Hồ Núi Cốc & ATK Định Hóa",
        "intro": "Thái Nguyên là thủ phủ chè của cả nước với những nương chè xanh mướt uốn lượn, huyền thoại tình yêu Hồ Núi Cốc và di tích lịch sử cách mạng hào hùng:",
        "spots": [
            "Không gian văn hóa Trà và đồi chè Tân Cương xanh ngát bạt ngàn",
            "Khu du lịch sinh thái Hồ Núi Cốc gắn liền huyền thoại nàng Công chàng Cốc",
            "Di tích Lịch sử Quốc gia đặc biệt ATK Định Hóa thiêng liêng",
            "Bảo tàng Văn hóa các Dân tộc Việt Nam tại trung tâm thành phố",
            "Thưởng thức trà Tân Cương trứ danh, cơm lam Định Hóa, trám đen Hà Châu, nem chua Đại Từ"
        ],
        "itinerary": [
            {"day": 1, "title": "Đồi Chè Tân Cương & Huyền Thoại Hồ Núi Cốc", "activities": ["Trải nghiệm hái chè và thưởng trà tại vùng chè đặc sản Tân Cương", "Du thuyền ngắm cảnh lòng hồ Núi Cốc", "Tham quan Bảo tàng Văn hóa các Dân tộc Việt Nam", "Thưởng thức cơm lam gà nướng và đặc sản vùng chè"]}
        ]
    },
    "tuyên quang": {
        "title": "Tuyên Quang - Vịnh Hạ Long trên núi Na Hang & Thủ đô kháng chiến",
        "intro": "Tuyên Quang thu hút du khách bởi cảnh sắc non nước hữu tình của hồ thủy điện Na Hang - Lâm Bình và khu di tích lịch sử cách mạng Tân Trào thiêng liêng:",
        "spots": [
            "Khu bảo tồn thiên nhiên Na Hang - Lâm Bình với ngọn núi cọc Vài Phạ kỳ vĩ",
            "Khu di tích lịch sử quốc gia đặc biệt Tân Trào - thủ đô khu giải phóng",
            "Suối khoáng nóng Mỹ Lâm phục hồi sức khỏe",
            "Thác Mơ hùng vĩ giữa đại ngàn",
            "Thưởng thức gỏi cá bỗng sông Lô, thịt trâu gác bếp, ngô nếp nương và rượu ngô Na Hang"
        ],
        "itinerary": [
            {"day": 1, "title": "Chiêm Ngưỡng Vịnh Hạ Long Trên Cạn Na Hang & Suối Khoáng", "activities": ["Du thuyền trên lòng hồ Na Hang ngắm núi Pác Tạ và cọc Vài Phạ", "Chụp ảnh tại Thác Mơ trong vắt", "Thư giãn tắm suối khoáng nóng Mỹ Lâm", "Thưởng thức cá lăng cá bỗng nướng sông Lô"]}
        ]
    },
    "lạng sơn": {
        "title": "Lạng Sơn - Xứ Lạng kỳ vĩ, Động Tam Thanh & Đỉnh Mẫu Sơn mây phủ",
        "intro": "Lạng Sơn miền biên ải Đông Bắc nổi tiếng với cảnh quan karst hiểm trở, những phiên chợ vùng biên sầm uất và đỉnh núi Mẫu Sơn săn mây mùa đông:",
        "spots": [
            "Quần thể danh thắng Động Tam Thanh, Động Nhị Thanh và tượng Nàng Tô Thị",
            "Đỉnh núi Mẫu Sơn quanh năm mát mẻ và có băng tuyết mùa đông",
            "Cửa khẩu quốc tế Hữu Nghị và Chợ Tân Thanh nhộn nhịp",
            "Khu di tích Ải Chi Lăng oanh liệt trong lịch sử chống giặc",
            "Thưởng thức vịt quay Thất Khê, khâu nhục Xứ Lạng, phở chua và đào Mẫu Sơn"
        ],
        "itinerary": [
            {"day": 1, "title": "Danh Thắng Tam Thanh & Chinh Phục Mẫu Sơn", "activities": ["Khám phá Động Tam Thanh và viếng Chùa Tam Thanh", "Check-in ngắm tượng Nàng Tô Thị hóa đá", "Lên đỉnh Mẫu Sơn ngắm toàn cảnh thung lũng mây", "Thưởng thức vịt quay lá mác mật và khâu nhục nóng hổi"]}
        ]
    },
    "lai châu": {
        "title": "Lai Châu - Đỉnh non ngút ngàn, Đèo Ô Quy Hồ & Cầu kính Rồng Mây",
        "intro": "Lai Châu quy tụ những đỉnh núi cao bậc nhất Việt Nam, những bản làng nguyên sơ của đồng bào vùng cao và những hang động thạch nhũ tráng lệ:",
        "spots": [
            "Trải nghiệm cảm giác mạnh tại Cầu kính Rồng Mây trên đỉnh Đèo Ô Quy Hồ",
            "Cao nguyên Sìn Hồ mát lạnh quanh năm với biển mây bồng bềnh",
            "Động Pu Sam Cáp kỳ bí được ví như thiên đường ngầm",
            "Bản du lịch cộng đồng Sin Suối Hồ ngập tràn hoa lan nở rộ",
            "Thưởng thức lợn cắp nách nướng lá mắc khén, măng đắng và cá suối chiên giòn"
        ],
        "itinerary": [
            {"day": 1, "title": "Đèo Ô Quy Hồ, Cầu Kính Rồng Mây & Bản Sin Suối Hồ", "activities": ["Chinh phục Cổng trời Ô Quy Hồ Lai Châu", "Đi bộ trên Cầu kính Rồng Mây ngắm vực sâu thung lũng", "Ghé thăm bản hoa Sin Suối Hồ mộc mạc", "Thưởng thức ẩm thực Tây Bắc và rượu ngô men lá"]}
        ]
    },
    "hà nam": {
        "title": "Hà Nam - Đại cảnh Chùa Tam Chúc & Quần thể văn hóa Đền Trúc",
        "intro": "Hà Nam bình yên nơi châu thổ sông Đáy với quần thể tâm linh Chùa Tam Chúc lớn nhất hành tinh cùng những làng nghề truyền thống lâu đời:",
        "spots": [
            "Quần thể tâm linh Chùa Tam Chúc tựa lưng vào núi Thất Tinh hướng ra hồ Lục Nhạc",
            "Khu du lịch Đền Trúc - Ngũ Động Thi Sơn rợp bóng trúc",
            "Làng Vũ Đại gắn liền với đặc sản cá kho niêu đất trứ danh",
            "Chùa Bà Đanh thanh tịnh bên sông Đáy",
            "Thưởng thức cá kho niêu đất làng Vũ Đại, bánh cuốn chả Phủ Lý, chuối ngự Đại Hoàng tiến vua"
        ],
        "itinerary": [
            {"day": 1, "title": "Chiêm Bái Đại Quần Thể Tam Chúc & Thưởng Thức Cá Kho Vũ Đại", "activities": ["Du thuyền trên hồ Lục Nhạc vào chiêm bái Chùa Tam Chúc", "Tham quan Điện Tam Thế, Điện Giáo Chủ và Vườn Cột Kinh khổng lồ", "Ghé thăm làng cổ Vũ Đại thưởng thức và mua cá kho niêu đất", "Thưởng thức bánh cuốn Phủ Lý nóng hổi thơm ngon"]}
        ]
    },
    "hải dương": {
        "title": "Hải Dương - Đất danh nhân Côn Sơn Kiếp Bạc & Đảo Cò Chi Lăng Nam",
        "intro": "Hải Dương là vùng đất địa linh nhân kiệt gắn liền cuộc đời danh nhân Nguyễn Trãi và Hưng Đạo Đại Vương Trần Quốc Tuấn:",
        "spots": [
            "Khu di tích quốc gia đặc biệt Côn Sơn - Kiếp Bạc linh thiêng",
            "Khu bảo tồn sinh thái Đảo Cò Chi Lăng Nam với hàng vạn cánh cò trắng",
            "Làng gốm Chu Đậu cổ kính vang danh thế giới",
            "Thưởng thức bánh đậu xanh Hải Dương ngọt bùi, bánh gai Ninh Giang, rươi Tứ Kỳ và vải thiều Thanh Hà"
        ],
        "itinerary": [
            {"day": 1, "title": "Di Tích Côn Sơn Kiếp Bạc & Hệ Sinh Thái Đảo Cò", "activities": ["Dâng hương tại Đền Kiếp Bạc và Chùa Côn Sơn", "Thăm suối Côn Sơn róc rách dưới rặng thông già", "Ngắm hoàng hôn với hàng vạn đàn cò bay về tổ tại Đảo Cò Chi Lăng Nam", "Thưởng thức bánh đậu xanh uống cùng trà nóng chuẩn vị"]}
        ]
    },
    "hưng yên": {
        "title": "Hưng Yên - Xứ Phố Hiến nghìn năm vang danh & Nhãn lồng ngọt thơm",
        "intro": "Hưng Yên nức tiếng với câu ca Thứ nhất Kinh Kỳ, thứ nhì Phố Hiến, nơi lưu giữ tinh hoa đô thị cổ phồn hoa bên bờ sông Hồng:",
        "spots": [
            "Quần thể di tích Phố Hiến, Đền Mẫu soi bóng hồ Bán Nguyệt",
            "Chùa Chuông cổ kính - Phố Hiến đệ nhất danh lam",
            "Làng cổ Đông Tảo với giống gà chân to quý hiếm",
            "Làng hương xạ Cao Thôn rực rỡ sắc màu",
            "Thưởng thức nhãn lồng tiến vua cùi dày giòn ngọt, bún thang lươn Phố Hiến, ếch om Phượng Tường"
        ],
        "itinerary": [
            {"day": 1, "title": "Khám Phá Di Sản Phố Hiến & Làng Cổ Hưng Yên", "activities": ["Dạo quanh hồ Bán Nguyệt và chiêm bái Đền Mẫu Hưng Yên", "Vãn cảnh Chùa Chuông cổ kính", "Check-in làng hương xạ Cao Thôn thơm ngát", "Thưởng thức bún thang lươn và nhãn lồng đặc sản"]}
        ]
    },
    "nam định": {
        "title": "Nam Định - Đất học thành Nam, Di tích Đền Trần & Chùa Cổ Lễ",
        "intro": "Nam Định giàu truyền thống hiếu học và tâm linh với hào khí Đông A thời Trần, những giáo đường kiến trúc Gothic tráng lệ và ẩm thực phở bò trứ danh:",
        "spots": [
            "Khu di tích lịch sử Đền Trần nơi phát tích vương triều Trần",
            "Chùa Cổ Lễ với kiến trúc kết hợp Phật giáo và Gothic độc đáo",
            "Nhà thờ đổ Hải Lý bên bờ biển đón bình minh kỳ ảo",
            "Vườn quốc gia Xuân Thủy - điểm dừng chân của hàng triệu chim di cư",
            "Thưởng thức phở bò Nam Định chuẩn vị gia truyền, bánh xíu páo, kẹo sìu châu và nem nắm Giao Thủy"
        ],
        "itinerary": [
            {"day": 1, "title": "Hào Khí Đền Trần, Nhà Thờ Đổ & Ẩm Thực Phố Cổ Thành Nam", "activities": ["Dâng hương tại Khu di tích Đền Trần hào hùng", "Khám phá Chùa Cổ Lễ và tháp Cửu Phẩm Liên Hoa", "Đón hoàng hôn tại Nhà thờ đổ Hải Lý bên sóng biển", "Thưởng thức tô phở bò gia truyền thơm nức và bánh xíu páo giòn rụm"]}
        ]
    },
    "thái bình": {
        "title": "Thái Bình - Quê lúa thanh bình, Chùa Keo cổ vũ & Biển Cồn Vành",
        "intro": "Thái Bình mộc mạc với những cánh đồng lúa thẳng cánh cò bay, kiệt tác kiến trúc gỗ Chùa Keo gần 400 năm tuổi và bãi biển hoang sơ đón gió biển đông:",
        "spots": [
            "Chùa Keo - kiệt tác kiến trúc gỗ cổ bậc nhất Việt Nam với gác chuông 3 tầng gỗ lim",
            "Bãi biển Cồn Vành và Cồn Đen lộng gió biển phù sa",
            "Đền Đồng Bằng trung tâm tín ngưỡng Tứ phủ linh thiêng",
            "Làng nghề chạm bạc Đồng Xâm tinh xảo",
            "Thưởng thức bánh cáy Làng Nguyễn ngọt thơm, canh cá Quỳnh Côi đậm đà, giò chả Tiền Hải"
        ],
        "itinerary": [
            {"day": 1, "title": "Kiệt Tác Gác Chuông Chùa Keo & Trải Nghiệm Biển Cồn Vành", "activities": ["Chiêm ngưỡng gác chuông Chùa Keo tuyệt mỹ không dùng đinh", "Dạo bước trên bãi biển Cồn Vành ngắm rừng ngập mặn", "Tìm hiểu làng nghề chạm bạc Đồng Xâm lâu đời", "Thưởng thức bát canh cá Quỳnh Côi nóng hổi và bánh cáy thơm bùi"]}
        ]
    },
    "quảng trị": {
        "title": "Quảng Trị - Đất lửa anh hùng, Địa đạo Vịnh Mốc & Di tích Thành cổ",
        "intro": "Quảng Trị khắc ghi những trang sử hào hùng của dân tộc bên dòng sông Bến Hải, Cầu Hiền Lương và huyền thoại lòng đất Vịnh Mốc:",
        "spots": [
            "Di tích Địa đạo Vịnh Mốc - kỳ tích sống và chiến đấu trong lòng đất",
            "Di tích Quốc gia đặc biệt Thành cổ Quảng Trị linh thiêng",
            "Đôi bờ Hiền Lương - Sông Bến Hải vĩ tuyến 17",
            "Nghĩa trang Liệt sĩ Quốc gia Trường Sơn",
            "Thưởng thức bánh lọc Mỹ Chánh, cháo bột cá lóc (bánh canh cá lóc), thịt trâu lá trơng"
        ],
        "itinerary": [
            {"day": 1, "title": "Vĩ Tuyến 17 Lịch Sử & Kỳ Tích Địa Đạo Vịnh Mốc", "activities": ["Dâng hương tưởng niệm tại Thành cổ Quảng Trị", "Tham quan Cầu Hiền Lương và Cột cờ Giới tuyến bên dòng sông Bến Hải", "Khám phá hệ thống làng hầm Địa đạo Vịnh Mốc hướng ra biển", "Thưởng thức đặc sản cháo bột cá lóc và bánh lọc Mỹ Chánh nóng hổi"]}
        ]
    },
    "quảng ngãi": {
        "title": "Quảng Ngãi - Đảo tiền tiêu Lý Sơn & Núi Ấn Sông Trà kỳ vĩ",
        "intro": "Quảng Ngãi nức tiếng với đảo thiên đường Lý Sơn hình thành từ trầm tích núi lửa triệu năm và danh thắng Núi Thiên Ấn soi bóng dòng Trà Khúc:",
        "spots": [
            "Đảo Lý Sơn - Cổng Tò Vò, Đỉnh Thới Lới và Hang Câu hùng vĩ",
            "Chùa Hang và cánh đồng tỏi Lý Sơn xanh ngát",
            "Núi Thiên Ấn và mộ Cụ Huỳnh Thúc Kháng",
            "Thưởng thức tỏi cô đơn Lý Sơn, don sông Trà Khúc đậm đà, kẹo gương, cá bống sông Trà kho tiêu"
        ],
        "itinerary": [
            {"day": 1, "title": "Khám Phá Thiên Đường Biển Đảo Núi Lửa Lý Sơn", "activities": ["Đi tàu cao tốc ra đảo ngọc Lý Sơn", "Check-in Cổng Tò Vò lúc hoàng hôn buông lỏng", "Chinh phục đỉnh núi lửa Thới Lới ngắm biển trời mênh mông", "Thưởng thức gỏi tỏi tươi Lý Sơn, cua huỳnh đế và ốc xà cừ nướng"]}
        ]
    },
    "ninh thuận": {
        "title": "Ninh Thuận - Vườn nho trĩu quả, Vịnh Vĩnh Hy & Tháp Chàm Po Klong Garai",
        "intro": "Ninh Thuận tràn ngập nắng gió duyên hải với vịnh biển hoang sơ Vĩnh Hy, những giàn nho mọng nước và cụm tháp Chăm cổ kính trầm mặc:",
        "spots": [
            "Vịnh Vĩnh Hy nước biển trong vắt nhìn thấy đáy",
            "Công viên đá và Hang Rái ngắm rạn san hô cổ hàng triệu năm",
            "Tháp Po Klong Garai kiệt tác kiến trúc Chăm Pa trên đồi Trầu",
            "Vườn nho Ba Mọi tự tay cắt nho chín mọng tại giàn",
            "Thưởng thức cừu nướng Ninh Thuận, bánh căn bánh xèo Phan Rang, mứt nho và rượu vang nho"
        ],
        "itinerary": [
            {"day": 1, "title": "Vịnh Biển Vĩnh Hy, Hang Rái & Tháp Chàm Cổ Kính", "activities": ["Đi tàu đáy kính ngắm san hô tại Vịnh Vĩnh Hy", "Ngắm sóng biển vỗ vào rạn san hô cổ Hang Rái kỳ ảo", "Chiêm ngưỡng kiến trúc Tháp Chăm Po Klong Garai", "Ghé thăm vườn nho thưởng thức siro nho mát lạnh và bánh căn nóng hổi"]}
        ]
    },
    "bình phước": {
        "title": "Bình Phước - Thủ phủ hạt điều, Vườn quốc gia Bù Gia Mập & Thác Mơ",
        "intro": "Bình Phước bạt ngàn rừng cao su ngút ngàn, những vườn điều xum xuê và thiên nhiên rừng nguyên sinh hoang dã giáp biên giới:",
        "spots": [
            "Vườn quốc gia Bù Gia Mập lý tưởng cho các chuyến trekking khám phá thiên nhiên",
            "Núi Bà Rá - ngọn núi cao thứ 3 Nam Bộ nhìn xuống hồ thủy điện Thác Mơ",
            "Trảng cỏ Bù Lạch bạt ngàn xanh mướt",
            "Thưởng thức hạt điều rang muối giòn béo, cơm lam thịt nướng, đọt mây nướng than hồng"
        ],
        "itinerary": [
            {"day": 1, "title": "Trekking Rừng Bù Gia Mập & Ngắm Hồ Thác Mơ Từ Núi Bà Rá", "activities": ["Trekking khám phá hệ động thực vật Vườn quốc gia Bù Gia Mập", "Lên đỉnh Núi Bà Rá ngắm toàn cảnh hồ Thác Mơ lấp lánh", "Thư giãn cắm trại bên trảng cỏ Bù Lạch", "Thưởng thức hạt điều rang củi thơm lừng và đặc sản vùng đất đỏ"]}
        ]
    },
    "bình dương": {
        "title": "Bình Dương - Thủ phủ gốm sứ Lái Thiêu & Quần thể Lạc cảnh Đại Nam",
        "intro": "Bình Dương kết hợp hài hòa giữa nhịp sống công nghiệp hiện đại với các làng nghề truyền thống trăm năm và điểm đến tâm linh nổi tiếng:",
        "spots": [
            "Khu du lịch Đại Nam Văn Hiến với quy mô đền đài hoành tráng",
            "Làng gốm Lái Thiêu truyền thống với nét mộc mạc tinh hoa",
            "Chùa Bà Thiên Hậu linh thiêng tại trung tâm Thủ Dầu Một",
            "Nhà thờ Phú Cường kiến trúc Gothic hiện đại",
            "Thưởng thức bánh bèo bì Mỹ Liên hơn 100 năm tuổi, gỏi măng cụt Lái Thiêu, nem Lái Thiêu"
        ],
        "itinerary": [
            {"day": 1, "title": "Làng Gốm Truyền Thống, Chùa Bà & Ẩm Thực Miệt Vườn", "activities": ["Tự tay nặn gốm tại Làng gốm Lái Thiêu", "Chiêm bái Chùa Bà Thiên Hậu cầu may mắn", "Check-in Nhà thờ chánh tòa Phú Cường tuyệt đẹp", "Thưởng thức bánh bèo bì và gỏi gà măng cụt mùa trái chín"]}
        ]
    },
    "đồng nai": {
        "title": "Đồng Nai - Khu dự trữ sinh quyển Cát Tiên & Khu du lịch Bửu Long",
        "intro": "Đồng Nai sở hữu Khu dự trữ sinh quyển thế giới Vườn quốc gia Cát Tiên cùng danh thắng đá rêu Bửu Long được ví như Vịnh Hạ Long thu nhỏ của phương Nam:",
        "spots": [
            "Vườn quốc gia Cát Tiên - xem thú đêm hoang dã và Bàu Sấu",
            "Khu du lịch Bửu Long với hồ Long Ẩn thơ mộng",
            "Thác Đá Hàn, Thác Giang Điền hoang sơ mát lành",
            "Làng bưởi Tân Triều nổi danh",
            "Thưởng thức bưởi đường lá cam Tân Triều, gỏi cá Biên Hòa, tôm càng xanh sông Đồng Nai"
        ],
        "itinerary": [
            {"day": 1, "title": "Khám Phá Thiên Nhiên Cát Tiên & Làng Bưởi Tân Triều", "activities": ["Trekking rừng nguyên sinh Cát Tiên và thăm trạm cứu hộ gấu", "Trải nghiệm tour xe mui trần xem thú đêm hoang dã kỳ thú", "Ghé thăm vườn bưởi Tân Triều thưởng thức rượu bưởi và gỏi bưởi", "Nghỉ ngơi hòa mình vào thiên nhiên thanh bình"]}
        ]
    },
    "long an": {
        "title": "Long An - Cửa ngõ miền Tây, Làng nổi Tân Lập & Cánh Đồng Bất Tận",
        "intro": "Long An đón chào du khách bằng những con đường xuyên rừng tràm huyền ảo, cánh đồng sen thơm ngát và nét mộc mạc đặc trưng của vùng đồng bằng châu thổ:",
        "spots": [
            "Con đường xi măng xuyên rừng tràm ngập nước tại Làng nổi Tân Lập",
            "Khu du lịch sinh thái Cánh Đồng Bất Tận đậm chất điện ảnh",
            "Khu phức hợp giải trí Happyland bên sông Vàm Cỏ Đông",
            "Thưởng thức lẩu mắm cá linh, cá lóc nướng trui cuốn lá sen non, thanh long Châu Thành ruột đỏ"
        ],
        "itinerary": [
            {"day": 1, "title": "Đi Xuồng Rừng Tràm Tân Lập & Khám Phá Hương Sen Vùng Nước Nổi", "activities": ["Đi xuồng ba lá lướt nhẹ trên dòng kênh xanh mát", "Đi bộ trên con đường xuyên rừng tràm Tân Lập chụp ảnh nghệ thuật", "Lên đài quan sát ngắm toàn cảnh rừng tràm bát ngát", "Thưởng thức cá lóc nướng trui thơm lừng cuốn bánh tráng rau rừng"]}
        ]
    },
    "trà vinh": {
        "title": "Trà Vinh - Xứ sở chùa cổ Khmer, Ao Bà Om & Hàng cây cổ thụ xanh mát",
        "intro": "Trà Vinh nổi bật với hơn 140 ngôi chùa Khmer kiến trúc Angkor rực rỡ, những cây dầu cổ thụ rợp bóng mát khắp nội ô và văn hóa đa sắc tộc hài hòa:",
        "spots": [
            "Thắng cảnh Ao Bà Om phẳng lặng soi bóng hàng cây sao cổ thụ hàng trăm năm",
            "Chùa Âng cổ kính nhất Trà Vinh đậm nét kiến trúc Phật giáo Nam tông",
            "Chùa Hang với cổng vòm tự nhiên và xưởng điêu khắc gỗ độc đáo",
            "Biển Ba Động hoang sơ bờ cát mịn",
            "Thưởng thức bún nước lèo Trà Vinh đậm đà mắm bò hóc, bánh tét Trà Cuôn, trái dừa sáp Cầu Kè béo ngậy"
        ],
        "itinerary": [
            {"day": 1, "title": "Chiêm Ngưỡng Chùa Cổ Khmer & Thưởng Thức Dừa Sáp", "activities": ["Dạo quanh thắng cảnh Ao Bà Om ngắm hàng cây cổ thụ", "Chiêm bái Chùa Âng kiến trúc Angkor tuyệt mỹ", "Khám phá nghệ thuật đục tượng gỗ độc đáo tại Chùa Hang", "Thưởng thức tô bún nước lèo thơm ngon và dừa sáp dầm đá béo ngậy"]}
        ]
    },
    "vĩnh long": {
        "title": "Vĩnh Long - Miệt vườn cù lao An Bình & Vương quốc gốm đỏ Mang Thít",
        "intro": "Vĩnh Long giữa hai nhánh sông Tiền và sông Hậu, nơi quy tụ những vườn cây trái bốn mùa trĩu quả và di sản lò gạch gốm đỏ Mang Thít độc nhất vô nhị:",
        "spots": [
            "Cù lao An Bình trải nghiệm đi xuồng, tát mương bắt cá và hái chôm chôm tại vườn",
            "Vương quốc lò gạch gốm đỏ Mang Thít bên dòng kênh Thầy Cai đẹp tựa kim tự tháp",
            "Cầu Mỹ Thuận dây văng tráng lệ",
            "Thưởng thức cá tai tượng chiên xù giòn rụm, ốc bươu nướng tiêu, bưởi Năm Roi Bình Minh ngọt thanh"
        ],
        "itinerary": [
            {"day": 1, "title": "Miệt Vườn Trái Cây An Bình & Vương Quốc Gốm Mang Thít", "activities": ["Đi đò ngang sang cù lao An Bình thưởng thức trái cây tại vườn", "Trải nghiệm tát mương bắt cá cùng nông dân miền Tây", "Đi thuyền chiêm ngưỡng hàng nghìn lò gạch gốm đỏ Mang Thít", "Thưởng thức cá tai tượng chiên xù cuốn bánh tráng rau sống"]}
        ]
    },
    "hậu giang": {
        "title": "Hậu Giang - Chợ nổi Ngã Bảy Phụng Hiệp & Rừng tràm Lung Ngọc Hoàng",
        "intro": "Hậu Giang mang đậm nét văn hóa sông nước Cửu Long với rốn chim Lung Ngọc Hoàng bảo tồn sinh thái và chợ nổi bảy ngả giao thương tấp nập:",
        "spots": [
            "Khu bảo tồn thiên nhiên Lung Ngọc Hoàng - lá phổi xanh rợp bóng chim trời",
            "Khu di tích Chợ nổi Ngã Bảy nơi 7 nhánh sông gặp gỡ",
            "Cánh đồng khóm Cầu Đúc bạt ngàn",
            "Thưởng thức chả cá thát lát Hậu Giang dai ngọt tự nhiên, khóm Cầu Đúc ngọt thanh, đọt choại xào tỏi"
        ],
        "itinerary": [
            {"day": 1, "title": "Khám Phá Rừng Tràm Lung Ngọc Hoàng & Cánh Đồng Khóm", "activities": ["Chèo xuồng len lỏi ngắm đàn chim quý tại Lung Ngọc Hoàng", "Lên tháp canh ngắm trọn vẹn thảm rừng ngập nước nguyên sơ", "Check-in đồng khóm Cầu Đúc và thưởng thức nước khóm ép tươi", "Thưởng thức lẩu cù lao và chả cá thát lát rút xương"]}
        ]
    },
    "sóc trăng": {
        "title": "Sóc Trăng - Miền đất giao thoa văn hóa, Chùa Dơi & Bánh pía sầu riêng",
        "intro": "Sóc Trăng cuốn hút với hệ thống chùa chiền lộng lẫy của ba dân tộc Kinh - Hoa - Khmer, lễ hội đua ghe Ngo rộn rã và đặc sản bánh pía ngọt bùi:",
        "spots": [
            "Chùa Dơi Wat Mahatup nơi hàng vạn chú dơi ngựa quý hiếm cư ngụ",
            "Chùa Chén Kiểu (Sà Lôn) ốp hàng triệu mảnh chén đĩa sứ tinh xảo",
            "Chùa Som Rong với tượng Phật Thích Ca nhập niết bàn khổng lồ",
            "Bảo tàng Văn hóa Khmer Sóc Trăng",
            "Thưởng thức bánh pía sầu riêng trứng muối thơm nức, bún nước lèo Sóc Trăng, bánh cóng Đại Tâm giòn rụm"
        ],
        "itinerary": [
            {"day": 1, "title": "Hành Trình Chùa Đẹp Sóc Trăng & Hương Vị Bánh Pía", "activities": ["Viếng Chùa Dơi chiêm ngưỡng đàn dơi treo ngược trên cành cây cổ thụ", "Chiêm ngưỡng kiến trúc độc nhất của Chùa Chén Kiểu", "Chụp ảnh tượng Phật khổng lồ thanh tịnh tại Chùa Som Rong", "Thưởng thức tô bún nước lèo cá lóc và mua bánh pía sầu riêng làm quà"]}
        ]
    },
    "bạc liêu": {
        "title": "Bạc Liêu - Nhà Công tử Bạc Liêu, Cánh đồng điện gió & Đờn ca tài tử",
        "intro": "Bạc Liêu vang danh với những giai thoại Công tử Bạc Liêu hào hoa, cái nôi bản Dạ cổ hoài lang bất hủ và cánh đồng quạt gió khổng lồ vươn ra biển lớn:",
        "spots": [
            "Khu dinh thự Công tử Bạc Liêu kiến trúc bề thế sang trọng bậc nhất lục tỉnh",
            "Cánh đồng điện gió Bạc Liêu trải dài trên biển đẹp ngỡ trời Âu",
            "Khu lưu niệm Nghệ thuật Đờn ca tài tử Nam Bộ và Cố nhạc sĩ Cao Văn Lầu",
            "Chùa Xiêm Cán uy nghi rực rỡ sắc vàng",
            "Thưởng thức lẩu mắm cá kèo, bún bò cay Bạc Liêu nồng nàn, bánh tằm bì Ngan Dừa béo thơm"
        ],
        "itinerary": [
            {"day": 1, "title": "Dinh Thự Công Tử Bạc Liêu, Cánh Đồng Điện Gió & Chùa Xiêm Cán", "activities": ["Tham quan dinh thự Công tử Bạc Liêu nghe kể các giai thoại xưa", "Dạo bước trên cầu vươn biển ngắm tua-bin điện gió quay đều", "Chiêm bái Chùa Xiêm Cán lộng lẫy", "Thưởng thức tô bún bò cay thơm lừng và nghe đờn ca tài tử Nam Bộ"]}
        ]
    }
}


def _weather_from_open_meteo(city: str, data: Dict[str, Any]) -> WeatherSnapshot:
    current = data.get("current", {})
    code = current.get("weather_code")
    if code in {0, 1}:
        condition, description = "clear", "Trời quang"
    elif code in {2, 3, 45, 48}:
        condition, description = "cloudy", "Nhiều mây"
    elif code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}:
        condition, description = "rain", "Có mưa"
    elif code in {71, 73, 75, 77}:
        condition, description = "cool", "Trời lạnh"
    else:
        condition, description = "unknown", "Đang cập nhật"
    temperature = current.get("temperature_2m")
    if isinstance(temperature, (int, float)):
        if temperature >= 32:
            condition = "hot"
        elif temperature <= 18 and condition == "unknown":
            condition = "cool"
    return WeatherSnapshot(
        city=city,
        condition=condition,
        temperature=temperature,
        description=description,
    )


def _cached_weather(city: str) -> WeatherSnapshot:
    cached = _weather_cache.get(city.strip().lower())
    return cached[1] if cached else WeatherSnapshot(city=city, condition="unknown")


def _casual_reply(message: str) -> Optional[str]:
    normalized = re.sub(r"[^a-zA-ZÀ-ỹ0-9 ]", "", message.lower()).strip()
    if re.fullmatch(r"(alo|hello|hi|hey|chào|xin chào|chao|ê|ơi)( bạn| bot| ai)?", normalized):
        return "Chào bạn! Mình là trợ lý du lịch SmartTravel. Bạn đang muốn tìm hiểu điểm đến, xem cẩm nang du lịch hay muốn tìm một tour phù hợp cho chuyến đi sắp tới?"
    if any(phrase in normalized for phrase in ["cảm ơn", "cam on", "thanks", "thank you"]):
        return "Rất vui được hỗ trợ bạn! Chúc bạn có những chuyến đi thật trọn vẹn và nhiều trải nghiệm đáng nhớ cùng SmartTravel."
    if any(phrase in normalized for phrase in ["bạn là ai", "ban la ai", "giúp được gì", "giup duoc gi", "ban lam gi"]):
        return "Mình là trợ lý du lịch thông minh SmartTravel. Mình có thể cung cấp cẩm nang danh lam thắng cảnh, thời tiết thời gian thực của 63 tỉnh thành Việt Nam, gợi ý lịch trình chi tiết và kết nối các tour du lịch có thật trên hệ thống. Bạn đang dự định đi đâu?"
    if normalized in {"tạm biệt", "tam biet", "bye", "goodbye"}:
        return "Tạm biệt bạn! Chúc bạn một ngày tốt lành và hẹn gặp lại bạn trong những chuyến hành trình tiếp theo cùng SmartTravel!"
    return None


def _coverage_reply(message: str) -> Optional[str]:
    normalized = re.sub(r"[^a-zA-ZÀ-ỹ0-9 ]", " ", message.lower()).strip()
    patterns = [
        r"63\s*(tỉnh|tinh)",
        r"(đủ|du|toàn bộ|toan bo|tất cả|tat ca)\s*(các\s*)?(tỉnh|tinh)",
        r"(bao nhiêu|bao nhieu)\s*(tỉnh|tinh)",
        r"(dữ liệu|du lieu|thông tin|thong tin).*(63|tỉnh thành|tinh thanh|toàn quốc|toan quoc)",
        r"(hỗ trợ|ho tro|có|co).*(63|tỉnh thành|tinh thanh|toàn quốc|toan quoc)",
        r"(phạm vi|pham vi).*(hỗ trợ|ho tro|dữ liệu|du lieu|tỉnh|tinh)"
    ]
    if any(re.search(pattern, normalized) for pattern in patterns):
        return (
            "Dạ chắc chắn rồi ạ! Trợ lý SmartTravel được trang bị đầy đủ cẩm nang du lịch, thời tiết thời gian thực và thông tin địa danh của toàn bộ 63 tỉnh thành trên khắp lãnh thổ Việt Nam:\n\n"
            "• Miền Bắc: Hà Nội, Quảng Ninh (Hạ Long), Ninh Bình, Hải Phòng, Phú Thọ, Lào Cai (Sa Pa), Hà Giang, Cao Bằng, Sơn La (Mộc Châu), Hòa Bình, Tuyên Quang, Lạng Sơn...\n"
            "• Miền Trung & Tây Nguyên: Thừa Thiên Huế, Đà Nẵng, Quảng Nam (Hội An), Bình Định (Quy Nhơn), Phú Yên, Khánh Hòa (Nha Trang), Ninh Thuận, Bình Thuận, Lâm Đồng (Đà Lạt), Kon Tum (Măng Đen), Đắk Lắk...\n"
            "• Miền Nam: TP. Hồ Chí Minh, Bà Rịa - Vũng Tàu, Tây Ninh, Cần Thơ, An Giang, Bến Tre, Bạc Liêu, Cà Mau, Kiên Giang (Phú Quốc)...\n\n"
            "Hệ thống cũng đang mở bán các tour du lịch thực tế với giá ưu đãi minh bạch. Bạn có thể gõ tên bất kỳ tỉnh thành nào bạn muốn đến, hoặc tham khảo các tour nổi bật bên dưới để mình tư vấn cụ thể nhé!"
        )
    return None


def _feature_reply(message: str) -> Optional[str]:
    normalized = message.lower()
    if any(phrase in normalized for phrase in ["hướng dẫn viên", "huong dan vien", "hdv", "thuê hdv", "thue hdv", "tìm hdv", "tim hdv"]):
        return (
            "SmartTravel cung cấp dịch vụ 'Thuê Hướng Dẫn Viên' bản địa uy tín tại mục 'Thuê HDV' trên thanh điều hướng:\n\n"
            "• Đội ngũ HDV đều đã được ban quản trị kiểm duyệt hồ sơ căn cước công dân (CCCD/KYC) và kiểm tra nghiệp vụ du lịch nghiêm ngặt.\n"
            "• Bạn có thể lọc HDV theo tỉnh thành, ngôn ngữ giao tiếp (Tiếng Việt, Anh, Pháp, Hàn...) và số năm kinh nghiệm.\n"
            "• Xem mức phí thuê theo ngày minh bạch, đánh giá thực tế từ các đoàn khách trước và gửi yêu cầu đặt lịch trực tiếp."
        )
    if any(phrase in normalized for phrase in ["khuyến mãi", "khuyen mai", "voucher", "mã giảm giá", "ma giam gia", "ưu đãi", "uu dai", "giảm giá", "giam gia"]):
        return (
            "Bạn có thể vào mục 'Khuyến mãi' trên thanh menu để nhận các mã giảm giá hấp dẫn khi đặt tour trên SmartTravel:\n\n"
            "• Mã giảm trực tiếp từ 10% đến 30% giá trị tour hoặc voucher giảm tiền mặt đến 500.000đ.\n"
            "• Khi tiến hành đặt tour, bạn chỉ cần nhập mã voucher vào ô 'Mã giảm giá' tại trang thanh toán để được khấu trừ ngay lập tức.\n"
            "• Bạn cũng có thể đăng ký tài khoản thành viên để lưu trữ và quản lý các voucher cá nhân trong ví ưu đãi."
        )
    if any(phrase in normalized for phrase in ["bản đồ", "ban do", "map", "xem bản đồ"]):
        return (
            "Tính năng 'Bản đồ' trên website SmartTravel mang đến trải nghiệm trực quan toàn diện:\n\n"
            "• Định vị tọa độ và xem vị trí các điểm du lịch nổi tiếng trên khắp 63 tỉnh thành Việt Nam.\n"
            "• Xem điều kiện thời tiết, nhiệt độ thời gian thực được đồng bộ trực tiếp từ trạm khí tượng.\n"
            "• Dễ dàng tìm kiếm và lên lộ trình di chuyển tối ưu cho chuyến đi."
        )
    if any(phrase in normalized for phrase in ["cách đặt tour", "cach dat tour", "đặt tour thế nào", "dat tour the nao", "thanh toán", "thanh toan", "vnpay", "hủy tour", "huy tour", "quy trình đặt"]):
        return (
            "Quy trình đặt tour và thanh toán trên website SmartTravel rất đơn giản, nhanh chóng và an toàn:\n\n"
            "1. Chọn tour: Truy cập mục 'Tour du lịch' hoặc bấm xem chi tiết các tour do trợ lý AI gợi ý.\n"
            "2. Điền thông tin: Chọn ngày khởi hành mong muốn, số lượng hành khách và thông tin liên hệ.\n"
            "3. Áp dụng ưu đãi: Nhập mã voucher khuyến mãi (nếu có) để nhận giảm giá.\n"
            "4. Thanh toán: Xác nhận và thanh toán trực tuyến qua cổng VNPay bảo mật (hỗ trợ quét mã VNPAY-QR, thẻ ATM nội địa hoặc thẻ quốc tế)."
        )
    if any(phrase in normalized for phrase in ["web có gì", "trang web", "smarttravel", "dự án", "tính năng", "chức năng", "website có gì"]):
        return (
            "SmartTravel là hệ thống du lịch thông minh toàn diện, tích hợp các dịch vụ cốt lõi:\n\n"
            "• Đặt tour du lịch trực tuyến: Đa dạng các hành trình biển đảo, nghỉ dưỡng, văn hóa lịch sử và khám phá thiên nhiên với giá niêm yết rõ ràng.\n"
            "• Thuê Hướng dẫn viên bản địa: Kết nối HDV chuyên nghiệp đã được chứng thực định danh CCCD/KYC.\n"
            "• Bản đồ & Thời tiết 63 tỉnh thành: Cập nhật liên tục thời tiết thực tế để bạn chọn thời điểm du lịch lý tưởng.\n"
            "• Khuyến mãi & Thanh toán an toàn: Kho voucher phong phú và thanh toán trực tuyến qua VNPay."
        )
    return None


def _needs_travel_guidance(message: str) -> bool:
    normalized = message.lower()
    return any(keyword in normalized for keyword in [
        "tour", "du lịch", "du lich", "đi đâu", "di dau", "lịch trình", "lich trinh",
        "ngân sách", "ngan sach", "tham quan", "đặt tour", "dat tour", "kỳ nghỉ", "ky nghi",
        "thì sao", "thi sao", "có gì", "co gi", "chơi gì", "choi gi", "ăn gì", "an gi",
        "tư vấn", "tu van", "gợi ý", "goi y", "chuyến đi", "chuyen di",
    ])


def _is_weather_request(message: str) -> bool:
    normalized = message.lower()
    return "thời tiết" in normalized or "thoi tiet" in normalized or "mưa không" in normalized or "mua khong" in normalized


def _guidance_reply(message: str, city: str, max_budget: Optional[float]) -> Optional[str]:
    if not _needs_travel_guidance(message):
        return None
    if not city and max_budget is not None:
        return f"Ngân sách {max_budget:,.0f}đ của bạn rất tuyệt vời! Bạn đang muốn tìm tour hoặc khám phá tỉnh thành nào (ví dụ: Hà Giang, Đà Nẵng, Đà Lạt, Sa Pa, Phú Quốc, Nha Trang, Ninh Bình...)?"
    return None


def _extract_budget(message: str) -> Optional[float]:
    normalized = message.lower().replace(" ", "")
    match = re.search(r"(?:dưới|duoi|tốiđa|toida|khôngquá|khongqua|\bgiá\b|\bgia\b)\D{0,8}(\d[\d.,]*)\s*(triệu|tr|k|nghìn|nghin)?", normalized)
    if not match:
        match = re.search(r"(\d[\d.,]*)\s*(triệu|tr)\b", normalized)
    if not match:
        return None
    amount_text = match.group(1)
    unit = match.group(2) or ""
    if unit:
        amount = float(amount_text.replace(",", "."))
    elif re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", amount_text):
        amount = float(amount_text.replace(".", "").replace(",", ""))
    else:
        amount = float(amount_text.replace(",", "."))
    if unit in {"triệu", "tr"}:
        amount *= 1_000_000
    elif unit in {"k", "nghìn", "nghin"}:
        amount *= 1_000
    elif amount < 1000:
        amount *= 1_000_000
    return amount


def _extract_city(message: str, requested_city: Optional[str]) -> str:
    if requested_city and requested_city.strip():
        req = requested_city.strip().lower()
        if req in CANONICAL_CITY_NAMES:
            return CANONICAL_CITY_NAMES[req]
        for key, aliases in LOCATION_ALIASES.items():
            if any(alias in req for alias in aliases):
                return CANONICAL_CITY_NAMES.get(key, requested_city.strip())
        return requested_city.strip()

    lowered = message.lower()
    matches = []
    for key, aliases in LOCATION_ALIASES.items():
        for alias in aliases:
            escaped = re.escape(alias)
            match = re.search(r"(?<![a-zA-ZÀ-ỹ0-9])" + escaped + r"(?![a-zA-ZÀ-ỹ0-9])", lowered)
            if match:
                matches.append((len(alias), CANONICAL_CITY_NAMES.get(key, key.title())))
    if matches:
        matches.sort(key=lambda item: item[0], reverse=True)
        return matches[0][1]
    return ""


async def _load_history(session_id: Optional[str]) -> List[Dict[str, str]]:
    if not session_id:
        return []
    db = get_db()
    if db is None:
        return []
    session = await db.chat_sessions.find_one({"session_id": session_id})
    return session.get("messages", [])[-CHAT_HISTORY_LIMIT:] if session else []


async def _save_history(session_id: Optional[str], user_message: str, assistant_message: str) -> None:
    if not session_id:
        return
    db = get_db()
    if db is None:
        return
    await db.chat_sessions.update_one(
        {"session_id": session_id},
        {
            "$push": {
                "messages": {
                    "$each": [
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": assistant_message},
                    ],
                    "$slice": -CHAT_HISTORY_LIMIT,
                }
            },
            "$set": {"updated_at": monotonic()},
        },
        upsert=True,
    )


def _weather_condition(weather: Dict[str, Any]) -> str:
    main = str(weather.get("weather", [{}])[0].get("main", "")).lower()
    temperature = weather.get("main", {}).get("temp")
    if "rain" in main or "drizzle" in main or "thunder" in main:
        return "rain"
    if isinstance(temperature, (int, float)) and temperature >= 32:
        return "hot"
    if isinstance(temperature, (int, float)) and temperature <= 18:
        return "cool"
    if "cloud" in main:
        return "cloudy"
    if "clear" in main:
        return "clear"
    return "unknown"


async def _get_weather(city: str) -> WeatherSnapshot:
    cache_key = city.strip().lower()
    cached = _weather_cache.get(cache_key)
    if cached and monotonic() - cached[0] < 600:
        return cached[1]
    coordinates = CITY_COORDINATES.get(cache_key)
    if not coordinates:
        for k, coords in CITY_COORDINATES.items():
            if k in cache_key or cache_key in k:
                coordinates = coords
                break
    if coordinates:
        params = {
            "latitude": coordinates[0],
            "longitude": coordinates[1],
            "current": "temperature_2m,weather_code",
            "timezone": "Asia/Bangkok",
        }
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            snapshot = _weather_from_open_meteo(city, response.json())
            _weather_cache[cache_key] = (monotonic(), snapshot)
            return snapshot
        except (httpx.HTTPError, ValueError, KeyError):
            return _cached_weather(city)

    if not settings.OPENWEATHER_API_KEY:
        return WeatherSnapshot(city=city, condition="unknown")

    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "vi",
    }
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(
                f"{settings.OPENWEATHER_BASE_URL}/weather", params=params
            )
        response.raise_for_status()
        data = response.json()
        snapshot = WeatherSnapshot(
            city=data.get("name", city),
            condition=_weather_condition(data),
            temperature=data.get("main", {}).get("temp"),
            description=data.get("weather", [{}])[0].get("description"),
        )
        _weather_cache[cache_key] = (monotonic(), snapshot)
        return snapshot
    except (httpx.HTTPError, ValueError, KeyError):
        return WeatherSnapshot(city=city, condition="unknown")


async def _find_tours(city: str, weather: WeatherSnapshot, max_budget: Optional[float] = None) -> List[Dict[str, Any]]:
    db = get_db()
    if db is None:
        return []

    query: Dict[str, Any] = {"is_active": True}
    if city:
        key = city.strip().lower()
        aliases = LOCATION_ALIASES.get(key, [key, city.strip()])
        regex_patterns = [re.escape(alias) for alias in aliases]
        pattern_str = "|".join(regex_patterns)
        query["$or"] = [
            {"location": {"$regex": pattern_str, "$options": "i"}},
            {"title": {"$regex": pattern_str, "$options": "i"}},
            {"tags": {"$elemMatch": {"$regex": pattern_str, "$options": "i"}}},
            {"description": {"$regex": pattern_str, "$options": "i"}},
        ]

    tours = await db.tours.find(query).sort([("rating", -1), ("review_count", -1)]).to_list(40)

    if max_budget is not None:
        tours = [
            tour for tour in tours
            if float(tour.get("discount_price") or tour.get("price") or 0) <= max_budget
        ]

    if weather.condition == "rain":
        indoor_tours = [tour for tour in tours if tour.get("indoor") is True]
        if indoor_tours:
            tours = indoor_tours + [tour for tour in tours if tour not in indoor_tours]

    return tours[:24]


def _tour_context(tours: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "tour_id": str(tour.get("_id")),
            "title": tour.get("title", "Tour"),
            "location": tour.get("location", ""),
            "price": tour.get("discount_price", tour.get("price", 0)),
            "rating": tour.get("rating", 0),
            "tags": tour.get("tags", []),
            "indoor": tour.get("indoor", False),
            "outdoor": tour.get("outdoor", True),
            "best_weather": tour.get("best_weather", []),
            "estimated_duration_hours": tour.get("estimated_duration_hours"),
            "difficulty_level": tour.get("difficulty_level"),
            "suitable_for_children": tour.get("suitable_for_children", True),
            "suitable_for_elderly": tour.get("suitable_for_elderly", True),
            "image_url": (tour.get("images") or [None])[0],
        }
        for tour in tours
    ]


def _extract_json(text: str) -> Dict[str, Any]:
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("Gemini returned invalid JSON")
        return json.loads(match.group(0))


async def _ask_gemini(
    request: ChatRequest,
    weather: WeatherSnapshot,
    tours: List[Dict[str, Any]],
    history: List[Dict[str, str]],
    max_budget: Optional[float],
) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Chưa cấu hình GEMINI_API_KEY trong backend/.env")

    city = _extract_city(request.message, request.city)
    key = city.lower() if city else ""
    city_guide = CITY_HIGHLIGHTS.get(key, {})

    prompt = {
        "user_query": request.message,
        "destination": city,
        "destination_guide": city_guide,
        "conversation_history": history,
        "max_budget": max_budget,
        "weather": weather.model_dump(),
        "tour_catalog": _tour_context(tours),
        "instructions": [
            "Trả về duy nhất JSON hợp lệ, không markdown.",
            "Trả lời câu hỏi của người dùng thật đầy đủ, nhiệt tình, logic và tuyệt đối chính xác về địa lý Việt Nam.",
            "Nếu người dùng hỏi về điểm đến, cẩm nang du lịch: Hãy cung cấp danh sách địa điểm nổi bật, nét đặc sắc ẩm thực và lịch trình khám phá chi tiết.",
            "Chỉ đề xuất các tour có tour_id nằm trong tour_catalog. Tuyệt đối không bịa đặt tour hoặc id ảo.",
            "Nếu tour_catalog rỗng, để recommendations là mảng rỗng [] và thông báo rõ ràng rằng hiện hệ thống chưa mở bán tour trọn gói trực tiếp tại điểm đến này.",
            "Nếu thời tiết mưa, nhắc người dùng mang ô và ưu tiên các điểm trong nhà.",
            "Viết câu trả lời bằng tiếng Việt hấp dẫn và tự nhiên.",
        ],
        "output_schema": {
            "message": "string",
            "itinerary": [
                {
                    "day": "positive integer",
                    "title": "string",
                    "activities": ["string"],
                }
            ],
            "recommendations": [
                {
                    "tour_id": "string from tour_catalog",
                    "reason": "string",
                }
            ],
        },
    }
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}],
        "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"},
    }

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(endpoint, json=payload)
        if response.status_code in (401, 403):
            raise HTTPException(status_code=502, detail="Gemini từ chối API key. Hãy kiểm tra GEMINI_API_KEY.")
        if response.status_code == 404:
            raise HTTPException(status_code=502, detail=f"Gemini không tìm thấy model {settings.GEMINI_MODEL}.")
        if response.status_code == 429:
            raise HTTPException(status_code=502, detail="Gemini đã hết quota hoặc vượt giới hạn request.")
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return _extract_json(text)
    except HTTPException:
        raise
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Không thể nhận phản hồi hợp lệ từ Gemini") from exc


def _fallback_result(
    city: str,
    tours: List[Dict[str, Any]],
    weather: WeatherSnapshot,
    max_budget: Optional[float]
) -> Dict[str, Any]:
    key = city.strip().lower() if city else ""
    info = None
    if key:
        info = CITY_HIGHLIGHTS.get(key)
        if not info:
            for k, v in CITY_HIGHLIGHTS.items():
                if k in key or key in k:
                    info = v
                    break

    if info:
        title = info.get("title", f"Khám phá {city}")
        intro = info.get("intro", f"{city} là điểm đến tuyệt vời với cảnh quan thiên nhiên và trải nghiệm đặc sắc.")
        spots = info.get("spots", [])
        spot_lines = "\n".join([f"• {spot}" for spot in spots])

        weather_tip = ""
        if weather.condition == "rain":
            weather_tip = f"\n\nThời tiết hiện tại ở {weather.city} có mưa rải rác ({round(weather.temperature) if weather.temperature is not None else '--'}°C). Bạn nên chuẩn bị theo ô hoặc áo mưa tiện lợi, và ưu tiên ghé thăm các điểm tham quan trong nhà hoặc các quán cà phê ngắm cảnh tuyệt đẹp."
        elif weather.condition == "cool":
            weather_tip = f"\n\nThời tiết hiện tại se lạnh mát mẻ ({round(weather.temperature) if weather.temperature is not None else '--'}°C), vô cùng lý tưởng cho các hoạt động dã ngoại ngoài trời, săn mây và chụp ảnh check-in."
        elif weather.condition in {"clear", "hot"}:
            weather_tip = f"\n\nThời tiết hiện tại nắng ráo trong xanh ({round(weather.temperature) if weather.temperature is not None else '--'}°C), rất thuận lợi cho việc di chuyển khám phá các danh thắng nổi tiếng."

        if tours:
            conclusion = f"\n\nDưới đây là lịch trình gợi ý chi tiết cùng các tour du lịch {city} chất lượng cao đang sẵn sàng phục vụ bạn:"
            recommendations = [
                {
                    "tour_id": str(tour.get("_id")),
                    "reason": f"Tour khám phá {city} nổi bật, đánh giá {tour.get('rating', 4.9)}⭐ với lịch trình chuyên nghiệp.",
                }
                for tour in tours[:6]
            ]
        else:
            conclusion = f"\n\nHiện tại trên hệ thống SmartTravel chưa mở bán tour trọn gói trực tiếp tại {city}. Dưới đây là lịch trình gợi ý chi tiết cùng các điểm đến đặc sắc để bạn tự túc lên kế hoạch và trải nghiệm thuận tiện nhất nhé:"
            recommendations = []

        message = f"🌟 {title}\n\n{intro}\n\n{spot_lines}{weather_tip}{conclusion}"
        itinerary = info.get("itinerary", [])
        return {
            "message": message,
            "itinerary": itinerary,
            "recommendations": recommendations,
        }

    if city and not tours:
        return {
            "message": f"🌟 Khám phá {city}\n\n{city} là điểm đến mang nhiều nét đẹp thiên nhiên và văn hóa đặc trưng. Hiện tại hệ thống SmartTravel chưa mở bán tour trọn gói tại {city}, nhưng bạn hoàn toàn có thể tự túc lên kế hoạch khám phá các danh lam thắng cảnh và ẩm thực địa phương đặc sắc nơi đây.",
            "itinerary": [],
            "recommendations": [],
        }

    if tours and not city:
        if max_budget is not None:
            message = f"Dựa trên ngân sách tối ưu {max_budget:,.0f}đ của bạn, SmartTravel xin chọn lọc các tour du lịch chất lượng cao có sẵn trên hệ thống:"
        else:
            message = "Chào bạn! Dưới đây là các tour du lịch được đánh giá cao nhất đang có trên hệ thống SmartTravel. Bạn có thể bấm xem chi tiết từng tour hoặc đặt vé trực tiếp:"
        return {
            "message": message,
            "itinerary": [],
            "recommendations": [
                {
                    "tour_id": str(tour.get("_id")),
                    "reason": f"Tour du lịch {tour.get('location', '')} nổi bật, đánh giá {tour.get('rating', 4.8)} sao.",
                }
                for tour in tours[:6]
            ],
        }

    return {
        "message": "SmartTravel luôn sẵn sàng đồng hành cùng bạn trên khắp 63 tỉnh thành Việt Nam! Bạn có thể cho mình biết điểm đến mong muốn (ví dụ: Đà Lạt, Sa Pa, Hà Giang, Phú Thọ, Nha Trang, Phú Quốc...) hoặc khoảng ngân sách để mình hỗ trợ chu đáo nhất nhé.",
        "itinerary": [],
        "recommendations": [],
    }


@router.get("/weather", response_model=WeatherSnapshot)
async def weather(city: str = Query("Hà Nội", min_length=1, max_length=100)):
    try:
        return await asyncio.wait_for(_get_weather(city.strip()), timeout=3.5)
    except asyncio.TimeoutError:
        return _cached_weather(city.strip())


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    client_key = http_request.client.host if http_request.client else "unknown"
    now = monotonic()
    recent = [timestamp for timestamp in _chat_requests.get(client_key, []) if now - timestamp < CHAT_WINDOW_SECONDS]
    if len(recent) >= CHAT_LIMIT:
        raise HTTPException(status_code=429, detail="Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau một phút.")
    recent.append(now)
    _chat_requests[client_key] = recent

    city = _extract_city(request.message, request.city)
    max_budget = _extract_budget(request.message)

    coverage_reply = _coverage_reply(request.message)
    if coverage_reply:
        weather_snapshot = _cached_weather("Hà Nội")
        tours = await _find_tours("", weather_snapshot, None)
        recommendations = [
            Recommendation(
                tour_id=str(tour["_id"]),
                title=tour.get("title", "Tour"),
                reason=f"Tour du lịch {tour.get('location', '')} chất lượng cao, đánh giá {tour.get('rating', 4.9)}⭐.",
                estimated_price=tour.get("discount_price", tour.get("price", 0)),
                image_url=(tour.get("images") or [None])[0],
                location=tour.get("location", ""),
            )
            for tour in tours[:6]
        ]
        response = ChatResponse(
            message=coverage_reply,
            recommendations=recommendations,
            itinerary=[],
            weather=weather_snapshot,
        )
        await _save_history(request.session_id, request.message, response.message)
        return response

    feature_reply = _feature_reply(request.message)
    if feature_reply:
        response = ChatResponse(
            message=feature_reply,
            recommendations=[],
            itinerary=[],
            weather=_cached_weather(city or "Hà Nội"),
        )
        await _save_history(request.session_id, request.message, response.message)
        return response

    casual_reply = _casual_reply(request.message)
    if casual_reply:
        response = ChatResponse(
            message=casual_reply,
            recommendations=[],
            itinerary=[],
            weather=_cached_weather(city or "Hà Nội"),
        )
        await _save_history(request.session_id, request.message, response.message)
        return response

    guidance_reply = _guidance_reply(request.message, city, max_budget)
    if guidance_reply:
        response = ChatResponse(
            message=guidance_reply,
            recommendations=[],
            itinerary=[],
            weather=_cached_weather(city or "Hà Nội"),
        )
        await _save_history(request.session_id, request.message, response.message)
        return response

    try:
        weather_snapshot = await asyncio.wait_for(_get_weather(city or "Hà Nội"), timeout=3.5)
    except asyncio.TimeoutError:
        weather_snapshot = _cached_weather(city or "Hà Nội")

    if _is_weather_request(request.message):
        weather_text = weather_snapshot.description or "Mình chưa lấy được dữ liệu thời tiết mới nhất."
        temperature_text = f" Nhiệt độ hiện tại khoảng {round(weather_snapshot.temperature)}°C." if weather_snapshot.temperature is not None else ""
        response = ChatResponse(
            message=f"Thời tiết ở {weather_snapshot.city}: {weather_text}.{temperature_text}",
            recommendations=[],
            itinerary=[],
            weather=weather_snapshot,
        )
        await _save_history(request.session_id, request.message, response.message)
        return response

    tours = await _find_tours(city, weather_snapshot, max_budget)
    catalog_by_id = {str(tour.get("_id")): tour for tour in tours}
    history = await _load_history(request.session_id)

    ai_result = None
    if settings.GEMINI_API_KEY:
        try:
            ai_result = await _ask_gemini(request, weather_snapshot, tours, history, max_budget)
        except Exception:
            ai_result = None

    if not ai_result:
        ai_result = _fallback_result(city, tours, weather_snapshot, max_budget)

    recommendations = []
    raw_recommendations = ai_result.get("recommendations") or []
    for item in raw_recommendations:
        if not isinstance(item, dict):
            continue
        tour = catalog_by_id.get(str(item.get("tour_id")))
        if not tour:
            continue
        recommendations.append(
            Recommendation(
                tour_id=str(tour["_id"]),
                title=tour.get("title", "Tour"),
                reason=item.get("reason", "Phù hợp với yêu cầu của bạn."),
                estimated_price=tour.get("discount_price", tour.get("price", 0)),
                image_url=(tour.get("images") or [None])[0],
                location=tour.get("location", ""),
            )
        )

    itinerary = []
    raw_itinerary = ai_result.get("itinerary") or []
    for item in raw_itinerary:
        if not isinstance(item, dict):
            continue
        try:
            day = int(item.get("day"))
        except (TypeError, ValueError):
            continue
        activities = item.get("activities", [])
        if not isinstance(activities, list):
            activities = [str(activities)]
        itinerary.append(
            ItineraryDay(
                day=max(1, day),
                title=str(item.get("title") or f"Ngày {day}"),
                activities=[str(activity) for activity in activities[:8]],
            )
        )

    response = ChatResponse(
        message=ai_result.get("message", "Mình đã tìm thấy một số lựa chọn phù hợp."),
        recommendations=recommendations,
        itinerary=itinerary[:7],
        weather=weather_snapshot,
    )
    await _save_history(request.session_id, request.message, response.message)
    return response
