from django.contrib import admin
from .models import *
from easy_select2 import select2_modelform


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    fields = [
                ('uploader', 'date'),
                'image',
                'caption'
             ]
    list_display = ('image', 'uploader', 'date')
    list_filter = ['date']
    search_fields = ['uploader']
    select2 = select2_modelform(Photo, attrs={'width': '250px'})
    form = select2


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    fields = [
                'title',
                ('uploader', 'date'),
                'description',
                'photos',
            ]
    list_display = ('title', 'uploader', 'date')
    list_filter = ('date',)
    search_fields = ['uploader',]
    select2 = select2_modelform(Album, attrs={'width': '250px'})
    form = select2
