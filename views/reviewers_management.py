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
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.urlresolvers import reverse
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

from base.models import academic_year, person, entity_version

from assistant.forms import MandatesArchivesForm, ReviewersFormset, ReviewerForm, ReviewerReplacementForm
from assistant.models import reviewer, review
from assistant.utils import manager_access


class ReviewersListView(LoginRequiredMixin, UserPassesTestMixin, ListView, FormMixin):
    context_object_name = 'reviewers_list'
    template_name = 'reviewers_list.html'
    form_class = MandatesArchivesForm

    def test_func(self):
        return manager_access.user_is_manager(self.request.user)

    def get_login_url(self):
        return reverse('assistants_home')

    def get_queryset(self):
        queryset = reviewer.find_reviewers()
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ReviewersListView, self).get_context_data(**kwargs)
        return context


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def reviewers_index(request):
    all_reviewers = reviewer.find_reviewers()
    initial_formset_content = [{'action': None,
                                'entity': rev.entity,
                                'entity_version': entity_version.get_last_version(rev.entity),
                                'role': rev.role,
                                'person': rev.person,
                                'id': rev.id,
                                } for rev in all_reviewers]
    reviewers_formset = formset_factory(ReviewersFormset, extra=0)(initial=initial_formset_content)
    for form in reviewers_formset:
        current_reviewer = reviewer.find_by_id(form['id'].value())
        if review.find_by_reviewer(current_reviewer).count() == 0:
            form.fields['action'].choices = (('-----', _('-----')), ('DELETE', _('delete')),
                                             ('REPLACE', _('replace')))
        else:
            form.fields['action'].choices = (('-----', _('-----')), ('REPLACE', _('replace')))
    return render(request, "reviewers_list.html", {'reviewers_formset': reviewers_formset
                                                   })


@require_http_methods(["POST"])
@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def reviewer_action(request):
    reviewers_formset = formset_factory(ReviewersFormset)(request.POST, request.FILES)
    if reviewers_formset.is_valid():
        for reviewer_form in reviewers_formset:
            action = reviewer_form.cleaned_data.get('action')
            if action == 'DELETE':
                reviewer_delete(request, reviewer_form.cleaned_data.get('id'))
            elif action == 'REPLACE':
                year = academic_year.current_academic_year().year
                reviewer_id = reviewer_form.cleaned_data.get('id')
                this_reviewer = reviewer.find_by_id(reviewer_id)
                entity = entity_version.get_last_version(this_reviewer.entity)
                form = ReviewerReplacementForm(initial={'person': this_reviewer.person,
                                                        'id': this_reviewer.id}, prefix="rev",
                                               instance=this_reviewer)
                return render(request, "manager_replace_reviewer.html", {'reviewer': this_reviewer,
                                                                         'entity': entity,
                                                                         'year': year,
                                                                         'form': form})
    return HttpResponseRedirect(reverse('reviewers_list'))


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def reviewer_delete(request, reviewer_id):
    reviewer_to_delete = reviewer.find_by_id(reviewer_id)
    reviewer_to_delete.delete()
    return HttpResponseRedirect(reverse('reviewers_list'))


@require_http_methods(["POST"])
@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def reviewer_replace(request):
    year = academic_year.current_academic_year().year
    form = ReviewerReplacementForm(data=request.POST, prefix='rev')
    reviewer_to_replace = reviewer.find_by_id(request.POST.get('reviewer_id'))
    entity = entity_version.get_last_version(reviewer_to_replace.entity)
    this_person = request.POST.get('person_id')
    if form.is_valid() and this_person:
        this_person = person.find_by_id(this_person)
        if reviewer.find_by_person(this_person):
            msg = _("person_already_reviewer_msg")
            form.add_error(None, msg)
        else:
            reviewer_to_replace.person = this_person
            reviewer_to_replace.save()
            return redirect('reviewers_list')
    else:
        msg = _("bad_person_msg")
        form.add_error(None, msg)
    return render(request, "manager_replace_reviewer.html", {'reviewer': reviewer_to_replace,
                                                             'entity': entity,
                                                             'year': year,
                                                             'form': form})


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def reviewer_add(request):
    year = academic_year.current_academic_year().year
    if request.POST:
        form = ReviewerForm(data=request.POST)
        this_person = request.POST.get('person_id')
        if form.is_valid() and this_person:
            this_person = person.find_by_id(this_person)
            new_reviewer = form.save(commit=False)
            if reviewer.find_by_person(this_person):
                msg = _("person_already_reviewer_msg")
                form.add_error(None, msg)
            if reviewer.find_by_entity_and_role(new_reviewer.entity, new_reviewer.role):
                msg = _("reviewer_with_same_role_already_exists_msg")
                form.add_error(None, msg)
            if not form.has_error(field=NON_FIELD_ERRORS):
                new_reviewer.person = this_person
                new_reviewer.save()
                return redirect('reviewers_list')
        else:
            msg = _("bad_person_msg")
            form.add_error(None, msg)
    else:
        form = ReviewerForm(initial={'year': year})
    return render(request, "manager_add_reviewer.html", {'form': form, 'year': year})
