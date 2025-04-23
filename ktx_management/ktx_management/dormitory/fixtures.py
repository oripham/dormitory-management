# fixtures.py - Dữ liệu mẫu cho các bảng trong hệ thống quản lý ký túc xá
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random
from .models import (
    TaiKhoan, DayPhong, LoaiPhong, Phong, SinhVien, QuanLy, DonDangKy,
    ViPham, HopDong, BaoHong, HoaDon, TaiSan, ChiTietTaiSan, ChiSoDienNuoc
)

def create_sample_data():
    """Tạo dữ liệu mẫu cho toàn bộ hệ thống"""
    # Xóa dữ liệu hiện tại để tránh lỗi khóa trùng
    ChiSoDienNuoc.objects.all().delete()
    ChiTietTaiSan.objects.all().delete()
    HoaDon.objects.all().delete()
    BaoHong.objects.all().delete()
    HopDong.objects.all().delete()
    ViPham.objects.all().delete()
    DonDangKy.objects.all().delete()
    QuanLy.objects.all().delete()
    SinhVien.objects.all().delete()
    Phong.objects.all().delete()
    LoaiPhong.objects.all().delete()
    DayPhong.objects.all().delete()
    TaiKhoan.objects.all().delete()
    
    # Delete all non-superuser users
    User.objects.exclude(is_superuser=True).delete()
    
    # Tạo tài khoản và người dùng
    create_users_and_accounts()
    
    # Tạo dãy phòng và loại phòng
    create_building_and_room_types()
    
    # Tạo phòng
    create_rooms()
    
    # Tạo sinh viên và quản lý
    create_students_and_managers()
    
    # Tạo đơn đăng ký
    create_applications()
    
    # Tạo hợp đồng
    create_contracts()
    
    # Tạo vi phạm
    create_violations()
    
    # Tạo báo hỏng
    create_damage_reports()
    
    # Tạo tài sản và chi tiết tài sản
    create_assets()
    
    # Tạo chỉ số điện nước
    create_utility_readings()
    
    # Tạo hóa đơn
    create_invoices()

def create_users_and_accounts():
    """Tạo người dùng và tài khoản"""
    # Lấy admin user hiện có thay vì tạo mới
    try:
        admin_user = User.objects.get(username='admin')
        # Tạo tài khoản cho admin nếu chưa có
        TaiKhoan.objects.get_or_create(user=admin_user, defaults={'role': 'admin'})
    except User.DoesNotExist:
        # Trường hợp hiếm gặp: nếu không có admin, tạo mới
        admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )
        TaiKhoan.objects.create(user=admin_user, role='admin')
    
    # Tạo tài khoản quản lý
    for i in range(1, 6):
        username = f'quanly{i}'
        # Check if user exists first
        if not User.objects.filter(username=username).exists():
            manager_user = User.objects.create_user(
                username=username,
                password=username,
                email=f'{username}@example.com',
                first_name=f'Quản Lý {i}',
                last_name='Nguyễn'
            )
            TaiKhoan.objects.create(user=manager_user, role='manager')
    
    # Tạo tài khoản sinh viên
    for i in range(1, 51):
        username = f'sv{i:03d}'
        # Check if user exists first
        if not User.objects.filter(username=username).exists():
            student_user = User.objects.create_user(
                username=username,
                password=username,
                email=f'{username}@example.com',
                first_name=random.choice(['Anh', 'Bình', 'Cường', 'Dũng', 'Em', 'Phong', 'Quang', 'Hùng', 'Minh', 'Nam']),
                last_name=random.choice(['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng'])
            )
            TaiKhoan.objects.create(user=student_user, role='student')

def create_building_and_room_types():
    """Tạo dãy phòng và loại phòng"""
    # Tạo dãy phòng
    day_phongs = [
        ('A', 'A Block', 20, 'Nam'),
        ('B', 'B Block', 20, 'Nam'),
        ('C', 'C Block', 20, 'Nữ'),
        ('D', 'D Block', 20, 'Nữ'),
        ('E', 'E Block', 10, 'Nam Nữ')
    ]
    
    for ma, ten, so_phong, doi_tuong in day_phongs:
        DayPhong.objects.create(
            ma_day_phong=ma,
            ten_day_phong=ten,
            so_phong=so_phong,
            doi_tuong=doi_tuong
        )
    
    # Tạo loại phòng
    loai_phongs = [
        ('LP01', 'Phòng 4 người', 50),
        ('LP02', 'Phòng 6 người', 30),
        ('LP03', 'Phòng 8 người', 20),
        ('LP04', 'Phòng VIP 2 người', 10)
    ]
    
    for ma, ten, so_luong in loai_phongs:
        LoaiPhong.objects.create(
            ma_loai_phong=ma,
            ten_loai_phong=ten,
            so_luong=so_luong
        )

