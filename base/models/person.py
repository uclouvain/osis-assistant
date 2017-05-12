##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin
from base.models.enums import person_source_type


class PersonAdmin(SerializableModelAdmin):
    list_display = ('first_name', 'middle_name', 'last_name', 'username', 'email', 'gender', 'global_id',
                    'national_id', 'changed', 'source', 'employee')
    search_fields = ['first_name', 'middle_name', 'last_name', 'user__username', 'email', 'global_id']
    fieldsets = ((None, {'fields': ('user', 'global_id', 'national_id', 'gender', 'first_name',
                                    'middle_name', 'last_name', 'birth_date', 'email', 'phone',
                                    'phone_mobile', 'language','employee')}),)
    raw_id_fields = ('user',)
    list_filter = ('gender', 'language')


class Person(SerializableModel):
    GENDER_CHOICES = (
        ('F', _('female')),
        ('M', _('male')),
        ('U', _('unknown')))

    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    global_id = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    gender = models.CharField(max_length=1, blank=True, null=True, choices=GENDER_CHOICES, default='U')
    national_id = models.CharField(max_length=25, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    phone_mobile = models.CharField(max_length=30, blank=True, null=True)
    language = models.CharField(max_length=30, null=True, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    birth_date = models.DateField(blank=True, null=True)
    source = models.CharField(max_length=25, blank=True, null=True, choices=person_source_type.CHOICES,
                              default=person_source_type.BASE)
    employee = models.BooleanField(default=False)

    def save(self, **kwargs):
        # When person is created by another application this rule can be applied.
        if hasattr(settings, 'INTERNAL_EMAIL_SUFFIX'):
            if settings.INTERNAL_EMAIL_SUFFIX.strip():
                # It limits the creation of person with external emails. The domain name is case insensitive.
                if self.source and self.source != person_source_type.BASE \
                               and settings.INTERNAL_EMAIL_SUFFIX in str(self.email).lower():
                    raise AttributeError('Invalid email for external person.')

        super(Person, self).save()

    def username(self):
        if self.user is None:
            return None
        return self.user.username

    def __str__(self):
        first_name = ""
        middle_name = ""
        last_name = ""
        if self.first_name:
            first_name = self.first_name
        if self.middle_name:
            middle_name = self.middle_name
        if self.last_name:
            last_name = self.last_name + ","

        return u"%s %s %s" % (last_name.upper(), first_name, middle_name)

    class Meta:
        permissions = (
            ("is_administrator", "Is administrator"),
            ("is_institution_administrator", "Is institution administrator "),
        )


def find_by_id(person_id):
    return Person.objects.get(id=person_id)


def find_by_user(user):
    person = Person.objects.filter(user=user).first()
    return person


def change_language(user, new_language):
    if new_language:
        person = Person.objects.get(user=user)
        person.language = new_language
        person.save()


def find_by_global_id(global_id):
    return Person.objects.filter(global_id=global_id).first() if global_id else None


def find_by_last_name_or_email(query):
    return Person.objects.filter(Q(email__icontains=query) | Q(last_name__icontains=query))


def search_by_email(email):
    return Person.objects.filter(email=email)


def count_by_email(email):
    return search_by_email(email).count()


def search(a_lastname, a_firstname, is_employee):

    out = None
    queryset = Person.objects

    queryset = lastname_parameter(a_lastname, queryset)

    queryset = firstname_parameter(a_firstname, queryset)

    queryset = employee_parameter(is_employee, queryset)

    if a_lastname or a_firstname or a_status or is_employee:
        out = queryset.order_by('last_name')

    return out


def employee_parameter(is_employee, queryset):
    if is_employee:
        queryset = queryset.filter(employee=is_employee)
    return queryset


def firstname_parameter(a_first_name, queryset):
    if a_first_name:
        queryset = queryset.filter(first_name__icontains=a_first_name)
    return queryset


def lastname_parameter(a_lastname_part, queryset):
    if a_lastname_part:
        queryset = queryset.filter(last_name__icontains=a_lastname_part)
    return queryset

