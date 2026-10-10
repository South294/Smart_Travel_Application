var userLatLng = null;
var virtualLatLng = null;
var activeCategory = 'all';
var currentViewMode = 'local';
var filterRadius10km = true;
var isLoggedIn = false;
var hasActiveBooking = false;
var locationRequired = false;
var hasLocationPermission = false;
var wasSkipped = false;
var selectedPlaceId = null;
var isSimulating = false;
var simulationInterval = null;
var simulationStep = 0;
var simulationWaypoints = [];
var watchPositionId = null;

var PLACES_DATA = [
    {
        "id": "hoan-kiem-lake",
        "name": "Hồ Hoàn Kiếm",
        "category": "tourist",
        "lat": 21.0285,
        "lng": 105.8542,
        "rating": 4.9,
        "reviews": 5800,
        "address": "Quận Hoàn Kiếm, Hà Nội",
        "image": "images/hoan_kiem_lake.png",
        "desc": "Trái tim của thủ đô Hà Nội với Tháp Rùa cổ kính, Đền Ngọc Sơn và cầu Thê Húc cong cong son đỏ.",
        "bestMonths": "Tháng 9 - 4",
        "tip": "Dạo quanh hồ vào sáng sớm hoặc buổi tối để tận hưởng không khí trong lành."
    },
    {
        "id": "temple-literature",
        "name": "Văn Miếu - Quốc Tử Giám",
        "category": "tourist",
        "lat": 21.0294,
        "lng": 105.8355,
        "rating": 4.8,
        "reviews": 4500,
        "address": "58 Quốc Tử Giám, Đống Đa, Hà Nội",
        "image": "images/temple_literature.png",
        "desc": "Trường đại học đầu tiên của Việt Nam, biểu tượng cho truyền thống hiếu học ngàn năm văn hiến.",
        "bestMonths": "Tháng 10 - 3",
        "tip": "Nên mang trang phục lịch sự và chuẩn bị máy ảnh để lưu lại kiến trúc gỗ cổ truyền."
    },
    {
        "id": "thang-long-citadel",
        "name": "Hoàng Thành Thăng Long",
        "category": "tourist",
        "lat": 21.0358,
        "lng": 105.84,
        "rating": 4.6,
        "reviews": 3400,
        "address": "19C Hoàng Diệu, Ba Đình, Hà Nội",
        "image": "images/thang_long_citadel.png",
        "desc": "Di sản Văn hóa Thế giới UNESCO gắn liền với hơn 1000 năm lịch sử triều đại phong kiến Thăng Long.",
        "bestMonths": "Tháng 9 - 2",
        "tip": "Dành 2-3 giờ để tham quan các khu khảo cổ và Cột cờ Hà Nội."
    },
    {
        "id": "st-joseph-cathedral",
        "name": "Nhà Thờ Lớn Hà Nội",
        "category": "tourist",
        "lat": 21.0288,
        "lng": 105.849,
        "rating": 4.5,
        "reviews": 2100,
        "address": "40 Nhà Chung, Hoàn Kiếm, Hà Nội",
        "image": "images/cathedral_hanoi.png",
        "desc": "Nhà thờ kiến trúc Gothic cổ kính giữa lòng phố cổ, điểm check-in văn hóa quen thuộc của du khách.",
        "bestMonths": "Tháng 11 - 2",
        "tip": "Uống trà chanh Nhà Thờ và ngắm ánh hoàng hôn buông xuống nhà thờ."
    },
    {
        "id": "ethnology-museum",
        "name": "Bảo tàng Dân tộc học",
        "category": "tourist",
        "lat": 21.0412,
        "lng": 105.8007,
        "rating": 4.7,
        "reviews": 1800,
        "address": "Nguyễn Văn Huyên, Cầu Giấy, Hà Nội",
        "image": "images/museum_ethnology.png",
        "desc": "Không gian trưng bày sống động văn hóa 54 dân tộc anh em với khu nhà sàn ngoài trời độc đáo.",
        "bestMonths": "Tháng 9 - 4",
        "tip": "Ghé khu trưng bày kiến trúc ngoài trời để trải nghiệm nhà rông và nhà mồ Tây Nguyên."
    },
    {
        "id": "chua-mot-cot",
        "name": "Chùa Một Cột",
        "category": "tourist",
        "lat": 21.0358,
        "lng": 105.8335,
        "rating": 4.8,
        "reviews": 4300,
        "address": "Phố Chùa Một Cột, Đội Cấn, Ba Đình, Hà Nội",
        "image": "images/chua_mot_cot.jpg",
        "desc": "Ngôi chùa cổ kính độc nhất vô nhị xây dựng trên một cột đá giữa hồ sen, biểu tượng văn hóa ngàn năm Thăng Long.",
        "bestMonths": "Quanh năm",
        "tip": "Nằm ngay cạnh quần thể Lăng Bác và Quảng trường Ba Đình."
    },
    {
        "id": "lang-bac",
        "name": "Lăng Chủ tịch Hồ Chí Minh",
        "category": "tourist",
        "lat": 21.0368,
        "lng": 105.8346,
        "rating": 4.9,
        "reviews": 9200,
        "address": "2 Hùng Vương, Điện Bàn, Ba Đình, Hà Nội",
        "image": "images/lang_bac.jpg",
        "desc": "Nơi an nghỉ vĩnh hằng của Chủ tịch Hồ Chí Minh, công trình kiến trúc thiêng liêng giữa Quảng trường Ba Đình lịch sử.",
        "bestMonths": "Quanh năm",
        "tip": "Mặc trang phục chỉnh tề, giữ trật tự và đến sớm các buổi sáng trong tuần."
    },
    {
        "id": "hoa-lo-prison",
        "name": "Di tích Lịch sử Nhà tù Hỏa Lò",
        "category": "tourist",
        "lat": 21.0253,
        "lng": 105.8465,
        "rating": 4.9,
        "reviews": 6700,
        "address": "1 Hỏa Lò, Trần Hưng Đạo, Hoàn Kiếm, Hà Nội",
        "image": "images/hoa_lo_prison.jpg",
        "desc": "Di tích lịch sử Maison Centrale nổi tiếng với các tour trải nghiệm đêm tái hiện tinh thần kiên cường của các chiến sĩ cách mạng.",
        "bestMonths": "Quanh năm",
        "tip": "Nên thuê tai nghe thuyết minh tự động (audio guide) để nghe các câu chuyện lịch sử xúc động."
    },
    {
        "id": "tran-quoc-pagoda",
        "name": "Chùa Trấn Quốc",
        "category": "tourist",
        "lat": 21.0478,
        "lng": 105.8368,
        "rating": 4.7,
        "reviews": 4800,
        "address": "Đường Thanh Niên, Yên Phụ, Tây Hồ, Hà Nội",
        "image": "images/tran_quoc_pagoda.jpg",
        "desc": "Ngôi chùa cổ nhất thủ đô hơn 1500 năm tuổi tọa lạc trên bán đảo xanh tươi bên bờ Hồ Tây thơ mộng.",
        "bestMonths": "Quanh năm",
        "tip": "Thời khắc hoàng hôn buông xuống trên bảo tháp lục độ đài sen là cảnh đẹp không thể bỏ lỡ."
    },
    {
        "id": "long-bien-bridge",
        "name": "Cầu Long Biên Lịch Sử",
        "category": "tourist",
        "lat": 21.0425,
        "lng": 105.856,
        "rating": 4.7,
        "reviews": 3600,
        "address": "Cầu Long Biên, Đồng Xuân, Hoàn Kiếm, Hà Nội",
        "image": "images/long_bien_bridge.jpg",
        "desc": "Cây cầu thép lịch sử bắc qua sông Hồng do Pháp xây dựng đầu thế kỷ 20, chứng nhân lịch sử kiên cường của Hà Nội.",
        "bestMonths": "Tháng 10 - 3",
        "tip": "Ghé các quán cà phê bãi giữa hoặc đi dạo trên làn bộ hành ngắm hoàng hôn sông Hồng."
    },
    {
        "id": "hanoi-opera-house",
        "name": "Nhà Hát Lớn Hà Nội",
        "category": "tourist",
        "lat": 21.0242,
        "lng": 105.8576,
        "rating": 4.8,
        "reviews": 3100,
        "address": "1 Tràng Tiền, Phan Chu Trinh, Hoàn Kiếm, Hà Nội",
        "image": "images/hanoi_opera_house.jpg",
        "desc": "Kiệt tác kiến trúc Tân cổ điển phong cách Pháp đầu thế kỷ 20, cái nôi biểu diễn nghệ thuật hàn lâm của thủ đô.",
        "bestMonths": "Quanh năm",
        "tip": "Quảng trường Cách Mạng Tháng Tám phía trước là điểm ngắm cảnh và chụp ảnh tuyệt đẹp về đêm."
    },
    {
        "id": "lang-lua-van-phuc",
        "name": "Làng lụa cổ Vạn Phúc Hà Đông",
        "category": "tourist",
        "lat": 20.9805,
        "lng": 105.7745,
        "rating": 4.6,
        "reviews": 2800,
        "address": "Phố Lụa, Vạn Phúc, Hà Đông, Hà Nội",
        "image": "images/lang_lua_van_phuc.jpg",
        "desc": "Làng nghề dệt lụa tơ tằm truyền thống lâu đời hơn 1000 năm với con đường ô dù rực rỡ sắc màu và xưởng dệt cổ.",
        "bestMonths": "Quanh năm",
        "tip": "Trải nghiệm quy trình ươm tơ dệt lụa thủ công và mua sắm khăn lụa tơ tằm nguyên chất."
    },
    {
        "id": "bat-trang-pottery",
        "name": "Làng Gốm Cổ Bát Tràng",
        "category": "tourist",
        "lat": 20.9782,
        "lng": 105.9125,
        "rating": 4.7,
        "reviews": 4600,
        "address": "Xã Bát Tràng, Gia Lâm, Hà Nội",
        "image": "images/bat_trang_pottery.jpg",
        "desc": "Làng nghề gốm sứ truyền thống trứ danh với bảo tàng gốm kiến trúc xoắn ốc đất nung độc đáo ven sông Hồng.",
        "bestMonths": "Quanh năm",
        "tip": "Tự tay nặn gốm trên bàn xoay và thưởng thức món canh măng mực truyền thống Bát Tràng."
    },
    {
        "id": "bao-tang-ha-noi",
        "name": "Bảo Tàng Hà Nội",
        "category": "tourist",
        "lat": 21.0089,
        "lng": 105.7892,
        "rating": 4.5,
        "reviews": 2400,
        "address": "Đường Phạm Hùng, Mễ Trì, Nam Từ Liêm, Hà Nội",
        "image": "images/bao_tang_ha_noi.jpg",
        "desc": "Công trình kiến trúc hình kim tự tháp ngược ấn tượng lưu giữ hàng nghìn cổ vật quý giá về lịch sử Thăng Long.",
        "bestMonths": "Quanh năm",
        "tip": "Nằm ngay đối diện Trung tâm Hội nghị Quốc gia, khuôn viên cây xanh mát mẻ."
    },
    {
        "id": "cong-vien-yen-so",
        "name": "Công Viên Yên Sở",
        "category": "tourist",
        "lat": 20.9734,
        "lng": 105.8525,
        "rating": 4.6,
        "reviews": 3200,
        "address": "Quốc lộ 1A, Yên Sở, Hoàng Mai, Hà Nội",
        "image": "images/cong_vien_yen_so.jpg",
        "desc": "Công viên sinh thái đô thị lớn nhất Hà Nội với thảm cỏ xanh mướt, hồ nước bao la lý tưởng để dã ngoại cắm trại.",
        "bestMonths": "Tháng 9 - 4",
        "tip": "Địa điểm tuyệt vời để tổ chức tiệc BBQ ngoài trời và đạp xe cuối tuần."
    },
    {
        "id": "den-quan-thanh",
        "name": "Đền Quán Thánh",
        "category": "tourist",
        "lat": 21.0435,
        "lng": 105.8362,
        "rating": 4.6,
        "reviews": 2100,
        "address": "Đường Thanh Niên, Quán Thánh, Ba Đình, Hà Nội",
        "image": "images/den_quan_thanh.jpg",
        "desc": "Một trong Thăng Long Tứ Trấn thờ Huyền Thiên Trấn Vũ với pho tượng đồng đen khổng lồ đúc từ thế kỷ 17.",
        "bestMonths": "Quanh năm",
        "tip": "Nằm ngay ngã tư đường Cổ Ngư xưa nhìn ra Hồ Trúc Bạch."
    },
    {
        "id": "hanoi-train-street",
        "name": "Phố Đường Tàu Hà Nội",
        "category": "tourist",
        "lat": 21.0298,
        "lng": 105.8428,
        "rating": 4.7,
        "reviews": 5100,
        "address": "Phố Phùng Hưng, Hàng Bông, Hoàn Kiếm, Hà Nội",
        "image": "images/hanoi_train_street.jpg",
        "desc": "Con ngõ độc đáo nơi đường ray xe lửa chạy sát các căn nhà cổ, điểm ngắm tàu hỏa và thưởng thức cà phê đường tàu.",
        "bestMonths": "Quanh năm",
        "tip": "Kiểm tra giờ tàu chạy và tuân thủ tuyệt đối tín hiệu an toàn của nhân viên đường sắt."
    },
    {
        "id": "chua-huong",
        "name": "Quần Thể Danh Thắng Chùa Hương",
        "category": "tourist",
        "lat": 20.6175,
        "lng": 105.7535,
        "rating": 4.8,
        "reviews": 5700,
        "address": "Xã Hương Sơn, Huyện Mỹ Đức, Hà Nội",
        "image": "images/chua_huong.jpg",
        "desc": "Miền đất Phật linh thiêng với dòng suối Yến êm đềm và động Hương Tích được xưng tụng Nam Thiên Đệ Nhất Động.",
        "bestMonths": "Tháng 1 - 3 âm lịch",
        "tip": "Trải nghiệm đi đò suối Yến vào mùa hoa súng nở rộ sắc tím tuyệt đẹp."
    },
    {
        "id": "den-hung-phu-tho",
        "name": "Khu Di tích Lịch sử Đền Hùng",
        "category": "tourist",
        "lat": 21.3653,
        "lng": 105.3267,
        "rating": 4.9,
        "reviews": 5100,
        "address": "Xã Hy Cương, TP. Việt Trì, Phú Thọ",
        "image": "images/den_hung_phu_tho.jpg",
        "desc": "Vùng đất cội nguồn linh thiêng của dân tộc Việt Nam, nơi thờ tự các Vua Hùng có công dựng nước.",
        "bestMonths": "Tháng 3 âm lịch",
        "tip": "Nên mang giày thể thao thoải mái để leo bậc thang lên Đền Thượng và Đền Giếng."
    },
    {
        "id": "trang-an-ninh-binh",
        "name": "Quần thể Danh thắng Tràng An",
        "category": "tourist",
        "lat": 20.2506,
        "lng": 105.9149,
        "rating": 4.9,
        "reviews": 6400,
        "address": "Huyện Hoa Lư, Ninh Bình",
        "image": "images/trang_an_ninh_binh.jpg",
        "desc": "Di sản hỗn hợp Văn hóa và Thiên nhiên Thế giới với cảnh quan thung lũng đá vôi và sông nước thanh bình.",
        "bestMonths": "Tháng 1 - 4",
        "tip": "Chọn tuyến thuyền số 2 hoặc 3 để đi qua nhiều hang động và phim trường Kong Skull Island."
    },
    {
        "id": "chua-bai-dinh",
        "name": "Quần Thể Chùa Bái Đính",
        "category": "tourist",
        "lat": 20.2692,
        "lng": 105.8565,
        "rating": 4.8,
        "reviews": 5900,
        "address": "Xã Gia Sinh, Huyện Gia Viễn, Ninh Bình",
        "image": "images/chua_bai_dinh.jpg",
        "desc": "Ngôi đại tự giữ nhiều kỷ lục châu Á với hành lang 500 vị La Hán bằng đá xanh và tượng Phật dát vàng uy nghiêm.",
        "bestMonths": "Tháng 1 - 3 âm lịch",
        "tip": "Có thể đi xe điện nội khu để thuận tiện di chuyển giữa chùa cổ và điện Tam Thế."
    },
    {
        "id": "tam-chuc-pagoda",
        "name": "Khu Du Lịch Tâm Linh Tam Chúc",
        "category": "tourist",
        "lat": 20.6185,
        "lng": 105.8115,
        "rating": 4.8,
        "reviews": 5300,
        "address": "Thị trấn Ba Sao, Kim Bảng, Hà Nam",
        "image": "images/tam_chuc_pagoda.jpg",
        "desc": "Ngôi chùa tựa lưng vào núi Thất Tinh hướng ra hồ Lục Nhạc, ví như Vịnh Hạ Long trên cạn của vùng đồng bằng Bắc Bộ.",
        "bestMonths": "Tháng 1 - 4",
        "tip": "Đi du thuyền ngắm hoàng hôn buông trên mặt hồ Lục Nhạc thơ mộng."
    },
    {
        "id": "vinh-ha-long",
        "name": "Kỳ Quan Thiên Nhiên Vịnh Hạ Long",
        "category": "tourist",
        "lat": 20.9101,
        "lng": 107.0845,
        "rating": 4.9,
        "reviews": 9800,
        "address": "Thành phố Hạ Long, Quảng Ninh",
        "image": "images/vinh_ha_long.jpg",
        "desc": "Di sản thiên nhiên thế giới UNESCO với hàng nghìn đảo đá vôi kỳ vĩ nhô lên giữa làn nước xanh màu ngọc bích.",
        "bestMonths": "Tháng 3 - 5 & Tháng 9 - 11",
        "tip": "Trải nghiệm du thuyền ngủ đêm trên vịnh và chèo kayak khám phá hang Luồn."
    },
    {
        "id": "pho-thin",
        "name": "Phở Thìn Bờ Hồ",
        "category": "food",
        "lat": 21.029,
        "lng": 105.8525,
        "rating": 4.6,
        "reviews": 2200,
        "address": "61 Đinh Tiên Hoàng, Hoàn Kiếm, Hà Nội",
        "image": "images/pho_bo_hanoi.jpg",
        "desc": "Thương hiệu phở bò gia truyền nổi tiếng với nước dùng trong veo, ngọt thanh và thịt bò tái tươi mềm.",
        "bestMonths": "Quanh năm",
        "tip": "Ăn kèm quẩy giòn và giấm tỏi ớt đặc trưng để cảm nhận trọn vẹn hương vị phở Bắc."
    },
    {
        "id": "pho-bat-dan",
        "name": "Phở Bát Đàn Gia Truyền",
        "category": "food",
        "lat": 21.0335,
        "lng": 105.8465,
        "rating": 4.7,
        "reviews": 3500,
        "address": "49 Bát Đàn, Cửa Đông, Hoàn Kiếm, Hà Nội",
        "image": "images/pho_bat_dan.jpg",
        "desc": "Hương vị phở bò truyền thống lâu đời nhất nhì khu phố cổ với phong cách xếp hàng tự phục vụ đặc sắc.",
        "bestMonths": "Quanh năm",
        "tip": "Nên đến vào khoảng 6h30 đến 7h30 sáng để thưởng thức nước dùng trong và ngọt xương nhất."
    },
    {
        "id": "pho-thin-lo-duc",
        "name": "Phở Thìn 13 Lò Đúc",
        "category": "food",
        "lat": 21.0152,
        "lng": 105.8568,
        "rating": 4.6,
        "reviews": 4100,
        "address": "13 Lò Đúc, Phạm Đình Hổ, Hai Bà Trưng, Hà Nội",
        "image": "images/pho_thin_lo_duc.jpg",
        "desc": "Thương hiệu phở bò tái lăn lừng danh với kỹ thuật xào thịt bò nhanh tay lửa lớn cùng gừng tỏi và ngập tràn hành hoa.",
        "bestMonths": "Quanh năm",
        "tip": "Nước dùng béo ngậy thơm lừng, cho thêm ớt tươi và trứng trần ăn kèm rất tuyệt."
    },
    {
        "id": "pho-ly-quoc-su",
        "name": "Phở Lý Quốc Sư Truyền Thống",
        "category": "food",
        "lat": 21.0305,
        "lng": 105.8492,
        "rating": 4.6,
        "reviews": 3100,
        "address": "10 Lý Quốc Sư, Hàng Trống, Hoàn Kiếm, Hà Nội",
        "image": "images/pho_ly_quoc_su.jpg",
        "desc": "Thương hiệu phở bò nổi tiếng thủ đô với công thức nước hầm xương ống cô đọng thơm lừng thảo mộc.",
        "bestMonths": "Quanh năm",
        "tip": "Nằm ngay đối diện Nhà Thờ Lớn, thuận tiện kết hợp tham quan phố cổ."
    },
    {
        "id": "bun-cha-huong-lien",
        "name": "Bún chả Hương Liên (Obama)",
        "category": "food",
        "lat": 21.0132,
        "lng": 105.8523,
        "rating": 4.5,
        "reviews": 3100,
        "address": "24 Lê Văn Hưu, Hai Bà Trưng, Hà Nội",
        "image": "images/bun_cha_hanoi.jpg",
        "desc": "Quán bún chả từng vinh dự đón Tổng thống Mỹ Barack Obama năm 2016 với chả nướng than hoa thơm lừng.",
        "bestMonths": "Quanh năm",
        "tip": "Nên gọi combo bún chả cùng nem cua bể giòn rụm."
    },
    {
        "id": "bun-cha-cau-den",
        "name": "Bún chả Cầu Đen Hà Đông",
        "category": "food",
        "lat": 20.9745,
        "lng": 105.782,
        "rating": 4.5,
        "reviews": 980,
        "address": "Tô Hiệu, Hà Đông, Hà Nội",
        "image": "images/bun_cha_cau_den.jpg",
        "desc": "Quán bún chả truyền thống nổi danh quận Hà Đông với thịt ba chỉ tẩm ướp đậm đà nướng than hoa vàng rộm.",
        "bestMonths": "Quanh năm",
        "tip": "Nước chấm ấm pha vừa vị, đu đủ cà rốt giòn ngọt."
    },
    {
        "id": "bun-dau-hang-khay",
        "name": "Bún Đậu Mắm Tôm Ngõ 31 Hàng Khay",
        "category": "food",
        "lat": 21.0268,
        "lng": 105.8512,
        "rating": 4.7,
        "reviews": 2900,
        "address": "Ngõ 31 Hàng Khay, Tràng Tiền, Hoàn Kiếm, Hà Nội",
        "image": "images/bun_dau_hang_khay.jpg",
        "desc": "Mẹt bún đậu đầy đặn với đậu mơ rán vàng phồng giòn tan, chả cốm dẻo thơm, dồi sụn nướng và mắm tôm Thanh Hóa đánh sủi bọt.",
        "bestMonths": "Quanh năm",
        "tip": "Quán trong ngõ sâu nhìn thẳng ra Bờ Hồ, nên đi bộ vào để cảm nhận không gian ẩm thực phố cổ."
    },
    {
        "id": "cha-ca-la-vong",
        "name": "Chả cá Lã Vọng",
        "category": "food",
        "lat": 21.034,
        "lng": 105.849,
        "rating": 4.4,
        "reviews": 1600,
        "address": "14 Chả Cá, Hoàn Kiếm, Hà Nội",
        "image": "images/cha_ca_la_vong.jpg",
        "desc": "Món chả cá lăng xào thì là gia truyền danh tiếng hơn một thế kỷ giữa lòng khu phố cổ Hà Nội.",
        "bestMonths": "Quanh năm",
        "tip": "Ăn nóng ngay trên chảo gang cùng bún tươi, lạc rang và mắm tôm đánh sủi bọt."
    },
    {
        "id": "banh-cuon-ba-hoanh",
        "name": "Bánh cuốn Bà Hoành",
        "category": "food",
        "lat": 21.0175,
        "lng": 105.8515,
        "rating": 4.4,
        "reviews": 1350,
        "address": "66 Tô Hiến Thành, Hai Bà Trưng, Hà Nội",
        "image": "images/banh_cuon_hanoi.jpg",
        "desc": "Bánh cuốn tráng mỏng mềm mướt gia truyền ăn kèm chả quế béo ngậy và nước mắm cà cuống thơm lừng.",
        "bestMonths": "Quanh năm",
        "tip": "Rất thích hợp cho bữa sáng hoặc ăn xế chiều nhẹ nhàng."
    },
    {
        "id": "giang-egg-coffee",
        "name": "Cà phê Trứng Giảng",
        "category": "food",
        "lat": 21.0345,
        "lng": 105.8532,
        "rating": 4.8,
        "reviews": 4200,
        "address": "39 Nguyễn Hữu Huân, Hoàn Kiếm, Hà Nội",
        "image": "images/egg_coffee_giang.jpg",
        "desc": "Nơi khai sinh ra món cà phê trứng trứ danh từ năm 1946 với lớp kem trứng béo ngậy thơm ngọt.",
        "bestMonths": "Quanh năm",
        "tip": "Uống nóng khi lớp trứng còn giữ trọn hương vị ngậy ấm áp."
    },
    {
        "id": "cafe-dinh",
        "name": "Cafe Đinh Ban Công Hồ Gươm",
        "category": "food",
        "lat": 21.0315,
        "lng": 105.853,
        "rating": 4.7,
        "reviews": 2900,
        "address": "Tầng 2, 13 Đinh Tiên Hoàng, Hoàn Kiếm, Hà Nội",
        "image": "images/cafe_dinh.jpg",
        "desc": "Quán cà phê cổ kính nép mình trên ban công tầng 2 ngắm trọn vẹn toàn cảnh Tháp Rùa và Hồ Gươm.",
        "bestMonths": "Quanh năm",
        "tip": "Chọn chỗ ngồi sát ban công để ngắm dòng người dạo quanh bờ hồ."
    },
    {
        "id": "banh-mi-25",
        "name": "Bánh Mì 25 Hàng Cá",
        "category": "food",
        "lat": 21.0348,
        "lng": 105.8488,
        "rating": 4.7,
        "reviews": 3800,
        "address": "25 Hàng Cá, Hàng Đào, Hoàn Kiếm, Hà Nội",
        "image": "images/banh_mi_hanoi.jpg",
        "desc": "Tiệm bánh mì giòn rụm với nhân thịt nướng sốt đậm đà, pate gan béo bùi và dưa góp thanh mát hấp dẫn du khách quốc tế.",
        "bestMonths": "Quanh năm",
        "tip": "Bánh mì thập cẩm kèm một ly nước chanh sả đá là sự kết hợp hoàn hảo."
    },
    {
        "id": "pho-cuon-hung-ben",
        "name": "Phở Cuốn Hưng Bền Ngũ Xá",
        "category": "food",
        "lat": 21.0465,
        "lng": 105.8415,
        "rating": 4.5,
        "reviews": 2100,
        "address": "33 Ngũ Xá, Trúc Bạch, Ba Đình, Hà Nội",
        "image": "images/pho_cuon_hanoi.jpg",
        "desc": "Quán phở cuốn nổi danh bán đảo Trúc Bạch với những cuốn phở trắng mềm bọc thịt bò xào thơm lừng và rau thơm tươi non.",
        "bestMonths": "Quanh năm",
        "tip": "Nên gọi thêm món phở chiên phồng trứng và phở chiên trứng giòn rụm."
    },
    {
        "id": "nem-chua-tam-thuong",
        "name": "Nem Chua Rán Ngõ Tạm Thương",
        "category": "food",
        "lat": 21.0318,
        "lng": 105.8472,
        "rating": 4.6,
        "reviews": 2700,
        "address": "Ngõ Tạm Thương, Hàng Gai, Hoàn Kiếm, Hà Nội",
        "image": "images/nem_chua_ran.jpg",
        "desc": "Con ngõ ẩm thực vặt nức tiếng phố cổ với món nem chua rán giòn vỏ dẻo ruột chấm tương ớt cay nồng ăn kèm xoài bao tử.",
        "bestMonths": "Quanh năm",
        "tip": "Thích hợp tụ họp bạn bè buổi tối sau khi đi dạo phố đi bộ."
    },
    {
        "id": "tra-sen-tay-ho",
        "name": "Trà Sen Quảng An Phủ Tây Hồ",
        "category": "food",
        "lat": 21.062,
        "lng": 105.826,
        "rating": 4.8,
        "reviews": 1400,
        "address": "Phố Quảng Khánh, Quảng An, Tây Hồ, Hà Nội",
        "image": "images/tra_sen_tay_ho.jpg",
        "desc": "Nơi gìn giữ nghệ thuật ướp trà sen Bách Diệp cầu kỳ của người Tràng An bên không gian lộng gió Hồ Tây.",
        "bestMonths": "Tháng 5 - 8",
        "tip": "Thưởng thức trà sen nóng vào buổi chiều tà ven hồ để cảm nhận phong vị tao nhã đất kinh kỳ."
    },
    {
        "id": "metropole-hotel-hanoi",
        "name": "Sofitel Legend Metropole Hanoi",
        "category": "hotel",
        "lat": 21.0255,
        "lng": 105.8562,
        "rating": 4.9,
        "reviews": 3200,
        "address": "15 Ngô Quyền, Hoàn Kiếm, Hà Nội",
        "image": "images/metropole_hotel.jpg",
        "desc": "Khách sạn 5 sao mang phong cách kiến trúc Pháp cổ điển sang trọng từ năm 1901 ngay trung tâm thủ đô.",
        "bestMonths": "Quanh năm",
        "tip": "Thưởng thức trà chiều sang trọng tại La Terrasse hoặc cà phê sân vườn."
    },
    {
        "id": "hanoi-pearl-hotel",
        "name": "Hanoi Pearl Hotel Bảo Khánh",
        "category": "hotel",
        "lat": 21.031,
        "lng": 105.8502,
        "rating": 4.6,
        "reviews": 1400,
        "address": "6 Bảo Khánh, Hàng Trống, Hoàn Kiếm, Hà Nội",
        "image": "images/hanoi_pearl_hotel.jpg",
        "desc": "Khách sạn boutique tiện nghi nằm ngay ngõ Bảo Khánh yên tĩnh chỉ cách Hồ Gươm 2 phút đi bộ.",
        "bestMonths": "Quanh năm",
        "tip": "Vị trí tuyệt vời để dạo bộ khám phá các món ăn đêm phố cổ."
    },
    {
        "id": "apricot-hotel-hanoi",
        "name": "Apricot Hotel Hanoi Hàng Trống",
        "category": "hotel",
        "lat": 21.0289,
        "lng": 105.8509,
        "rating": 4.8,
        "reviews": 2100,
        "address": "136 Hàng Trống, Hoàn Kiếm, Hà Nội",
        "image": "images/apricot_hotel.jpg",
        "desc": "Khách sạn nghệ thuật 5 sao ven Hồ Gươm trưng bày hàng trăm tác phẩm hội họa nguyên bản của các danh họa Việt Nam.",
        "bestMonths": "Quanh năm",
        "tip": "Bể bơi vô cực trên tầng thượng ngắm trọn cảnh sắc Tháp Rùa và Hồ Gươm."
    },
    {
        "id": "lotte-hotel-hanoi",
        "name": "Lotte Hotel Hanoi Liễu Giai",
        "category": "hotel",
        "lat": 21.033,
        "lng": 105.813,
        "rating": 4.8,
        "reviews": 2600,
        "address": "54 Liễu Giai, Cống Vị, Ba Đình, Hà Nội",
        "image": "images/lotte_hotel_hanoi.jpg",
        "desc": "Khách sạn 5 sao đẳng cấp quốc tế tọa lạc từ tầng 33 đến 64 của tòa tháp Lotte với tầm nhìn ôm trọn thủ đô.",
        "bestMonths": "Quanh năm",
        "tip": "Ghé Top of Hanoi tại tầng 67 để thưởng thức cocktail và ngắm hoàng hôn lung linh."
    },
    {
        "id": "pan-pacific-hanoi",
        "name": "Pan Pacific Hanoi Thanh Niên",
        "category": "hotel",
        "lat": 21.0455,
        "lng": 105.8402,
        "rating": 4.7,
        "reviews": 2250,
        "address": "1 Thanh Niên, Ba Đình, Hà Nội",
        "image": "images/pan_pacific_hotel.jpg",
        "desc": "Khách sạn 5 sao sang trọng nằm ngay giao điểm giữa Hồ Tây, Hồ Trúc Bạch và sông Hồng với tầm nhìn sông hồ ngoạn mục.",
        "bestMonths": "Quanh năm",
        "tip": "Quán bar The Summit tầng thượng có tầm view ngắm hoàng hôn Hồ Tây đẹp nhất thủ đô."
    },
    {
        "id": "jw-marriott-hanoi",
        "name": "JW Marriott Hotel Hanoi Đỗ Đức Dục",
        "category": "hotel",
        "lat": 21.0068,
        "lng": 105.7835,
        "rating": 4.9,
        "reviews": 3800,
        "address": "8 Đỗ Đức Dục, Mễ Trì, Nam Từ Liêm, Hà Nội",
        "image": "images/jw_marriott_hanoi.jpg",
        "desc": "Khách sạn 5 sao hàng đầu lấy cảm hứng thiết kế từ hình tượng con rồng bên bờ biển Đông, cạnh Trung tâm Hội nghị Quốc gia.",
        "bestMonths": "Quanh năm",
        "tip": "Hệ thống nhà hàng buffet quốc tế JW Cafe và hồ bơi trong nhà trên không trung."
    },
    {
        "id": "intercontinental-westlake",
        "name": "InterContinental Hanoi Westlake",
        "category": "hotel",
        "lat": 21.056,
        "lng": 105.8305,
        "rating": 4.8,
        "reviews": 2700,
        "address": "5 Từ Hoa, Quảng An, Tây Hồ, Hà Nội",
        "image": "images/intercontinental_westlake.jpg",
        "desc": "Khu nghỉ dưỡng 5 sao độc đáo xây dựng hoàn toàn trên mặt nước mặt Hồ Tây mang phong cách thanh bình biệt lập.",
        "bestMonths": "Quanh năm",
        "tip": "Sunset Bar giữa mặt hồ là nơi ngắm chiều tà lãng mạn bậc nhất Hà Nội."
    },
    {
        "id": "sheraton-hanoi-hotel",
        "name": "Sheraton Hanoi Hotel Nghi Tàm",
        "category": "hotel",
        "lat": 21.0585,
        "lng": 105.832,
        "rating": 4.7,
        "reviews": 2400,
        "address": "K5 Nghi Tàm, 11 Xuân Diệu, Tây Hồ, Hà Nội",
        "image": "images/sheraton_hanoi.jpg",
        "desc": "Khách sạn 5 sao sang trọng ven Hồ Tây với khuôn viên vườn cây xanh mướt và phong cách phục vụ quốc tế chuyên nghiệp.",
        "bestMonths": "Quanh năm",
        "tip": "Thưởng thức ẩm thực nướng tại nhà hàng Hemispheres bên hồ."
    },
    {
        "id": "melia-hotel-hanoi",
        "name": "Melia Hanoi Hotel Lý Thường Kiệt",
        "category": "hotel",
        "lat": 21.025,
        "lng": 105.8475,
        "rating": 4.7,
        "reviews": 2300,
        "address": "44 Lý Thường Kiệt, Trần Hưng Đạo, Hoàn Kiếm, Hà Nội",
        "image": "images/melia_hotel.jpg",
        "desc": "Khách sạn 5 sao trung tâm quận Hoàn Kiếm với dịch vụ phòng hội nghị tiêu chuẩn quốc tế và tiện nghi cao cấp.",
        "bestMonths": "Quanh năm",
        "tip": "Khoảng cách đi bộ thuận tiện tới Nhà tù Hỏa Lò và Nhà ga Hà Nội."
    },
    {
        "id": "muong-thanh-xa-la",
        "name": "Khách sạn Mường Thanh Grand Xa La",
        "category": "hotel",
        "lat": 20.963,
        "lng": 105.792,
        "rating": 4.5,
        "reviews": 1150,
        "address": "Khu đô thị Xa La, Phúc La, Hà Đông, Hà Nội",
        "image": "images/muong_thanh_xa_la.jpg",
        "desc": "Khách sạn tiêu chuẩn 4 sao hiện đại với hệ thống phòng nghỉ cao cấp, bể bơi và dịch vụ hội thảo chuyên nghiệp tại Hà Đông.",
        "bestMonths": "Quanh năm",
        "tip": "Vị trí thuận tiện di chuyển về phía Tây Nam thủ đô và viện Bỏng Quốc gia."
    },
    {
        "id": "royal-city-residence",
        "name": "Royal City Luxury Apartment Hotel",
        "category": "hotel",
        "lat": 21.002,
        "lng": 105.817,
        "rating": 4.7,
        "reviews": 1680,
        "address": "72A Nguyễn Trãi, Thượng Đình, Thanh Xuân, Hà Nội",
        "image": "images/royal_city.jpg",
        "desc": "Căn hộ khách sạn cao cấp ngay quần thể đô thị Hoàng Gia Royal City với trung tâm thương mại và khu vui chơi ẩm thực dưới lòng đất.",
        "bestMonths": "Quanh năm",
        "tip": "Dưới tầng hầm có sân trượt băng nghệ thuật và khu ẩm thực phong phú."
    },
    {
        "id": "tram-xang-do-nghia",
        "name": "Trạm xăng Đô Nghĩa Yên Nghĩa",
        "category": "gas",
        "lat": 20.9635,
        "lng": 105.7485,
        "rating": 4.8,
        "reviews": 420,
        "address": "Khu đô thị Đô Nghĩa, Yên Nghĩa, Hà Đông, Hà Nội",
        "image": "images/tram_xang_do_nghia.jpg",
        "desc": "Cây xăng hiện đại phục vụ khu đô thị Đô Nghĩa, Yên Nghĩa và trục đường Tố Hữu kéo dài, cung cấp đầy đủ xăng Ron 95 và dầu DO.",
        "bestMonths": "Quanh năm",
        "tip": "Vị trí thuận tiện ngay gần ngã tư đường trục KĐT Đô Nghĩa, thanh toán không dùng tiền mặt."
    },
    {
        "id": "petrolimex-ba-la-ha-dong",
        "name": "Trạm xăng Petrolimex Số 45 Ba La Hà Đông",
        "category": "gas",
        "lat": 20.9575,
        "lng": 105.761,
        "rating": 4.6,
        "reviews": 580,
        "address": "Quốc lộ 6, Ba La, Phú Lương, Hà Đông, Hà Nội",
        "image": "images/petrolimex_ba_la.jpg",
        "desc": "Trạm xăng cửa ngõ Tây Nam phục vụ xăng sinh học E5, Ron 95-V và dầu DO 24/7 trên trục Quốc lộ 6.",
        "bestMonths": "Quanh năm",
        "tip": "Có làn tiếp nhiên liệu riêng cho xe buýt và xe tải đường dài."
    },
    {
        "id": "petrolimex-quang-trung-ha-dong",
        "name": "Cây xăng Petrolimex Quang Trung Hà Đông",
        "category": "gas",
        "lat": 20.9705,
        "lng": 105.7785,
        "rating": 4.6,
        "reviews": 720,
        "address": "430 Quang Trung, La Khê, Hà Đông, Hà Nội",
        "image": "images/petrolimex_quang_trung.jpg",
        "desc": "Trạm xăng lớn trung tâm quận Hà Đông nằm sát tuyến đường sắt đô thị Cát Linh - Hà Đông.",
        "bestMonths": "Quanh năm",
        "tip": "Trang bị hệ thống thanh toán không dùng tiền mặt qua thẻ ATM và ví VNPAY."
    },
    {
        "id": "pvoil-to-huu-van-phuc",
        "name": "Cây xăng PVOIL Tố Hữu Vạn Phúc",
        "category": "gas",
        "lat": 20.979,
        "lng": 105.7725,
        "rating": 4.5,
        "reviews": 490,
        "address": "Đường Tố Hữu, Vạn Phúc, Hà Đông, Hà Nội",
        "image": "images/pvoil_to_huu.jpg",
        "desc": "Trạm cấp xăng dầu hiện đại của PVOIL với 6 trụ bơm thông minh phục vụ trục đường Lê Văn Lương kéo dài.",
        "bestMonths": "Quanh năm",
        "tip": "Có cửa hàng tiện ích PVOIL Easy cung cấp nước uống giải khát."
    },
    {
        "id": "petrolimex-nguyen-trai",
        "name": "Trạm xăng Petrolimex 235 Nguyễn Trãi",
        "category": "gas",
        "lat": 20.997,
        "lng": 105.815,
        "rating": 4.5,
        "reviews": 730,
        "address": "235 Nguyễn Trãi, Thanh Xuân Trung, Thanh Xuân, Hà Nội",
        "image": "images/petrolimex_nguyen_trai.jpg",
        "desc": "Cây xăng lớn trên trục đường huyết mạch Nguyễn Trãi kết nối Hà Đông, Thanh Xuân và Đống Đa.",
        "bestMonths": "Quanh năm",
        "tip": "Mở cửa liên tục 24/24, phục vụ cả ban đêm."
    },
    {
        "id": "petrolimex-khuat-duy-tien",
        "name": "Trạm xăng Petrolimex Khuất Duy Tiến",
        "category": "gas",
        "lat": 20.9925,
        "lng": 105.7995,
        "rating": 4.6,
        "reviews": 680,
        "address": "Đường Khuất Duy Tiến, Thanh Xuân Bắc, Thanh Xuân, Hà Nội",
        "image": "images/petrolimex_khuat_duy_tien.jpg",
        "desc": "Cây xăng nằm ngay trục đường Vành đai 3 trên cao, điểm tiếp nhiên liệu thuận tiện cho ô tô và xe khách liên tỉnh.",
        "bestMonths": "Quanh năm",
        "tip": "Có khu rửa kính xe và kiểm tra áp suất lốp tự động."
    },
    {
        "id": "petrolimex-lang-ha",
        "name": "Trạm xăng Petrolimex Láng Hạ",
        "category": "gas",
        "lat": 21.0175,
        "lng": 105.8145,
        "rating": 4.5,
        "reviews": 590,
        "address": "95 Láng Hạ, Thành Công, Ba Đình, Hà Nội",
        "image": "images/petrolimex_lang_ha.jpg",
        "desc": "Cây xăng trung tâm phục vụ khu văn phòng tài chính Láng Hạ - Huỳnh Thúc Kháng, trang bị vòi bơm tự động tốc độ cao.",
        "bestMonths": "Quanh năm",
        "tip": "Hỗ trợ quét mã thanh toán ví VNPAY và thẻ ngân hàng tiện lợi."
    },
    {
        "id": "petrolimex-cua-nam",
        "name": "Trạm xăng Petrolimex Số 1 Cửa Nam",
        "category": "gas",
        "lat": 21.0268,
        "lng": 105.842,
        "rating": 4.7,
        "reviews": 820,
        "address": "1 Cửa Nam, Hoàn Kiếm, Hà Nội",
        "image": "images/petrolimex_cua_nam.jpg",
        "desc": "Trạm xăng trung tâm thủ đô phục vụ xăng Ron 95-V, E5 và dầu DO, mở cửa 24/7 với dịch vụ chuẩn Petrolimex.",
        "bestMonths": "Quanh năm",
        "tip": "Hỗ trợ thanh toán không dùng tiền mặt qua thẻ ngân hàng và ví điện tử."
    },
    {
        "id": "pvoil-cau-giay",
        "name": "Cây xăng PVOIL Hoàng Quốc Việt",
        "category": "gas",
        "lat": 21.045,
        "lng": 105.795,
        "rating": 4.5,
        "reviews": 510,
        "address": "180 Hoàng Quốc Việt, Cầu Giấy, Hà Nội",
        "image": "images/pvoil_hoang_quoc_viet.jpg",
        "desc": "Trạm cấp nhiên liệu lớn của PVOIL với 8 làn bơm xe máy và ô tô thông thoáng, thanh toán PVOIL Easy.",
        "bestMonths": "Quanh năm",
        "tip": "Nên ghé đổ đầy bình trước khi lên đường cao tốc Nội Bài - Lào Cai."
    },
    {
        "id": "petrolimex-yen-phu",
        "name": "Trạm xăng Petrolimex Yên Phụ",
        "category": "gas",
        "lat": 21.046,
        "lng": 105.845,
        "rating": 4.6,
        "reviews": 610,
        "address": "120 Yên Phụ, Nguyễn Trung Trực, Ba Đình, Hà Nội",
        "image": "images/petrolimex_yen_phu.jpg",
        "desc": "Trạm xăng ven đê Nghi Tàm - Yên Phụ kết nối cầu Long Biên, cầu Chương Dương và hướng đi sân bay Nội Bài.",
        "bestMonths": "Quanh năm",
        "tip": "Mở cửa phục vụ liên tục 24/7."
    },
    {
        "id": "petrolimex-nguyen-van-cu",
        "name": "Trạm xăng Petrolimex Nguyễn Văn Cừ",
        "category": "gas",
        "lat": 21.0485,
        "lng": 105.872,
        "rating": 4.6,
        "reviews": 740,
        "address": "250 Nguyễn Văn Cừ, Bồ Đề, Long Biên, Hà Nội",
        "image": "images/petrolimex_nguyen_van_cu.jpg",
        "desc": "Cây xăng lớn cửa ngõ phía Đông thủ đô trên trục Quốc lộ 5 đi Hải Phòng và Quảng Ninh.",
        "bestMonths": "Quanh năm",
        "tip": "Có làn bơm dầu chuyên dụng công suất lớn cho xe tải và xe container."
    },
    {
        "id": "petrolimex-tam-diep",
        "name": "Trạm xăng Petrolimex Tam Điệp Ninh Bình",
        "category": "gas",
        "lat": 20.155,
        "lng": 105.908,
        "rating": 4.7,
        "reviews": 480,
        "address": "Quốc lộ 1A, TP. Tam Điệp, Ninh Bình",
        "image": "images/petrolimex_tam_diep.jpg",
        "desc": "Trạm dừng chân và cấp nhiên liệu lớn trên tuyến Quốc lộ 1A xuyên Việt phục vụ các hành trình du lịch miền Bắc.",
        "bestMonths": "Quanh năm",
        "tip": "Có bãi đỗ xe rộng rãi và khu vệ sinh tiện nghi cho du khách đường dài."
    }
];

