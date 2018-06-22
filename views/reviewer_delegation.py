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
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView

from base.models import academic_year, person, entity, entity_version

from assistant.business.users_access import user_is_reviewer_and_procedure_is_open
from assistant.forms import ReviewerDelegationForm
from assistant.models.academic_assistant import is_supervisor
from assistant.models import reviewer
from assistant.utils.send_email import send_message



class StructuresListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    context_object_name = 'reviewer_structures_list'
    template_name = 'reviewer_structures_list.html'
    form_class = ReviewerDelegationForm

    def test_func(self):
        return user_is_reviewer_and_procedure_is_open(self.request.user)

    def get_login_url(self):
        return reverse('access_denied')

    def get_queryset(self):
        rev = reviewer.find_by_person(self.request.user.person)
        entities_version = entity_version.get_last_version(rev.entity).children
        entities = [this_entity_version.entity for this_entity_version in entities_version]
        entities.insert(0, entity_version.get_last_version(rev.entity).entity)
        queryset = [{
            'id': entity.id,
            'title': entity_version.get_last_version(entity, None).title,
            'acronym': entity.most_recent_acronym,
            'has_already_delegate': reviewer.get_delegate_for_entity(rev, entity)
        } for entity in entities]
        return queryset

    def get_context_data(self, **kwargs):
        context = super(StructuresListView, self).get_context_data(**kwargs)
        context['year'] = academic_year.current_academic_year().year
        context['current_reviewer'] = reviewer.find_by_person(self.request.user.person)
        entity = entity_version.get_last_version(context['current_reviewer'].entity)
        context['entity'] = entity
        context['is_supervisor'] = is_supervisor(self.request.user.person)
        return context


@require_http_methods(["POST"])
@user_passes_test(user_is_reviewer_and_procedure_is_open, login_url='assistants_home')
def add_reviewer_for_structure(request):
    current_entity = entity.find_by_id(request.POST.get("entity"))
    year = academic_year.current_academic_year().year
    if not reviewer.can_delegate_to_entity(reviewer.find_by_person(request.user.person), current_entity):
        return redirect('assistants_home')
    form = ReviewerDelegationForm(data=request.POST)
    if form.is_valid() and request.POST.get('person_id'):
        new_reviewer = form.save(commit=False)
        this_person = person.find_by_id(request.POST.get('person_id'))
        if reviewer.find_by_person(this_person):
            msg = _("person_already_reviewer_msg")
            form.add_error(None, msg)
            return render(request, "reviewer_add_reviewer.html", {
                'form': form,
                'year': year,
                'entity': current_entity,
                'reviewer': reviewer.find_by_person(request.user.person)
            })
        new_reviewer.person = this_person
        new_reviewer.save()
        html_template_ref = 'assistant_reviewers_startup_html'
        txt_template_ref = 'assistant_reviewers_startup_txt'
        send_message(person=this_person, html_template_ref=html_template_ref,
                     txt_template_ref=txt_template_ref)
        return redirect('reviewer_delegation')
    else:
        this_reviewer = reviewer.find_by_person(person=request.user.person)
        role = this_reviewer.role + '_ASSISTANT'
        form = ReviewerDelegationForm(initial={'entity': current_entity, 'year': year, 'role': role})
        return render(request, "reviewer_add_reviewer.html", {
            'form': form,
            'year': year,
            'entity': current_entity,
            'reviewer': reviewer.find_by_person(request.user.person)
        })
