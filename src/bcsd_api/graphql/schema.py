import logging
from typing import List

import strawberry
from graphql import GraphQLError
from strawberry.types import ExecutionContext

from bcsd_api.apply import resolvers as apply_resolvers
from bcsd_api.apply.types import ApplicationType, PagedApplications
from bcsd_api.exception.base import AppException
from bcsd_api.form import resolvers as form_resolvers
from bcsd_api.form.types import FormType
from bcsd_api.member import resolvers as member_resolvers
from bcsd_api.recruit import resolvers as recruit_resolvers
from bcsd_api.recruit.types import PeriodType
from bcsd_api.setting import resolvers as setting_resolvers
from bcsd_api.member.types import (
    FiltersType,
    MeType,
    MemberDetailType,
    MemberFilterInput,
    PagedMembers,
)
from bcsd_api.shorten import resolvers as link_resolvers
from bcsd_api.shorten.types import (
    CreateLinkInput,
    LinkDetailType,
    LinkFilterInput,
    LinkFiltersType,
    LinkType,
    PagedLinks,
    UpdateLinkInput,
)

from .errors import AppErrorExtension


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> str:
        return "ok"

    members: PagedMembers = strawberry.field(resolver=member_resolvers.resolve_members)
    member: MemberDetailType = strawberry.field(resolver=member_resolvers.resolve_member)
    member_filters: FiltersType = strawberry.field(resolver=member_resolvers.resolve_filters)
    tracks: list[str] = strawberry.field(resolver=member_resolvers.resolve_tracks)
    me: MeType = strawberry.field(resolver=member_resolvers.resolve_me)

    links: PagedLinks = strawberry.field(resolver=link_resolvers.resolve_links)
    link: LinkDetailType = strawberry.field(resolver=link_resolvers.resolve_link)
    link_filters: LinkFiltersType = strawberry.field(resolver=link_resolvers.resolve_link_filters)

    setting: str | None = strawberry.field(resolver=setting_resolvers.resolve_setting)

    periods: list[PeriodType] = strawberry.field(resolver=recruit_resolvers.resolve_periods)
    period: PeriodType = strawberry.field(resolver=recruit_resolvers.resolve_period)
    active_period: PeriodType | None = strawberry.field(resolver=recruit_resolvers.resolve_active_period)

    form: FormType = strawberry.field(resolver=form_resolvers.resolve_form)
    forms: list[FormType] = strawberry.field(resolver=form_resolvers.resolve_forms)

    applications: PagedApplications = strawberry.field(resolver=apply_resolvers.resolve_applications)
    application: ApplicationType = strawberry.field(resolver=apply_resolvers.resolve_application)
    my_applications: list[ApplicationType] = strawberry.field(resolver=apply_resolvers.resolve_my_applications)


@strawberry.type
class Mutation:
    create_link: LinkType = strawberry.mutation(resolver=link_resolvers.resolve_create)
    update_link: LinkType = strawberry.mutation(resolver=link_resolvers.resolve_update)
    toggle_link: LinkType = strawberry.mutation(resolver=link_resolvers.resolve_toggle)
    delete_link: bool = strawberry.mutation(resolver=link_resolvers.resolve_delete)

    set_setting: bool = strawberry.mutation(resolver=setting_resolvers.resolve_set_setting)

    create_period: PeriodType = strawberry.mutation(resolver=recruit_resolvers.resolve_create_period)
    update_period: PeriodType = strawberry.mutation(resolver=recruit_resolvers.resolve_update_period)

    create_form: FormType = strawberry.mutation(resolver=form_resolvers.resolve_create_form)
    update_form: FormType = strawberry.mutation(resolver=form_resolvers.resolve_update_form)

    submit_application: ApplicationType = strawberry.mutation(resolver=apply_resolvers.resolve_submit)
    confirm_payment: ApplicationType = strawberry.mutation(resolver=apply_resolvers.resolve_confirm_payment)
    approve_applications: list[ApplicationType] = strawberry.mutation(resolver=apply_resolvers.resolve_approve)
    cancel_application: bool = strawberry.mutation(resolver=apply_resolvers.resolve_cancel)


logger = logging.getLogger("strawberry.execution")


class _Schema(strawberry.Schema):
    def process_errors(self, errors: List[GraphQLError], execution_context: ExecutionContext | None = None) -> None:
        for err in errors:
            if not err.original_error:
                continue
            if isinstance(err.original_error, AppException):
                continue
            logger.error(err.message, exc_info=err.original_error)


schema = _Schema(
    query=Query,
    mutation=Mutation,
    extensions=[AppErrorExtension],
)