def create_rooms():
    """Tạo phòng"""
    day_phongs = DayPhong.objects.all()
    loai_phongs = LoaiPhong.objects.all()
    
    gia_phong = {
        'LP01': 350000,  # 4 người
        'LP02': 300000,  # 6 người
        'LP03': 250000,  # 8 người
        'LP04': 600000   # VIP 2 người
    }
    
    # Khởi tạo số lượng sinh viên dựa trên loại phòng
    sv_in_room = {
        'LP01': 4,
        'LP02': 6,
        'LP03': 8,
        'LP04': 2
    }
    
    for day in day_phongs:
        for i in range(1, day.so_phong + 1):
            # Phân bổ loại phòng
            if i <= 5:
                loai = LoaiPhong.objects.get(ma_loai_phong='LP01')  # 4 người
            elif i <= 10:
                loai = LoaiPhong.objects.get(ma_loai_phong='LP02')  # 6 người
            elif i <= 15:
                loai = LoaiPhong.objects.get(ma_loai_phong='LP03')  # 8 người
            else:
                loai = LoaiPhong.objects.get(ma_loai_phong='LP04')  # VIP 2 người
            
            # Tạo mã phòng, ví dụ: A101, B203,...
            ma_phong = f"{day.ma_day_phong}{i:03d}"
            
            # Xác định trạng thái phòng ngẫu nhiên
            trang_thai = random.choice(['Trống', 'Đầy', 'Bảo trì', 'Đang sửa chữa'])
            if trang_thai == 'Đầy':
                so_luong_sv = sv_in_room[loai.ma_loai_phong]
            elif trang_thai == 'Trống':
                so_luong_sv = 0
            else:
                so_luong_sv = random.randint(0, sv_in_room[loai.ma_loai_phong] - 1)
            
            Phong.objects.create(
                ma_phong=ma_phong,
                so_luong_sv=so_luong_sv,
                loai_phong=loai,
                day_phong=day,
                gia=gia_phong[loai.ma_loai_phong],
                danh_sach_sv="",  # Sẽ được cập nhật sau
                trang_thai=trang_thai
            )

def create_students_and_managers():
    """Tạo sinh viên và quản lý"""
    tinh_thanh = ['Hà Nội', 'TP.HCM', 'Đà Nẵng', 'Cần Thơ', 'Hải Phòng', 'Huế', 'Quảng Ninh', 'Nghệ An', 'Thanh Hóa', 'Lâm Đồng']
    
    # Tạo quản lý
    manager_accounts = TaiKhoan.objects.filter(role='manager')
    for i, account in enumerate(manager_accounts, 1):
        QuanLy.objects.create(
            ma_quan_ly=f'QL{i:02d}',
            ten_quan_ly=f"{account.user.last_name} {account.user.first_name}",
            cccd=f"0{random.randint(10000000, 99999999)}",
            ngay_sinh=timezone.now() - timedelta(days=random.randint(10000, 15000)),
            gioi_tinh=random.choice([True, False]),
            que_quan=random.choice(tinh_thanh),
            sdt=f"09{random.randint(10000000, 99999999)}",
            tai_khoan=account
        )
    
    # Tạo sinh viên
    student_accounts = TaiKhoan.objects.filter(role='student')
    phong_list = list(Phong.objects.all())
    
    for i, account in enumerate(student_accounts, 1):
        # Phân bổ phòng cho sinh viên
        if phong_list:
            phong = random.choice(phong_list)
            so_phong = phong.ma_phong
            
            # Số giường thường dựa vào số thứ tự và loại phòng
            max_bed = {'LP01': 4, 'LP02': 6, 'LP03': 8, 'LP04': 2}
            so_giuong = random.randint(1, max_bed[phong.loai_phong.ma_loai_phong])
        else:
            so_phong = ""
            so_giuong = 0
        
        SinhVien.objects.create(
            mssv=f'SV{i:04d}',
            ho_ten=f"{account.user.last_name} {account.user.first_name}",
            cccd=f"0{random.randint(10000000, 99999999)}",
            ngay_sinh=timezone.now() - timedelta(days=random.randint(6500, 9000)),
            gioi_tinh=random.choice([True, False]),
            que_quan=random.choice(tinh_thanh),
            trang_thai=random.choice(['Đang ở', 'Đã rời', 'Đăng ký mới', 'Chờ duyệt']),
            so_phong=so_phong,
            so_giuong=so_giuong,
            tai_khoan=account
        )
    
    # Cập nhật danh sách sinh viên trong phòng
    update_room_student_list()