var CATEGORY_LABELS = {
    tourist: 'Du lịch',
    food: 'Quán ăn & Uống',
    hotel: 'Khách sạn',
    gas: 'Trạm xăng'
};

function calculateDistance(lat1, lng1, lat2, lng2) {
    var R = 6371;
    var dLat = (lat2 - lat1) * Math.PI / 180;
    var dLng = (lng2 - lng1) * Math.PI / 180;
    var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLng / 2) * Math.sin(dLng / 2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function formatDistance(km) {
    if (km < 1) return Math.round(km * 1000) + 'm';
    return km.toFixed(1) + 'km';
}

function getEffectiveLatLng() {
    return virtualLatLng || userLatLng || [21.0285, 105.8542];
}

function calculateDistanceToSegment(pLat, pLng, aLat, aLng, bLat, bLng) {
    var dx = bLng - aLng;
    var dy = bLat - aLat;
    var lengthSquared = dx * dx + dy * dy;

    if (lengthSquared === 0) {
        return {
            distanceKm: calculateDistance(pLat, pLng, aLat, aLng),
            fraction: 0
        };
    }

    var t = ((pLng - aLng) * dx + (pLat - aLat) * dy) / lengthSquared;
    t = Math.max(0, Math.min(1, t));

    var projLat = aLat + t * dy;
    var projLng = aLng + t * dx;
    var dist = calculateDistance(pLat, pLng, projLat, projLng);

    return {
        distanceKm: dist,
        fraction: t
    };
}

function initMapPage() {
    isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    hasActiveBooking = localStorage.getItem('hasActiveBooking') === 'true';
    locationRequired = isLoggedIn || hasActiveBooking;

    var btnAllow = document.getElementById('btnAllowLocation');
    var btnSkip = document.getElementById('btnSkipLocation');
    var chkRadius = document.getElementById('chkRadius10km');
    var btnSimulate = document.getElementById('btnSimulateTrip');
    var btnModeLocal = document.getElementById('btnModeLocal');
    var btnModeCorridor = document.getElementById('btnModeCorridor');

    updateGateContent();
    updateSkipVisibility();

    if (btnAllow) {
        btnAllow.addEventListener('click', function() {
            requestGeolocation();
        });
    }

    if (btnSkip) {
        btnSkip.addEventListener('click', function() {
            wasSkipped = true;
            userLatLng = [21.0285, 105.8542];
            updateLocationStatus('Gợi ý theo trung tâm Hà Nội');
            hideLocationGate();
            addAllPlaces();
        });
    }

    if (chkRadius) {
        chkRadius.addEventListener('change', function() {
            filterRadius10km = this.checked;
            addAllPlaces();
        });
    }

    if (btnSimulate) {
        btnSimulate.addEventListener('click', function() {
            toggleSimulation();
        });
    }

    if (btnModeLocal) {
        btnModeLocal.addEventListener('click', function() {
            switchViewMode('local');
        });
    }

    if (btnModeCorridor) {
        btnModeCorridor.addEventListener('click', function() {
            switchViewMode('corridor');
        });
    }

    setupCategoryTabs();
    setupSearch();

    if (locationRequired) {
        showPermissionRequiredMessage();
        updateLocationStatus('Cần bật định vị để tiếp tục');
    } else {
        updateLocationStatus('Bạn có thể bật định vị hoặc bỏ qua');
    }

    userLatLng = [21.0285, 105.8542];
    addAllPlaces();

    if (navigator.geolocation && !wasSkipped) {
        requestGeolocation();
    }
}

function switchViewMode(mode) {
    currentViewMode = mode;
    var btnLocal = document.getElementById('btnModeLocal');
    var btnCorridor = document.getElementById('btnModeCorridor');
    var corridorBox = document.getElementById('corridorSummaryBox');
    var radarBox = document.getElementById('radarBox');

    if (mode === 'local') {
        if (btnLocal) btnLocal.classList.add('active');
        if (btnCorridor) btnCorridor.classList.remove('active');
        if (corridorBox) corridorBox.style.display = 'none';
        if (radarBox) radarBox.style.display = 'flex';
    } else {
        if (btnCorridor) btnCorridor.classList.add('active');
        if (btnLocal) btnLocal.classList.remove('active');
        if (corridorBox) corridorBox.style.display = 'flex';
        if (radarBox) radarBox.style.display = 'none';
    }

    addAllPlaces();
}

function requestGeolocation() {
    if (locationRequired && !navigator.geolocation) {
        updateLocationStatus('Thiết bị không hỗ trợ định vị');
        showPermissionRequiredMessage();
        return;
    }

    updateLocationStatus('Đang xác định vị trí...');

    if (!navigator.geolocation) {
        userLatLng = [21.0285, 105.8542];
        updateLocationStatus('Trình duyệt không hỗ trợ. Mặc định Hà Nội');
        addAllPlaces();
        hideLocationGate();
        return;
    }

    navigator.geolocation.getCurrentPosition(
        function(position) {
            userLatLng = [position.coords.latitude, position.coords.longitude];
            hasLocationPermission = true;
            updateLocationStatus('Đang hiển thị vị trí của bạn');
            hideLocationGate();
            addAllPlaces();
            startWatchingPosition();
        },
        function() {
            userLatLng = [21.0285, 105.8542];
            if (locationRequired) {
                updateLocationStatus('Cần bật định vị để tiếp tục');
                showPermissionRequiredMessage();
                return;
            }
            updateLocationStatus('Chưa bật GPS. Hiển thị mặc định');
            addAllPlaces();
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    );
}

function startWatchingPosition() {
    if (!navigator.geolocation || watchPositionId !== null) return;
    watchPositionId = navigator.geolocation.watchPosition(
        function(pos) {
            if (!isSimulating) {
                userLatLng = [pos.coords.latitude, pos.coords.longitude];
                updateLocationStatus('Đã cập nhật vị trí di chuyển');
                addAllPlaces();
                var currentPlace = getSelectedPlace();
                if (currentPlace) {
                    updateMapAndHud(currentPlace);
                }
            }
        },
        function() {},
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
    );
}

function updateLocationStatus(text) {
    var el = document.getElementById('locationStatus');
    if (el) el.textContent = text;
}

function hideLocationGate() {
    var gate = document.getElementById('locationGate');
    if (gate) gate.style.display = 'none';
}

function showPermissionRequiredMessage() {
    var gate = document.getElementById('locationGate');
    if (!gate) return;
    gate.style.display = 'flex';
}

function updateGateContent() {
    var title = document.getElementById('gateTitle');
    var desc = document.getElementById('gateDesc');
    if (!title || !desc) return;

    if (locationRequired) {
        title.textContent = 'Bắt buộc bật định vị để tiếp tục';
        desc.textContent = 'Tài khoản đang đăng nhập hoặc có lịch trình cần định vị để chỉ đường và quét POI chính xác.';
    } else {
        title.textContent = 'Bật định vị để nhận gợi ý chuẩn xác';
        desc.textContent = 'Hệ thống tự động quét địa điểm du lịch, quán ăn, khách sạn và trạm xăng trong bán kính 10km quanh bạn.';
    }
}

function updateSkipVisibility() {
    var btnSkip = document.getElementById('btnSkipLocation');
    if (!btnSkip) return;
    btnSkip.style.display = locationRequired ? 'none' : 'inline-flex';
}

function updateRadarCounter(allCount, touristCount, foodCount, hotelCount, gasCount) {
    var el = document.getElementById('radarCounter');
    if (el) {
        el.innerHTML = '<i class="bx bx-check-circle"></i> Có <b>' + allCount + '</b> điểm trong 10km (' +
            touristCount + ' du lịch, ' + foodCount + ' quán ăn, ' + hotelCount + ' khách sạn, ' + gasCount + ' trạm xăng)';
    }

    var badge = document.getElementById('localCountBadge');
    if (badge) {
        badge.textContent = allCount;
    }
}

function updateCorridorSummary(target, corridorPlaces) {
    var routeLabel = document.getElementById('corridorRouteName');
    if (routeLabel && target) {
        routeLabel.textContent = 'Xuất phát ➔ ' + target.name;
    }

    var badge = document.getElementById('corridorCountBadge');
    if (badge) {
        badge.textContent = corridorPlaces.length;
    }

    var stats = document.getElementById('corridorStats');
    if (stats && target) {
        var tCount = corridorPlaces.filter(function(item) { return item.place.category === 'tourist'; }).length;
        var fCount = corridorPlaces.filter(function(item) { return item.place.category === 'food'; }).length;
        var hCount = corridorPlaces.filter(function(item) { return item.place.category === 'hotel'; }).length;
        var gCount = corridorPlaces.filter(function(item) { return item.place.category === 'gas'; }).length;

        stats.innerHTML = 'Phát hiện <b>' + corridorPlaces.length + '</b> điểm trong 10km dọc tuyến đường:<br>' +
            '🏛️ ' + tCount + ' du lịch &nbsp;|&nbsp; 🍜 ' + fCount + ' ăn uống &nbsp;|&nbsp; 🏨 ' + hCount + ' khách sạn &nbsp;|&nbsp; ⛽ ' + gCount + ' trạm xăng';
    }
}

function getCorridorPlaces(startCoords, destPlace) {
    if (!destPlace) return [];
    var results = [];
    for (var i = 0; i < PLACES_DATA.length; i++) {
        var p = PLACES_DATA[i];
        var segInfo = calculateDistanceToSegment(p.lat, p.lng, startCoords[0], startCoords[1], destPlace.lat, destPlace.lng);
        if (segInfo.distanceKm <= 10) {
            results.push({
                place: p,
                corridorDist: segInfo.distanceKm,
                fraction: segInfo.fraction
            });
        }
    }
    results.sort(function(a, b) {
        return a.fraction - b.fraction;
    });
    return results;
}

function addAllPlaces() {
    var container = document.getElementById('placesList');
    if (container) container.innerHTML = '';

    var currentCoords = getEffectiveLatLng();
    var selectedPlace = getSelectedPlace();
    var startCoords = userLatLng || [21.0285, 105.8542];

    var in10kmAll = 0;
    var in10kmTourist = 0;
    var in10kmFood = 0;
    var in10kmHotel = 0;
    var in10kmGas = 0;

    PLACES_DATA.forEach(function(p) {
        var dist = calculateDistance(currentCoords[0], currentCoords[1], p.lat, p.lng);
        if (dist <= 10) {
            in10kmAll++;
            if (p.category === 'tourist') in10kmTourist++;
            else if (p.category === 'food') in10kmFood++;
            else if (p.category === 'hotel') in10kmHotel++;
            else if (p.category === 'gas') in10kmGas++;
        }
    });

    updateRadarCounter(in10kmAll, in10kmTourist, in10kmFood, in10kmHotel, in10kmGas);

    var corridorList = getCorridorPlaces(startCoords, selectedPlace || PLACES_DATA[0]);
    updateCorridorSummary(selectedPlace || PLACES_DATA[0], corridorList);

    var displayItems = [];

    var searchTerm = '';
    var searchInput = document.getElementById('mapSearchInput');
    if (searchInput) searchTerm = searchInput.value.trim().toLowerCase();

    if (currentViewMode === 'local') {
        var localFiltered = PLACES_DATA.filter(function(place) {
            return activeCategory === 'all' || place.category === activeCategory;
        });

        if (searchTerm) {
            localFiltered = localFiltered.filter(function(place) {
                return place.name.toLowerCase().indexOf(searchTerm) !== -1 ||
                       place.address.toLowerCase().indexOf(searchTerm) !== -1 ||
                       place.desc.toLowerCase().indexOf(searchTerm) !== -1;
            });
        }

        if (filterRadius10km) {
            localFiltered = localFiltered.filter(function(place) {
                var d = calculateDistance(currentCoords[0], currentCoords[1], place.lat, place.lng);
                return d <= 10;
            });
        }

        localFiltered.sort(function(a, b) {
            var distA = calculateDistance(currentCoords[0], currentCoords[1], a.lat, a.lng);
            var distB = calculateDistance(currentCoords[0], currentCoords[1], b.lat, b.lng);
            return distA - distB;
        });

        displayItems = localFiltered.map(function(p) {
            var km = calculateDistance(currentCoords[0], currentCoords[1], p.lat, p.lng);
            return {
                place: p,
                distanceText: formatDistance(km),
                stageTag: ''
            };
        });
    } else {
        var corridorFiltered = corridorList.filter(function(item) {
            return activeCategory === 'all' || item.place.category === activeCategory;
        });

        if (searchTerm) {
            corridorFiltered = corridorFiltered.filter(function(item) {
                var place = item.place;
                return place.name.toLowerCase().indexOf(searchTerm) !== -1 ||
                       place.address.toLowerCase().indexOf(searchTerm) !== -1 ||
                       place.desc.toLowerCase().indexOf(searchTerm) !== -1;
            });
        }

        displayItems = corridorFiltered.map(function(item) {
            var p = item.place;
            var currentDist = calculateDistance(currentCoords[0], currentCoords[1], p.lat, p.lng);
            var stageLabel = '';
            var isNear = currentDist <= 1.5;

            if (isSimulating) {
                if (isNear) {
                    stageLabel = '<span class="place-stage-tag stage-near"><i class="bx bx-broadcast"></i> Đang qua (' + formatDistance(currentDist) + ')</span>';
                } else if (item.fraction < (simulationStep / 20)) {
                    stageLabel = '<span class="place-stage-tag"><i class="bx bx-check"></i> Đã đi qua</span>';
                } else {
                    stageLabel = '<span class="place-stage-tag"><i class="bx bx-time"></i> Sắp tới (' + formatDistance(currentDist) + ')</span>';
                }
            } else {
                stageLabel = '<span class="place-stage-tag"><i class="bx bx-transfer-alt"></i> Lệch tuyến ' + formatDistance(item.corridorDist) + '</span>';
            }

            return {
                place: p,
                distanceText: formatDistance(currentDist),
                stageTag: stageLabel,
                isNear: isNear
            };
        });
    }

    displayItems.forEach(function(item) {
        addPlaceRow(item.place, item.distanceText, item.stageTag, item.isNear);
    });

    if (displayItems.length === 0 && container) {
        container.innerHTML = '<div class="empty-places"><i class="bx bx-search-alt"></i><p>Không có địa điểm nào phù hợp với bộ lọc hiện tại</p><small class="text-muted">Bạn có thể chọn tab khác hoặc mở rộng bán kính tìm kiếm</small></div>';
    }

    if (!selectedPlace && displayItems.length > 0) {
        selectPlace(displayItems[0].place);
    } else if (selectedPlace) {
        updateSelectedRow();
    }
}

function addPlaceRow(place, distanceText, stageTag, isNear) {
    var container = document.getElementById('placesList');
    if (!container) return;

    var catLabel = CATEGORY_LABELS[place.category] || place.category;
    var catClass = 'tag-' + place.category;
    var nearClass = isNear ? ' is-active' : '';

    var html = '<button class="place-row' + nearClass + '" data-place-id="' + place.id + '">' +
        '<img src="' + place.image + '" alt="' + place.name + '" class="place-row-thumb" loading="lazy">' +
        '<div class="place-row-body">' +
        '<div class="place-row-meta">' +
        '<span class="place-tag ' + catClass + '">' + catLabel + '</span>' +
        '<span class="place-row-rating"><i class="bx bxs-star"></i> ' + place.rating + '</span>' +
        '</div>' +
        '<h4 class="font-bold">' + place.name + '</h4>' +
        '<p class="text-muted text-sm">' + place.address + '</p>' +
        '<div class="place-row-foot">' +
        '<span class="place-distance"><i class="bx bx-walk"></i> ' + distanceText + '</span>' +
        (stageTag || '') +
        '</div>' +
        '</div>' +
        '</button>';

    container.insertAdjacentHTML('beforeend', html);

    var row = container.lastElementChild;
    row.addEventListener('click', function() {
        selectPlace(place);
    });
}

function setupCategoryTabs() {
    var tabs = document.querySelectorAll('#categoryTabs .map-tab');
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            tabs.forEach(function(t) { t.classList.remove('active'); });
            this.classList.add('active');
            activeCategory = this.getAttribute('data-category');
            addAllPlaces();
        });
    });
}

