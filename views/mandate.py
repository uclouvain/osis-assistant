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
import time

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _, pgettext
from openpyxl import Workbook

from assistant import models as assistant_mdl
from assistant.forms.mandate import MandateForm, entity_inline_formset, DocumentFileForm
from assistant.models import assistant_mandate, review, assistant_document_file
from assistant.models import reviewer, mandate_entity
from assistant.models.enums import reviewer_role, assistant_mandate_state, document_type
from assistant.views.mails import send_message
from base.models import academic_year, entity, person
from base.models.enums import entity_type
from osis_common.document.xls_build import save_virtual_workbook


def user_is_manager(user):
    try:
        if user.is_authenticated:
            return assistant_mdl.manager.Manager.objects.get(person=user.person)
    except ObjectDoesNotExist:
        return False


@user_passes_test(user_is_manager, login_url='assistants_home')
def mandate_edit(request, mandate_id=None):
    if mandate_id is None:
        mandate_id = request.POST.get("mandate_id")
    mandate = assistant_mdl.assistant_mandate.find_mandate_by_id(mandate_id)
    files = assistant_document_file.find_by_assistant_mandate_and_description(mandate, document_type.PHD_DOCUMENT)
    supervisor = mandate.assistant.supervisor
    form = MandateForm(initial={'comment': mandate.comment,
                                'renewal_type': mandate.renewal_type,
                                'absences': mandate.absences,
                                'other_status': mandate.other_status,
                                'contract_duration': mandate.contract_duration,
                                'contract_duration_fte': mandate.contract_duration_fte,
                                }, prefix="mand", instance=mandate)
    document_form = DocumentFileForm(initial={'update_by': request.user,
                                              'application_name': 'assistant',
                                              'description': document_type.PHD_DOCUMENT,
                                              'storage_duration': 0
                                              }, prefix='doc')
    formset = entity_inline_formset(instance=mandate, prefix="entity")

    return render(request, 'mandate_form.html', {
        'mandate': mandate,
        'form': form,
        'document_form': document_form,
        'formset': formset,
        'assistant_mandate_state': assistant_mandate_state,
        'supervisor': supervisor,
        'document_type': document_type.PHD_DOCUMENT,
        'files': files,
    })


@user_passes_test(user_is_manager, login_url='access_denied')
def mandate_save(request):
    mandate_id = request.POST.get("mandate_id")
    mandate = assistant_mdl.assistant_mandate.find_mandate_by_id(mandate_id)
    if request.POST.get('del_rev'):
        mandate.assistant.supervisor = None
        mandate.assistant.save()
    elif request.POST.get('person_id'):
        try:
            substitute_supervisor = person.find_by_id(request.POST.get('person_id'))
            if substitute_supervisor:
                mandate.assistant.supervisor = substitute_supervisor
                mandate.assistant.save()
                html_template_ref = 'assistant_phd_supervisor_html'
                txt_template_ref = 'assistant_phd_supervisor_txt'
                send_message(person=substitute_supervisor, html_template_ref=html_template_ref,
                             txt_template_ref=txt_template_ref, assistant=mandate.assistant)
        except ObjectDoesNotExist:
            pass
    form = MandateForm(data=request.POST, instance=mandate, prefix='mand')
    document_form = DocumentFileForm(request.POST, request.FILES, prefix='doc')
    formset = entity_inline_formset(request.POST, request.FILES, instance=mandate, prefix='entity')
    files = assistant_document_file.find_by_assistant_mandate_and_description(mandate, document_type.PHD_DOCUMENT)
    if form.is_valid():
        form.save()
        if formset.is_valid():
            formset.save()
            if 'doc-file' in request.FILES and document_form.is_valid():
                new_document = document_form.save()
                assistant_mandate_document_file = assistant_mdl.assistant_document_file.AssistantDocumentFile()
                assistant_mandate_document_file.assistant_mandate = mandate
                assistant_mandate_document_file.document_file = new_document
                assistant_mandate_document_file.save()
                return mandate_edit(request)
            else:
                return render(request, "mandate_form.html", {'mandate': mandate, 'form': form, 'formset': formset,
                                                             'document_form': document_form, 'files': files})
        else:
            return render(request, "mandate_form.html", {'mandate': mandate, 'form': form, 'formset': formset,
                                                         'document_form': document_form, 'files': files})
    else:
        return render(request, "mandate_form.html", {'mandate': mandate, 'form': form, 'formset': formset,
                                                     'document_form': document_form, 'files': files})