def update_room_student_list():
    """Cập nhật danh sách sinh viên trong mỗi phòng"""
    for phong in Phong.objects.all():
        student_list = SinhVien.objects.filter(so_phong=phong.ma_phong, trang_thai="Đang ở")
        phong.danh_sach_sv = ", ".join([sv.mssv for sv in student_list])
        phong.so_luong_sv = student_list.count()
        phong.save()

def create_applications():
    """Tạo đơn đăng ký"""
    sinh_viens = SinhVien.objects.all()
    
    for i, sv in enumerate(random.sample(list(sinh_viens), min(30, sinh_viens.count())), 1):
        ngay_dk = timezone.now() - timedelta(days=random.randint(1, 180))
        
        DonDangKy.objects.create(
            ma_don=f'DK{timezone.now().year}{i:04d}',
            mssv=sv,
            ngay_dang_ky=ngay_dk,
            trang_thai=random.choice(['Chờ duyệt', 'Đã duyệt', 'Đã hủy', 'Từ chối']),
            loai_phong=random.choice(['LP01', 'LP02', 'LP03', 'LP04']),
            day_phong=random.choice(['A', 'B', 'C', 'D', 'E'])
        )

def create_contracts():
    """Tạo hợp đồng"""
    sinh_viens = SinhVien.objects.filter(trang_thai='Đang ở')
    phongs = Phong.objects.all()
    
    for sv in sinh_viens:
        if sv.so_phong:
            try:
                phong = Phong.objects.get(ma_phong=sv.so_phong)
                ngay_vao = timezone.now() - timedelta(days=random.randint(30, 365))
                ngay_ra = ngay_vao + timedelta(days=365)  # Hợp đồng 1 năm
                
                HopDong.objects.create(
                    ma_hop_dong=f'HD{timezone.now().year}{sv.mssv[-4:]}',
                    ngay_vao=ngay_vao,
                    ngay_ra=ngay_ra,
                    ma_phong=phong,
                    mssv=sv
                )
            except Phong.DoesNotExist:
                continue

def create_violations():
    """Tạo vi phạm"""
    sinh_viens = SinhVien.objects.all()
    mo_ta_vi_pham = [
        "Về kí túc xá trễ giờ quy định",
        "Gây ồn ào sau 23:00",
        "Sử dụng thiết bị điện không được phép",
        "Không dọn dẹp phòng ở",
        "Để người ngoài ở qua đêm không báo cáo",
        "Sử dụng rượu bia trong kí túc xá",
        "Hút thuốc trong phòng",
        "Vắng mặt không báo cáo",
        "Làm hỏng tài sản công",
        "Gây mất đoàn kết trong phòng ở"
    ]
    
    muc_do = ["Nhẹ", "Trung bình", "Nặng"]
    hinh_thuc_xu_ly = [
        "Nhắc nhở",
        "Cảnh cáo",
        "Phạt tiền",
        "Tạm đình chỉ ở",
        "Buộc thôi ở",
        "Bồi thường"
    ]
    
    # Tạo ngẫu nhiên vi phạm cho khoảng 20% sinh viên
    for sv in random.sample(list(sinh_viens), int(sinh_viens.count() * 0.2)):
        for i in range(random.randint(1, 3)):  # Mỗi sinh viên có thể có 1-3 vi phạm
            ViPham.objects.create(
                ma_vi_pham=f'VP{timezone.now().year}{sv.mssv[-4:]}{i+1}',
                mo_ta=random.choice(mo_ta_vi_pham),
                muc_do=random.choice(muc_do),
                hinh_thuc_xu_ly=random.choice(hinh_thuc_xu_ly),
                mssv=sv
            )

