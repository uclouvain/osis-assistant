##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext as _

from assistant import models as mdl
from assistant.forms.common import RADIO_SELECT_REQUIRED
from assistant.models.enums import assistant_phd_inscription


class AssistantFormPart1(ModelForm):
    external_functions = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '60', 'rows': '4'}))
    external_contract = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '60', 'rows': '4'}))
    justification = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '60', 'rows': '4'}))

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('external_functions', 'external_contract', 'justification')

    def __init__(self, *args, **kwargs):
        super(AssistantFormPart1, self).__init__(*args, **kwargs)
        self.fields['external_functions'].widget.attrs['class'] = 'form-control'
        self.fields['external_contract'].widget.attrs['class'] = 'form-control'
        self.fields['justification'].widget.attrs['class'] = 'form-control'


class AssistantFormPart3(ModelForm):
    PARAMETERS = dict(required=False, widget=forms.DateInput(format='%d/%m/%Y', attrs={'placeholder': 'dd/mm/yyyy'}),
                      input_formats=['%d/%m/%Y'])
    inscription = forms.ChoiceField(choices=assistant_phd_inscription.PHD_INSCRIPTION_CHOICES, **RADIO_SELECT_REQUIRED)
    expected_phd_date = forms.DateField(**PARAMETERS)
    thesis_date = forms.DateField(**PARAMETERS)
    phd_inscription_date = forms.DateField(**PARAMETERS)
    confirmation_test_date = forms.DateField(**PARAMETERS)
    thesis_title = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    remark = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))

    class Meta:
        model = mdl.academic_assistant.AcademicAssistant
        fields = ('thesis_title', 'confirmation_test_date', 'remark', 'inscription',
                  'expected_phd_date', 'phd_inscription_date', 'confirmation_test_date', 'thesis_date'
                  )
        exclude = ['supervisor']

    def __init__(self, *args, **kwargs):
        super(AssistantFormPart3, self).__init__(*args, **kwargs)
        self.fields['expected_phd_date'].widget.attrs['class'] = 'form-control'
        self.fields['phd_inscription_date'].widget.attrs['class'] = 'form-control'
        self.fields['thesis_date'].widget.attrs['class'] = 'form-control'
        self.fields['confirmation_test_date'].widget.attrs['class'] = 'form-control'
        self.fields['thesis_title'].widget.attrs['class'] = 'form-control'
        self.fields['remark'].widget.attrs['class'] = 'form-control'


class AssistantFormPart4(ModelForm):
    internships = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    conferences = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    publications = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    awards = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    framing = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    remark = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('internships', 'conferences', 'publications',
                  'awards', 'framing', 'remark')

    def __init__(self, *args, **kwargs):
        super(AssistantFormPart4, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class AssistantFormPart5(ModelForm):
    formations = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('faculty_representation', 'institute_representation', 'sector_representation',
                  'governing_body_representation', 'corsci_representation', 'students_service',
                  'infrastructure_mgmt_service', 'events_organisation_service', 'publishing_field_service',
                  'scientific_jury_service', 'formations')

    def __init__(self, *args, **kwargs):
        super(AssistantFormPart5, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class AssistantFormPart6(ModelForm):
    activities_report_remark = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))
    tutoring_percent = forms.IntegerField(required=True)
    service_activities_percent = forms.IntegerField(required=True)
    formation_activities_percent = forms.IntegerField(required=True)
    research_percent = forms.IntegerField(required=True)
    honour_declaration = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'style': 'width:15px;height:15px;'}),
    )

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('tutoring_percent', 'service_activities_percent', 'formation_activities_percent',
                  'research_percent', 'activities_report_remark')

    def __init__(self, *args, **kwargs):
        super(AssistantFormPart6, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean(self):
        tutoring_percent = self.cleaned_data.get('tutoring_percent', 0)
        service_activities_percent = self.cleaned_data.get('service_activities_percent', 0)
        formation_activities_percent = self.cleaned_data.get('formation_activities_percent', 0)
        research_percent = self.cleaned_data.get('research_percent', 0)

        if tutoring_percent + service_activities_percent + formation_activities_percent + research_percent != 100:
            raise ValidationError(_('The total must be equal to 100'))
        else:
            return self.cleaned_data
