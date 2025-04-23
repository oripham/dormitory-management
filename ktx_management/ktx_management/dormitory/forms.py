from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import SinhVien, QuanLy, DonDangKy, BaoHong, HoaDon, ViPham, ChiSoDienNuoc


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class SinhVienForm(forms.ModelForm):
    class Meta:
        model = SinhVien
        fields = ['mssv', 'ho_ten', 'cccd', 'ngay_sinh', 'gioi_tinh', 'que_quan']
        widgets = {
            'ngay_sinh': forms.DateInput(attrs={'type': 'date'}),
        }

class QuanLyForm(forms.ModelForm):
    class Meta:
        model = QuanLy
        fields = ['ma_quan_ly', 'ten_quan_ly', 'cccd', 'ngay_sinh', 'gioi_tinh', 'que_quan', 'sdt']
        widgets = {
            'ngay_sinh': forms.DateInput(attrs={'type': 'date'}),
        }

class DonDangKyForm(forms.ModelForm):
    class Meta:
        model = DonDangKy
        fields = ['loai_phong', 'day_phong']

class BaoHongForm(forms.ModelForm):
    class Meta:
        model = BaoHong
        fields = ['mo_ta']
        widgets = {
            'mo_ta': forms.Textarea(attrs={'rows': 3}),
        }

class HoaDonForm(forms.ModelForm):
    class Meta:
        model = HoaDon
        fields = ['so_tien', 'loai_hoa_don', 'thang']

class ViPhamForm(forms.ModelForm):
    class Meta:
        model = ViPham
        fields = ['mo_ta', 'muc_do', 'hinh_thuc_xu_ly']
        widgets = {
            'mo_ta': forms.Textarea(attrs={'rows': 3}),
        }

class ChiSoDienNuocForm(forms.ModelForm):
    class Meta:
        model = ChiSoDienNuoc
        fields = ['chi_so_dien_moi', 'chi_so_nuoc_moi']
        labels = {
            'chi_so_dien_moi': 'Chỉ số điện mới',
            'chi_so_nuoc_moi': 'Chỉ số nước mới',
        }
