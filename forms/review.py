from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext as _

from assistant import models as mdl
from assistant.forms.common import RADIO_SELECT_REQUIRED
from assistant.models.enums import review_advice_choices


class ReviewForm(ModelForm):
    justification = forms.CharField(
        help_text=_("A justification is required if the opinion is unfavourable or conditional"),
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'})
    )
    remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'}))
    comment_vice_rector = forms.CharField(
        help_text=_("This information is only transmitted to DAS/CAS and Vice-Rector"),
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'})
    )
    confidential = forms.CharField(help_text=_("This information will not be transmitted to the assistant"),
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
        if (advice == review_advice_choices.UNFAVOURABLE or advice == review_advice_choices.CONDITIONAL) \
                and not justification:
            msg = _("A justification is required if the opinion is unfavourable or conditional")
            self.add_error('justification', msg)