function setupSearch() {
    var input = document.getElementById('mapSearchInput');
    if (!input) return;

    var debounceTimer;
    input.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function() {
            addAllPlaces();
        }, 300);
    });
}

function getSelectedPlace() {
    if (!selectedPlaceId) return null;
    for (var i = 0; i < PLACES_DATA.length; i++) {
        if (PLACES_DATA[i].id === selectedPlaceId) {
            return PLACES_DATA[i];
        }
    }
    return null;
}

function updateMapAndHud(place) {
    if (!place) return;
    var origin = getEffectiveLatLng();
    var iframe = document.getElementById('gmapIframe');
    if (iframe) {
        var embedUrl = 'https://maps.google.com/maps?saddr=' + origin[0] + ',' + origin[1] +
                       '&daddr=' + place.lat + ',' + place.lng +
                       '&output=embed&hl=vi';
        if (iframe.src !== embedUrl) {
            iframe.src = embedUrl;
        }
    }

    var dist = calculateDistance(origin[0], origin[1], place.lat, place.lng);
    var estMinutes = Math.max(3, Math.round(dist * 2.3));

    var hudDist = document.getElementById('hudDistance');
    if (hudDist) {
        hudDist.innerHTML = '<i class="bx bx-trip"></i> ' + formatDistance(dist);
    }

    var hudTime = document.getElementById('hudTime');
    if (hudTime) {
        hudTime.innerHTML = '<i class="bx bx-time-five"></i> ~' + estMinutes + ' phút';
    }

    var btnExt = document.getElementById('btnExternalMap');
    if (btnExt) {
        btnExt.href = 'https://www.google.com/maps/dir/?api=1' +
                      '&origin=' + origin[0] + ',' + origin[1] +
                      '&destination=' + place.lat + ',' + place.lng +
                      '&travelmode=driving';
    }
}

