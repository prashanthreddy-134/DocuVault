from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
urlpatterns=[
 path("",views.dashboard,name="dashboard"),path("signup/",views.signup,name="signup"),path("login/",views.login_view,name="login"),
 path("logout/",LogoutView.as_view(),name="logout"),path("documents/",views.document_list,name="document_list"),
 path("documents/upload/",views.upload_document,name="upload_document"),path("documents/<int:pk>/",views.document_detail,name="document_detail"),
 path("documents/<int:pk>/edit/",views.edit_document,name="edit_document"),path("documents/<int:pk>/version/",views.upload_version,name="upload_version"),
 path("documents/<int:pk>/download/",views.download_document,name="download_document"),path("documents/<int:pk>/preview/",views.preview_document,name="preview_document"),
 path("documents/<int:pk>/access/",views.manage_access,name="manage_access"),path("documents/<int:pk>/permission/<int:permission_id>/revoke/",views.revoke_permission,name="revoke_permission"),
 path("documents/<int:pk>/share/<int:share_id>/revoke/",views.revoke_share,name="revoke_share"),
 path("documents/<int:pk>/favorite/",views.toggle_favorite,name="toggle_favorite"),path("documents/<int:pk>/audit/",views.audit_trail,name="audit_trail"),
 path("categories/",views.category_list,name="categories"),
]
