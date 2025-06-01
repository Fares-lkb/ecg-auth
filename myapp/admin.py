from django.contrib import admin
from django.template.response import TemplateResponse
from .models import Info, UserDB
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
import os
from django.contrib.admin import AdminSite
from .models import UserDB, ECGRecord, SVMModels
from .forms import UserWithECGForm


class CustomAdminSite(AdminSite):
    site_header = "ECG Authentication Admin"
    site_title = "ECG Admin Portal"
    index_title = "📊 Admin Dashboard & Shortcuts"

    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}


# Instantiate your custom site
custom_admin_site = CustomAdminSite(name="custom_admin")

# 📁 Define logs folder path
LOGS_BASE_PATH = os.path.join(settings.BASE_DIR, "logs")

# 🛡 Custom Admin for User (Admins Management)
from django.contrib.auth.forms import UserChangeForm


class CustomUserAdmin(BaseUserAdmin):
    form = UserChangeForm  # Use Django's secure form that hides password

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Remove raw password field (read-only hash) from all fieldsets
        new_fieldsets = []
        for name, options in fieldsets:
            fields = list(options.get("fields", []))
            if "password" in fields:
                fields.remove("password")
            new_fieldsets.append((name, {"fields": fields}))
        return new_fieldsets

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if not change:
            if not obj.is_superuser:
                obj.is_staff = True
                obj.save()
                try:
                    group = Group.objects.get(name="StaffAdmins")
                    obj.groups.add(group)
                except Group.DoesNotExist:
                    pass
            else:
                obj.save()
        else:
            obj.save()


# 🛡 Custom Admin for Group (Only Superadmins can manage)
class CustomGroupAdmin(GroupAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


class UserWithECGAdmin(admin.ModelAdmin):
    form = UserWithECGForm
    list_display = ("user_id", "first_name", "last_name", "matricule")

    def has_module_permission(self, request):
        print("🔍 User:", request.user)
        print("🔍 Groups:", [g.name for g in request.user.groups.all()])
        print(
            "🔍 is in StaffAdmins:",
            request.user.groups.filter(name="StaffAdmins").exists(),
        )
        return request.user.groups.filter(name="StaffAdmins").exists()

    def has_view_permission(self, request, obj=None):
        return request.user.groups.filter(name="StaffAdmins").exists()

    def has_add_permission(self, request):
        return request.user.groups.filter(name="StaffAdmins").exists()

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name="StaffAdmins").exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name="StaffAdmins").exists()

    def get_inline_instances(self, request, obj=None):
        if not self.has_view_permission(request, obj):
            return []
        return super().get_inline_instances(request, obj)


# ✅ Register the model here
admin.site.register(UserDB, UserWithECGAdmin)


# 🛡 Custom Admin for Info (Users Form Uploads) — only StaffAdmins
@admin.register(Info)
class InfoAdmin(admin.ModelAdmin):
    list_display = ("matricule", "username", "name", "get_filename")

    def has_add_permission(self, request):
        return False

    class Media:
        css = {"all": ("myapp/css/admin.css",)}  # Adjust the path if needed
        js = ("myapp/js/hideadd.js",)

    def get_filename(self, obj):
        return obj.fileupload.name.split("/")[-1] if obj.fileupload else "No file"

    get_filename.short_description = "ECG File"

    def has_module_permission(self, request):
        return request.user.groups.filter(name="StaffAdmins").exists()

    def has_view_permission(self, request, obj=None):
        return request.user.groups.filter(name="StaffAdmins").exists()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# 🛡 Custom Admin for UserDB (Users Database) — only StaffAdmins
class UserDBAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "matricule")

    class Media:
        css = {"all": ("static/css/admin.css",)}

    search_fields = ("matricule", "first_name", "last_name")

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.groups.filter(name="StaffAdmins").exists()

    def has_add_permission(self, request):
        return request.user.groups.filter(name="StaffAdmins").exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name="StaffAdmins").exists()

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name="StaffAdmins").exists()

    def has_add_permission(self, request):
        if request.path.endswith("/userdb/"):
            return True
        return False


class SVMModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nom",
    )  # Remplace par les champs de ton modèle
    search_fields = ("nom",)


# 🔄 Unregister default User and Group and Register with Custom Admins
admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, CustomUserAdmin)
admin.site.register(ECGRecord)
# 📋 Custom Admin Homepage (dex.html)
from django.shortcuts import redirect


def custom_admin_index(request):
    folders = (
        sorted(os.listdir(LOGS_BASE_PATH), reverse=True)[:5]
        if os.path.exists(LOGS_BASE_PATH)
        else []
    )

    app_list = admin.site.get_app_list(request)

    # Allow StaffAdmins even if no models visible
    if request.user.groups.filter(name="StaffAdmins").exists() and not app_list:
        app_list = [
            {
                "name": "User Management",
                "app_label": "user_management",
                "models": [],
            }
        ]

    # Separate Admin and User management
    admin_management = []
    user_management = []

    for app in app_list:
        models = []
        for model in app["models"]:
            if model["object_name"] in ["User", "Group"]:
                admin_management.append(model)
            elif model["object_name"] in ["UserDB", "Info"]:
                user_management.append(model)

    context = dict(
        admin.site.each_context(request),
        title="ECG Dashboard",
        recent_days=folders,
        admin_management=admin_management,
        user_management=user_management,
    )

    return TemplateResponse(request, "adpage/dex.html", context)


# 🛠 Override the default admin index
original_index = admin.site.index


