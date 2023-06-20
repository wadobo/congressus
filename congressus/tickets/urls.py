from django.urls import path

from tickets import views


urlpatterns = [
    path("", views.last_event, name="last_event"),
    path("event/<str:ev>/", views.event, name="event"),
    path(
        "event/<str:ev>/<str:space>/<str:session>/register/",
        views.register,
        name="register",
    ),
    path("ticket/<str:order>/payment/", views.payment, name="payment"),
    path("ticket/<str:order>/thanks/", views.thanks, name="thanks"),
    path("ticket/confirm/", views.confirm, name="confirm"),
    path("ticket/confirm/paypal/", views.confirm_paypal, name="confirm_paypal"),
    path(
        "ticket/<str:order>/confirm/stripe/",
        views.confirm_stripe,
        name="confirm_stripe",
    ),
    path(
        "ticket/template/<int:id>/preview/",
        views.TicketTemplatePreview.as_view(),
        name="template_preview",
    ),
    path(
        "ticket/template/<int:id>/preview/pdf/",
        views.TicketTemplatePreviewPDF.as_view(),
        name="template_preview_pdf",
    ),
    path(
        "ticket/email-confirm/<int:id>/preview/",
        views.email_confirm_preview,
        name="email_confirm_preview",
    ),
    path("<str:ev>/", views.multipurchase, name="multipurchase"),
    path("seats/<int:session>/<int:layout>/", views.ajax_layout, name="ajax_layout"),
    path("seats/view/<int:map>/", views.seats, name="seats"),
    path("seats/auto/", views.autoseats, name="autoseats"),
    path("seats/bystr/", views.seats_by_str, name="seats_by_str"),
]
