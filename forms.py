##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.forms import ModelForm, Textarea, ModelChoiceField
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext as _

import base.models.entity
from base.models import academic_year, entity, entity_version
from base.models.enums import entity_type
from assistant import models as mdl
from assistant.models.enums import review_advice_choices, assistant_type
from assistant.models.enums import assistant_mandate_renewal, reviewer_role, assistant_phd_inscription


class MandateFileForm(forms.Form):
    file = forms.FileField(error_messages={'required': _('no_file_submitted')})

    def clean_file(self):
        file = self.cleaned_data['file']
        content_type = file.content_type.split('/')[1]
        valid_content_type = 'vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type
        if ".xlsx" not in file.name or not valid_content_type:
            self.add_error('file', forms.ValidationError(_('file_must_be_xlsx'), code='invalid'))
        return file


class MandateForm(ModelForm):
    comment = forms.CharField(required=False, widget=Textarea(
        attrs={'rows': '4', 'cols': '80'}))
    absences = forms.CharField(required=False, widget=Textarea(
        attrs={'rows': '4', 'cols': '80'}))
    other_status = forms.CharField(max_length=50, required=False)
    renewal_type = forms.ChoiceField(
        choices=assistant_mandate_renewal.ASSISTANT_MANDATE_RENEWAL_TYPES)
    assistant_type = forms.ChoiceField(
        choices=assistant_type.ASSISTANT_TYPES)
    sap_id = forms.CharField(required=True, max_length=12, strip=True)
    contract_duration = forms.CharField(
        required=True, max_length=30, strip=True)
    contract_duration_fte = forms.CharField(
        required=True, max_length=30, strip=True)
    fulltime_equivalent = forms.NumberInput()

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('comment', 'absences', 'other_status', 'renewal_type', 'assistant_type', 'sap_id',
                  'contract_duration', 'contract_duration_fte', 'fulltime_equivalent')

    def __init__(self, *args, **kwargs):
        super(MandateForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class EntityChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "{0} ({1})".format(obj.acronym, obj.title)

    def __init__(self, *args, **kwargs):
        super(EntityChoiceField, self).__init__(*args, **kwargs)
        self.widget.attrs['class'] = 'form-control'


def get_field_qs(field, **kwargs):
    if field.name == 'entity':
        return EntityChoiceField(queryset=base.models.entity.find_versions_from_entites(
            entity.search(entity_type=entity_type.SECTOR) |
            entity.search(entity_type=entity_type.FACULTY) |
            entity.search(entity_type=entity_type.LOGISTICS_ENTITY) |
            entity.search(entity_type=entity_type.SCHOOL) |
            entity.search(entity_type=entity_type.INSTITUTE) |
            entity.search(entity_type=entity_type.POLE), None))
    return field.formfield(**kwargs)


entity_inline_formset = inlineformset_factory(mdl.assistant_mandate.AssistantMandate,
                                              mdl.mandate_entity.MandateEntity,
                                              formfield_callback=get_field_qs,
                                              fields=('entity', 'assistant_mandate'),
                                              extra=1, can_delete=True, min_num=1, max_num=5)


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


class MandatesArchivesForm(ModelForm):
    academic_year = forms.ModelChoiceField(queryset=academic_year.AcademicYear.objects.all())

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('academic_year',)


RADIO_SELECT_REQUIRED = dict(
    required=True,
    widget=forms.RadioSelect(attrs={'onChange': 'Hide()'})
)


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


class TutoringLearningUnitForm(ModelForm):
    sessions_number = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'input session_number',
                                                                         'style': 'width:6ch'}))
    sessions_duration = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'input session_duration',
                                                                           'style': 'width:6ch'}))
    series_number = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'input series_numbers',
                                                                       'style': 'width:6ch'}))
    face_to_face_duration = forms.IntegerField(widget=forms.NumberInput(attrs={'readonly': 'enabled',
                                                                               'style': 'width:6ch'}))
    attendees = forms.IntegerField(widget=forms.NumberInput(attrs={'min': '1', 'max': '999', 'step': '1',
                                                                   'style': 'width:6ch'}))
    exams_supervision_duration = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': '1', 'max': '999', 'step': '1', 'style': 'width:6ch'}))
    others_delivery = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))
    mandate_id = forms.CharField(widget=forms.HiddenInput(), required=True)
    tutoring_learning_unit_year_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = mdl.tutoring_learning_unit_year.TutoringLearningUnitYear
        fields = ('sessions_number', 'sessions_duration', 'series_number', 'face_to_face_duration',
                  'attendees', 'exams_supervision_duration', 'others_delivery')
        exclude = ['learning_unit_year', 'mandate']

    def __init__(self, *args, **kwargs):
        super(TutoringLearningUnitForm, self).__init__(*args, **kwargs)
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


