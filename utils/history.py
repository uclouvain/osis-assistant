#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from django.utils import translation
from django.utils.translation import gettext_lazy as _
from osis_history.utilities import add_history_entry

from assistant.models.assistant_mandate import AssistantMandate
from assistant.models.review import Review
from base.models.person import Person

TAGS = ["review"]


def add_review_history_entry(review: Review, person: Person) -> None:
    uuid_generated = _generate_history_uuid(review.mandate)
    with translation.override('fr-be'):
        message_fr = str(_generate_text(review))
    with translation.override('en'):
        message_en = str(_generate_text(review))

    add_history_entry(
        uuid_generated,
        message_fr,
        message_en,
        author=str(person),
        tags=TAGS,
        extra_data={'mandate_uuid': review.mandate.uuid}
    )


def _generate_text(review: Review) -> str:
    return _("(%(state)s) Remark has been updated: %(remark)s") % {
        "state": review.mandate.get_state_display(),
        "remark": review.remark if review.remark else ""
    }


def _generate_history_uuid(mandate: AssistantMandate) -> str:
    return mandate.uuid
