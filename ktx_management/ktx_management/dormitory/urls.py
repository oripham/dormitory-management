from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dang-ky-phong/', views.dang_ky_phong, name='dang_ky_phong'),
    path('bao-hong/', views.bao_hong, name='bao_hong'),
    path('quan-ly-don-dang-ky/', views.quan_ly_don_dang_ky, name='quan_ly_don_dang_ky'),
    path('xu-ly-don-dang-ky/<str:ma_don>/', views.xu_ly_don_dang_ky, name='xu_ly_don_dang_ky'),
    path('quan-ly-phong/', views.quan_ly_phong, name='quan_ly_phong'),
    path('chi-tiet-phong/<str:ma_phong>/', views.chi_tiet_phong, name='chi_tiet_phong'),
    path('quan-ly-sinh-vien/', views.quan_ly_sinh_vien, name='quan_ly_sinh_vien'),
    path('quan-ly-bao-hong/', views.quan_ly_bao_hong, name='quan_ly_bao_hong'),
    path('xu-ly-bao-hong/<str:ma_bh>/', views.xu_ly_bao_hong, name='xu_ly_bao_hong'),
    path('quan-ly-hoa-don/', views.quan_ly_hoa_don, name='quan_ly_hoa_don'),
    path('xem-hoa-don/', views.xem_hoa_don, name='xem_hoa_don'),
    path('thanh-toan-hoa-don/<str:ma_hoa_don>/', views.thanh_toan_hoa_don, name='thanh_toan_hoa_don'),
    path('login/', auth_views.LoginView.as_view(template_name='dormitory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='dormitory/logout.html'), name='logout'),
    path('quan-ly-vi-pham/', views.quan_ly_vi_pham, name='quan_ly_vi_pham'),
    path('them-vi-pham/<str:mssv>/', views.them_vi_pham, name='them_vi_pham'),

    path('quan-ly-dien-nuoc/', views.quan_ly_dien_nuoc, name='quan_ly_dien_nuoc'),
    path('ghi-so-dien-nuoc/<str:ma_phong>/', views.ghi_so_dien_nuoc, name='ghi_so_dien_nuoc'),
    path('ghi-so-dien-nuoc/', views.ghi_so_dien_nuoc_sinh_vien, name='ghi_so_dien_nuoc_sinh_vien'),
    path('bao-cao-dien-nuoc/', views.bao_cao_dien_nuoc, name='bao_cao_dien_nuoc'),

    path('doi-mat-khau/', views.doi_mat_khau, name='doi-mat-khau'),
    path('chi-tiet-hoa-don/<str:ma_hoa_don>/', views.chi_tiet_hoa_don, name='chi_tiet_hoa_don'),
    path('chinh-sua-hoa-don/<str:ma_hoa_don>/', views.chinh_sua_hoa_don, name='chinh_sua_hoa_don'),
    path('xoa-hoa-don/', views.xoa_hoa_don, name='xoa_hoa_don'),

    path('quan-ly-hop-dong/', views.quan_ly_hop_dong, name='quan_ly_hop_dong'),
    path('cap-nhat-trang-thai-phong/', views.cap_nhat_trang_thai_phong, name='cap_nhat_trang_thai_phong'),
    path('cap-nhat-chuyen-phong/', views.cap_nhat_chuyen_phong, name='cap_nhat_chuyen_phong'),
    path('cap-nhat-trang-thai-bao-hong/', views.cap_nhat_trang_thai_bao_hong, name='cap_nhat_trang_thai_bao_hong'),

    path('xuat-pdf-hop-dong/<str:ma_hop_dong>/', views.xuat_pdf_hop_dong, name='xuat_pdf_hop_dong'),
    path('hien-thi-hop-dong/<str:ma_hop_dong>/', views.hien_thi_hop_dong, name='hien_thi_hop_dong'),

    #sinh-vien
    path('xem-hoa-don/', views.xem_hoa_don, name='xem_hoa_don'),
    path('tao-hoa-don/<int:chi_so_id>/', views.tao_hoa_don, name='tao_hoa_don'),
]