class ReviewForm(ModelForm):
    justification = forms.CharField(help_text=_("justification_required_if_conditional_or_negative"),
                                    required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'}))
    remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'}))
    comment_vice_rector = forms.CharField(help_text=("information_only_for_DAS_CAS_and_VICE_RECTOR"),
                                          required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'}))
    confidential = forms.CharField(help_text=_("information_not_provided_to_assistant"),
                                   required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'}))
    advice = forms.ChoiceField(choices=review_advice_choices.REVIEW_ADVICE_CHOICES, **RADIO_SELECT_REQUIRED)

    class Meta:
        model = mdl.review.Review
        fields = ('mandate', 'advice', 'status', 'justification', 'remark', 'confidential', 'changed',
                  'comment_vice_rector')
        widgets = {'mandate': forms.HiddenInput(), 'reviewer': forms.HiddenInput, 'status': forms.HiddenInput,
                   'changed': forms.HiddenInput}

    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.fields['justification'].widget.attrs['class'] = 'form-control'
        self.fields['remark'].widget.attrs['class'] = 'form-control'
        self.fields['comment_vice_rector'].widget.attrs['class'] = 'form-control'
        self.fields['confidential'].widget.attrs['class'] = 'form-control'

    def clean(self):
        super(ReviewForm, self).clean()
        advice = self.cleaned_data.get("advice")
        justification = self.cleaned_data.get('justification')
        if advice != review_advice_choices.FAVORABLE and not justification:
            msg = _("justification_required_if_conditional_or_negative")
            self.add_error('justification', msg)


class AssistantFormPart6(ModelForm):
    activities_report_remark = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('tutoring_percent', 'service_activities_percent', 'formation_activities_percent',
                  'research_percent', 'activities_report_remark')

    def __init__(self, *args, **kwargs):
        super(AssistantFormPart6, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean(self):
        tutoring_percent = self.cleaned_data['tutoring_percent']
        service_activities_percent = self.cleaned_data['service_activities_percent']
        formation_activities_percent = self.cleaned_data['formation_activities_percent']
        research_percent = self.cleaned_data['research_percent']

        if tutoring_percent + service_activities_percent + formation_activities_percent + research_percent != 100:
            raise ValidationError(_('total_must_be_100_message'))
        else:
            return self.cleaned_data


class ReviewerDelegationForm(ModelForm):
    role = forms.CharField(widget=forms.HiddenInput(), required=True)
    entities = \
        entity.search(entity_type=entity_type.INSTITUTE) | entity.search(entity_type=entity_type.FACULTY) | \
        entity.search(entity_type=entity_type.SCHOOL) | entity.search(entity_type=entity_type.PLATFORM) | \
        entity.search(entity_type=entity_type.POLE)
    entity = EntityChoiceField(required=True, queryset=base.models.entity.find_versions_from_entites(entities, None))

    class Meta:
        model = mdl.reviewer.Reviewer
        fields = ('entity', 'role')
        exclude = ['person']
        widgets = {
            'entity': forms.HiddenInput()
        }


class ReviewerForm(ModelForm):
    role = forms.ChoiceField(required=True, choices=reviewer_role.ROLE_CHOICES)
    entities = \
        entity.search(entity_type=entity_type.INSTITUTE) | entity.search(entity_type=entity_type.FACULTY) | \
        entity.search(entity_type=entity_type.SECTOR) | entity.search(entity_type=entity_type.LOGISTICS_ENTITY)
    entity = EntityChoiceField(required=True, queryset=base.models.entity.find_versions_from_entites(entities, None))

    class Meta:
        model = mdl.reviewer.Reviewer
        fields = ('entity', 'role')
        exclude = ['person']

    def __init__(self, *args, **kwargs):
        super(ReviewerForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class ReviewerReplacementForm(ModelForm):
    person = forms.ChoiceField(required=False)
    id = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = mdl.reviewer.Reviewer
        fields = ('id',)
        exclude = ('person', 'entity', 'role')


class ReviewersFormset(ModelForm):
    role = forms.ChoiceField(required=False)
    entity = forms.CharField(required=False)
    entity_version = forms.CharField(required=False)
    person = forms.ChoiceField(required=False)
    id = forms.IntegerField(required=False)
    ACTIONS = (
        ('-----', _('-----')),
        ('DELETE', _('delete')),
        ('REPLACE', _('replace'))
    )
    action = forms.ChoiceField(required=False, choices=ACTIONS,
                               widget=forms.Select(attrs={'class': 'selector', 'onchange': 'this.form.submit();'}))

    class Meta:
        model = mdl.reviewer.Reviewer
        exclude = ('entity', 'role', 'person')


class SettingsForm(ModelForm):
    starting_date = forms.DateField(required=True)
    ending_date = forms.DateField(required=True)
    assistants_starting_date = forms.DateField(required=True)
    assistants_ending_date = forms.DateField(required=True)
    assistants_contract_end_starting_date = forms.DateField(required=True)
    assistants_contract_end_ending_date = forms.DateField(required=True)

    class Meta:
        model = mdl.settings.Settings
        fields = ('starting_date', 'ending_date', 'assistants_starting_date', 'assistants_ending_date',
                  'assistants_contract_end_starting_date', 'assistants_contract_end_ending_date')

    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
