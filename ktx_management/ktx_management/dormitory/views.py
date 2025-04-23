from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Sum, F
from django.utils import timezone
import datetime, calendar
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import get_template
from .models import (
    TaiKhoan, DayPhong, LoaiPhong, Phong, SinhVien, QuanLy, 
    DonDangKy, ViPham, HopDong, BaoHong, HoaDon, TaiSan, ChiTietTaiSan, ChiSoDienNuoc
)
from .forms import (
    UserRegisterForm, SinhVienForm, QuanLyForm, DonDangKyForm, 
    BaoHongForm, HoaDonForm, ViPhamForm, ChiSoDienNuocForm
)
from django.http import JsonResponse
import json
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
            hop_dong = HopDong.objects.filter(mssv=sinh_vien).order_by('-ngay_vao').first()
            # Kiểm tra hóa đơn chưa thanh toán
            hoa_don_chua_tt = HoaDon.objects.filter(mssv=sinh_vien, ngay_thanh_toan=None).count()
            # Kiểm tra vi phạm
            vi_pham = ViPham.objects.filter(mssv=sinh_vien).count()
            
            context = {
                'sinh_vien': sinh_vien,
                'hop_dong': hop_dong,
                'hoa_don_chua_tt': hoa_don_chua_tt,
                'vi_pham': vi_pham,
                'role': 'student',
                'so_phong': sinh_vien.so_phong,
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
    
    # Kiểm tra xem sinh viên đã có phòng ở hay chưa
    if student.so_phong and student.so_phong != 'Chưa có':
        messages.info(request, 'Bạn đã có phòng ở. Không thể đăng ký thêm.')
        return redirect('dashboard')
    
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
        'day_phong_list': day_phong_list,
        'role': tai_khoan.role
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
        'so_phong': phong.ma_phong,
        'role': tai_khoan.role
    })

@login_required
def quan_ly_don_dang_ky(request):
    # Lấy trạng thái từ query parameters
    trang_thai = request.GET.get('trang_thai', '')

    # Lấy danh sách đơn đăng ký
    don_dang_ky_list = DonDangKy.objects.all()

    # Lọc theo trạng thái nếu có
    if trang_thai:
        don_dang_ky_list = don_dang_ky_list.filter(trang_thai=trang_thai)

    # Sắp xếp theo ngày đăng ký (ưu tiên ai đăng ký trước)
    don_dang_ky_list = don_dang_ky_list.order_by('ngay_dang_ky')

    return render(request, 'dormitory/quan_ly_don_dang_ky.html', {
        'don_dang_ky_list': don_dang_ky_list,
        'trang_thai': trang_thai,
        'role': TaiKhoan.objects.get(user=request.user).role
    })

