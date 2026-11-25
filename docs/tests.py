
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from .models import (
    Category,
    Document,
    DocumentPermission,
    DocumentAuditLog,
    DocumentShare,
    DocumentFavorite,
)
from .services import can_access


class DocumentSystemTests(TestCase):

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.settings = override_settings(MEDIA_ROOT=self.temp.name)
        self.settings.enable()
        self.addCleanup(self.settings.disable)

        self.owner = User.objects.create_user(
            username="owner",
            password="StrongPass123!"
        )

        self.reader = User.objects.create_user(
            username="reader",
            password="StrongPass123!"
        )

        self.category = Category.objects.create(name="Policies")

        self.client = Client()
        self.client.force_login(self.owner)

    def upload(self, title="Safety policy"):
        uploaded_file = SimpleUploadedFile(
            "policy.txt",
            b"Example policy content",
            content_type="text/plain"
        )

        return self.client.post(
            reverse("upload_document"),
            {
                "title": title,
                "description": "Company safety",
                "file": uploaded_file,
                "category": self.category.id,
                "status": "published",
                "tags_text": "safety, policy",
            }
        )

    def test_dashboard_and_auth_pages(self):
        self.client.logout()

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)

    def test_upload_creates_version_and_audit(self):
        response = self.upload()

        document = Document.objects.get(title="Safety policy")

        self.assertRedirects(
            response,
            reverse("document_detail", args=[document.pk])
        )

        self.assertEqual(document.versions.count(), 1)

        self.assertTrue(
            document.audit_logs.filter(action="upload").exists()
        )

        self.assertEqual(
            document.file_size,
            len(b"Example policy content")
        )

    def test_search_and_category_filter(self):
        self.upload()

        response = self.client.get(
            reverse("document_list"),
            {
                "q": "safety",
                "category": self.category.id,
            }
        )

        self.assertContains(response, "Safety policy")

        response = self.client.get(
            reverse("document_list"),
            {"q": "notfound"}
        )

        self.assertNotContains(response, "Safety policy")

    def test_owner_can_preview_download_and_counts_increment(self):
        self.upload()

        document = Document.objects.get(title="Safety policy")

        # Test preview and explicitly close the file response.
        preview_response = self.client.get(
            reverse("preview_document", args=[document.pk])
        )

        self.assertEqual(preview_response.status_code, 200)
        preview_response.close()

        # Test download and explicitly close the file response.
        download_response = self.client.get(
            reverse("download_document", args=[document.pk])
        )

        self.assertEqual(download_response.status_code, 200)
        download_response.close()

        document.refresh_from_db()

        self.assertEqual(document.view_count, 1)
        self.assertEqual(document.download_count, 1)

        self.assertTrue(
            document.audit_logs.filter(action="download").exists()
        )

    def test_version_upload_updates_current_file(self):
        self.upload()

        document = Document.objects.get(title="Safety policy")

        uploaded_file = SimpleUploadedFile(
            "policy-v2.txt",
            b"Updated policy",
            content_type="text/plain"
        )

        response = self.client.post(
            reverse("upload_version", args=[document.pk]),
            {
                "file": uploaded_file,
                "change_note": "Updated wording",
            }
        )

        document.refresh_from_db()

        self.assertRedirects(
            response,
            reverse("document_detail", args=[document.pk])
        )

        self.assertEqual(document.version, "1.1")
        self.assertEqual(document.versions.count(), 2)

        self.assertTrue(
            document.audit_logs.filter(action="version").exists()
        )

    def test_private_document_denies_other_users_until_permission(self):
        self.upload()

        document = Document.objects.get(title="Safety policy")

        self.assertFalse(
            can_access(self.reader, document, "view")
        )

        DocumentPermission.objects.create(
            document=document,
            user=self.reader,
            permission_type="view"
        )

        self.assertTrue(
            can_access(self.reader, document, "view")
        )

        self.client.force_login(self.reader)

        response = self.client.get(
            reverse("document_detail", args=[document.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_share_expiry_and_favorite_toggle(self):
        self.upload()

        document = Document.objects.get(title="Safety policy")

        DocumentShare.objects.create(
            document=document,
            shared_by=self.owner,
            shared_with=self.reader
        )

        self.assertTrue(
            can_access(self.reader, document, "view")
        )

        self.client.post(
            reverse("toggle_favorite", args=[document.pk])
        )

        self.assertTrue(
            DocumentFavorite.objects.filter(
                document=document,
                user=self.owner
            ).exists()
        )

        self.client.post(
            reverse("toggle_favorite", args=[document.pk])
        )

        self.assertFalse(
            DocumentFavorite.objects.filter(
                document=document,
                user=self.owner
            ).exists()
        )

    def test_edit_comment_and_audit_trail(self):
        self.upload()

        document = Document.objects.get(title="Safety policy")

        self.client.post(
            reverse("document_detail", args=[document.pk]),
            {"comment": "Reviewed"}
        )

        self.assertEqual(document.comments.count(), 1)

        response = self.client.get(
            reverse("audit_trail", args=[document.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_access_management_and_revoke(self):
        self.upload()

        document = Document.objects.get(title="Safety policy")

        self.client.post(
            reverse("manage_access", args=[document.pk]),
            {
                "action": "permission",
                "username": "reader",
                "permission_type": "view",
            }
        )

        permission = DocumentPermission.objects.get(
            document=document,
            user=self.reader
        )

        self.assertTrue(
            can_access(self.reader, document, "view")
        )

        self.client.post(
            reverse(
                "revoke_permission",
                args=[document.pk, permission.pk]
            )
        )

        self.assertFalse(
            can_access(self.reader, document, "view")
        )

    def test_category_creation_and_admin(self):
        response = self.client.post(
            reverse("categories"),
            {"name": "HR"}
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Category.objects.filter(name="HR").exists()
        )

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 302)
