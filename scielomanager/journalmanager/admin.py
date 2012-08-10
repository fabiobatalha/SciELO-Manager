# -*- coding: utf-8 -*-
from django.contrib import admin
from scielomanager.journalmanager.models import *
from django.contrib.auth.admin import UserAdmin

import reversion


class JournalMissionInline(admin.StackedInline):
    model = JournalMission


class SectionTitleInline(admin.StackedInline):
    model = SectionTitle


class JournalStudyAreaInline(admin.StackedInline):
    model = JournalStudyArea


class CollectionAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return Collection.nocacheobjects

    list_display = ('name',)
    search_fields = ('name',)


class SectionAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return Section.nocacheobjects


class JournalAdmin(reversion.VersionAdmin):

    def queryset(self, request):
        return Journal.nocacheobjects

    list_display = ('title',)
    search_fields = ('title',)
    filter_horizontal = ('collections', 'languages')
    inlines = [JournalMissionInline,
        JournalStudyAreaInline]


class InstitutionAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return Institution.nocacheobjects

    list_display = ('name',)
    search_fields = ('name',)


class UserCollectionsInline(admin.TabularInline):

    def queryset(self, request):
        return UserCollections.nocacheobjects

    model = UserCollections
    extra = 1
    can_delete = True


class UserProfileInline(admin.StackedInline):

    def queryset(self, request):
        return UserProfile.nocacheobjects

    model = UserProfile
    max_num = 1
    can_delete = True


class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, UserCollectionsInline)


class IssueAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return Issue.nocacheobjects

    list_display = ('journal', 'volume', 'number', 'is_trashed', 'is_marked_up')


class SponsorAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return Sponsor.nocacheobjects

    filter_horizontal = ('collections',)


class PublisherAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return Publisher.nocacheobjects

    filter_horizontal = ('collections',)


class UseLicenseAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return UseLicense.nocacheobjects


class LanguageAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return Language.nocacheobjects


class TranslatedDataAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return TranslatedData.nocacheobjects


class SupplementAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return Supplement.nocacheobjects


class JournalPublicationEventsAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return JournalPublicationEvents.nocacheobjects

    list_display = ['journal', 'status', 'created_at']
    list_filter = ('status',)
    search_fields = ('journal',)

admin.site.register(Collection, CollectionAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Journal, JournalAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(Sponsor, SponsorAdmin)
admin.site.register(Publisher, PublisherAdmin)
admin.site.register(UseLicense, UseLicenseAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(TranslatedData)
admin.site.register(Supplement, SupplementAdmin)
admin.site.register(JournalPublicationEvents, JournalPublicationEventsAdmin)