@login_required
def xu_ly_don_dang_ky(request, ma_don):
    # Lấy thông tin đơn đăng ký
    don = get_object_or_404(DonDangKy, ma_don=ma_don)
    tai_khoan = TaiKhoan.objects.get(user=request.user)

    # Kiểm tra số chỗ trống trong dãy phòng
    phong_list = Phong.objects.filter(day_phong=don.day_phong, loai_phong=don.loai_phong)
    so_cho_trong = phong_list.aggregate(
        tong_cho_trong=Sum(F('loai_phong__so_luong') - F('so_luong_sv'))
    )['tong_cho_trong']

    # Nếu không còn chỗ trống, tự động từ chối đơn
    if so_cho_trong is None or so_cho_trong <= 0:
        don.trang_thai = 'Từ chối'
        don.save()
        messages.error(request, 'Loại phòng thuộc dãy này đã hết chỗ. Đơn đăng ký đã bị từ chối.')
        return redirect('quan_ly_don_dang_ky')

    if request.method == 'POST':
        # Lấy trạng thái từ form
        trang_thai = request.POST.get('trang_thai')

        if trang_thai == 'Đã duyệt':
            # Cập nhật trạng thái đơn
            don.trang_thai = trang_thai
            don.save()

            # Gửi thông báo thành công
            messages.success(request, f'Đã {trang_thai.lower()} đơn đăng ký!')
            return redirect('quan_ly_don_dang_ky')

        elif trang_thai == 'Từ chối':
            # Cập nhật trạng thái đơn
            don.trang_thai = trang_thai
            don.save()
            # Gửi thông báo từ chối
            messages.success(request, f'Đã {trang_thai.lower()} đơn đăng ký!')
            return redirect('quan_ly_don_dang_ky')

    return render(request, 'dormitory/xu_ly_don_dang_ky.html', {
        'don': don,
        'role': tai_khoan.role
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
    
    # Lấy danh sách sinh viên chỉ có trạng thái "Đang ở"
    sinh_vien_list = SinhVien.objects.filter(trang_thai='Đang ở').order_by('mssv')
    phong_list = Phong.objects.all()  # Lấy danh sách phòng để hiển thị trong dropdown

    return render(request, 'dormitory/quan_ly_sinh_vien.html', {
        'sinh_vien_list': sinh_vien_list,
        'phong_list': phong_list,
        'role': tai_khoan.role,
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
    # Kiểm tra quyền truy cập
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    # Lấy giá trị lọc từ query parameters
    loai_hoa_don = request.GET.get('loai_hoa_don', '')
    
    # Khởi tạo query set
    hoa_don_list = HoaDon.objects.all()
    
    # Lọc theo loại hóa đơn nếu có
    if loai_hoa_don:
        hoa_don_list = hoa_don_list.filter(loai_hoa_don=loai_hoa_don)
    
    # Sắp xếp kết quả
    hoa_don_list = hoa_don_list.order_by('-thang')
    
    # Chuẩn bị context cho template
    context = {
        'hoa_don_list': hoa_don_list,
        'role': tai_khoan.role,
        'loai_hoa_don': loai_hoa_don,  # Truyền giá trị lọc vào context
        'current_year': timezone.now().year
    }
    
    return render(request, 'dormitory/quan_ly_hoa_don.html', context)

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
        'hoa_don_list': hoa_don_list,
        'role': tai_khoan.role
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
        'sinh_vien_list': student_list,
        'role': tai_khoan.role
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
        'sinh_vien': student,
        'vi_pham_list': vi_pham_list,
        'role': tai_khoan.role
    })


@login_required
def quan_ly_dien_nuoc(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    phong_list = Phong.objects.all().order_by('day_phong__ten_day_phong', 'ma_phong')
    
    return render(request, 'dormitory/quan_ly_dien_nuoc.html', {
        'phong_list': phong_list,
        'role': tai_khoan.role
    })

@login_required
def ghi_so_dien_nuoc(request, ma_phong):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    # Lấy thông tin phòng từ mã phòng
    phong = get_object_or_404(Phong, ma_phong=ma_phong)
    
    # Kiểm tra quyền truy cập
    if tai_khoan.role == 'student':
        # Nếu là sinh viên, chỉ được ghi chỉ số cho phòng của mình
        sinh_vien = SinhVien.objects.get(tai_khoan=tai_khoan)
        if sinh_vien.so_phong != ma_phong:
            messages.error(request, 'Bạn không có quyền ghi chỉ số cho phòng này!')
            return redirect('dashboard')
    elif tai_khoan.role != 'manager':
        # Nếu không phải manager hoặc student, từ chối truy cập
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
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
            messages.warning(request, f'Chỉ số điện nước tháng {thang}/{nam} đã được ghi trước đó!')
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
        'lich_su': lich_su,
        'role': tai_khoan.role
    })

@login_required
def ghi_so_dien_nuoc_sinh_vien(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    # Kiểm tra quyền truy cập
    if tai_khoan.role != 'student':
        messages.error(request, 'Chức năng này chỉ dành cho sinh viên!')
        return redirect('dashboard')
    
    # Lấy thông tin sinh viên và phòng
    sinh_vien = get_object_or_404(SinhVien, tai_khoan=tai_khoan)
    if not sinh_vien.so_phong:
        messages.error(request, 'Bạn chưa được phân phòng!')
        return redirect('dashboard')
    
    phong = get_object_or_404(Phong, ma_phong=sinh_vien.so_phong)
    
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
            messages.warning(request, f'Chỉ số điện nước tháng {thang}/{nam} đã được ghi trước đó!')
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
            
        return redirect('ghi_so_dien_nuoc_sinh_vien')
    
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
        'lich_su': lich_su,
        'role': tai_khoan.role
    })

