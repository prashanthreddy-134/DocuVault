import os, mimetypes
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import render,redirect,get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Document,Category,Tag,DocumentVersion,DocumentPermission,DocumentAuditLog,DocumentShare,DocumentFavorite
from .forms import DocumentForm,VersionForm,PermissionForm,ShareForm,CommentForm
from .services import can_access,audit

def signup(request):
    if request.user.is_authenticated: return redirect("dashboard")
    form=UserCreationForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        user=form.save();login(request,user);messages.success(request,"Your account is ready.");return redirect("dashboard")
    return render(request,"docs/auth.html",{"form":form,"mode":"Create account"})
def login_view(request):
    form=AuthenticationForm(request,data=request.POST or None)
    if request.method=="POST" and form.is_valid():
        login(request,form.get_user());return redirect("dashboard")
    return render(request,"docs/auth.html",{"form":form,"mode":"Sign in"})
@login_required
def dashboard(request):
    qs=Document.objects.exclude(status="deleted")
    mine=qs.filter(uploaded_by=request.user)
    context={"total":qs.count(),"mine":mine.count(),"shared":DocumentShare.objects.filter(shared_with=request.user,is_active=True).count(),
      "categories":Category.objects.count(),"recent":qs.filter(Q(uploaded_by=request.user)|Q(permissions__user=request.user)|Q(shares__shared_with=request.user)).distinct()[:6]}
    return render(request,"docs/dashboard.html",context)
@login_required
def document_list(request):
    qs=Document.objects.exclude(status="deleted").filter(Q(uploaded_by=request.user)|Q(permissions__user=request.user,permissions__permission_type="view")|Q(permissions__user=request.user,permissions__permission_type="edit")|Q(shares__shared_with=request.user,shares__is_active=True)).distinct()
    q=request.GET.get("q","").strip();category=request.GET.get("category","");status=request.GET.get("status","")
    if q: qs=qs.filter(Q(title__icontains=q)|Q(description__icontains=q)|Q(tags__name__icontains=q)|Q(category__name__icontains=q)).distinct()
    if category.isdigit(): qs=qs.filter(category_id=int(category))
    if status: qs=qs.filter(status=status)
    return render(request,"docs/document_list.html",{"documents":qs,"categories":Category.objects.all(),"q":q,"selected_category":category,"selected_status":status,"statuses":Document.STATUS_CHOICES})
@login_required
def upload_document(request):
    form=DocumentForm(request.POST or None,request.FILES or None)
    if request.method=="POST" and form.is_valid():
        doc=form.save(commit=False);doc.uploaded_by=request.user;doc.file_size=doc.file.size;doc.file_type=os.path.splitext(doc.file.name)[1].lower().lstrip(".");doc.save();form.save_m2m() if hasattr(form,"save_m2m") else None
        names=[x.strip() for x in form.cleaned_data.get("tags_text","").split(",") if x.strip()]
        doc.tags.set([Tag.objects.get_or_create(name=n)[0] for n in names])
        DocumentVersion.objects.create(document=doc,version_number=doc.version,file=doc.file, file_size=doc.file_size,change_note="Initial upload",uploaded_by=request.user)
        audit(doc,request.user,"upload",request,"Document uploaded")
        messages.success(request,"Document uploaded successfully.");return redirect("document_detail",pk=doc.pk)
    return render(request,"docs/form.html",{"form":form,"heading":"Upload document"})
def _doc(request,pk,permission="view"):
    doc=get_object_or_404(Document,pk=pk)
    if not can_access(request.user,doc,permission): raise Http404
    return doc
@login_required
def document_detail(request,pk):
    doc=_doc(request,pk);audit(doc,request.user,"view",request,"Document opened")
    form=CommentForm()
    if request.method=="POST":
        if not can_access(request.user,doc,"edit"): return HttpResponseForbidden("Edit permission required")
        form=CommentForm(request.POST)
        if form.is_valid():
            c=form.save(commit=False);c.document=doc;c.user=request.user;c.save();messages.success(request,"Comment added.");return redirect("document_detail",pk=pk)
    return render(request,"docs/document_detail.html",{"document":doc,"versions":doc.versions.all(),"comments":doc.comments.select_related("user"),"comment_form":form,"can_edit":can_access(request.user,doc,"edit"),"can_download":can_access(request.user,doc,"download")})
@login_required
def edit_document(request,pk):
    doc=_doc(request,pk,"edit");form=DocumentForm(request.POST or None,request.FILES or None,instance=doc)
    if request.method=="POST" and form.is_valid():
        obj=form.save(commit=False)
        if request.FILES.get("file"):
            obj.file_size=obj.file.size;obj.file_type=os.path.splitext(obj.file.name)[1].lower().lstrip(".")
        obj.save()
        names=[x.strip() for x in form.cleaned_data.get("tags_text","").split(",") if x.strip()]
        obj.tags.set([Tag.objects.get_or_create(name=n)[0] for n in names])
        audit(obj,request.user,"edit",request,"Document metadata updated")
        messages.success(request,"Document updated.");return redirect("document_detail",pk=pk)
    return render(request,"docs/form.html",{"form":form,"heading":"Edit document"})
