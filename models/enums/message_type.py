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
from django.utils.translation import gettext_lazy as _

TO_ALL_ASSISTANTS = 'TO_ALL_ASSISTANTS'
TO_ALL_DEANS = 'TO_ALL_DEANS'
TO_PHD_SUPERVISOR = 'TO_PHD_SUPERVISOR'
TO_ONE_DEAN = 'TO_ONE_DEAN'
TO_ALL_REVIEWERS = 'TO_ALL_REVIEWERS'

TYPES = ((TO_ALL_ASSISTANTS, _('To the assistants')),
         (TO_ALL_DEANS, _('To the Deans of Faculty')),
         (TO_PHD_SUPERVISOR, _('To Ph.D. promoter')),
         (TO_ONE_DEAN, _('To one Dean')),
         (TO_ALL_REVIEWERS, _('To all reviewers')))