@login_required
def bao_cao_dien_nuoc(request):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    # Lấy thông tin tháng và năm hiện tại
    thang_hien_tai = timezone.now().month
    nam_hien_tai = timezone.now().year
    
    # Lọc dữ liệu theo tháng, năm, dãy phòng, trạng thái
    thang = request.GET.get('thang', None)
    nam = request.GET.get('nam', None)
    day_phong_selected = request.GET.get('day_phong', None)
    trang_thai_selected = request.GET.get('trang_thai', None)
    
    filters = {}
    if thang:
        filters['thang'] = thang
    if nam:
        filters['nam'] = nam
    if day_phong_selected:
        filters['ma_phong__day_phong__ma_day_phong'] = day_phong_selected
    if trang_thai_selected == 'chua_thanh_toan':
        filters['hoa_don__ngay_thanh_toan__isnull'] = True  # Hóa đơn chưa được thanh toán
    elif trang_thai_selected == 'da_thanh_toan':
        filters['hoa_don__ngay_thanh_toan__isnull'] = False  # Hóa đơn đã được thanh toán
    
    # Lấy danh sách chỉ số điện nước
    chi_so_list = ChiSoDienNuoc.objects.filter(**filters).select_related('hoa_don', 'ma_phong', 'ma_phong__day_phong')
    
    # Tính toán các giá trị cần thiết
    chi_so_data = []
    tong_dien_tieu_thu = 0
    tong_nuoc_tieu_thu = 0
    tong_tien_dien = 0
    tong_tien_nuoc = 0
    
    for chi_so in chi_so_list:
        tieu_thu_dien = chi_so.chi_so_dien_moi - chi_so.chi_so_dien_cu
        tieu_thu_nuoc = chi_so.chi_so_nuoc_moi - chi_so.chi_so_nuoc_cu
        tien_dien = tieu_thu_dien * 3000  # Giá điện: 3000 VND/kWh
        tien_nuoc = tieu_thu_nuoc * 25000  # Giá nước: 25000 VND/m³
        thanh_tien = tien_dien + tien_nuoc
        
        tong_dien_tieu_thu += tieu_thu_dien
        tong_nuoc_tieu_thu += tieu_thu_nuoc
        tong_tien_dien += tien_dien
        tong_tien_nuoc += tien_nuoc
        
        chi_so_data.append({
            'chi_so': chi_so,
            'tieu_thu_dien': tieu_thu_dien,
            'tieu_thu_nuoc': tieu_thu_nuoc,
            'tien_dien': tien_dien,
            'tien_nuoc': tien_nuoc,
            'thanh_tien': thanh_tien,
        })
    
    # Danh sách các tháng và năm
    thang_list = list(range(1, 13))
    nam_list = list(range(nam_hien_tai - 2, nam_hien_tai + 1))
    day_phong_list = DayPhong.objects.all()
    
    return render(request, 'dormitory/bao_cao_dien_nuoc.html', {
        'lich_su_dien_nuoc': chi_so_data,
        'thang_selected': thang,
        'nam_selected': nam,
        'day_phong_selected': day_phong_selected,
        'trang_thai_selected': trang_thai_selected,
        'thang_options': thang_list,
        'nam_options': nam_list,
        'day_phong_list': day_phong_list,
        'tong_dien_tieu_thu': tong_dien_tieu_thu,
        'tong_nuoc_tieu_thu': tong_nuoc_tieu_thu,
        'tong_tien_dien': tong_tien_dien,
        'tong_tien_nuoc': tong_tien_nuoc,
        'role': tai_khoan.role
    })