def create_damage_reports():
    """Tạo báo hỏng"""
    phongs = Phong.objects.all()
    mo_ta_hu_hong = [
        "Bóng đèn hỏng",
        "Quạt trần không hoạt động",
        "Ổ điện bị chập",
        "Vòi nước rò rỉ",
        "Cửa sổ không đóng được",
        "Tủ quần áo bị hỏng khóa",
        "Bồn cầu bị tắc",
        "Bồn rửa bị rò nước",
        "Giường bị gãy chân",
        "Kệ sách bị hỏng",
        "Tường bị nứt",
        "Trần nhà bị dột",
        "Máy lạnh không hoạt động",
        "Cửa phòng khó mở",
        "Sàn nhà bị ngập nước"
    ]
    
    # Tạo ngẫu nhiên báo hỏng cho khoảng 30% phòng
    for idx, phong in enumerate(random.sample(list(phongs), int(phongs.count() * 0.3))):
        for i in range(random.randint(1, 2)):  # Mỗi phòng có thể có 1-2 báo hỏng
            ngay_bao = timezone.now() - timedelta(days=random.randint(1, 90))
            
            # Sử dụng idx thay vì chỉ dựa vào mã phòng để đảm bảo tính duy nhất
            ma_bh = f'BH{timezone.now().year}{phong.ma_phong[-3:]}{idx+1}{i+1}'
            
            BaoHong.objects.create(
                ma_bh=ma_bh,
                mo_ta=random.choice(mo_ta_hu_hong),
                ngay_bao=ngay_bao,
                trang_thai=random.choice(['Chờ xử lý', 'Đang xử lý', 'Đã xử lý', 'Hủy']),
                ma_phong=phong
            )

def create_assets():
    """Tạo tài sản và chi tiết tài sản"""
    # Tạo danh sách tài sản
    tai_sans = [
        ('TS01', 'Giường'),
        ('TS02', 'Tủ quần áo'),
        ('TS03', 'Bàn học'),
        ('TS04', 'Ghế'),
        ('TS05', 'Quạt trần'),
        ('TS06', 'Đèn học'),
        ('TS07', 'Đèn phòng'),
        ('TS08', 'Kệ sách'),
        ('TS09', 'Bồn rửa'),
        ('TS10', 'Gương'),
        ('TS11', 'Máy lạnh'),
        ('TS12', 'Bảng thông báo')
    ]
    
    for ma, ten in tai_sans:
        TaiSan.objects.create(ma_tai_san=ma, ten_tai_san=ten)
    
    # Tạo chi tiết tài sản cho mỗi dãy phòng và loại phòng
    day_phongs = DayPhong.objects.all()
    loai_phongs = LoaiPhong.objects.all()
    tai_sans = TaiSan.objects.all()
    
    for day in day_phongs:
        for loai in loai_phongs:
            for tai_san in tai_sans:
                # Xác định số lượng tài sản dựa trên loại phòng và tài sản
                if tai_san.ma_tai_san in ['TS01', 'TS02', 'TS03', 'TS04']:  # Giường, tủ, bàn, ghế
                    if loai.ma_loai_phong == 'LP01':  # 4 người
                        so_luong = 4
                    elif loai.ma_loai_phong == 'LP02':  # 6 người
                        so_luong = 6
                    elif loai.ma_loai_phong == 'LP03':  # 8 người
                        so_luong = 8
                    else:  # VIP 2 người
                        so_luong = 2
                elif tai_san.ma_tai_san in ['TS05', 'TS07', 'TS09', 'TS10']:  # Quạt trần, đèn phòng, bồn rửa, gương
                    so_luong = 1
                elif tai_san.ma_tai_san == 'TS06':  # Đèn học
                    if loai.ma_loai_phong == 'LP01':  # 4 người
                        so_luong = 4
                    elif loai.ma_loai_phong == 'LP02':  # 6 người
                        so_luong = 6
                    elif loai.ma_loai_phong == 'LP03':  # 8 người
                        so_luong = 8
                    else:  # VIP 2 người
                        so_luong = 2
                elif tai_san.ma_tai_san == 'TS08':  # Kệ sách
                    if loai.ma_loai_phong == 'LP01':  # 4 người
                        so_luong = 2
                    elif loai.ma_loai_phong == 'LP02':  # 6 người
                        so_luong = 3
                    elif loai.ma_loai_phong == 'LP03':  # 8 người
                        so_luong = 4
                    else:  # VIP 2 người
                        so_luong = 1
                elif tai_san.ma_tai_san == 'TS11':  # Máy lạnh
                    if loai.ma_loai_phong == 'LP04':  # Chỉ phòng VIP có máy lạnh
                        so_luong = 1
                    else:
                        so_luong = 0
                else:  # Các tài sản khác
                    so_luong = 1
                
                if so_luong > 0:
                    ChiTietTaiSan.objects.create(
                        ma_day_phong=day,
                        ma_loai_phong=loai,
                        ma_tai_san=tai_san,
                        so_luong=so_luong
                    )