function selectPlace(place) {
    if (!place || !place.id) return;
    selectedPlaceId = place.id;

    updateMapAndHud(place);

    var detail = document.getElementById('placeDetail');
    if (!detail) return;

    var bestMonths = place.bestMonths || 'Quanh năm';
    var tip = place.tip || 'Nên chuẩn bị trước lộ trình để có trải nghiệm thuận lợi nhất.';
    var catLabel = CATEGORY_LABELS[place.category] || place.category;

    detail.innerHTML = '<div class="detail-cover">' +
        '<img src="' + place.image + '" alt="' + place.name + '">' +
        '<span class="detail-badge">' + catLabel + '</span>' +
        '</div>' +
        '<div class="detail-body">' +
        '<h3 class="font-bold">' + place.name + '</h3>' +
        '<p class="text-muted"><i class="bx bx-map"></i> ' + place.address + '</p>' +
        '<p class="detail-desc">' + place.desc + '</p>' +
        '<div class="detail-info">' +
        '<div>' +
        '<p class="detail-label">Thời điểm lý tưởng</p>' +
        '<p class="detail-value">' + bestMonths + '</p>' +
        '</div>' +
        '<div>' +
        '<p class="detail-label">Lời khuyên / Mẹo</p>' +
        '<p class="detail-value">' + tip + '</p>' +
        '</div>' +
        '</div>' +
        '<div class="detail-actions">' +
        '<button class="btn btn-primary" id="btnReroute"><i class="bx bx-navigation"></i> Đổi lộ trình tới đây</button>' +
        '<a class="btn btn-outline" id="btnDirectGoogleMaps" href="' +
        'https://www.google.com/maps/dir/?api=1&destination=' + place.lat + ',' + place.lng + '&travelmode=driving" target="_blank" rel="noopener">' +
        '<i class="bx bx-map"></i> Mở App Google Maps</a>' +
        '</div>' +
        '</div>';

    var btnReroute = document.getElementById('btnReroute');
    if (btnReroute) {
        btnReroute.addEventListener('click', function() {
            updateMapAndHud(place);
            var hudStatus = document.getElementById('hudStatus');
            if (hudStatus) {
                hudStatus.innerHTML = '<i class="bx bx-check-circle"></i> Tuyến đường tới ' + place.name;
            }
        });
    }

    updateSelectedRow();
}

