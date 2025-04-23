from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Sum, F
from django.utils import timezone
import datetime, calendar

from .models import (
    TaiKhoan, DayPhong, LoaiPhong, Phong, SinhVien, QuanLy, 
    DonDangKy, ViPham, HopDong, BaoHong, HoaDon, TaiSan, ChiTietTaiSan, ChiSoDienNuoc
)
from .forms import (
    UserRegisterForm, SinhVienForm, QuanLyForm, DonDangKyForm, 
    BaoHongForm, HoaDonForm, ViPhamForm, ChiSoDienNuocForm
)

@login_required
def home(request):
    try:
        tai_khoan = TaiKhoan.objects.get(user=request.user)
        role = tai_khoan.role
    except TaiKhoan.DoesNotExist:
        role = None

    return render(request, 'dormitory/home.html', {'role': role})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Tạo tài khoản mặc định với vai trò sinh viên
            TaiKhoan.objects.create(user=user, role='student')
            messages.success(request, 'Tài khoản đã được tạo! Bạn có thể đăng nhập ngay.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'dormitory/register.html', {'form': form})

@login_required
def profile(request):
    try:
        tai_khoan = TaiKhoan.objects.get(user=request.user)
        
        if tai_khoan.role == 'student':
            try:
                student = SinhVien.objects.get(tai_khoan=tai_khoan)
                return render(request, 'dormitory/profile.html', {'user_profile': student, 'role': 'student'})
            except SinhVien.DoesNotExist:
                return redirect('complete_profile')
        elif tai_khoan.role == 'manager':
            try:
                manager = QuanLy.objects.get(tai_khoan=tai_khoan)
                return render(request, 'dormitory/profile.html', {'user_profile': manager, 'role': 'manager'})
            except QuanLy.DoesNotExist:
                return redirect('complete_profile')
    except TaiKhoan.DoesNotExist:
        # Nếu không có tài khoản, tạo một tài khoản mới với vai trò mặc định là sinh viên
        tai_khoan = TaiKhoan.objects.create(user=request.user, role='student')
        return redirect('complete_profile')

@login_required
def complete_profile(request):
    try:
        tai_khoan = TaiKhoan.objects.get(user=request.user)
        
        if request.method == 'POST':
            if tai_khoan.role == 'student':
                form = SinhVienForm(request.POST)
                if form.is_valid():
                    student = form.save(commit=False)
                    student.tai_khoan = tai_khoan
                    student.trang_thai = 'Chưa đăng ký KTX'
                    student.so_phong = 'Chưa có'
                    student.so_giuong = 0
                    student.save()
                    return redirect('profile')
            elif tai_khoan.role == 'manager':
                form = QuanLyForm(request.POST)
                if form.is_valid():
                    manager = form.save(commit=False)
                    manager.tai_khoan = tai_khoan
                    manager.save()
                    return redirect('profile')
        else:
            if tai_khoan.role == 'student':
                form = SinhVienForm()
            else:
                form = QuanLyForm()
        
        return render(request, 'dormitory/complete_profile.html', {
            'form': form,
            'role': tai_khoan.role
        })
    except TaiKhoan.DoesNotExist:
        return redirect('profile')

@login_required
def dashboard(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role == 'manager':
        # Thống kê cho quản lý
        tong_sinh_vien = SinhVien.objects.count()
        tong_phong = Phong.objects.count()
        phong_trong = Phong.objects.filter(so_luong_sv__lt=F('loai_phong__so_luong')).count()
        don_dang_ky_moi = DonDangKy.objects.filter(trang_thai='Chờ duyệt').count()
        bao_hong_moi = BaoHong.objects.filter(trang_thai='Chờ xử lý').count()
        
        context = {
            'tong_sinh_vien': tong_sinh_vien,
            'tong_phong': tong_phong,
            'phong_trong': phong_trong,
            'don_dang_ky_moi': don_dang_ky_moi,
            'bao_hong_moi': bao_hong_moi,
            'role': 'manager'
        }
    else:
        # Thông tin cho sinh viên
        sinh_vien = SinhVien.objects.get(tai_khoan=tai_khoan)
        
        try:
            # Kiểm tra hợp đồng
            hop_dong = HopDong.objects.filter(mssv=student).order_by('-ngay_vao').first()
            # Kiểm tra hóa đơn chưa thanh toán
            hoa_don_chua_tt = HoaDon.objects.filter(mssv=student, ngay_thanh_toan=None).count()
            # Kiểm tra vi phạm
            vi_pham = ViPham.objects.filter(mssv=student).count()
            
            context = {
                'sinh_vien': sinh_vien,
                'hop_dong': hop_dong,
                'hoa_don_chua_tt': hoa_don_chua_tt,
                'vi_pham': vi_pham,
                'role': 'student'
            }
        except Exception as e:
            context = {
                'sinh_vien': sinh_vien,
                'error': str(e),
                'role': 'student'
            }
    
    return render(request, 'dormitory/dashboard.html', context)

@login_required
def dang_ky_phong(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'student':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    student = SinhVien.objects.get(tai_khoan=tai_khoan)
    
    # Kiểm tra xem sinh viên đã có đơn đăng ký chưa xử lý hay chưa
    don_dang_ky = DonDangKy.objects.filter(mssv=student, trang_thai='Chờ xử lý').first()
    
    if don_dang_ky:
        messages.warning(request, 'Bạn đang có đơn đăng ký đang chờ xử lý!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DonDangKyForm(request.POST)
        if form.is_valid():
            don = form.save(commit=False)
            don.mssv = student
            don.ngay_dang_ky = datetime.date.today()
            don.trang_thai = 'Chờ xử lý'
            don.ma_don = f"DK{student.mssv}{datetime.date.today().strftime('%Y%m%d')}"
            don.save()
            messages.success(request, 'Đăng ký phòng thành công! Vui lòng chờ xét duyệt.')
            return redirect('dashboard')
    else:
        form = DonDangKyForm()
    
    # Lấy danh sách loại phòng và dãy phòng
    loai_phong_list = LoaiPhong.objects.all()
    day_phong_list = DayPhong.objects.all()
    
    return render(request, 'dormitory/dang_ky_phong.html', {
        'form': form,
        'loai_phong_list': loai_phong_list,
        'day_phong_list': day_phong_list
    })

@login_required
def bao_hong(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'student':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    student = SinhVien.objects.get(tai_khoan=tai_khoan)
    
    # Kiểm tra sinh viên đã có phòng chưa
    if student.so_phong == 'Chưa có':
        messages.error(request, 'Bạn chưa có phòng ở KTX!')
        return redirect('dashboard')
    
    try:
        phong = Phong.objects.get(ma_phong=student.so_phong)
    except Phong.DoesNotExist:
        messages.error(request, 'Không tìm thấy thông tin phòng!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = BaoHongForm(request.POST)
        if form.is_valid():
            bao_hong = form.save(commit=False)
            bao_hong.ma_bh = f"BH{student.mssv}{datetime.date.today().strftime('%Y%m%d')}"
            bao_hong.ngay_bao = datetime.date.today()
            bao_hong.trang_thai = 'Chờ xử lý'
            bao_hong.ma_phong = phong
            bao_hong.save()
            messages.success(request, 'Báo hỏng thành công! Vui lòng chờ xử lý.')
            return redirect('dashboard')
    else:
        form = BaoHongForm()
    
    # Lấy danh sách báo hỏng của phòng
    bao_hong_list = BaoHong.objects.filter(ma_phong=phong).order_by('-ngay_bao')
    
    return render(request, 'dormitory/bao_hong.html', {
        'form': form,
        'bao_hong_list': bao_hong_list,
        'phong': phong
    })

@login_required
def quan_ly_don_dang_ky(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    # Lấy danh sách đơn đăng ký
    don_dang_ky_list = DonDangKy.objects.all().order_by('-ngay_dang_ky')
    
    return render(request, 'dormitory/quan_ly_don_dang_ky.html', {
        'don_dang_ky_list': don_dang_ky_list,
        'role': tai_khoan.role
    })

@login_required
def xu_ly_don_dang_ky(request, ma_don):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    don = get_object_or_404(DonDangKy, ma_don=ma_don)
    
    if request.method == 'POST':
        trang_thai = request.POST.get('trang_thai')
        ma_phong = request.POST.get('ma_phong')
        so_giuong = request.POST.get('so_giuong')
        
        if trang_thai == 'Đã duyệt':
            if not ma_phong or not so_giuong:
                messages.error(request, 'Vui lòng chọn phòng và giường!')
                return redirect('xu_ly_don_dang_ky', ma_don=ma_don)
            
            try:
                phong = Phong.objects.get(ma_phong=ma_phong)
                # Kiểm tra số lượng sinh viên trong phòng
                if phong.so_luong_sv >= phong.loai_phong.so_luong:
                    messages.error(request, 'Phòng đã đầy!')
                    return redirect('xu_ly_don_dang_ky', ma_don=ma_don)
                
                # Cập nhật thông tin sinh viên
                student = don.mssv
                student.so_phong = ma_phong
                student.so_giuong = so_giuong
                student.trang_thai = 'Đã có phòng'
                student.save()
                
                # Cập nhật số lượng sinh viên trong phòng
                phong.so_luong_sv += 1
                phong.save()
                
                # Tạo hợp đồng
                ngay_vao = datetime.date.today()
                ngay_ra = ngay_vao.replace(year=ngay_vao.year + 1)
                
                hop_dong = HopDong.objects.create(
                    ma_hop_dong=f"HD{student.mssv}{ngay_vao.strftime('%Y%m%d')}",
                    ngay_vao=ngay_vao,
                    ngay_ra=ngay_ra,
                    ma_phong=phong,
                    mssv=student
                )
                
                # Tạo hóa đơn phòng cho tháng hiện tại
                thang_hien_tai = datetime.date.today().month
                HoaDon.objects.create(
                    ma_hoa_don=f"HD{student.mssv}{thang_hien_tai}{datetime.date.today().year}",
                    so_tien=phong.gia,
                    loai_hoa_don='Tiền phòng',
                    ngay_thanh_toan=None,
                    mssv=student,
                    thang=thang_hien_tai,
                    ma_phong=phong
                )
                
            except Phong.DoesNotExist:
                messages.error(request, 'Không tìm thấy phòng này!')
                return redirect('xu_ly_don_dang_ky', ma_don=ma_don)
        
        # Cập nhật trạng thái đơn
        don.trang_thai = trang_thai
        don.save()
        
        messages.success(request, f'Đã {trang_thai.lower()} đơn đăng ký!')
        return redirect('quan_ly_don_dang_ky')
    
    # Lấy danh sách phòng có thể đăng ký
    phong_list = Phong.objects.filter(
        so_luong_sv__lt=F('loai_phong__so_luong'),
        loai_phong__ma_loai_phong=don.loai_phong,
        day_phong__ma_day_phong=don.day_phong
    )
    
    return render(request, 'dormitory/xu_ly_don_dang_ky.html', {
        'don': don,
        'phong_list': phong_list
    })

@login_required
def quan_ly_phong(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    # Lấy danh sách phòng
    phong_list = Phong.objects.all().order_by('day_phong', 'ma_phong')
    
    # Thống kê theo dãy phòng
    thong_ke_day = DayPhong.objects.annotate(so_phong_day=Count('phong'))
    
    return render(request, 'dormitory/quan_ly_phong.html', {
        'phong_list': phong_list,
        'thong_ke_day': thong_ke_day,
        'role': tai_khoan.role
    })

@login_required
def chi_tiet_phong(request, ma_phong):
    phong = get_object_or_404(Phong, ma_phong=ma_phong)
    
    # Lấy danh sách sinh viên trong phòng
    student_list = SinhVien.objects.filter(so_phong=ma_phong).order_by('so_giuong')
    
    # Lấy danh sách báo hỏng của phòng
    bao_hong_list = BaoHong.objects.filter(ma_phong=phong).order_by('-ngay_bao')
    
    return render(request, 'dormitory/chi_tiet_phong.html', {
        'phong': phong,
        'student_list': student_list,
        'bao_hong_list': bao_hong_list
    })

@login_required
def quan_ly_sinh_vien(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    # Lấy danh sách sinh viên
    student_list = SinhVien.objects.all().order_by('mssv')
    
    return render(request, 'dormitory/quan_ly_sinh_vien.html', {
        'student_list': student_list,
        'role': tai_khoan.role
    })

@login_required
def quan_ly_bao_hong(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    # Lấy danh sách báo hỏng
    bao_hong_list = BaoHong.objects.all().order_by('-ngay_bao')
    
    return render(request, 'dormitory/quan_ly_bao_hong.html', {
        'bao_hong_list': bao_hong_list,
        'role': tai_khoan.role
    })

@login_required
def xu_ly_bao_hong(request, ma_bh):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    bao_hong = get_object_or_404(BaoHong, ma_bh=ma_bh)
    
    if request.method == 'POST':
        trang_thai = request.POST.get('trang_thai')
        
        bao_hong.trang_thai = trang_thai
        bao_hong.save()
        
        messages.success(request, f'Đã cập nhật trạng thái báo hỏng thành {trang_thai}!')
        return redirect('quan_ly_bao_hong')
    
    return render(request, 'dormitory/xu_ly_bao_hong.html', {
        'bao_hong': bao_hong
    })

@login_required
def quan_ly_hoa_don(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    # Lấy danh sách hóa đơn
    hoa_don_list = HoaDon.objects.all().order_by('-thang')
    
    return render(request, 'dormitory/quan_ly_hoa_don.html', {
        'hoa_don_list': hoa_don_list,
        'role': tai_khoan.role
    })

@login_required
def xem_hoa_don(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'student':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    student = SinhVien.objects.get(tai_khoan=tai_khoan)
    
    # Lấy danh sách hóa đơn của sinh viên
    hoa_don_list = HoaDon.objects.filter(mssv=student).order_by('-thang')
    
    return render(request, 'dormitory/xem_hoa_don.html', {
        'hoa_don_list': hoa_don_list
    })

@login_required
def thanh_toan_hoa_don(request, ma_hoa_don):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'student':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    student = SinhVien.objects.get(tai_khoan=tai_khoan)
    hoa_don = get_object_or_404(HoaDon, ma_hoa_don=ma_hoa_don, mssv=student)
    
    if hoa_don.ngay_thanh_toan:
        messages.warning(request, 'Hóa đơn này đã được thanh toán rồi!')
        return redirect('xem_hoa_don')
    
    if request.method == 'POST':
        hoa_don.ngay_thanh_toan = datetime.date.today()
        hoa_don.save()
        
        messages.success(request, 'Thanh toán hóa đơn thành công!')
        return redirect('xem_hoa_don')
    
    return render(request, 'dormitory/thanh_toan_hoa_don.html', {
        'hoa_don': hoa_don
    })

@login_required
def quan_ly_vi_pham(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    # Lấy danh sách sinh viên
    student_list = SinhVien.objects.all()
    
    return render(request, 'dormitory/quan_ly_vi_pham.html', {
        'student_list': student_list
    })

@login_required
def them_vi_pham(request, mssv):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    student = get_object_or_404(SinhVien, mssv=mssv)
    
    if request.method == 'POST':
        form = ViPhamForm(request.POST)
        if form.is_valid():
            vi_pham = form.save(commit=False)
            vi_pham.ma_vi_pham = f"VP{student.mssv}{timezone.now().strftime('%Y%m%d%H%M')}"
            vi_pham.mssv = student
            vi_pham.save()
            messages.success(request, f'Đã thêm vi phạm cho sinh viên {student.ho_ten}')
            return redirect('quan_ly_vi_pham')
    else:
        form = ViPhamForm()
    
    # Lấy danh sách vi phạm của sinh viên
    vi_pham_list = ViPham.objects.filter(mssv=student)
    
    return render(request, 'dormitory/them_vi_pham.html', {
        'form': form,
        'student': student,
        'vi_pham_list': vi_pham_list
    })

@login_required
def quan_ly_dien_nuoc(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    # Lấy danh sách phòng
    phong_list = Phong.objects.all()
    
    return render(request, 'dormitory/quan_ly_dien_nuoc.html', {
        'phong_list': phong_list
    })

@login_required
def quan_ly_dien_nuoc(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    phong_list = Phong.objects.all().order_by('day_phong__ten_day_phong', 'ma_phong')
    
    return render(request, 'dormitory/quan_ly_dien_nuoc.html', {
        'phong_list': phong_list
    })

@login_required
def ghi_so_dien_nuoc(request, ma_phong):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    phong = get_object_or_404(Phong, ma_phong=ma_phong)
    
    # Lấy ngày hiện tại
    ngay_hien_tai = datetime.date.today()
    thang_hien_tai = ngay_hien_tai.month
    nam_hien_tai = ngay_hien_tai.year
    
    # Tạo danh sách tháng và năm cho form
    thang_options = range(1, 13)
    nam_options = range(nam_hien_tai - 2, nam_hien_tai + 1)
    
    # Lấy chỉ số điện nước cũ nhất
    chi_so_cu = ChiSoDienNuoc.objects.filter(ma_phong=phong).order_by('-nam', '-thang').first()
    
    chi_so_dien_cu = 0
    chi_so_nuoc_cu = 0
    
    if chi_so_cu:
        chi_so_dien_cu = chi_so_cu.chi_so_dien_moi
        chi_so_nuoc_cu = chi_so_cu.chi_so_nuoc_moi
    
    if request.method == 'POST':
        thang = int(request.POST.get('thang'))
        nam = int(request.POST.get('nam'))
        chi_so_dien_moi = int(request.POST.get('chi_so_dien_moi'))
        chi_so_nuoc_moi = int(request.POST.get('chi_so_nuoc_moi'))
        ngay_ghi = request.POST.get('ngay_ghi')
        ghi_chu = request.POST.get('ghi_chu', '')
        
        # Kiểm tra xem đã có chỉ số cho tháng này chưa
        chi_so_ton_tai = ChiSoDienNuoc.objects.filter(ma_phong=phong, thang=thang, nam=nam).first()
        
        if chi_so_ton_tai:
            # Cập nhật chỉ số cũ
            chi_so_ton_tai.chi_so_dien_moi = chi_so_dien_moi
            chi_so_ton_tai.chi_so_nuoc_moi = chi_so_nuoc_moi
            chi_so_ton_tai.ngay_ghi = ngay_ghi
            chi_so_ton_tai.ghi_chu = ghi_chu
            chi_so_ton_tai.save()
            messages.success(request, f'Cập nhật chỉ số điện nước tháng {thang}/{nam} thành công!')
        else:
            # Tạo chỉ số mới
            ChiSoDienNuoc.objects.create(
                ma_phong=phong,
                thang=thang,
                nam=nam,
                chi_so_dien_cu=chi_so_dien_cu,
                chi_so_dien_moi=chi_so_dien_moi,
                chi_so_nuoc_cu=chi_so_nuoc_cu,
                chi_so_nuoc_moi=chi_so_nuoc_moi,
                ngay_ghi=ngay_ghi,
                ghi_chu=ghi_chu
            )
            messages.success(request, f'Ghi chỉ số điện nước tháng {thang}/{nam} thành công!')
            
        return redirect('ghi_so_dien_nuoc', ma_phong=ma_phong)
    
    # Lấy lịch sử ghi chỉ số
    lich_su = ChiSoDienNuoc.objects.filter(ma_phong=phong).order_by('-nam', '-thang')
    
    return render(request, 'dormitory/ghi_so_dien_nuoc.html', {
        'phong': phong,
        'thang_options': thang_options,
        'nam_options': nam_options,
        'thang_hien_tai': thang_hien_tai,
        'nam_hien_tai': nam_hien_tai,
        'chi_so_dien_cu': chi_so_dien_cu,
        'chi_so_nuoc_cu': chi_so_nuoc_cu,
        'ngay_ghi': ngay_hien_tai,
        'lich_su': lich_su
    })

@login_required
def bao_cao_dien_nuoc(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    # Lấy thông tin tháng năm hiện tại
    thang_hien_tai = timezone.now().month
    nam_hien_tai = timezone.now().year
    
    # Mặc định là tháng hiện tại
    thang = request.GET.get('thang', thang_hien_tai)
    nam = request.GET.get('nam', nam_hien_tai)
    
    try:
        thang = int(thang)
        nam = int(nam)
    except ValueError:
        thang = thang_hien_tai
        nam = nam_hien_tai
    
    # Lấy dữ liệu điện nước theo tháng năm
    chi_so_list = ChiSoDienNuoc.objects.filter(thang=thang, nam=nam)
    
    # Tổng số điện nước
    tong_dien = chi_so_list.aggregate(Sum('tong_dien'))['tong_dien__sum'] or 0
    tong_nuoc = chi_so_list.aggregate(Sum('tong_nuoc'))['tong_nuoc__sum'] or 0
    
    # Gia điện nước
    gia_dien = 3000  # VND/kWh
    gia_nuoc = 25000  # VND/m3
    
    # Tổng tiền
    tong_tien_dien = tong_dien * gia_dien
    tong_tien_nuoc = tong_nuoc * gia_nuoc
    tong_tien = tong_tien_dien + tong_tien_nuoc
    
    # Danh sách các tháng và năm
    thang_list = list(range(1, 13))
    nam_list = list(range(nam_hien_tai - 2, nam_hien_tai + 1))
    
    return render(request, 'dormitory/bao_cao_dien_nuoc.html', {
        'chi_so_list': chi_so_list,
        'thang': thang,
        'nam': nam,
        'thang_list': thang_list,
        'nam_list': nam_list,
        'tong_dien': tong_dien,
        'tong_nuoc': tong_nuoc,
        'gia_dien': gia_dien,
        'gia_nuoc': gia_nuoc,
        'tong_tien_dien': tong_tien_dien,
        'tong_tien_nuoc': tong_tien_nuoc,
        'tong_tien': tong_tien
    })

@login_required
def doi_mat_khau(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Giữ người dùng đăng nhập sau khi đổi mật khẩu
            messages.success(request, 'Mật khẩu của bạn đã được thay đổi thành công.')
            return redirect('doi-mat-khau')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'dormitory/doi_mat_khau.html', {'form': form})