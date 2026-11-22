from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("activate/<str:token>/", views.activate, name="activate"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("applications/add/", views.add_application, name="add_application"),
    path("applications/import/", views.import_applications, name="import_applications"),
    path(
        "applications/<int:pk>/delete/",
        views.delete_application,
        name="delete_application",
    ),
    path(
        "applications/<int:pk>/edit/", views.edit_application, name="edit_application"
    ),
    path("export/", views.export_data, name="export_data"),
    path("account/delete/", views.delete_account, name="delete_account"),
    path("billing/checkout/", views.checkout, name="checkout"),
    path("billing/cancel/", views.cancel_subscription, name="cancel_subscription"),
    path("billing/razorpay/webhook/", views.razorpay_webhook, name="razorpay_webhook"),
    path("health/", views.health, name="health"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
    path("pricing/", views.home, name="pricing"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="tracker/form_page.html",
            extra_context={"title": "Reset password", "submit": "Send reset link"},
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="tracker/message_page.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="tracker/form_page.html",
            extra_context={"title": "Choose a new password", "submit": "Save password"},
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="tracker/message_page.html"
        ),
        name="password_reset_complete",
    ),
]
