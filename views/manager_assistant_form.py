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

from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from assistant.models import assistant_document_file
from assistant.models import assistant_mandate
from assistant.models import tutoring_learning_unit_year
from assistant.models.enums import assistant_mandate_renewal
from assistant.models.enums import assistant_type
from assistant.models.enums import document_type
from assistant.utils import manager_access


@require_http_methods(["GET"])
@user_passes_test(manager_access.user_is_manager, login_url='access_denied')
def assistant_form_view(request, mandate_id):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    learning_units = tutoring_learning_unit_year.find_by_mandate(mandate)
    phd_files = assistant_document_file.find_by_assistant_mandate_and_description(mandate,
                                                                                  document_type.PHD_DOCUMENT)
    research_files = assistant_document_file.find_by_assistant_mandate_and_description(mandate,
                                                                                       document_type.RESEARCH_DOCUMENT)
    tutoring_files = assistant_document_file.find_by_assistant_mandate_and_description(mandate,
                                                                                       document_type.TUTORING_DOCUMENT)
    return render(
        request, 'manager_assistant_form_view.html',
        {
            'mandate_id': mandate_id,
            'assistant': mandate.assistant,
            'mandate': mandate,
            'learning_units': learning_units,
            'phd_files': phd_files,
            'assistant_mandate_renewal': assistant_mandate_renewal,
            'research_files': research_files,
            'tutoring_files': tutoring_files,
            'year': mandate.academic_year.year + 1,
            'assistant_type': assistant_type
        }
    )
