from django.contrib import admin
from .models import User, Post

# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ('username',)
admin.site.register(User, UserAdmin)


class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp',)
    filter_horizontal = ('liked_by', )
admin.site.register(Post, PostAdmin)