def wrapped_admin_index(request, extra_context=None):
    response = custom_admin_index(request)
    response.context_data["app_list"] = admin.site.get_app_list(request)
    return response


admin.site.index = wrapped_admin_index


# 📁 Log Folder Overview View
def user_logs_view(request):
    print("✅ Reached user_logs_view")
    search_query = request.GET.get("q", "").strip().lower()
    folders = (
        sorted(os.listdir(LOGS_BASE_PATH), reverse=True)
        if os.path.exists(LOGS_BASE_PATH)
        else []
    )

    # 🔍 Ajoute un filtrage si une recherche est lancée
    if search_query:
        folders = [f for f in folders if search_query in f.lower()]

    context = dict(
        admin.site.each_context(request),
        title="User Logs by Day",
        folders=folders,
        search_query=search_query,
    )
    return TemplateResponse(request, "archpage/user_logs.html", context)


# 📄 Logs for a Specific Day View
def user_logs_by_date_view(request, log_date):
    search_query = request.GET.get("q", "").lower()
    folder_path = os.path.join(LOGS_BASE_PATH, log_date)
    entries = []

    # 🔁 Si suppression demandée
    if request.method == "POST" and "delete_files" in request.POST:
        filenames = request.POST.getlist("delete_files")
        for filename in filenames:
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        return redirect(request.path)

    if os.path.exists(folder_path):
        for filename in sorted(os.listdir(folder_path)):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, "r") as f:
                    content = f.read()

                if not search_query or search_query in content.lower():
                    entries.append(
                        {
                            "filename": filename,
                            "content": content,
                            "download_path": f"/logs/{log_date}/{filename}",
                        }
                    )
            except Exception as e:
                entries.append(
                    {
                        "filename": filename,
                        "content": f"Could not read file: {e}",
                        "download_path": "",
                    }
                )

    context = dict(
        admin.site.each_context(request),
        title=f"Logs for {log_date}",
        log_date=log_date,
        entries=entries,
        search_query=search_query,
    )
    return TemplateResponse(request, "archpage/user_logs_by_day.html", context)


from django.urls import path
from django.utils.safestring import mark_safe
from django.template.response import TemplateResponse
from .models import ContactMessage
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.conf import settings
import os
from django.shortcuts import redirect

from .models import ContactMessage

# ✅ Chemin des messages (à partir de BASE_DIR/messages/...)
MESSAGES_BASE_PATH = os.path.join(settings.BASE_DIR, "messages")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    readonly_fields = ("name", "email", "message")

    # ✅ Supprimer complètement la liste normale (aucun objet visible)
    def get_queryset(self, request):
        return self.model.objects.none()

    # ✅ Quand on entre dans ContactMessage, afficher les dossiers directement
    def changelist_view(self, request, extra_context=None):
        return self.messages_by_day(request)

    # ✅ Supprimer un message (bouton visible dans la fiche)
    def change_view(self, request, object_id, form_url="", extra_context=None):
        delete_url = reverse("admin:myapp_contactmessage_delete", args=[object_id])
        extra_context = extra_context or {}
        extra_context["custom_button"] = format_html(
            '<div style="margin: 20px 0;">'
            '<a class="button" style="background:red;color:white;padding:6px 12px;border-radius:5px;" href="{}">'
            "🗑 Delete this message</a></div>",
            delete_url,
        )
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )

    # ✅ Ajouter les URLs personnalisées à ContactMessage
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "by-day/",
                self.admin_site.admin_view(self.messages_by_day),
                name="contactmessage_by_day",
            ),
            path(
                "by-day/<str:day>/",
                self.admin_site.admin_view(self.messages_by_date),
                name="contactmessage_by_date",
            ),
        ]
        return custom_urls + urls

    # ✅ Afficher les dossiers (dates)
    def messages_by_day(self, request):
        folders = []
        if os.path.exists(MESSAGES_BASE_PATH):
            folders = sorted(os.listdir(MESSAGES_BASE_PATH), reverse=True)

        # ✅ Filtrage par date (GET ?q=2025-05-18)
        search_query = request.GET.get("q")
        if search_query:
            folders = [f for f in folders if search_query in f]

        context = dict(
            self.admin_site.each_context(request),
            title="📂 Contact Messages by Day",
            folders=folders,
        )
        return TemplateResponse(request, "archpage/contact_message_days.html", context)

    # ✅ Afficher tous les fichiers d’un jour donné
    def messages_by_date(self, request, day):
        folder_path = os.path.join(MESSAGES_BASE_PATH, day, "contact_messages")
        entries = []

        # 🔁 Si l'utilisateur a cliqué sur "Delete"
        if request.method == "POST" and "delete_filename" in request.POST:
            filename = request.POST["delete_filename"]
            file_path = os.path.join(folder_path, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                self.message_user(request, f"✅ Message '{filename}' deleted.")
                return redirect(request.path)  # 🔁 Recharge la même page

        if os.path.exists(folder_path):
            for filename in sorted(os.listdir(folder_path)):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    entries.append(
                        {
                            "filename": filename,
                            "content": content,
                        }
                    )
                except Exception as e:
                    entries.append(
                        {
                            "filename": filename,
                            "content": f"Erreur: {e}",
                        }
                    )

        context = dict(
            self.admin_site.each_context(request),
            title=f"🗂 Contact Messages – {day}",
            log_date=day,
            entries=entries,
        )
        return TemplateResponse(request, "archpage/contact_message_files.html", context)

    # ✅ Permissions strictes
    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from .forms import PasswordResetRequestForm
from django.core.mail import send_mail
import random, string
from django.contrib.auth.models import User
