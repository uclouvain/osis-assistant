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
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Prefetch
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView

from assistant.business.users_access import user_is_reviewer_and_procedure_is_open
from assistant.forms.reviewer import ReviewerDelegationForm
from assistant.models import reviewer
from assistant.models.academic_assistant import is_supervisor
from assistant.views.mails import send_message
from base.models import academic_year, person, entity, entity_version


class StructuresListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    context_object_name = 'reviewer_structures_list'
    template_name = 'reviewer_structures_list.html'
    form_class = ReviewerDelegationForm

    def test_func(self):
        return user_is_reviewer_and_procedure_is_open(self.request.user)

    def get_login_url(self):
        return reverse('access_denied')

    @cached_property
    def reviewers(self):
        return reviewer.find_by_person(self.request.user.person)

    def get_queryset(self):
        delegate_roles = [rev.role + '_ASSISTANT' for rev in self.reviewers]
        entities = [rev.entity for rev in self.reviewers]
        return entity_version.EntityVersion.objects.current(
            academic_year.starting_academic_year().start_date
        ).filter(
            Q(entity__in=entities) | Q(parent__in=entities)
        ).prefetch_related(
            Prefetch(
                "entity__reviewer_set",
                queryset=reviewer.Reviewer.objects.filter(role__in=delegate_roles),
                to_attr="delegated_reviewer"
            )
        )

    def get_context_data(self, **kwargs):
        context = super(StructuresListView, self).get_context_data(**kwargs)
        context['year'] = academic_year.starting_academic_year().year
        context['current_reviewer'] = self.reviewers[0]
        context['entity'] = entity_version.get_last_version(context['current_reviewer'].entity)
        context['is_supervisor'] = is_supervisor(self.request.user.person)
        return context


@require_http_methods(["POST"])
@user_passes_test(user_is_reviewer_and_procedure_is_open, login_url='assistants_home')
def add_reviewer_for_structure(request):
    current_entity = entity.find_by_id(request.POST.get("entity"))
    year = academic_year.starting_academic_year().year
    current_reviewer = reviewer_eligible_to_delegate(
        reviewer.find_by_person(request.user.person),
        current_entity
    )
    if not current_reviewer:
        return redirect('assistants_home')

    form = ReviewerDelegationForm(data=request.POST)
    if form.is_valid() and request.POST.get('person_id'):
        new_reviewer = form.save(commit=False)
        new_reviewer.person = person.find_by_id(request.POST.get('person_id'))
        new_reviewer.save()
        send_message(
            person=new_reviewer.person,
            html_template_ref='assistant_reviewers_startup_html',
            txt_template_ref='assistant_reviewers_startup_txt'
        )
        return redirect('reviewer_delegation')

    role = current_reviewer.role + '_ASSISTANT'
    form = ReviewerDelegationForm(initial={'entity': current_entity, 'year': year, 'role': role})
    return render(request, "reviewer_add_reviewer.html", {
        'form': form,
        'year': year,
        'entity': current_entity,
        'reviewer': current_reviewer
    })


def reviewer_eligible_to_delegate(reviewers, entity_to_delegate):
    for rev in reviewers:
        if reviewer.can_delegate_to_entity(rev, entity_to_delegate):
            return rev
    return None
