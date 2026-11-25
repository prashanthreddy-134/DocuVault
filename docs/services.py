from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import DocumentPermission, DocumentShare, DocumentAuditLog
def can_access(user,doc,permission="view"):
    if not user.is_authenticated: return False
    if user.is_superuser or doc.uploaded_by_id==user.id: return True
    if doc.status=="deleted": return False
    if DocumentPermission.objects.filter(document=doc,user=user,permission_type=permission).exists(): return True
    if permission in ("view","download") and DocumentShare.objects.filter(document=doc,shared_with=user,is_active=True).filter(models_expiry()).exists(): return True
    return False
def models_expiry():
    from django.db.models import Q
    return Q(expires_at__isnull=True)|Q(expires_at__gt=timezone.now())
def audit(doc,user,action,request=None,details=""):
    meta=request.META if request else {}
    ip=meta.get("HTTP_X_FORWARDED_FOR","").split(",")[0].strip() or meta.get("REMOTE_ADDR")
    DocumentAuditLog.objects.create(document=doc,user=user,action=action,details=details,
      ip_address=ip or None,user_agent=meta.get("HTTP_USER_AGENT","")[:200])