def create_utility_readings():
    """Tạo chỉ số điện nước"""
    phongs = Phong.objects.filter(trang_thai='Đầy')
    
    # Tạo dữ liệu cho 6 tháng gần đây
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    for phong in phongs:
        chi_so_dien_cu = random.randint(500, 1000)
        chi_so_nuoc_cu = random.randint(50, 100)
        
        for i in range(6):
            month = current_month - i
            year = current_year
            
            if month <= 0:
                month += 12
                year -= 1
            
            # Tính chỉ số mới: chỉ số cũ + lượng sử dụng
            tieu_thu_dien = random.randint(20, 100)  # kWh
            tieu_thu_nuoc = random.randint(2, 10)    # m³
            
            chi_so_dien_moi = chi_so_dien_cu + tieu_thu_dien
            chi_so_nuoc_moi = chi_so_nuoc_cu + tieu_thu_nuoc
            
            ngay_ghi = datetime(year, month, random.randint(25, 28))
            
            ChiSoDienNuoc.objects.create(
                ma_phong=phong,
                thang=month,
                nam=year,
                chi_so_dien_cu=chi_so_dien_cu,
                chi_so_dien_moi=chi_so_dien_moi,
                chi_so_nuoc_cu=chi_so_nuoc_cu,
                chi_so_nuoc_moi=chi_so_nuoc_moi,
                ngay_ghi=ngay_ghi,
                ghi_chu=""
            )
            
            # Cập nhật chỉ số cũ cho tháng tiếp theo
            chi_so_dien_cu = chi_so_dien_moi
            chi_so_nuoc_cu = chi_so_nuoc_moi

def create_invoices():
    """Tạo hóa đơn"""
    # Tạo hóa đơn tiền phòng
    sinh_viens = SinhVien.objects.filter(trang_thai='Đang ở')
    
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    for sv in sinh_viens:
        if sv.so_phong:
            try:
                phong = Phong.objects.get(ma_phong=sv.so_phong)
                
                # Tạo hóa đơn tiền phòng cho 6 tháng gần đây
                for i in range(6):
                    month = current_month - i
                    year = current_year
                    
                    if month <= 0:
                        month += 12
                        year -= 1
                    
                    ma_hd = f'HD{year}{month:02d}{sv.mssv[-4:]}'
                    ngay_thanh_toan = None
                    
                    # 80% hóa đơn đã thanh toán
                    if random.random() < 0.8:
                        ngay_thanh_toan = datetime(year, month, random.randint(1, 28))
                    
                    HoaDon.objects.create(
                        ma_hoa_don=ma_hd,
                        so_tien=float(phong.gia),
                        loai_hoa_don='Tiền phòng',
                        ngay_thanh_toan=ngay_thanh_toan,
                        mssv=sv,
                        thang=month,
                        ma_phong=phong
                    )
            except Phong.DoesNotExist:
                continue
    
    # Tạo hóa đơn điện nước dựa trên chỉ số đã ghi
    chi_so_list = ChiSoDienNuoc.objects.all()
    
    for chi_so in chi_so_list:
        # Tính tiền điện (3,000 đ/kWh) và tiền nước (25,000 đ/m³)
        tieu_thu_dien = chi_so.chi_so_dien_moi - chi_so.chi_so_dien_cu
        tieu_thu_nuoc = chi_so.chi_so_nuoc_moi - chi_so.chi_so_nuoc_cu
        
        tien_dien = float(tieu_thu_dien * 3000)
        tien_nuoc = float(tieu_thu_nuoc * 25000)
        tong_tien = tien_dien + tien_nuoc
        
        ma_hd = f'DN{chi_so.nam}{chi_so.thang:02d}{chi_so.ma_phong.ma_phong[-3:]}'
        ngay_thanh_toan = None
        
        # 70% hóa đơn đã thanh toán
        if random.random() < 0.7:
            ngay_thanh_toan = chi_so.ngay_ghi + timedelta(days=random.randint(1, 15))
        
        # Tìm một sinh viên trong phòng để gán hóa đơn
        sv_trong_phong = SinhVien.objects.filter(so_phong=chi_so.ma_phong.ma_phong, trang_thai='Đang ở').first()
        
        if sv_trong_phong:
            hoa_don = HoaDon.objects.create(
                ma_hoa_don=ma_hd,
                so_tien=tong_tien,
                loai_hoa_don='Điện nước',
                ngay_thanh_toan=ngay_thanh_toan,
                mssv=sv_trong_phong,
                thang=chi_so.thang,
                ma_phong=chi_so.ma_phong
            )
            
            # Cập nhật hóa đơn cho chỉ số điện nước
            chi_so.hoa_don = hoa_don
            chi_so.save()

# Để chạy script tạo dữ liệu:
# from your_app.fixtures import create_sample_data
# create_sample_data()