@login_required
def tao_hoa_don(request, chi_so_id):
    tai_khoan = TaiKhoan.objects.get(user=request.user)
    
    if tai_khoan.role != 'manager':
        messages.error(request, 'Bạn không có quyền truy cập chức năng này!')
        return redirect('dashboard')
    
    # Lấy thông tin chỉ số điện nước
    chi_so = get_object_or_404(ChiSoDienNuoc, id=chi_so_id)
    
    # Lấy danh sách sinh viên trong phòng
    sinh_vien_list = SinhVien.objects.filter(so_phong=chi_so.ma_phong.ma_phong)
    
    # Tính toán các giá trị cần thiết
    tieu_thu_dien = chi_so.chi_so_dien_moi - chi_so.chi_so_dien_cu
    tieu_thu_nuoc = chi_so.chi_so_nuoc_moi - chi_so.chi_so_nuoc_cu
    tong_tien_dien = tieu_thu_dien * 3000
    tong_tien_nuoc = tieu_thu_nuoc * 25000
    tong_tien = tong_tien_dien + tong_tien_nuoc
    
    if request.method == 'POST':
        # Lấy sinh viên đại diện từ form
        sinh_vien_dai_dien_mssv = request.POST.get('sinh_vien_dai_dien')
        sinh_vien_dai_dien = get_object_or_404(SinhVien, mssv=sinh_vien_dai_dien_mssv)
        
        # Tạo hóa đơn
        hoa_don = HoaDon.objects.create(
            ma_hoa_don=f"HD{timezone.now().strftime('%Y%m%d%H%M%S')}",
            so_tien=tong_tien,
            loai_hoa_don='Điện nước',
            ma_phong=chi_so.ma_phong,
            thang=chi_so.thang,
            mssv=sinh_vien_dai_dien,  # Lưu sinh viên đại diện
            ngay_thanh_toan=None  # Chưa thanh toán
        )
        
        # Liên kết hóa đơn với chỉ số điện nước
        chi_so.hoa_don = hoa_don
        chi_so.save()
        
        messages.success(request, f'Đã tạo hóa đơn cho phòng {chi_so.ma_phong.ma_phong}.')
        return redirect('bao_cao_dien_nuoc')
    
    return render(request, 'dormitory/tao_hoa_don.html', {
        'chi_so': chi_so,
        'sinh_vien_list': sinh_vien_list,
        'tieu_thu_dien': tieu_thu_dien,
        'tieu_thu_nuoc': tieu_thu_nuoc,
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

@login_required
def chi_tiet_hoa_don(request, ma_hoa_don):
    """
    Hiển thị chi tiết của một hóa đơn dựa trên mã hóa đơn.
    """
    # Lấy hóa đơn từ mã hoặc trả về 404 nếu không tìm thấy
    hoa_don = get_object_or_404(HoaDon, ma_hoa_don=ma_hoa_don)
    
    # Kiểm tra quyền truy cập
    # Nếu là sinh viên, chỉ được xem hóa đơn của mình
    if hasattr(request.user, 'taikhoan') and request.user.taikhoan.role == 'sinh_vien':
        if hasattr(request.user.taikhoan, 'sinhvien') and request.user.taikhoan.sinhvien.mssv != hoa_don.mssv.mssv:
            return render(request, '403.html', {'message': 'Bạn không có quyền xem hóa đơn này'}, status=403)
    
    # Nếu là hóa đơn điện nước, lấy thêm thông tin chi tiết
    chi_so_dien_nuoc = None
    if hoa_don.loai_hoa_don == 'Điện nước':
        try:
            chi_so_dien_nuoc = ChiSoDienNuoc.objects.get(hoa_don=hoa_don)
        except ChiSoDienNuoc.DoesNotExist:
            pass
    
    context = {
        'hoa_don': hoa_don,
        'chi_so_dien_nuoc': chi_so_dien_nuoc,
        'sinh_vien': hoa_don.mssv,
        'phong': hoa_don.ma_phong,
        'role': TaiKhoan.objects.get(user=request.user).role,
    }
    
    return render(request, 'dormitory/chi_tiet_hoa_don.html', context)

@login_required
def chinh_sua_hoa_don(request, ma_hoa_don):
    hoa_don = get_object_or_404(HoaDon, ma_hoa_don=ma_hoa_don)

    # Khởi tạo biến chi_so_dien_nuoc mặc định là None
    chi_so_dien_nuoc = None

    # Nếu hóa đơn là loại "Điện nước", lấy thông tin chỉ số điện nước
    if hoa_don.loai_hoa_don == 'Điện nước':
        chi_so_dien_nuoc = ChiSoDienNuoc.objects.filter(hoa_don=hoa_don).first()
        print(chi_so_dien_nuoc)

    if request.method == 'POST':
        hoa_don_form = HoaDonForm(request.POST, instance=hoa_don)
        chi_so_form = ChiSoDienNuocForm(request.POST, instance=chi_so_dien_nuoc) if chi_so_dien_nuoc else None

        if hoa_don_form.is_valid() and (chi_so_form is None or chi_so_form.is_valid()):
            hoa_don_form.save()
            if chi_so_form:
                chi_so_form.save()
            messages.success(request, 'Hóa đơn đã được cập nhật thành công.')
            return redirect('quan_ly_hoa_don')
    else:
        hoa_don_form = HoaDonForm(instance=hoa_don)
        chi_so_form = ChiSoDienNuocForm(instance=chi_so_dien_nuoc) if chi_so_dien_nuoc else None

    return render(request, 'dormitory/chinh_sua_hoa_don.html', {
        'hoa_don_form': hoa_don_form,
        'chi_so_form': chi_so_form,
        'role': TaiKhoan.objects.get(user=request.user).role
    })

@csrf_exempt
@login_required
def xoa_hoa_don(request):
    if request.method == 'POST':
        try:
            # Lấy dữ liệu JSON từ body
            data = json.loads(request.body)
            ma_hoa_don = data.get('ma_hoa_don')
            print(f"Yêu cầu xóa hóa đơn: {ma_hoa_don}")

            # Kiểm tra và xóa hóa đơn
            hoa_don = get_object_or_404(HoaDon, ma_hoa_don=ma_hoa_don)
            hoa_don.delete()
            print(f"Đã xóa hóa đơn: {ma_hoa_don}")
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            print("Dữ liệu JSON không hợp lệ.")
            return JsonResponse({'success': False, 'error': 'Dữ liệu JSON không hợp lệ.'}, status=400)
        except Exception as e:
            print(f"Lỗi: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    print("Yêu cầu không phải POST")
    return JsonResponse({'success': False, 'error': 'Yêu cầu không phải POST'}, status=400)

@login_required
def quan_ly_hop_dong(request):
    # Lấy danh sách hợp đồng
    hop_dong_list = HopDong.objects.all().order_by('-ngay_vao')

    return render(request, 'dormitory/quan_ly_hop_dong.html', {
        'hop_dong_list': hop_dong_list,
        'role': TaiKhoan.objects.get(user=request.user).role
    })

@csrf_exempt
@login_required
def cap_nhat_trang_thai_phong(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ma_phong = data.get('ma_phong')
            trang_thai = data.get('trang_thai')

            # Kiểm tra trạng thái hợp lệ
            if trang_thai not in ['Trống', 'Đầy', 'Bảo trì', 'Đang sửa chữa']:
                return JsonResponse({'success': False, 'error': 'Trạng thái không hợp lệ.'})

            # Cập nhật trạng thái phòng
            phong = Phong.objects.get(ma_phong=ma_phong)
            phong.trang_thai = trang_thai
            phong.save()

            return JsonResponse({'success': True})
        except Phong.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Phòng không tồn tại.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Phương thức không hợp lệ.'})

@csrf_exempt
@login_required
def cap_nhat_chuyen_phong(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mssv = data.get('mssv')
            phong_moi = data.get('phong_moi')

            # Kiểm tra sinh viên tồn tại
            sinh_vien = SinhVien.objects.get(mssv=mssv)

            # Cập nhật phòng mới
            sinh_vien.so_phong = phong_moi
            sinh_vien.save()

            return JsonResponse({'success': True})
        except SinhVien.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Sinh viên không tồn tại.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Phương thức không hợp lệ.'})

@csrf_exempt
@login_required
def cap_nhat_trang_thai_bao_hong(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ma_bh = data.get('ma_bh')
            trang_thai = data.get('trang_thai')

            # Kiểm tra báo hỏng tồn tại
            bao_hong = BaoHong.objects.get(ma_bh=ma_bh)

            # Cập nhật trạng thái
            bao_hong.trang_thai = trang_thai
            bao_hong.save()

            return JsonResponse({'success': True})
        except BaoHong.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Báo hỏng không tồn tại.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Phương thức không hợp lệ.'})

def xuat_pdf_hop_dong(request, ma_hop_dong):
    # Lấy thông tin hợp đồng từ cơ sở dữ liệu
    hop_dong = get_object_or_404(HopDong, ma_hop_dong=ma_hop_dong)

    # Dữ liệu truyền vào template
    context = {
        'hopDong': hop_dong,
        'sinhVien': hop_dong.mssv,
        'quanLy': {
            'ten_quan_ly': 'Nguyễn Văn A',  # Thay bằng thông tin quản lý thực tế
            'cccd': '123456789012',
            'sdt': '0987654321',
        },
        'phong': hop_dong.ma_phong,
    }

    # Đường dẫn đến template HTML
    template_path = 'dormitory/template_hop_dong.html'

    # Render template HTML
    template = get_template(template_path)
    html = template.render(context)

    # Tạo file PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="hop_dong_{ma_hop_dong}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)

    # Kiểm tra lỗi
    if pisa_status.err:
        return HttpResponse('Có lỗi xảy ra khi tạo PDF', status=500)
    return response

from django.shortcuts import render, get_object_or_404

def hien_thi_hop_dong(request, ma_hop_dong):
    # Lấy thông tin hợp đồng từ cơ sở dữ liệu
    hop_dong = get_object_or_404(HopDong, ma_hop_dong=ma_hop_dong)

    # Truyền dữ liệu vào template
    context = {
        'hopDong': hop_dong,
        'sinhVien': hop_dong.mssv,
        'quanLy': {
            'ten_quan_ly': 'Nguyễn Văn A',  # Thay bằng thông tin quản lý thực tế
            'cccd': '123456789012',
            'sdt': '0987654321',
        },
        'phong': hop_dong.ma_phong,
    }
    return render(request, 'dormitory/template_hop_dong.html', context)