@login_required
def upload_version(request,pk):
    doc=_doc(request,pk,"edit");form=VersionForm(request.POST or None,request.FILES or None)
    if request.method=="POST" and form.is_valid():
        f=form.cleaned_data["file"];major,_,minor=doc.version.partition(".")
        try: new_version=f"{major}.{int(minor or 0)+1}"
        except ValueError: new_version="1.1"
        DocumentVersion.objects.create(document=doc,version_number=new_version,file=f,file_size=f.size,change_note=form.cleaned_data["change_note"],uploaded_by=request.user)
        doc.file=f;doc.file_size=f.size;doc.file_type=os.path.splitext(f.name)[1].lower().lstrip(".");doc.version=new_version;doc.save()
        audit(doc,request.user,"version",request,f"Uploaded version {new_version}")
        messages.success(request,f"Version {new_version} uploaded.");return redirect("document_detail",pk=pk)
    return render(request,"docs/simple_form.html",{"form":form,"heading":"Upload new version","document":doc})
@login_required
def download_document(request,pk):
    doc=_doc(request,pk,"download");audit(doc,request.user,"download",request,"File downloaded");doc.download_count+=1;doc.save(update_fields=["download_count"])
    return FileResponse(doc.file.open("rb"),as_attachment=True,filename=os.path.basename(doc.file.name))
@login_required
def preview_document(request,pk):
    doc=_doc(request,pk,"view");audit(doc,request.user,"view",request,"Document previewed");doc.view_count+=1;doc.save(update_fields=["view_count"])
    ext=doc.file_type.lower()
    if ext not in ("pdf","png","jpg","jpeg","txt"): return redirect("document_detail",pk=pk)
    response=FileResponse(doc.file.open("rb"),as_attachment=False,filename=os.path.basename(doc.file.name))
    response["Content-Type"]=mimetypes.guess_type(doc.file.name)[0] or "application/octet-stream"
    response["X-Content-Type-Options"]="nosniff"
    return response
@login_required
def manage_access(request,pk):
    doc=_doc(request,pk,"share")
    permission_form=PermissionForm();share_form=ShareForm()
    if request.method=="POST":
        action=request.POST.get("action")
        if action=="permission":
            permission_form=PermissionForm(request.POST)
            if permission_form.is_valid():
                user=get_object_or_404(User,username=permission_form.cleaned_data["username"])
                DocumentPermission.objects.get_or_create(document=doc,user=user,permission_type=permission_form.cleaned_data["permission_type"])
                audit(doc,request.user,"permission",request,f"Granted {permission_form.cleaned_data['permission_type']} to {user.username}")
                messages.success(request,"Permission granted.");return redirect("manage_access",pk=pk)
        elif action=="share":
            share_form=ShareForm(request.POST)
            if share_form.is_valid():
                user=get_object_or_404(User,username=share_form.cleaned_data["username"])
                if user==request.user: messages.error(request,"You cannot share a document with yourself.")
                else:
                    share,created=DocumentShare.objects.update_or_create(document=doc,shared_with=user,defaults={"shared_by":request.user,"expires_at":share_form.cleaned_data["expires_at"],"is_active":True})
                    audit(doc,request.user,"share",request,f"Shared with {user.username}")
                    messages.success(request,"Document shared.");return redirect("manage_access",pk=pk)
    return render(request,"docs/access.html",{"document":doc,"permission_form":permission_form,"share_form":share_form,"permissions":doc.permissions.select_related("user"),"shares":doc.shares.select_related("shared_with")})
@login_required
@require_POST
def revoke_permission(request,pk,permission_id):
    doc=_doc(request,pk,"share");obj=get_object_or_404(DocumentPermission,pk=permission_id,document=doc);obj.delete();audit(doc,request.user,"permission",request,"Permission revoked");return redirect("manage_access",pk=pk)
@login_required
@require_POST
def revoke_share(request,pk,share_id):
    doc=_doc(request,pk,"share");obj=get_object_or_404(DocumentShare,pk=share_id,document=doc);obj.is_active=False;obj.save(update_fields=["is_active"]);audit(doc,request.user,"share",request,"Share revoked");return redirect("manage_access",pk=pk)
@login_required
@require_POST
def toggle_favorite(request,pk):
    doc=_doc(request,pk)
    fav,created=DocumentFavorite.objects.get_or_create(document=doc,user=request.user)
    if not created: fav.delete()
    return redirect("document_detail",pk=pk)
@login_required
def audit_trail(request,pk):
    doc=_doc(request,pk,"view")
    if not (doc.uploaded_by_id==request.user.id or request.user.is_superuser or can_access(request.user,doc,"edit")): raise Http404
    return render(request,"docs/audit.html",{"document":doc,"logs":doc.audit_logs.select_related("user")})
@login_required
def category_list(request):
    if request.method=="POST":
        name=request.POST.get("name","").strip()
        if name: Category.objects.get_or_create(name=name,defaults={"description":request.POST.get("description","")})
        return redirect("categories")
    return render(request,"docs/categories.html",{"categories":Category.objects.all()})