@user_passes_test(user_is_manager, login_url='access_denied')
def mandate_change_state(request):
    mandate = assistant_mandate.find_mandate_by_id(request.POST.get("mandate_id"))
    if mandate:
        if 'bt_mandate_decline' in request.POST:
            mandate.state = assistant_mandate_state.DECLINED
            faculty = mandate_entity.find_by_mandate_and_type(mandate, entity_type.FACULTY)
            if faculty:
                faculty_dean = reviewer.find_by_entity_and_role(
                    faculty.first().entity, reviewer_role.SUPERVISION).first()
                assistant = mandate.assistant
                html_template_ref = 'assistant_dean_assistant_decline_html'
                txt_template_ref = 'assistant_dean_assistant_decline_txt'
                send_message(person=faculty_dean.person, html_template_ref=html_template_ref,
                             txt_template_ref=txt_template_ref, assistant=assistant)
        mandate.save()
    return HttpResponseRedirect(reverse("mandate_read", args=[request.POST.get("mandate_id")]))


@user_passes_test(user_is_manager, login_url='access_denied')
def load_mandates(request):
    return render(request, "load_mandates.html", {})


@user_passes_test(user_is_manager, login_url='access_denied')
def export_mandates(request):
    xls = generate_xls()
    filename = '{}_{}.xlsx'.format(_('assistants_mandates'), time.strftime("%Y%m%d_%H%M"))
    response = HttpResponse(xls, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = "%s%s" % ("attachment; filename=", filename)
    return response


def generate_xls():
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = _('Mandates')
    worksheet.append([
        _("Sector"),
        _("Faculty"),
        _("Logistics entity"),
        _("Institution"),
        _("Registration number"),
        _("Name"),
        _("Firstname"),
        _("Email"),
        "FGS",
        _("Age"),
        pgettext("assistant", "Status"),
        _("Renewal type"),
        _("Assistant type"),
        _("Full-time equivalent"),
        _("Full-time equivalent"),
        _("Contract length"),
        _("Contract start date"),
        _("End date"),
        _("Comment"),
        _("Absences"),
        _("Opinion of the sector vice-rector"),
        _("Justification"),
        _("Comment"),
        _("Confidential"),
    ])
    mandates = assistant_mandate.find_by_academic_year(academic_year.starting_academic_year())
    for mandate in mandates:
        line = construct_line(mandate)
        worksheet.append(line)
    return save_virtual_workbook(workbook)


def construct_line(mandate):
    line = get_entities_for_mandate(mandate)
    line += [
        mandate.sap_id,
        str(mandate.assistant.person.last_name),
        str(mandate.assistant.person.first_name),
        str(mandate.assistant.person.email),
        str(mandate.assistant.person.global_id),
        person.calculate_age(mandate.assistant.person),
    ]
    line += [
        mandate.get_state_display(),
    ]
    line += [
        mandate.get_renewal_type_display(),
        mandate.get_assistant_type_display(),
        mandate.fulltime_equivalent,
        mandate.contract_duration_fte,
        mandate.contract_duration,
        mandate.entry_date,
        mandate.end_date,
        mandate.comment,
        mandate.absences if mandate.absences != 'None' else '',
    ]
    line += get_reviews(mandate)
    return line


def get_entities_for_mandate(mandate):
    ent_type = {entity_type.SECTOR, entity_type.FACULTY, entity_type.LOGISTICS_ENTITY, entity_type.INSTITUTE}
    entities_id = mandate.mandateentity_set.all().order_by('id').values_list('entity', flat=True)
    entities = (
        ent for ent in entity.find_versions_from_entites(entities_id, mandate.academic_year.start_date)
        if ent.entity_type in ent_type
    )
    mandate_entities = [''] * 4
    for ent in entities:
        if ent.entity_type == entity_type.SECTOR:
            mandate_entities[0] = ent.acronym
        elif ent.entity_type == entity_type.FACULTY:
            mandate_entities[1] = ent.acronym
        elif ent.entity_type == entity_type.LOGISTICS_ENTITY:
            mandate_entities[2] = ent.acronym
        else:
            mandate_entities[3] = ent.acronym
    return mandate_entities


def get_reviews(mandate):
    reviews_details = []
    vrs_review = review.find_review_for_mandate_by_role(mandate.id, reviewer_role.VICE_RECTOR)
    if vrs_review:
        reviews_details += [_(vrs_review.advice)] if vrs_review.advice is not None else ['']
        reviews_details += [vrs_review.justification] if vrs_review.justification is not None else ['']
        reviews_details += [vrs_review.remark] if vrs_review.remark is not None else ['']
        reviews_details += [vrs_review.confidential] if vrs_review.confidential is not None else ['']
    return reviews_details
