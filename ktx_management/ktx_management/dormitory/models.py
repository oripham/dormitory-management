from django.db import models
from django.contrib.auth.models import User

class TaiKhoan(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)

    def __str__(self):
        return self.user.username

class DayPhong(models.Model):
    ma_day_phong = models.CharField(max_length=20, primary_key=True)
    ten_day_phong = models.CharField(max_length=50)
    so_phong = models.IntegerField()
    doi_tuong = models.CharField(max_length=20)

    def __str__(self):
        return self.ten_day_phong

class LoaiPhong(models.Model):
    ma_loai_phong = models.CharField(max_length=20, primary_key=True)
    ten_loai_phong = models.CharField(max_length=50)
    so_luong = models.IntegerField()

    def __str__(self):
        return self.ten_loai_phong

class Phong(models.Model):
    ma_phong = models.CharField(max_length=20, primary_key=True)
    so_luong_sv = models.IntegerField()
    loai_phong = models.ForeignKey(LoaiPhong, on_delete=models.CASCADE)
    day_phong = models.ForeignKey(DayPhong, on_delete=models.CASCADE)
    gia = models.IntegerField()
    danh_sach_sv = models.TextField(blank=True, null=True)
    trang_thai = models.CharField(max_length=20)

    def __str__(self):
        return self.ma_phong

class SinhVien(models.Model):
    mssv = models.CharField(max_length=20, primary_key=True)
    ho_ten = models.CharField(max_length=50)
    cccd = models.CharField(max_length=12)
    ngay_sinh = models.DateField()
    gioi_tinh = models.BooleanField()
    que_quan = models.CharField(max_length=100)
    trang_thai = models.CharField(max_length=20)
    so_phong = models.CharField(max_length=20)
    so_giuong = models.IntegerField()
    tai_khoan = models.OneToOneField(TaiKhoan, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.mssv} - {self.ho_ten}"

class QuanLy(models.Model):
    ma_quan_ly = models.CharField(max_length=20, primary_key=True)
    ten_quan_ly = models.CharField(max_length=50)
    cccd = models.CharField(max_length=12)
    ngay_sinh = models.DateField()
    gioi_tinh = models.BooleanField()
    que_quan = models.CharField(max_length=100)
    sdt = models.CharField(max_length=15)
    tai_khoan = models.OneToOneField(TaiKhoan, on_delete=models.CASCADE)

    def __str__(self):
        return self.ten_quan_ly

class DonDangKy(models.Model):
    ma_don = models.CharField(max_length=20, primary_key=True)
    mssv = models.ForeignKey(SinhVien, on_delete=models.CASCADE)
    ngay_dang_ky = models.DateField()
    trang_thai = models.CharField(max_length=20)
    loai_phong = models.CharField(max_length=20)
    day_phong = models.CharField(max_length=20)

    def __str__(self):
        return f"Đơn {self.ma_don} - {self.mssv}"

class ViPham(models.Model):
    ma_vi_pham = models.CharField(max_length=20, primary_key=True)
    mo_ta = models.TextField()
    muc_do = models.CharField(max_length=20)
    hinh_thuc_xu_ly = models.CharField(max_length=50)
    mssv = models.ForeignKey(SinhVien, on_delete=models.CASCADE)

    def __str__(self):
        return f"Vi phạm {self.ma_vi_pham} - {self.mssv}"

class HopDong(models.Model):
    ma_hop_dong = models.CharField(max_length=20, primary_key=True)
    ngay_vao = models.DateField()
    ngay_ra = models.DateField()
    ma_phong = models.ForeignKey(Phong, on_delete=models.CASCADE)
    mssv = models.ForeignKey(SinhVien, on_delete=models.CASCADE)

    def __str__(self):
        return f"Hợp đồng {self.ma_hop_dong} - {self.mssv}"

class BaoHong(models.Model):
    ma_bh = models.CharField(max_length=20, primary_key=True)
    mo_ta = models.TextField()
    ngay_bao = models.DateField()
    trang_thai = models.CharField(max_length=20)
    ma_phong = models.ForeignKey(Phong, on_delete=models.CASCADE)

    def __str__(self):
        return f"Báo hỏng {self.ma_bh} - {self.ma_phong}"

class HoaDon(models.Model):
    ma_hoa_don = models.CharField(max_length=20, primary_key=True)
    so_tien = models.FloatField()
    loai_hoa_don = models.CharField(max_length=20)
    ngay_thanh_toan = models.DateField(null=True, blank=True)
    mssv = models.ForeignKey(SinhVien, on_delete=models.CASCADE)
    thang = models.IntegerField()
    ma_phong = models.ForeignKey(Phong, on_delete=models.CASCADE)

    def __str__(self):
        return f"Hóa đơn {self.ma_hoa_don} - {self.mssv}"

class TaiSan(models.Model):
    ma_tai_san = models.CharField(max_length=20, primary_key=True)
    ten_tai_san = models.CharField(max_length=50)

    def __str__(self):
        return self.ten_tai_san

class ChiTietTaiSan(models.Model):
    ma_day_phong = models.ForeignKey(DayPhong, on_delete=models.CASCADE)
    ma_loai_phong = models.ForeignKey(LoaiPhong, on_delete=models.CASCADE)
    ma_tai_san = models.ForeignKey(TaiSan, on_delete=models.CASCADE)
    so_luong = models.IntegerField()

    class Meta:
        unique_together = (('ma_day_phong', 'ma_loai_phong', 'ma_tai_san'),)

    def __str__(self):
        return f"Tài sản {self.ma_tai_san} - Dãy {self.ma_day_phong} - Loại phòng {self.ma_loai_phong}"
    
class ChiSoDienNuoc(models.Model):
    ma_phong = models.ForeignKey(Phong, on_delete=models.CASCADE)
    thang = models.IntegerField()
    nam = models.IntegerField()
    chi_so_dien_cu = models.IntegerField()
    chi_so_dien_moi = models.IntegerField()
    chi_so_nuoc_cu = models.IntegerField()
    chi_so_nuoc_moi = models.IntegerField()
    ngay_ghi = models.DateField()
    ghi_chu = models.CharField(max_length=255, blank=True, null=True)
    hoa_don = models.OneToOneField(HoaDon, on_delete=models.SET_NULL, null=True, blank=True, related_name='chi_so_dien_nuoc')
    
    @property
    def tieu_thu_dien(self):
        return self.chi_so_dien_moi - self.chi_so_dien_cu
    
    @property
    def tieu_thu_nuoc(self):
        return self.chi_so_nuoc_moi - self.chi_so_nuoc_cu
    
    @property
    def tien_dien(self):
        return self.tieu_thu_dien * 3000  # 3,000 đ/kWh
    
    @property
    def tien_nuoc(self):
        return self.tieu_thu_nuoc * 25000  # 25,000 đ/m³
    
    @property
    def thanh_tien(self):
        return self.tien_dien + self.tien_nuoc
    
    class Meta:
        unique_together = (('ma_phong', 'thang', 'nam'),)
        ordering = ['-nam', '-thang']
    
    def __str__(self):
        return f"Điện nước phòng {self.ma_phong} - {self.thang}/{self.nam}"
