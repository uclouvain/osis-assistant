############################################################################
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
############################################################################
from django import template
from django.utils.translation import gettext_lazy as _

from assistant.models.enums import reviewer_role, review_advice_choices

register = template.Library()


@register.inclusion_tag("assistant/inclusion_tags/review_status.html", takes_context=False)
def display_status(review, supervisor):
    return {
        "review": review,
        "css_class": get_css_class(review),
        "color_code": get_color_code(review),
        "title": get_title(review, supervisor)
    }


def get_css_class(review):
    css_class = "fas fa-battery-quarter"
    if not review.reviewer:
        return css_class

    if reviewer_role.RESEARCH in review.reviewer.role:
        css_class = "fas fa-battery-half"
    elif reviewer_role.SUPERVISION in review.reviewer.role:
        css_class = "fas fa-battery-three-quarters"
    elif reviewer_role.VICE_RECTOR in review.reviewer.role:
        css_class = "fas fa-battery-full"
    return css_class


def get_color_code(review):
    color_code = "#EFC345"
    if review_advice_choices.FAVORABLE in review.advice:
        color_code = "#79C84F"
    elif review_advice_choices.UNFAVOURABLE in review.advice:
        color_code = "#E06D5A"
    return color_code


def get_title(review, supervisor):
    title_format = "{role} : {person}"
    if review.reviewer:
        return title_format.format(role=review.reviewer.get_role_display(), person=str(review.reviewer.person))
    return title_format.format(role=_("Thesis promoter"), person=str(supervisor))
