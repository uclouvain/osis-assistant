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
import json
from django.db import DataError
from django.contrib.auth.decorators import login_required
from django.http import *
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods

from osis_common.models import document_file as document_file
from assistant import models as mdl


@login_required
def download(request, document_file_id):
    assistant_mandate_document = mdl.assistant_document_file.find_by_id(document_file_id)
    document = document_file.find_by_id(assistant_mandate_document.document_file.id)
    filename = document.file_name
    response = HttpResponse(document.file, content_type=document.content_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


@login_required
def delete(request, document_file_id, url):
    assistant_mandate_document = mdl.assistant_document_file.find_by_id(document_file_id)
    document = document_file.find_by_id(assistant_mandate_document.document_file.id)
    assistant_mandate_document.delete()
    document.delete()
    return HttpResponseRedirect(reverse(url))


@login_required
@require_http_methods(["POST"])
def save_uploaded_file(request):
    data = request.POST
    try:
        assistant_mandate = mdl.assistant_mandate.find_mandate_by_id(request.POST['mandate_id'])
    except:
        return HttpResponse(
            json.dumps({"error": True, "message": _('object_not_saved')}),
            content_type="application/json")
    file_selected = request.FILES['file']
    file = file_selected
    file_name = file_selected.name
    if len(file_name) > 100:
        return HttpResponse(
            json.dumps({"error":True, "message": _('maxlength_filename')}),
            content_type="application/json")
    content_type = file_selected.content_type
    if content_type != "application/pdf":
        return HttpResponse(
            json.dumps({"error": True, "message": _('only_pdf_file')}),
            content_type="application/json")
    description = data['description']
    storage_duration = 0
    new_document = document_file.DocumentFile(file_name=file_name,
                                              file=file,
                                              description=description,
                                              storage_duration=storage_duration,
                                              application_name='assistant',
                                              content_type=content_type,
                                              update_by=request.user)
    try:
        new_document.save()
        assistant_mandate_document_file = mdl.assistant_document_file.AssistantDocumentFile()
        assistant_mandate_document_file.assistant_mandate = assistant_mandate
        assistant_mandate_document_file.document_file = new_document
        assistant_mandate_document_file.save()
        return HttpResponse(
            json.dumps({"success": True, "message": file_selected.name + ' ' + _('file_uploaded')}),
            content_type="application/json")
    except DataError:
        return HttpResponse(
            json.dumps({"error": True, "message": _('object_not_saved')}),
            content_type="application/json")


