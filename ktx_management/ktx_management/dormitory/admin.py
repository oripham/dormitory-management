from django.contrib import admin
from .models import (
    TaiKhoan, DayPhong, LoaiPhong, Phong, SinhVien, QuanLy, 
    DonDangKy, ViPham, HopDong, BaoHong, HoaDon, TaiSan, ChiTietTaiSan,
    ChiSoDienNuoc
)

admin.site.register(TaiKhoan)
admin.site.register(DayPhong)
admin.site.register(LoaiPhong)
admin.site.register(Phong)
admin.site.register(SinhVien)
admin.site.register(QuanLy)
admin.site.register(DonDangKy)
admin.site.register(ViPham)
admin.site.register(HopDong)
admin.site.register(BaoHong)
admin.site.register(HoaDon)
admin.site.register(TaiSan)
admin.site.register(ChiTietTaiSan)
admin.site.register(ChiSoDienNuoc)