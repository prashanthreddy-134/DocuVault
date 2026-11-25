from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.urls import reverse

class Category(models.Model):
    name=models.CharField(max_length=100,unique=True)
    description=models.TextField(blank=True)
    parent=models.ForeignKey("self",on_delete=models.CASCADE,null=True,blank=True,related_name="subcategories")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=["name"]; verbose_name_plural="Categories"
    def __str__(self): return self.name

class Tag(models.Model):
    name=models.CharField(max_length=50,unique=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Document(models.Model):
    STATUS_CHOICES=[("draft","Draft"),("published","Published"),("archived","Archived"),("deleted","Deleted")]
    title=models.CharField(max_length=200)
    description=models.TextField(blank=True)
    file=models.FileField(upload_to="documents/",validators=[FileExtensionValidator(["pdf","doc","docx","xls","xlsx","txt","png","jpg","jpeg"])])
    file_size=models.BigIntegerField(default=0)
    file_type=models.CharField(max_length=50,blank=True)
    version=models.CharField(max_length=10,default="1.0")
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default="draft")
    category=models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,related_name="documents")
    tags=models.ManyToManyField(Tag,blank=True,related_name="documents")
    uploaded_by=models.ForeignKey(User,on_delete=models.CASCADE,related_name="uploaded_documents")
    uploaded_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    view_count=models.PositiveIntegerField(default=0)
    download_count=models.PositiveIntegerField(default=0)
    def __str__(self): return self.title
    def get_absolute_url(self): return reverse("document_detail",args=[self.pk])
    class Meta: ordering=["-uploaded_at"]

class DocumentVersion(models.Model):
    document=models.ForeignKey(Document,on_delete=models.CASCADE,related_name="versions")
    version_number=models.CharField(max_length=10)
    file=models.FileField(upload_to="documents/versions/")
    file_size=models.BigIntegerField(default=0)
    change_note=models.TextField(blank=True)
    uploaded_by=models.ForeignKey(User,on_delete=models.CASCADE)
    uploaded_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-uploaded_at"]
    def __str__(self): return f"{self.document.title} - v{self.version_number}"

class DocumentPermission(models.Model):
    PERMISSION_TYPES=[("view","View"),("edit","Edit"),("delete","Delete"),("download","Download"),("share","Share")]
    document=models.ForeignKey(Document,on_delete=models.CASCADE,related_name="permissions")
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="document_permissions")
    permission_type=models.CharField(max_length=20,choices=PERMISSION_TYPES)
    granted_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["document","user","permission_type"],name="unique_doc_user_permission")]

class DocumentAuditLog(models.Model):
    ACTION_CHOICES=[("upload","Upload"),("view","View"),("download","Download"),("edit","Edit"),("delete","Delete"),("share","Share"),("version","Version Upload"),("permission","Permission Change")]
    document=models.ForeignKey(Document,on_delete=models.CASCADE,related_name="audit_logs")
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    action=models.CharField(max_length=20,choices=ACTION_CHOICES)
    details=models.TextField(blank=True)
    ip_address=models.GenericIPAddressField(null=True,blank=True)
    user_agent=models.CharField(max_length=200,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-created_at"]

class DocumentShare(models.Model):
    document=models.ForeignKey(Document,on_delete=models.CASCADE,related_name="shares")
    shared_by=models.ForeignKey(User,on_delete=models.CASCADE,related_name="shared_documents")
    shared_with=models.ForeignKey(User,on_delete=models.CASCADE,related_name="received_documents")
    shared_at=models.DateTimeField(auto_now_add=True)
    expires_at=models.DateTimeField(null=True,blank=True)
    is_active=models.BooleanField(default=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["document","shared_with"],name="unique_document_share")]

class DocumentFavorite(models.Model):
    document=models.ForeignKey(Document,on_delete=models.CASCADE,related_name="favorites")
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="document_favorites")
    added_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["document","user"],name="unique_document_favorite")]

class DocumentComment(models.Model):
    document=models.ForeignKey(Document,on_delete=models.CASCADE,related_name="comments")
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    comment=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=["created_at"]