function updateSelectedRow() {
    var rows = document.querySelectorAll('.place-row');
    rows.forEach(function(row) {
        var id = row.getAttribute('data-place-id');
        if (id === selectedPlaceId) {
            row.classList.add('is-active');
        } else {
            row.classList.remove('is-active');
        }
    });
}

function findNearbyProactivePoi(coords, excludeId) {
    var candidates = PLACES_DATA.filter(function(p) {
        if (p.id === excludeId) return false;
        var d = calculateDistance(coords[0], coords[1], p.lat, p.lng);
        return d <= 2.5;
    });
    if (candidates.length === 0) return null;
    candidates.sort(function(a, b) {
        var dA = calculateDistance(coords[0], coords[1], a.lat, a.lng);
        var dB = calculateDistance(coords[0], coords[1], b.lat, b.lng);
        return dA - dB;
    });
    return candidates[0];
}

function toggleSimulation() {
    var btn = document.getElementById('btnSimulateTrip');
    var banner = document.getElementById('liveAlertBanner');
    var bannerText = document.getElementById('liveAlertText');
    var hudStatus = document.getElementById('hudStatus');

    if (isSimulating) {
        stopSimulation();
        return;
    }

    var target = getSelectedPlace();
    if (!target) {
        alert('Vui lòng chọn một địa điểm để bắt đầu mô phỏng tuyến đường.');
        return;
    }

    var startCoords = userLatLng || [21.0285, 105.8542];
    var totalDistance = calculateDistance(startCoords[0], startCoords[1], target.lat, target.lng);
    if (totalDistance < 0.1) {
        alert('Bạn đã ở ngay tại địa điểm này.');
        return;
    }

    switchViewMode('corridor');

    isSimulating = true;
    if (btn) {
        btn.innerHTML = '<i class="bx bx-stop-circle"></i> Dừng di chuyển';
        btn.classList.add('btn-primary');
        btn.classList.remove('btn-outline');
    }

    if (hudStatus) {
        hudStatus.innerHTML = '<i class="bx bx-loader-alt bx-spin"></i> Đang di chuyển mô phỏng...';
    }

    if (banner) {
        banner.style.display = 'flex';
        bannerText.innerHTML = '<i class="bx bx-car"></i> Đang khởi hành đến <b>' + target.name + '</b>...';
    }

    var stepsCount = 20;
    simulationWaypoints = [];
    for (var i = 0; i <= stepsCount; i++) {
        var progress = i / stepsCount;
        var pLat = startCoords[0] + (target.lat - startCoords[0]) * progress;
        var pLng = startCoords[1] + (target.lng - startCoords[1]) * progress;
        simulationWaypoints.push([pLat, pLng]);
    }

    simulationStep = 0;

    clearInterval(simulationInterval);
    simulationInterval = setInterval(function() {
        simulationStep++;
        if (simulationStep >= simulationWaypoints.length) {
            virtualLatLng = [target.lat, target.lng];
            stopSimulation();
            if (banner) {
                banner.style.display = 'flex';
                bannerText.innerHTML = '🎉 <b>Bạn đã đến nơi an toàn:</b> ' + target.name + '!';
                setTimeout(function() {
                    banner.style.display = 'none';
                }, 5000);
            }
            addAllPlaces();
            return;
        }

        virtualLatLng = simulationWaypoints[simulationStep];
        var remainingDist = calculateDistance(virtualLatLng[0], virtualLatLng[1], target.lat, target.lng);

        var hudDist = document.getElementById('hudDistance');
        if (hudDist) {
            hudDist.innerHTML = '<i class="bx bx-trip"></i> ' + formatDistance(remainingDist);
        }

        var hudTime = document.getElementById('hudTime');
        if (hudTime) {
            hudTime.innerHTML = '<i class="bx bx-time-five"></i> ~' + Math.max(1, Math.round(remainingDist * 2.3)) + ' phút';
        }

        var nearbyPoi = findNearbyProactivePoi(virtualLatLng, target.id);
        if (nearbyPoi && bannerText) {
            var pDist = calculateDistance(virtualLatLng[0], virtualLatLng[1], nearbyPoi.lat, nearbyPoi.lng);
            var icon = nearbyPoi.category === 'gas' ? '⛽ ' : (nearbyPoi.category === 'food' ? '🍜 ' : (nearbyPoi.category === 'hotel' ? '🏨 ' : '🏛️ '));
            bannerText.innerHTML = icon + '<b>Gợi ý trên đường:</b> ' + nearbyPoi.name + ' (cách ' + formatDistance(pDist) + ')';
        } else if (bannerText) {
            bannerText.innerHTML = '<i class="bx bx-navigation"></i> Đang di chuyển... Còn <b>' + formatDistance(remainingDist) + '</b> đến ' + target.name;
        }

        addAllPlaces();
    }, 1400);
}

function stopSimulation() {
    isSimulating = false;
    clearInterval(simulationInterval);
    simulationInterval = null;
    virtualLatLng = null;

    var btn = document.getElementById('btnSimulateTrip');
    if (btn) {
        btn.innerHTML = '<i class="bx bx-play-circle"></i> Mô phỏng di chuyển';
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-outline');
    }

    var hudStatus = document.getElementById('hudStatus');
    if (hudStatus) {
        hudStatus.innerHTML = '<i class="bx bx-navigation"></i> Tuyến đường Google Maps';
    }

    var banner = document.getElementById('liveAlertBanner');
    if (banner && !banner.textContent.includes('Bạn đã đến nơi')) {
        banner.style.display = 'none';
    }

    var selectedPlace = getSelectedPlace();
    if (selectedPlace) {
        updateMapAndHud(selectedPlace);
    }
    addAllPlaces();
}

document.addEventListener('DOMContentLoaded', initMapPage);
