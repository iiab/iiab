import itertools
from enum import Enum

from rest_framework import generics, status
from rest_framework.pagination import CursorPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from smartmin.views import SmartTemplateView

from django.conf import settings
from django.db.models import OuterRef, Prefetch, Q
from django.utils.translation import gettext_lazy as _

from temba.archives.models import Archive
from temba.campaigns.models import Campaign, CampaignEvent
from temba.channels.models import Channel, ChannelEvent
from temba.classifiers.models import Classifier
from temba.contacts.models import Contact, ContactField, ContactGroup, ContactNote, ContactURN
from temba.flows.models import Flow, FlowRun, FlowStart, FlowStartCount
from temba.globals.models import Global
from temba.locations.models import AdminBoundary, BoundaryAlias
from temba.msgs.models import Broadcast, BroadcastMsgCount, Label, LabelCount, Media, Msg, MsgFolder, OptIn
from temba.orgs.models import OrgMembership
from temba.orgs.views.mixins import OrgPermsMixin
from temba.tickets.models import Ticket, Topic
from temba.users.models import User
from temba.utils import str_to_bool
from temba.utils.db.queries import SubqueryCount, or_list
from temba.utils.uuid import is_uuid

from ..models import APIPermission, Resthook, ResthookSubscriber, SSLPermission, WebHookEvent
from ..support import (
    APIBasicAuthentication,
    APISessionAuthentication,
    APITokenAuthentication,
    CreatedOnCursorPagination,
    DateJoinedCursorPagination,
    DocumentationRenderer,
    InvalidQueryError,
    ModifiedOnCursorPagination,
    OrgUserRateThrottle,
    SentOnCursorPagination,
)
from ..views import BaseAPIView, BulkWriteAPIMixin, DeleteAPIMixin, ListAPIMixin, WriteAPIMixin
from .serializers import (
    AdminBoundaryReadSerializer,
    ArchiveReadSerializer,
    BroadcastReadSerializer,
    BroadcastWriteSerializer,
    CampaignEventReadSerializer,
    CampaignEventWriteSerializer,
    CampaignReadSerializer,
    CampaignWriteSerializer,
    ChannelEventReadSerializer,
    ChannelReadSerializer,
    ClassifierReadSerializer,
    ContactBulkActionSerializer,
    ContactFieldReadSerializer,
    ContactFieldWriteSerializer,
    ContactGroupReadSerializer,
    ContactGroupWriteSerializer,
    ContactReadSerializer,
    ContactWriteSerializer,
    FlowReadSerializer,
    FlowRunReadSerializer,
    FlowStartReadSerializer,
    FlowStartWriteSerializer,
    GlobalReadSerializer,
    GlobalWriteSerializer,
    LabelReadSerializer,
    LabelWriteSerializer,
    MediaReadSerializer,
    MediaWriteSerializer,
    MsgBulkActionSerializer,
    MsgReadSerializer,
    MsgWriteSerializer,
    OptInReadSerializer,
    OptInWriteSerializer,
    ResthookReadSerializer,
    ResthookSubscriberReadSerializer,
    ResthookSubscriberWriteSerializer,
    TicketBulkActionSerializer,
    TicketReadSerializer,
    TopicReadSerializer,
    TopicWriteSerializer,
    UserReadSerializer,
    WebHookEventReadSerializer,
    WorkspaceReadSerializer,
)


class ExplorerView(OrgPermsMixin, SmartTemplateView):
    """
    Explorer view which lets users experiment with endpoints against their own data
    """

    permission = "api.apitoken_explorer"
    template_name = "api/v2/explorer.html"
    title = _("API Explorer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["endpoints"] = [
            ArchivesEndpoint.get_read_explorer(),
            BroadcastsEndpoint.get_read_explorer(),
            BroadcastsEndpoint.get_write_explorer(),
            CampaignsEndpoint.get_read_explorer(),
            CampaignsEndpoint.get_write_explorer(),
            CampaignEventsEndpoint.get_read_explorer(),
            CampaignEventsEndpoint.get_write_explorer(),
            CampaignEventsEndpoint.get_delete_explorer(),
            ChannelsEndpoint.get_read_explorer(),
            ClassifiersEndpoint.get_read_explorer(),
            ContactsEndpoint.get_read_explorer(),
            ContactsEndpoint.get_write_explorer(),
            ContactsEndpoint.get_delete_explorer(),
            ContactActionsEndpoint.get_write_explorer(),
            FieldsEndpoint.get_read_explorer(),
            FieldsEndpoint.get_write_explorer(),
            FlowsEndpoint.get_read_explorer(),
            FlowStartsEndpoint.get_read_explorer(),
            FlowStartsEndpoint.get_write_explorer(),
            GlobalsEndpoint.get_read_explorer(),
            GlobalsEndpoint.get_write_explorer(),
            GroupsEndpoint.get_read_explorer(),
            GroupsEndpoint.get_write_explorer(),
            GroupsEndpoint.get_delete_explorer(),
            LabelsEndpoint.get_read_explorer(),
            LabelsEndpoint.get_write_explorer(),
            LabelsEndpoint.get_delete_explorer(),
            MessagesEndpoint.get_read_explorer(),
            MessagesEndpoint.get_write_explorer(),
            MessageActionsEndpoint.get_write_explorer(),
            ResthooksEndpoint.get_read_explorer(),
            ResthookEventsEndpoint.get_read_explorer(),
            ResthookSubscribersEndpoint.get_read_explorer(),
            ResthookSubscribersEndpoint.get_write_explorer(),
            ResthookSubscribersEndpoint.get_delete_explorer(),
            RunsEndpoint.get_read_explorer(),
            TicketsEndpoint.get_read_explorer(),
            TicketActionsEndpoint.get_write_explorer(),
            TopicsEndpoint.get_read_explorer(),
            TopicsEndpoint.get_write_explorer(),
            UsersEndpoint.get_read_explorer(),
            WorkspaceEndpoint.get_read_explorer(),
        ]

        # Ensure all endpoints have the correct script prefix
        prefix = getattr(settings, "FORCE_SCRIPT_NAME", None)
        if prefix:
             prefix = prefix.rstrip("/")
             for endpoint in context["endpoints"]:
                 if endpoint.get("url") and not endpoint["url"].startswith(prefix):
                     if endpoint["url"].startswith("/"):
                         endpoint["url"] = f"{prefix}{endpoint['url']}"
                     else:
                         endpoint["url"] = f"{prefix}/{endpoint['url']}"

        return context


class DocumentationRenderer(DocumentationRenderer):
    template = "api/v2/docs.html"


class BaseEndpoint(BaseAPIView):
    """
    Base class of all our API V2 endpoints
    """

    authentication_classes = (APISessionAuthentication, APITokenAuthentication, APIBasicAuthentication)
    permission_classes = (SSLPermission, APIPermission)
    renderer_classes = (DocumentationRenderer, JSONRenderer)
    throttle_classes = (OrgUserRateThrottle,)
    throttle_scope = "v2"


class RootView(BaseEndpoint):
    """
    We provide a RESTful JSON API for you to interact with your data from outside applications. The following endpoints
    are available:

     * [/api/v2/archives](/api/v2/archives) - to list archives of messages and runs
     * [/api/v2/broadcasts](/api/v2/broadcasts) - to list and send broadcasts
     * [/api/v2/campaigns](/api/v2/campaigns) - to list, create, or update campaigns
     * [/api/v2/campaign_events](/api/v2/campaign_events) - to list, create, update or delete campaign events
     * [/api/v2/channels](/api/v2/channels) - to list channels
     * [/api/v2/classifiers](/api/v2/classifiers) - to list classifiers
     * [/api/v2/contacts](/api/v2/contacts) - to list, create, update or delete contacts
     * [/api/v2/contact_actions](/api/v2/contact_actions) - to perform bulk contact actions
     * [/api/v2/fields](/api/v2/fields) - to list, create or update contact fields
     * [/api/v2/flow_starts](/api/v2/flow_starts) - to list flow starts and start contacts in flows
     * [/api/v2/flows](/api/v2/flows) - to list flows
     * [/api/v2/globals](/api/v2/globals) - to list globals
     * [/api/v2/groups](/api/v2/groups) - to list, create, update or delete contact groups
     * [/api/v2/labels](/api/v2/labels) - to list, create, update or delete message labels
     * [/api/v2/media](/api/v2/media) - to upload media for messages
     * [/api/v2/messages](/api/v2/messages) - to list and send messages
     * [/api/v2/message_actions](/api/v2/message_actions) - to perform bulk message actions
     * [/api/v2/runs](/api/v2/runs) - to list flow runs
     * [/api/v2/resthooks](/api/v2/resthooks) - to list resthooks
     * [/api/v2/resthook_events](/api/v2/resthook_events) - to list resthook events
     * [/api/v2/resthook_subscribers](/api/v2/resthook_subscribers) - to list, create or delete subscribers on your resthooks
     * [/api/v2/tickets](/api/v2/tickets) - to list tickets
     * [/api/v2/ticket_actions](/api/v2/ticket_actions) - to perform bulk ticket actions
     * [/api/v2/topics](/api/v2/topics) - to list and create topics
     * [/api/v2/users](/api/v2/users) - to list user logins
     * [/api/v2/workspace](/api/v2/workspace) - to view your workspace

    To use the endpoint simply append _.json_ to the URL. For example [/api/v2/flows](/api/v2/flows) will return the
    documentation for that endpoint but a request to [/api/v2/flows.json](/api/v2/flows.json) will return a JSON list of
    flow resources.

    You may wish to use the [API Explorer](/api/v2/explorer) to interactively experiment with the API.

    ## Verbs

    All endpoints follow standard REST conventions. You can list a set of resources by making a `GET` request to the
    endpoint, create or update resources by making a `POST` request, or delete a resource with a `DELETE` request.

    ## Status Codes

    The success or failure of requests is represented by status codes as well as a message in the response body:

     * **200**: A list or update request was successful.
     * **201**: A resource was successfully created (only returned for `POST` requests).
     * **204**: An empty response - used for both successful `DELETE` requests and `POST` requests that update multiple
                resources.
     * **400**: The request failed due to invalid parameters. Do not retry with the same values, and the body of the
                response will contain details.
     * **403**: You do not have permission to access this resource.
     * **404**: The resource was not found (returned by `POST` and `DELETE` methods).
     * **429**: You have exceeded the rate limit for this endpoint (see below).

    ## Rate Limiting

    All endpoints are subject to rate limiting. If you exceed the number of allowed requests in a given time window, you
    will get a response with status code 429. The response will also include a header called `Retry-After` which will
    specify the number of seconds that you should wait for before making further requests. It is important to honor the
    `Retry-After` header when encountering 429 responses as rate limits are subject to change without notice.

    ## Date Values

    Many endpoints either return datetime values or can take datatime parameters. The values returned will always be in
    UTC, in the following format: `YYYY-MM-DDThh:mm:ss.ssssssZ`, where `ssssss` is the number of microseconds and
    `Z` denotes the UTC timezone.

    When passing datetime values as parameters, you should use this same format, e.g. `2016-10-13T11:54:32.525277Z`.

    ## URN Values

    We use URNs (Uniform Resource Names) to describe the different ways of communicating with a contact. These can be
    phone numbers, Twitter handles etc. For example a contact might have URNs like:

     * **tel:+250788123123**
     * **twitter:jack**
     * **mailto:jack@example.com**

    Phone numbers should always be given in full [E164 format](http://en.wikipedia.org/wiki/E.164).

    ## Translatable Values

    Some endpoints return or accept text fields that may be translated into different languages. These should be objects
    with ISO-639-3 language codes as keys, e.g. `{"eng": "Hello", "fra": "Bonjour"}`

    ## Authentication

    You must authenticate all calls by including an `Authorization` header with your API token. The Authorization header
    should look like:

        Authorization: Token YOUR_API_TOKEN

    For security reasons, all calls must be made using HTTPS.

    ## Clients

    There is an official [Python client library](https://github.com/rapidpro/rapidpro-python) which we recommend for all
    Python users of the API.
    """

    permission_classes = (SSLPermission,)

    def get_view_description(self, html=False):
        description = super().get_view_description(html)
        prefix = getattr(settings, "FORCE_SCRIPT_NAME", None)
        if prefix:
             clean_prefix = prefix.rstrip('/')
             description = description.replace("(/api/v2/", f"({clean_prefix}/api/v2/")
             description = description.replace("[/api/v2/", f"[{clean_prefix}/api/v2/")
        return description

    def get_view_name(self):
        return self.request.branding["name"] + " API v2"

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "archives": reverse("api.v2.archives", request=request),
                "broadcasts": reverse("api.v2.broadcasts", request=request),
                "campaigns": reverse("api.v2.campaigns", request=request),
                "campaign_events": reverse("api.v2.campaign_events", request=request),
                "channels": reverse("api.v2.channels", request=request),
                "classifiers": reverse("api.v2.classifiers", request=request),
                "contacts": reverse("api.v2.contacts", request=request),
                "contact_actions": reverse("api.v2.contact_actions", request=request),
                "fields": reverse("api.v2.fields", request=request),
                "flow_starts": reverse("api.v2.flow_starts", request=request),
                "flows": reverse("api.v2.flows", request=request),
                "globals": reverse("api.v2.globals", request=request),
                "groups": reverse("api.v2.groups", request=request),
                "labels": reverse("api.v2.labels", request=request),
                "media": reverse("api.v2.media", request=request),
                "messages": reverse("api.v2.messages", request=request),
                "message_actions": reverse("api.v2.message_actions", request=request),
                "resthooks": reverse("api.v2.resthooks", request=request),
                "resthook_events": reverse("api.v2.resthook_events", request=request),
                "resthook_subscribers": reverse("api.v2.resthook_subscribers", request=request),
                "runs": reverse("api.v2.runs", request=request),
                "tickets": reverse("api.v2.tickets", request=request),
                "ticket_actions": reverse("api.v2.ticket_actions", request=request),
                "topics": reverse("api.v2.topics", request=request),
                "users": reverse("api.v2.users", request=request),
                "workspace": reverse("api.v2.workspace", request=request),
            }
        )


# ============================================================
# Endpoints (A-Z)
# ============================================================


class ArchivesEndpoint(ListAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list the data archives associated with your account.

    ## Listing Archives

    A `GET` returns the archives for your organization with the following fields.

      * **type** - the type of the archive, one of `message` or `run` (filterable as `type`).
      * **start_date** - the UTC date of the archive (string) (filterable as `before` and `after`).
      * **period** - `daily` for daily archives, `monthly` for monthly archives (filterable as `period`).
      * **record_count** - number of records in the archive (int).
      * **size** - size of the gzipped archive content (int).
      * **hash** - MD5 hash of the gzipped archive (string or null for empty archives).
      * **download_url** - temporary download URL of the archive (string or null for empty archives).

    Example:

        GET /api/v2/archives.json?type=message&before=2017-05-15&period=daily

    Response is a list of the archives on your account

        {
            "next": null,
            "previous": null,
            "count": 248,
            "results": [
            {
                "type": "message",
                "start_date": "2017-02-20",
                "period": "daily",
                "record_count": 1432,
                "size": 2304,
                "hash": "feca9988b7772c003204a28bd741d0d0",
                "download_url": "https://..."
            },
            ...
        }

    """

    model = Archive
    serializer_class = ArchiveReadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.order_by("-start_date").exclude(period=Archive.PERIOD_DAILY, rollup_id__isnull=False)

    def filter_queryset(self, queryset):
        # filter by `type`
        archive_type = self.request.query_params.get("type") or self.request.query_params.get("archive_type")
        if archive_type:
            queryset = queryset.filter(archive_type=archive_type)

        # filter by `period`
        period = self.request.query_params.get("period")

        if period == "daily":
            queryset = queryset.filter(period="D")
        elif period == "monthly":
            queryset = queryset.filter(period="M")

        # setup filter by before/after on start_date
        return self.filter_before_after(queryset, "start_date")

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Archives",
            "url": reverse("api.v2.archives"),
            "slug": "archive-list",
            "params": [
                {
                    "name": "type",
                    "required": False,
                    "help": "The archive type to filter by: run or message",
                },
                {"name": "period", "required": False, "help": "The period to filter by: daily or monthly"},
            ],
        }


class BoundariesEndpoint(ListAPIMixin, BaseEndpoint):
    """
    Unpublicized endpoint to list administrative boundaries.
    """

    class Pagination(CursorPagination):
        ordering = ("osm_id",)

    model = AdminBoundary
    serializer_class = AdminBoundaryReadSerializer
    pagination_class = Pagination

    def derive_queryset(self):
        org = self.request.org
        if not org.country:
            return AdminBoundary.objects.none()

        queryset = org.country.get_descendants(include_self=True)

        queryset = queryset.prefetch_related(
            Prefetch("aliases", queryset=BoundaryAlias.objects.filter(org=org).order_by("name"))
        )

        return queryset.select_related("parent")


class BroadcastsEndpoint(ListAPIMixin, WriteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to send new message broadcasts and list existing broadcasts in your account.

    ## Listing Broadcasts

    A `GET` returns the outgoing message activity for your organization, listing the most recent messages first.

     * **uuid** - the id of the broadcast (string), filterable as `uuid`.
     * **urns** - the URNs that received the broadcast (array of strings).
     * **contacts** - the contacts that received the broadcast (array of objects).
     * **groups** - the groups that received the broadcast (array of objects).
     * **text** - the message text translations (dict of strings).
     * **attachments** - the attachment translations (dict of lists of strings).
     * **quick_replies** - the quick_replies translations (dict of lists of objects).
     * **base_language** - the default translation language (string).
     * **status** - the status, one of `pending`, `queued`, `started`, `completed`, `failed`, `interrupted`.
     * **created_on** - when this broadcast was either created (datetime) (filterable as `before` and `after`).

    Example:

        GET /api/v2/broadcasts.json

    Response is a list of recent broadcasts:

        {
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "0199bb98-3637-778d-9dfc-0ab85c950d7c",
                    "urns": ["tel:+250788123123", "tel:+250788123124"],
                    "contacts": [{"uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab", "name": "Joe"}]
                    "groups": [],
                    "text": {"eng", "hello world"},
                    "attachments": {"eng", []},
                    "quick_replies": {"eng", [{"text": "Hey"}, {"text": "Hello!"}]},
                    "base_language": "eng",
                    "created_on": "2013-03-02T17:28:12.123456Z"
                },
                ...

    ## Sending Broadcasts

    A `POST` allows you to create and send new broadcasts. Attachments are media object UUIDs returned from POSTing
    to the [media](/api/v2/media) endpoint.

      * **urns** - the URNs of contacts to send to (array of up to 100 strings, optional)
      * **contacts** - the UUIDs of contacts to send to (array of up to 100 strings, optional)
      * **groups** - the UUIDs of contact groups to send to (array of up to 100 strings, optional)
      * **text** - the message text translations (dict of strings)
      * **attachments** - the attachment translations (dict of lists of strings)
      * **quick_replies** - the quick_replies translations (dict of lists of objects)
      * **base_language** - the default translation language (string, optional)

    Example:

        POST /api/v2/broadcasts.json
        {
            "urns": ["tel:+250788123123", "tel:+250788123124"],
            "contacts": ["09d23a05-47fe-11e4-bfe9-b8f6b119e9ab"],
            "text": {
                "eng": "Hello @contact.name! Burger or pizza?",
                "spa": "Hola @contact.name! Hamburguesa o pizza?"
            },
            "quick_replies": {
                "eng": [{"text": "Burger", "extra": "With cheese"}, {"text": "Pizza"}],
                "spa": [{"text": "Hamburguesa", "extra": "Con queso"}, {"text": "Pizza"}]
            },
            "base_language": "eng"
        }

    You will receive a response containing the message broadcast created:

        {
            "uuid": "0199bb98-3637-778d-9dfc-0ab85c950d7c",
            "urns": ["tel:+250788123123", "tel:+250788123124"],
            "contacts": [{"uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab", "name": "Joe"}]
            "groups": [],
            "text": {
                "eng": "Hello @contact.name! Burger or pizza?",
                "spa": "Hola @contact.name! Hamburguesa o pizza?"
            },
            "attachments": {"eng": [], "spa": []},
            "quick_replies": {
                "eng": [{"text": "Burger", "extra": "With cheese"}, {"text": "Pizza"}],
                "spa": [{"text": "Hamburguesa", "extra": "Con queso"}, {"text": "Pizza"}]
            },
            "base_language": "eng",
            "created_on": "2013-03-02T17:28:12.123456Z"
        }
    """

    model = Broadcast
    serializer_class = BroadcastReadSerializer
    write_serializer_class = BroadcastWriteSerializer
    pagination_class = CreatedOnCursorPagination

    def filter_queryset(self, queryset):
        queryset = queryset.filter(schedule=None, is_active=True)

        # filter by UUID (optional)
        if uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=uuid)

        # filter by id (optional, deprecated)
        broadcast_id = self.get_int_param("id")
        if broadcast_id:
            queryset = queryset.filter(id=broadcast_id)

        queryset = queryset.prefetch_related(
            Prefetch("contacts", queryset=Contact.objects.only("uuid", "name").order_by("id")),
            Prefetch("groups", queryset=ContactGroup.objects.only("uuid", "name").order_by("id")),
        )

        return self.filter_before_after(queryset, "created_on")

    def prepare_for_serialization(self, object_list, using: str):
        BroadcastMsgCount.bulk_annotate(object_list)

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Broadcasts",
            "url": reverse("api.v2.broadcasts"),
            "slug": "broadcast-list",
            "params": [
                {"name": "uuid", "required": False, "help": "A broadcast UUID to filter by"},
                {
                    "name": "before",
                    "required": False,
                    "help": "Only return broadcasts created before this date, ex: 2015-01-28T18:00:00.000",
                },
                {
                    "name": "after",
                    "required": False,
                    "help": "Only return broadcasts created after this date, ex: 2015-01-28T18:00:00.000",
                },
            ],
        }

    @classmethod
    def get_write_explorer(cls):
        return {
            "method": "POST",
            "title": "Send Broadcasts",
            "url": reverse("api.v2.broadcasts"),
            "slug": "broadcast-write",
            "fields": [
                {"name": "text", "required": True, "help": "The text of the message you want to send"},
                {"name": "urns", "required": False, "help": "The URNs of contacts you want to send to"},
                {"name": "contacts", "required": False, "help": "The UUIDs of contacts you want to send to"},
                {"name": "groups", "required": False, "help": "The UUIDs of contact groups you want to send to"},
            ],
        }


class CampaignsEndpoint(ListAPIMixin, WriteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list campaigns in your account.

    ## Listing Campaigns

    A `GET` returns the campaigns, listing the most recently created campaigns first.

     * **uuid** - the UUID of the campaign (string), filterable as `uuid`.
     * **name** - the name of the campaign (string).
     * **archived** - whether this campaign is archived (boolean).
     * **group** - the group this campaign operates on (object).
     * **created_on** - when the campaign was created (datetime), filterable as `before` and `after`.

    Example:

        GET /api/v2/campaigns.json

    Response is a list of the campaigns on your account

        {
            "next": null,
            "previous": null,
            "results": [
            {
                "uuid": "f14e4ff0-724d-43fe-a953-1d16aefd1c00",
                "name": "Reminders",
                "archived": false,
                "group": {"uuid": "7ae473e8-f1b5-4998-bd9c-eb8e28c92fa9", "name": "Reporters"},
                "created_on": "2013-08-19T19:11:21.088Z"
            },
            ...
        }

    ## Adding Campaigns

    A **POST** can be used to create a new campaign, by sending the following data. Don't specify a UUID as this will be
    generated for you.

    * **name** - the name of the campaign (string, required)
    * **group** - the UUID of the contact group this campaign will be run against (string, required)

    Example:

        POST /api/v2/campaigns.json
        {
            "name": "Reminders",
            "group": "7ae473e8-f1b5-4998-bd9c-eb8e28c92fa9"
        }

    You will receive a campaign object as a response if successful:

        {
            "uuid": "f14e4ff0-724d-43fe-a953-1d16aefd1c00",
            "name": "Reminders",
            "archived": false,
            "group": {"uuid": "7ae473e8-f1b5-4998-bd9c-eb8e28c92fa9", "name": "Reporters"},
            "created_on": "2013-08-19T19:11:21.088Z"
        }

    ## Updating Campaigns

    A **POST** can also be used to update an existing campaign if you specify its UUID in the URL.

    Example:

        POST /api/v2/campaigns.json?uuid=f14e4ff0-724d-43fe-a953-1d16aefd1c00
        {
            "name": "Reminders II",
            "group": "7ae473e8-f1b5-4998-bd9c-eb8e28c92fa9"
        }

    """

    model = Campaign
    serializer_class = CampaignReadSerializer
    write_serializer_class = CampaignWriteSerializer
    pagination_class = CreatedOnCursorPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.filter(is_active=True, is_archived=False)

    def filter_queryset(self, queryset):
        # filter by UUID (optional)
        if uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=uuid)

        return queryset.prefetch_related(Prefetch("group", queryset=ContactGroup.objects.only("uuid", "name")))

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Campaigns",
            "url": reverse("api.v2.campaigns"),
            "slug": "campaign-list",
            "params": [{"name": "uuid", "required": False, "help": "A campaign UUID to filter by"}],
        }

    @classmethod
    def get_write_explorer(cls):
        return {
            "method": "POST",
            "title": "Add or Update Campaigns",
            "url": reverse("api.v2.campaigns"),
            "slug": "campaign-write",
            "params": [{"name": "uuid", "required": False, "help": "UUID of the campaign to be updated"}],
            "fields": [
                {"name": "name", "required": True, "help": "The name of the campaign"},
                {
                    "name": "group",
                    "required": True,
                    "help": "The UUID of the contact group operated on by the campaign",
                },
            ],
        }


class CampaignEventsEndpoint(ListAPIMixin, WriteAPIMixin, DeleteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list campaign events in your account.

    ## Listing Campaign Events

    A `GET` returns the campaign events, listing the most recently created events first.

     * **uuid** - the UUID of the campaign (string), filterable as `uuid`.
     * **campaign** - the UUID and name of the campaign (object), filterable as `campaign` with UUID.
     * **relative_to** - the key and label of the date field this event is based on (object).
     * **offset** - the offset from our contact field (positive or negative integer).
     * **unit** - the unit for our offset, one of `minutes`, `hours`, `days` or `weeks`.
     * **delivery_hour** - the hour of the day to deliver the message (integer 0-24, -1 indicates send at the same hour as the contact field).
     * **message** - the message to send to the contact by language (object).
     * **flow** - the UUID and name of the flow if this is a flow event (object).
     * **created_on** - when the event was created (datetime).

    Example:

        GET /api/v2/campaign_events.json

    Response is a list of the campaign events on your account

        {
            "next": null,
            "previous": null,
            "results": [
            {
                "uuid": "f14e4ff0-724d-43fe-a953-1d16aefd1c00",
                "campaign": {"uuid": "f14e4ff0-724d-43fe-a953-1d16aefd1c00", "name": "Reminders"},
                "relative_to": {"key": "registration", "name": "Registration Date"},
                "offset": 7,
                "unit": "days",
                "delivery_hour": 9,
                "flow": {"uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab", "name": "Survey"},
                "message": null,
                "created_on": "2013-08-19T19:11:21.088Z"
            },
            ...
        }

    ## Adding Campaign Events

    A **POST** can be used to create a new campaign event, by sending the following data. Don't specify a UUID as this
    will be generated for you.

    * **campaign** - the UUID of the campaign this event should be part of (string, can't be changed for existing events)
    * **relative_to** - the field key that this event will be relative to (string)
    * **offset** - the offset from our contact field (positive or negative integer)
    * **unit** - the unit for our offset (`minutes`, `hours`, `days` or `weeks`)
    * **delivery_hour** - the hour of the day to deliver the message (integer 0-24, -1 indicates send at the same hour as the field)
    * **message** - the message to send to the contact (string, required if flow is not specified)
    * **flow** - the UUID of the flow to start the contact down (string, required if message is not specified)

    Example:

        POST /api/v2/campaign_events.json
        {
            "campaign": "f14e4ff0-724d-43fe-a953-1d16aefd1c00",
            "relative_to": "last_hit",
            "offset": 160,
            "unit": "weeks",
            "delivery_hour": -1,
            "message": "Feeling sick and helpless, lost the compass where self is."
        }

    You will receive an event object as a response if successful:

        {
            "uuid": "6a6d7531-6b44-4c45-8c33-957ddd8dfabc",
            "campaign": {"uuid": "f14e4ff0-724d-43fe-a953-1d16aefd1c00", "name": "Hits"},
            "relative_to": {"key": "last_hit", "name": "Last Hit"},
            "offset": 160,
            "unit": "W",
            "delivery_hour": -1,
            "message": {"eng": "Feeling sick and helpless, lost the compass where self is."},
            "flow": null,
            "created_on": "2013-08-19T19:11:21.088453Z"
        }

    ## Updating Campaign Events

    A **POST** can also be used to update an existing campaign event if you specify its UUID in the URL.

    Example:

        POST /api/v2/campaign_events.json?uuid=6a6d7531-6b44-4c45-8c33-957ddd8dfabc
        {
            "relative_to": "last_hit",
            "offset": 100,
            "unit": "weeks",
            "delivery_hour": -1,
            "message": "Feeling sick and helpless, lost the compass where self is."
        }

    ## Deleting Campaign Events

    A **DELETE** can be used to delete a campaign event if you specify its UUID in the URL.

    Example:

        DELETE /api/v2/campaign_events.json?uuid=6a6d7531-6b44-4c45-8c33-957ddd8dfabc

    You will receive either a 204 response if an event was deleted, or a 404 response if no matching event was found.

    """

    model = CampaignEvent
    serializer_class = CampaignEventReadSerializer
    write_serializer_class = CampaignEventWriteSerializer
    pagination_class = CreatedOnCursorPagination

    def derive_queryset(self):
        return self.model.objects.filter(campaign__org=self.request.org, is_active=True)

    def filter_queryset(self, queryset):
        params = self.request.query_params
        queryset = queryset.filter(is_active=True)
        org = self.request.org

        # filter by UUID (optional)
        if uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=uuid)

        # filter by campaign name/uuid (optional)
        campaign_ref = params.get("campaign")
        if campaign_ref:
            campaign_filter = Q(name=campaign_ref)
            if is_uuid(campaign_ref):
                campaign_filter |= Q(uuid=campaign_ref)
            campaign = org.campaigns.filter(campaign_filter).first()
            if campaign:
                queryset = queryset.filter(campaign=campaign)
            else:
                queryset = queryset.filter(pk=-1)

        return queryset.prefetch_related(
            Prefetch("campaign", queryset=Campaign.objects.only("uuid", "name")),
            Prefetch("flow", queryset=Flow.objects.only("uuid", "name")),
            Prefetch("relative_to", queryset=ContactField.objects.filter(is_active=True).only("key", "name")),
        )

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Campaign Events",
            "url": reverse("api.v2.campaign_events"),
            "slug": "campaign-event-list",
            "params": [
                {"name": "uuid", "required": False, "help": "A campaign event UUID to filter by"},
                {"name": "campaign", "required": False, "help": "A campaign UUID or name to filter"},
            ],
        }

    @classmethod
    def get_write_explorer(cls):
        return {
            "method": "POST",
            "title": "Add or Update Campaign Events",
            "url": reverse("api.v2.campaign_events"),
            "slug": "campaign-event-write",
            "params": [{"name": "uuid", "required": False, "help": "The UUID of the campaign event to update"}],
            "fields": [
                {"name": "campaign", "required": False, "help": "The UUID of the campaign this event belongs to"},
                {
                    "name": "relative_to",
                    "required": True,
                    "help": "The key of the contact field this event is relative to. (string)",
                },
                {
                    "name": "offset",
                    "required": True,
                    "help": "The offset from the relative_to field value (integer, positive or negative)",
                },
                {
                    "name": "unit",
                    "required": True,
                    "help": 'The unit of the offset (one of "minutes, "hours", "days", "weeks")',
                },
                {
                    "name": "delivery_hour",
                    "required": True,
                    "help": "The hour this event should be triggered, or -1 if the event should be sent at the same hour as our date (integer, -1 or 0-23)",
                },
                {
                    "name": "message",
                    "required": False,
                    "help": "The message that should be sent to the contact when this event is triggered (string)",
                },
                {
                    "name": "flow",
                    "required": False,
                    "help": "The UUID of the flow that the contact should start when this event is triggered (string)",
                },
            ],
        }

    @classmethod
    def get_delete_explorer(cls):
        return {
            "method": "DELETE",
            "title": "Delete Campaign Events",
            "url": reverse("api.v2.campaign_events"),
            "slug": "campaign-event-delete",
            "request": "",
            "params": [{"name": "uuid", "required": False, "help": "The UUID of the campaign event to delete"}],
        }


class ChannelsEndpoint(ListAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list channels in your account.

    ## Listing Channels

    A **GET** returns the list of channels for your organization, in the order of last created.  Note that for
    Android devices, all status information is as of the last time it was seen and can be null before the first sync.

     * **uuid** - the UUID of the channel (string), filterable as `uuid`.
     * **name** - the name of the channel (string).
     * **address** - the address (e.g. phone number, Twitter handle) of the channel (string), filterable as `address`.
     * **type** - the type of the channel (e.g. android, facebook, telegram, twilio, vonage...)
     * **country** - which country the sim card for this channel is registered for (string, two letter country code).
     * **device** - information about the device if this is an Android channel:
        * **name** - the name of the device (string).
        * **power_level** - the power level of the device (int).
        * **power_status** - the power status, either `CHA` (charging) or `DIS` (discharging) (string).
        * **power_source** - the source of power as reported by Android (string).
        * **network_type** - the type of network the device is connected to as reported by Android (string).
     * **last_seen** - the datetime when this channel was last seen (datetime).
     * **created_on** - the datetime when this channel was created (datetime).

    Example:

        GET /api/v2/channels.json

    Response containing the channels for your organization:

        {
            "next": null,
            "previous": null,
            "results": [
            {
                "uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
                "name": "Android Phone",
                "address": "+250788123123",
                "type": "android",
                "country": "RW",
                "device": {
                    "name": "Nexus 5X",
                    "power_level": 99,
                    "power_status": "STATUS_DISCHARGING",
                    "power_source": "BATTERY",
                    "network_type": "WIFI",
                },
                "last_seen": "2016-03-01T05:31:27.456",
                "created_on": "2014-06-23T09:34:12.866",
            }]
        }

    """

    model = Channel
    serializer_class = ChannelReadSerializer
    pagination_class = CreatedOnCursorPagination

    def filter_queryset(self, queryset):
        params = self.request.query_params
        queryset = queryset.filter(is_active=True)

        # filter by UUID (optional)
        if uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=uuid)

        # filter by address (optional)
        if address := params.get("address"):
            queryset = queryset.filter(address=address)

        return queryset

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Channels",
            "url": reverse("api.v2.channels"),
            "slug": "channel-list",
            "params": [
                {
                    "name": "uuid",
                    "required": False,
                    "help": "A channel UUID to filter by. ex: 09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
                },
                {"name": "address", "required": False, "help": "A channel address to filter by. ex: +250783530001"},
            ],
        }


class ChannelEventsEndpoint(ListAPIMixin, BaseEndpoint):
    """
    Deprecated endpoint for listing channel events on your account.
    """

    model = ChannelEvent
    serializer_class = ChannelEventReadSerializer
    pagination_class = CreatedOnCursorPagination

    def filter_queryset(self, queryset):
        params = self.request.query_params
        org = self.request.org

        # filter by id (optional)
        call_id = self.get_int_param("id")
        if call_id:
            queryset = queryset.filter(id=call_id)

        # filter by contact (optional)
        contact_uuid = params.get("contact")
        if contact_uuid:
            contact = Contact.objects.filter(org=org, is_active=True, uuid=contact_uuid).first()
            if contact:
                queryset = queryset.filter(contact=contact)
            else:
                queryset = queryset.filter(pk=-1)

        queryset = queryset.prefetch_related(
            Prefetch("contact", queryset=Contact.objects.only("uuid", "name")),
            Prefetch("channel", queryset=Channel.objects.only("uuid", "name")),
        )

        return self.filter_before_after(queryset, "created_on")


class ClassifiersEndpoint(ListAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list the active natural language understanding classifiers on your account.

    ## Listing Classifiers

    A **GET** returns the classifiers for your organization, most recent first.

     * **uuid** - the UUID of the classifier, filterable as `uuid`.
     * **name** - the name of the classifier.
     * **intents** - the list of intents this classifier exposes (list of strings).
     * **type** - the type of the classifier, one of `wit`, `luis` or `bothub`.
     * **created_on** - when this classifier was created.

    Example:

        GET /api/v2/classifiers.json

    Response:

        {
            "next": null,
            "previous": null,
            "results": [
            {
                "uuid": "9a8b001e-a913-486c-80f4-1356e23f582e",
                "name": "Temba Classifier",
                "intents": ["book_flight", "book_car"],
                "type": "wit",
                "created_on": "2013-02-27T09:06:15.456"
            },
            ...

    """

    model = Classifier
    serializer_class = ClassifierReadSerializer
    pagination_class = CreatedOnCursorPagination

    def filter_queryset(self, queryset):
        org = self.request.org
        queryset = queryset.filter(org=org, is_active=True)

        # filter by uuid (optional)
        if uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=uuid)

        return self.filter_before_after(queryset, "created_on")

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Classifiers",
            "url": reverse("api.v2.classifiers"),
            "slug": "classifier-list",
            "params": [
                {
                    "name": "uuid",
                    "required": False,
                    "help": "A classifier UUID to filter by. ex: 09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
                },
                {
                    "name": "before",
                    "required": False,
                    "help": "Only return classifiers created before this date, ex: 2015-01-28T18:00:00.000",
                },
                {
                    "name": "after",
                    "required": False,
                    "help": "Only return classifiers created after this date, ex: 2015-01-28T18:00:00.000",
                },
            ],
        }


class ContactsEndpoint(ListAPIMixin, WriteAPIMixin, DeleteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list, create, update and delete contacts in your account.

    ## Listing Contacts

    A **GET** returns the list of contacts for your organization, in the order of last modified.

     * **uuid** - the UUID of the contact (string), filterable as `uuid`.
     * **name** - the name of the contact (string).
     * **status** - the status of the contact, one of `active`, `blocked`, `stopped` or `archived`.
     * **language** - the preferred language of the contact (string).
     * **urns** - the URNs associated with the contact (string array), filterable as `urn`.
     * **groups** - the UUIDs of any groups the contact is part of (array of objects), filterable as `group` with group name or UUID.
     * **fields** - any contact fields on this contact (object).
     * **flow** - the flow that the contact is currently in, if any (object).
     * **created_on** - when this contact was created (datetime).
     * **modified_on** - when this contact was last modified (datetime), filterable as `before` and `after`.
     * **last_seen_on** - when this contact last communicated with us (datetime).

    Example:

        GET /api/v2/contacts.json

    Response containing the contacts for your organization:

        {
            "next": null,
            "previous": null,
            "results": [
            {
                "uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
                "name": "Ben Haggerty",
                "status": "active",
                "language": null,
                "urns": ["tel:+250788123123"],
                "groups": [{"name": "Customers", "uuid": "5a4eb79e-1b1f-4ae3-8700-09384cca385f"}],
                "fields": {
                  "nickname": "Macklemore",
                  "side_kick": "Ryan Lewis"
                },
                "flow": {"uuid": "c1bc5fcf-3e27-4265-97bf-f6c3a385c2d6", "name": "Registration"},
                "created_on": "2015-11-11T13:05:57.457742Z",
                "modified_on": "2020-08-11T13:05:57.576056Z",
                "last_seen_on": "2020-07-11T13:05:57.576056Z"
            }]
        }

    ## Adding Contacts

    You can add a new contact to your account by sending a **POST** request to this URL with the following JSON data:

    * **name** - the full name of the contact (string, optional).
    * **language** - the preferred language for the contact (3 letter iso code, optional).
    * **urns** - a list of URNs you want associated with the contact (array of up to 100 strings, optional).
    * **groups** - a list of the UUIDs of any groups this contact is part of (array of up to 100 strings, optional).
    * **fields** - the contact fields you want to set or update on this contact (dictionary of up to 100 items, optional).

    Example:

        POST /api/v2/contacts.json
        {
            "name": "Ben Haggerty",
            "language": "eng",
            "urns": ["tel:+250788123123", "twitter:ben"],
            "groups": ["6685e933-26e1-4363-a468-8f7268ab63a9"],
            "fields": {
              "nickname": "Macklemore",
              "side_kick": "Ryan Lewis"
            }
        }

    You will receive a contact object as a response if successful:

        {
            "uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
            "name": "Ben Haggerty",
            "status": "active",
            "language": "eng",
            "urns": ["tel:+250788123123", "twitter:ben"],
            "groups": [{"name": "Devs", "uuid": "6685e933-26e1-4363-a468-8f7268ab63a9"}],
            "fields": {
              "nickname": "Macklemore",
              "side_kick": "Ryan Lewis"
            },
            "flow": null,
            "created_on": "2015-11-11T13:05:57.457742Z",
            "modified_on": "2015-11-11T13:05:57.576056Z",
            "last_seen_on": null
        }

    ## Updating Contacts

    A **POST** can also be used to update an existing contact if you specify either its UUID or one of its URNs in the
    URL. Only those fields included in the body will be changed on the contact.

    If providing a URN in the URL then don't include URNs in the body. Also note that we will create a new contact if
    there is no contact with that URN. You will receive a 201 response if this occurs.

    Examples:

        POST /api/v2/contacts.json?uuid=09d23a05-47fe-11e4-bfe9-b8f6b119e9ab
        {
            "name": "Ben Haggerty",
            "language": "eng",
            "urns": ["tel:+250788123123", "twitter:ben"],
            "groups": [{"name": "Devs", "uuid": "6685e933-26e1-4363-a468-8f7268ab63a9"}],
            "fields": {}
        }

        POST /api/v2/contacts.json?urn=tel%3A%2B250783835665
        {
            "fields": {"nickname": "Ben"}
        }

    ## Deleting Contacts

    A **DELETE** can also be used to delete an existing contact if you specify either its UUID or one of its URNs in the
    URL.

    Examples:

        DELETE /api/v2/contacts.json?uuid=27fb583b-3087-4778-a2b3-8af489bf4a93

        DELETE /api/v2/contacts.json?urn=tel%3A%2B250783835665

    You will receive either a 204 response if a contact was deleted, or a 404 response if no matching contact was found.
    """

    model = Contact
    serializer_class = ContactReadSerializer
    write_serializer_class = ContactWriteSerializer
    write_with_transaction = False
    pagination_class = ModifiedOnCursorPagination
    throttle_scope = "v2.contacts"
    lookup_params = {"uuid": "uuid", "urn": "urns__identity"}

    def filter_queryset(self, queryset):
        params = self.request.query_params
        org = self.request.org

        deleted_only = str_to_bool(params.get("deleted"))
        queryset = queryset.filter(is_active=(not deleted_only))

        # filter by UUID (optional)
        if uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=uuid)

        # filter by URN (optional)
        if urn := params.get("urn"):
            queryset = queryset.filter(urns__identity=self.normalize_urn(urn))

        # filter by group name/uuid (optional)
        group_ref = params.get("group")
        if group_ref:
            group = ContactGroup.get_groups(org).filter(Q(uuid=group_ref) | Q(name=group_ref)).first()
            if group:
                queryset = queryset.filter(groups=group)
            else:
                queryset = queryset.filter(pk=-1)

        # use prefetch rather than select_related for foreign keys to avoid joins
        queryset = queryset.prefetch_related(
            Prefetch("org"),
            Prefetch(
                "groups",
                queryset=ContactGroup.get_groups(org).only("uuid", "name", "org").order_by("id"),
                to_attr="prefetched_groups",
            ),
            Prefetch("current_flow"),
            Prefetch("notes", queryset=ContactNote.objects.order_by("id")),
            Prefetch("notes__created_by"),
        )

        return self.filter_before_after(queryset, "modified_on")

    def prepare_for_serialization(self, object_list, using: str):
        Contact.bulk_urn_cache_initialize(object_list, using=using)

        if str_to_bool(self.request.query_params.get("expand_urns")):
            contact_info = Contact.bulk_inspect(object_list)

            for contact in object_list:
                contact.expanded_urns = contact_info[contact]["urns"]

    def get_serializer_context(self):
        """
        So that we only fetch active contact fields once for all contacts
        """
        context = super().get_serializer_context()
        context["contact_fields"] = ContactField.get_fields(org=self.request.org, viewable_by=self.request.user)
        return context

    def get_object(self):
        queryset = self.get_queryset().filter(**self.lookup_values)

        # don't blow up if posted a URN that doesn't exist - we'll let the serializer create a new contact
        if self.request.method == "POST" and "urns__identity" in self.lookup_values:
            return queryset.first()
        else:
            return generics.get_object_or_404(queryset)

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Contacts",
            "url": reverse("api.v2.contacts"),
            "slug": "contact-list",
            "params": [
                {
                    "name": "uuid",
                    "required": False,
                    "help": "A contact UUID to filter by. ex: 09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
                },
                {"name": "urn", "required": False, "help": "A contact URN to filter by. ex: tel:+250788123123"},
                {"name": "group", "required": False, "help": "A group name or UUID to filter by. ex: Customers"},
                {"name": "deleted", "required": False, "help": "Whether to return only deleted contacts. ex: false"},
                {
                    "name": "before",
                    "required": False,
                    "help": "Only return contacts modified before this date, ex: 2015-01-28T18:00:00.000",
                },
                {
                    "name": "after",
                    "required": False,
                    "help": "Only return contacts modified after this date, ex: 2015-01-28T18:00:00.000",
                },
            ],
            "example": {"query": "urn=tel%3A%2B250788123123"},
        }

    @classmethod
    def get_write_explorer(cls):
        return {
            "method": "POST",
            "title": "Add or Update Contacts",
            "url": reverse("api.v2.contacts"),
            "slug": "contact-write",
            "params": [
                {"name": "uuid", "required": False, "help": "UUID of the contact to be updated"},
                {"name": "urn", "required": False, "help": "URN of the contact to be updated. ex: tel:+250788123123"},
            ],
            "fields": [
                {"name": "name", "required": False, "help": "List of UUIDs of this contact's groups."},
                {
                    "name": "language",
                    "required": False,
                    "help": "Preferred language of the contact (3-letter ISO code). ex: fre, eng",
                },
                {"name": "urns", "required": False, "help": "List of URNs belonging to the contact."},
                {"name": "groups", "required": False, "help": "List of UUIDs of groups that the contact belongs to."},
                {"name": "fields", "required": False, "help": "Custom fields as a JSON dictionary."},
            ],
            "example": {"body": '{"name": "Ben Haggerty", "groups": [], "urns": ["tel:+250788123123"]}'},
        }

    @classmethod
    def get_delete_explorer(cls):
        return {
            "method": "DELETE",
            "title": "Delete Contacts",
            "url": reverse("api.v2.contacts"),
            "slug": "contact-delete",
            "params": [
                {"name": "uuid", "required": False, "help": "UUID of the contact to be deleted"},
                {"name": "urn", "required": False, "help": "URN of the contact to be deleted. ex: tel:+250788123123"},
            ],
        }


class ContactActionsEndpoint(BulkWriteAPIMixin, BaseEndpoint):
    """
    ## Bulk Contact Updating

    A **POST** can be used to perform an action on a set of contacts in bulk.

    * **contacts** - the contact UUIDs or URNs (array of up to 100 strings).
    * **action** - the action to perform, a string one of:

        * `add` - add the contacts to the given group.
        * `remove` - remove the contacts from the given group.
        * `block` - block the contacts.
        * `unblock` - unblock the contacts.
        * `interrupt` - interrupt and end any of the contacts' active flow runs.
        * `delete` - permanently delete the contacts.

    * **group** - the UUID or name of a contact group (string, optional).

    Example:

        POST /api/v2/contact_actions.json
        {
            "contacts": ["7acfa6d5-be4a-4bcc-8011-d1bd9dfasff3", "tel:+250783835665"],
            "action": "add",
            "group": "Testers"
        }

    You will receive an empty response with status code 204 if successful.
    """

    permission = "contacts.contact_update"
    serializer_class = ContactBulkActionSerializer

    @classmethod
    def get_write_explorer(cls):
        actions = cls.serializer_class.ACTIONS

        return {
            "method": "POST",
            "title": "Update Multiple Contacts",
            "url": reverse("api.v2.contact_actions"),
            "slug": "contact-actions",
            "fields": [
                {"name": "contacts", "required": True, "help": "The UUIDs of the contacts to update"},
                {"name": "action", "required": True, "help": "One of the following strings: " + ", ".join(actions)},
                {"name": "group", "required": False, "help": "The UUID or name of a contact group"},
            ],
        }


class DefinitionsEndpoint(BaseEndpoint):
    """
    Deprecated endpoint for exporting definitions of flows, campaigns and triggers in your account.
    """

    permission = "orgs.org_export"

    class Depends(Enum):
        none = 0
        flows = 1
        all = 2

    def get(self, request, *args, **kwargs):
        if self.is_docs():
            return Response({})

        org = request.org
        params = request.query_params
        flow_uuids = params.getlist("flow")
        campaign_uuids = params.getlist("campaign")
        include = params.get("dependencies", "all")

        if include not in DefinitionsEndpoint.Depends.__members__:
            raise InvalidQueryError(
                "dependencies must be one of %s" % ", ".join(DefinitionsEndpoint.Depends.__members__)
            )

        include = DefinitionsEndpoint.Depends[include]

        if flow_uuids:
            flows = set(Flow.objects.filter(uuid__in=flow_uuids, org=org, is_active=True))
        else:
            flows = set()

        if campaign_uuids:
            campaigns = set(Campaign.objects.filter(uuid__in=campaign_uuids, org=org, is_active=True))
        else:
            campaigns = set()

        include_fields_and_groups = False

        if include == DefinitionsEndpoint.Depends.none:
            components = set(itertools.chain(flows, campaigns))
        elif include == DefinitionsEndpoint.Depends.flows:
            components = org.resolve_dependencies(flows, campaigns, include_campaigns=False, include_triggers=True)
        else:
            components = org.resolve_dependencies(flows, campaigns, include_campaigns=True, include_triggers=True)
            include_fields_and_groups = True

        export = org.export_definitions(
            f"https://{org.get_brand_domain()}",
            components,
            include_fields=include_fields_and_groups,
            include_groups=include_fields_and_groups,
        )

        return Response(export, status=status.HTTP_200_OK)


class FieldsEndpoint(ListAPIMixin, WriteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list custom contact fields in your account.

    ## Listing Fields

    A **GET** returns the list of custom contact fields for your organization, in the order of last created.

     * **key** - the unique key of this field (string), filterable as `key`.
     * **name** - the display name of this field (string).
     * **type** - the data type of this field, one of `text`, `number`, `datetime`, `state`, `district` or `ward`.

    Example:

        GET /api/v2/fields.json

    Response containing the fields for your organization:

         {
            "next": null,
            "previous": null,
            "results": [
                {
                    "key": "nick_name",
                    "name": "Nick name",
                    "type": "text"
                },
                ...
            ]
        }

    ## Adding Fields

    A **POST** can be used to create a new contact field. Don't specify a key as this will be generated for you.

    * **name** - the display name (string)
    * **type** - one of the data type codes (string)

    Example:

        POST /api/v2/fields.json
        {
            "name": "Nick name",
            "type": "text"
        }

    You will receive a field object (with the new field key) as a response if successful:

        {
            "key": "nick_name",
            "name": "Nick name",
            "type": "text"
        }

    ## Updating Fields

    A **POST** can also be used to update an existing field if you include it's key in the URL.

    Example:

        POST /api/v2/fields.json?key=nick_name
        {
            "name": "New label",
            "type": "text"
        }

    You will receive the updated field object as a response if successful:

        {
            "key": "nick_name",
            "name": "New label",
            "type": "text"
        }
    """

    model = ContactField
    serializer_class = ContactFieldReadSerializer
    write_serializer_class = ContactFieldWriteSerializer
    pagination_class = CreatedOnCursorPagination
    lookup_params = {"key": "key"}

    def derive_queryset(self):
        org = self.request.org
        return (
            self.model.objects.filter(org=org, is_active=True, is_proxy=False)
            .annotate(
                flow_count=SubqueryCount(Flow.objects.filter(field_dependencies__id=OuterRef("id"), is_active=True))
            )
            .annotate(
                group_count=SubqueryCount(ContactGroup.objects.filter(query_fields__id=OuterRef("id"), is_active=True))
            )
            .annotate(
                campaignevent_count=SubqueryCount(
                    CampaignEvent.objects.filter(relative_to__id=OuterRef("id"), is_active=True)
                )
            )
        )

    def filter_queryset(self, queryset):
        params = self.request.query_params

        # filter by key (optional)
        key = params.get("key")
        if key:
            queryset = queryset.filter(key=key)

        return queryset

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Fields",
            "url": reverse("api.v2.fields"),
            "slug": "field-list",
            "params": [{"name": "key", "required": False, "help": "A field key to filter by. ex: nick_name"}],
            "example": {"query": "key=nick_name"},
        }

    @classmethod
    def get_write_explorer(cls):
        return {
            "method": "POST",
            "title": "Add or Update Fields",
            "url": reverse("api.v2.fields"),
            "slug": "field-write",
            "params": [{"name": "key", "required": False, "help": "Key of an existing field to update"}],
            "fields": [
                {"name": "name", "required": True, "help": "The display name of the field"},
                {"name": "type", "required": True, "help": "The data type of the field"},
            ],
            "example": {"query": "key=nick_name"},
        }


class FlowsEndpoint(ListAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list flows in your account.

    ## Listing Flows

    A **GET** returns the list of flows for your organization, in the order of last created.

     * **uuid** - the UUID of the flow (string), filterable as `uuid`.
     * **name** - the name of the flow (string).
     * **type** - the type of the flow (one of "message", "voice", "survey"), filterable as `type`.
     * **archived** - whether this flow is archived (boolean), filterable as `archived`.
     * **labels** - the labels for this flow (array of objects).
     * **expires** - the time (in minutes) when this flow's inactive contacts will expire (integer).
     * **runs** - the counts of active, completed, interrupted and expired runs (object).
     * **results** - the results that this flow may create (array).
     * **parent_refs** - the keys of the parent flow results referenced in this flow (array).
     * **created_on** - when this flow was created (datetime).
     * **modified_on** - when this flow was last modified (datetime), filterable as `before` and `after`.

    Example:

        GET /api/v2/flows.json

    Response containing the flows for your organization:

        {
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "5f05311e-8f81-4a67-a5b5-1501b6d6496a",
                    "name": "Survey",
                    "type": "message",
                    "archived": false,
                    "labels": [{"name": "Important", "uuid": "5a4eb79e-1b1f-4ae3-8700-09384cca385f"}],
                    "expires": 600,
                    "runs": {
                        "active": 47,
                        "completed": 123,
                        "interrupted": 2,
                        "expired": 34
                    },
                    "results": [
                        {
                            "key": "has_water",
                            "name": "Has Water",
                            "categories": ["Yes", "No", "Other"],
                            "node_uuids": ["99afcda7-f928-4d4a-ae83-c90c96deb76d"]
                        }
                    ],
                    "parent_refs": [],
                    "created_on": "2016-01-06T15:33:00.813162Z",
                    "modified_on": "2017-01-07T13:14:00.453567Z"
                },
                ...
            ]
        }
    """

    model = Flow
    serializer_class = FlowReadSerializer
    pagination_class = CreatedOnCursorPagination

    FLOW_TYPES = {v: k for k, v in FlowReadSerializer.FLOW_TYPES.items()}

    def filter_queryset(self, queryset):
        params = self.request.query_params
        queryset = queryset.exclude(is_active=False)

        # filter by UUID (optional)
        if uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=uuid)

        # filter by type (optional)
        if flow_type := params.get("type"):
            queryset = queryset.filter(flow_type=self.FLOW_TYPES.get(flow_type))

        # filter by archived (optional)
        if archived := params.get("archived"):
            queryset = queryset.filter(is_archived=str_to_bool(archived))

        queryset = queryset.prefetch_related("labels")

        return self.filter_before_after(queryset, "modified_on")

    def prepare_for_serialization(self, object_list, using: str):
        Flow.prefetch_run_counts(object_list, using=using)

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Flows",
            "url": reverse("api.v2.flows"),
            "slug": "flow-list",
            "params": [
                {
                    "name": "uuid",
                    "required": False,
                    "help": "A flow UUID filter by. ex: 5f05311e-8f81-4a67-a5b5-1501b6d6496a",
                },
                {
                    "name": "before",
                    "required": False,
                    "help": "Only return flows modified before this date, ex: 2017-01-28T18:00:00.000",
                },
                {
                    "name": "after",
                    "required": False,
                    "help": "Only return flows modified after this date, ex: 2017-01-28T18:00:00.000",
                },
            ],
        }


class GlobalsEndpoint(ListAPIMixin, WriteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list, create, and update active globals on your account.

    ## Listing Globals

    A **GET** returns the globals for your organization, most recently modified first.

     * **key** - the key of the global.
     * **name** - the name of the global.
     * **value** - the value of the global.
     * **modified_on** - when this global was modified.

    Example:

        GET /api/v2/globals.json

    Response:

        {
            "next": null,
            "previous": null,
            "results": [
                {
                    "key": "org_name",
                    "name": "Org Name",
                    "value": "Acme Ltd",
                    "modified_on": "2013-02-27T09:06:15.456"
                },
                ...
            ]
        }

    ## Adding a Global

    A **POST** can be used to create a new Global. Don't specify a key as this will be generated for you.

     * **name** - the name of the global
     * **value** - the value of the global

    Example:

        POST /api/v2/global.json
        {
            "name": "Org Name",
            "value": "Acme Ltd"
        }

    You will receive a global object as a response if successful:

        {
            "key": "org_name",
            "name": "Org Name",
            "value": "Acme Ltd",
            "modified_on": "2013-02-27T09:06:15.456"
        }

    ## Updating a Global

    A **POST** can also be used to update an existing global if you specify its key in the URL.

    Example:

        POST /api/v2/globals.json?key=org_name
        {
            "value": "Acme Ltd"
        }

    You will receive the updated global object as a response if successful:

        {
            "key": "org_name",
            "name": "Org Name",
            "value": "Acme Ltd",
            "modified_on": "2013-02-27T09:06:15.456"
        }
    """

    model = Global
    serializer_class = GlobalReadSerializer
    write_serializer_class = GlobalWriteSerializer
    pagination_class = ModifiedOnCursorPagination
    lookup_params = {"key": "key"}

    def derive_queryset(self):
        return self.model.objects.filter(org=self.request.org, is_active=True)

    def filter_queryset(self, queryset):
        params = self.request.query_params
        # filter by key (optional)
        key = params.get("key")
        if key:
            queryset = queryset.filter(key=key)

        return self.filter_before_after(queryset, "modified_on")

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Globals",
            "url": reverse("api.v2.globals"),
            "slug": "globals-list",
            "params": [
                {
                    "name": "before",
                    "required": False,
                    "help": "Only return globals modified before this date, ex: 2015-01-28T18:00:00.000",
                },
                {
                    "name": "after",
                    "required": False,
                    "help": "Only return globals modified after this date, ex: 2015-01-28T18:00:00.000",
                },
                {"name": "key", "required": False, "help": "A global key filter by"},
            ],
        }

    @classmethod
    def get_write_explorer(cls):
        return {
            "method": "POST",
            "title": "Add or Update Globals ",
            "url": reverse("api.v2.globals"),
            "slug": "globals-write",
            "params": [{"name": "key", "required": False, "help": "Key of an existing global to update"}],
            "fields": [
                {"name": "name", "required": False, "help": "the Name value of the global"},
                {"name": "value", "required": True, "help": "the new value of the global"},
            ],
        }


class GroupsEndpoint(ListAPIMixin, WriteAPIMixin, DeleteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list, create, update and delete contact groups in your account.

    ## Listing Groups

    A **GET** returns the list of contact groups for your organization, in the order of last created.

     * **uuid** - the UUID of the group (string), filterable as `uuid`.
     * **name** - the name of the group (string), filterable as `name`.
     * **query** - the query if a smart group (string).
     * **status** - the status, one of `initializing`, `evaluating` or `ready`.
     * **system** - whether this is a system group that can't be edited (bool).
     * **count** - the number of contacts in the group (int).

    Example:

        GET /api/v2/groups.json

    Response containing the groups for your organization:

        {
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "5f05311e-8f81-4a67-a5b5-1501b6d6496a",
                    "name": "Reporters",
                    "query": null,
                    "status": "ready",
                    "system": false,
                    "count": 315
                },
                ...
            ]
        }

    ## Adding a Group

    A **POST** can be used to create a new contact group. Don't specify a UUID as this will be generated for you.

    * **name** - the group name (string)

    Example:

        POST /api/v2/groups.json
        {
            "name": "Reporters"
        }

    You will receive a group object as a response if successful:

        {
            "uuid": "5f05311e-8f81-4a67-a5b5-1501b6d6496a",
            "name": "Reporters",
            "count": 0,
            "query": null
        }

    ## Updating a Group

    A **POST** can also be used to update an existing contact group if you specify its UUID in the URL.

    Example:

        POST /api/v2/groups.json?uuid=5f05311e-8f81-4a67-a5b5-1501b6d6496a
        {
            "name": "Checked"
        }

    You will receive the updated group object as a response if successful:

        {
            "uuid": "5f05311e-8f81-4a67-a5b5-1501b6d6496a",
            "name": "Checked",
            "count": 0,
            "query": null
        }

    ## Deleting a Group

    A **DELETE** can be used to delete a contact group if you specify its UUID in the URL.

    Notes:
        - cannot delete groups with associated active campaigns or triggers. You first need to delete related
          objects through the web interface

    Example:

        DELETE /api/v2/groups.json?uuid=5f05311e-8f81-4a67-a5b5-1501b6d6496a

    You will receive either a 204 response if a group was deleted, or a 404 response if no matching group was found.
    """

    model = ContactGroup
    serializer_class = ContactGroupReadSerializer
    write_serializer_class = ContactGroupWriteSerializer
    pagination_class = CreatedOnCursorPagination
    exclusive_params = ("uuid", "name")

    def derive_queryset(self):
        return ContactGroup.get_groups(self.request.org)

    def filter_queryset(self, queryset):
        params = self.request.query_params

        # filter by UUID (optional)
        if uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=uuid)

        # filter by name (optional)
        if name := params.get("name"):
            queryset = queryset.filter(name__iexact=name)

        return queryset.filter(is_active=True).exclude(status=ContactGroup.STATUS_INITIALIZING)

    def prepare_for_serialization(self, object_list, using: str):
        group_counts = ContactGroup.get_member_counts(object_list)
        for group in object_list:
            group.count = group_counts[group]

    def perform_destroy(self, instance):
        # if there are still dependencies, give up
        triggers = instance.triggers.filter(is_archived=False)
        if triggers:
            raise InvalidQueryError("Group is being used by triggers which must be archived first.")

        campaigns = instance.campaigns.filter(is_archived=False)
        if campaigns:
            raise InvalidQueryError("Group is being used by campaigns which must be archived first.")

        instance.release(self.request.user)

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Contact Groups",
            "url": reverse("api.v2.groups"),
            "slug": "group-list",
            "params": [
                {"name": "uuid", "required": False, "help": "A contact group UUID to filter by"},
                {"name": "name", "required": False, "help": "A contact group name to filter by"},
            ],
        }

    @classmethod
    def get_write_explorer(cls):
        return {
            "method": "POST",
            "title": "Add or Update Contact Groups",
            "url": reverse("api.v2.groups"),
            "slug": "group-write",
            "params": [{"name": "uuid", "required": False, "help": "The UUID of the contact group to update"}],
            "fields": [{"name": "name", "required": True, "help": "The name of the contact group"}],
        }

    @classmethod
    def get_delete_explorer(cls):
        return {
            "method": "DELETE",
            "title": "Delete Contact Groups",
            "url": reverse("api.v2.groups"),
            "slug": "group-delete",
            "params": [{"name": "uuid", "required": True, "help": "The UUID of the contact group to delete"}],
        }


class LabelsEndpoint(ListAPIMixin, WriteAPIMixin, DeleteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list, create, update and delete message labels in your account.

    ## Listing Labels

    A **GET** returns the list of message labels for your organization, in the order of last created.

     * **uuid** - the UUID of the label (string), filterable as `uuid`.
     * **name** - the name of the label (string), filterable as `name`.
     * **count** - the number of messages with this label (int).

    Example:

        GET /api/v2/labels.json

    Response containing the labels for your organization:

        {
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "5f05311e-8f81-4a67-a5b5-1501b6d6496a",
                    "name": "Screened",
                    "count": 315
                },
                ...
            ]
        }

    ## Adding a Label

    A **POST** can be used to create a new message label. Don't specify a UUID as this will be generated for you.

    * **name** - the label name (string)

    Example:

        POST /api/v2/labels.json
        {
            "name": "Screened"
        }

    You will receive a label object as a response if successful:

        {
            "uuid": "fdd156ca-233a-48c1-896d-a9d594d59b95",
            "name": "Screened",
            "count": 0
        }

    ## Updating a Label

    A **POST** can also be used to update an existing message label if you specify its UUID in the URL.

    Example:

        POST /api/v2/labels.json?uuid=fdd156ca-233a-48c1-896d-a9d594d59b95
        {
            "name": "Checked"
        }

    You will receive the updated label object as a response if successful:

        {
            "uuid": "fdd156ca-233a-48c1-896d-a9d594d59b95",
            "name": "Checked",
            "count": 0
        }

    ## Deleting a Label

    A **DELETE** can be used to delete a message label if you specify its UUID in the URL.

    Example:

        DELETE /api/v2/labels.json?uuid=fdd156ca-233a-48c1-896d-a9d594d59b95

    You will receive either a 204 response if a label was deleted, or a 404 response if no matching label was found.
    """

    model = Label
    serializer_class = LabelReadSerializer
    write_serializer_class = LabelWriteSerializer
    pagination_class = CreatedOnCursorPagination
    exclusive_params = ("uuid", "name")

    def derive_queryset(self):
        return self.model.objects.filter(org=self.request.org, is_active=True)

    def filter_queryset(self, queryset):
        params = self.request.query_params

        # filter by UUID (optional)
        if uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=uuid)

        # filter by name (optional)
        if name := params.get("name"):
            queryset = queryset.filter(name__iexact=name)

        return queryset.filter(is_active=True)

    def prepare_for_serialization(self, object_list, using: str):
        label_counts = LabelCount.get_totals(object_list)
        for label in object_list:
            label.count = label_counts[label]

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Message Labels",
            "url": reverse("api.v2.labels"),
            "slug": "label-list",
            "params": [
                {"name": "uuid", "required": False, "help": "A message label UUID to filter by"},
                {"name": "name", "required": False, "help": "A message label name to filter by"},
            ],
        }

    @classmethod
    def get_write_explorer(cls):
        return {
            "method": "POST",
            "title": "Add or Update Message Labels",
            "url": reverse("api.v2.labels"),
            "slug": "label-write",
            "params": [{"name": "uuid", "required": False, "help": "The UUID of the message label to update"}],
            "fields": [{"name": "name", "required": True, "help": "The name of the message label"}],
        }

    @classmethod
    def get_delete_explorer(cls):
        return {
            "method": "DELETE",
            "title": "Delete Message Labels",
            "url": reverse("api.v2.labels"),
            "slug": "label-delete",
            "params": [{"name": "uuid", "required": True, "help": "The UUID of the message label to delete"}],
        }


class MediaEndpoint(WriteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to upload new media objects for use as attachments on messages.

    ## Uploading Media

    A **POST** can be used to upload a new media object.

    * **file** - the file data (bytes)

    You will receive a media object as a response if successful:

        {
            "uuid": "fdd156ca-233a-48c1-896d-a9d594d59b95",
            "content_type": "image/jpeg",
            "url": "https://...test.jpg",
            "filename": "test.jpg",
            "size": 23452
        }
    """

    parser_classes = (MultiPartParser, FormParser)
    model = Media
    serializer_class = MediaReadSerializer
    write_serializer_class = MediaWriteSerializer


class MessagesEndpoint(ListAPIMixin, WriteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list messages in your account.

    ## Listing Messages

    A `GET` returns the messages for your organization, filtering them as needed. Each message has the following
    attributes:

     * **uuid** - the UUID of the message (string), filterable as `uuid`.
     * **contact** - the UUID and name of the contact (object).
     * **urn** - the URN of the sender or receiver, depending on direction (string).
     * **channel** - the UUID and name of the channel that handled this message (object).
     * **direction** - the direction of the message (one of `incoming` or `outgoing`).
     * **type** - the type of the message (one of `text`, `optin` or `voice`).
     * **status** - the status of the message, one of:
         * `queued` - incoming that has not yet been handled, or outgoing message that has not yet been sent.
         * `handled` - incoming that has been handled by a flow or put in the inbox.
         * `wired` - outgoing that has been wired to a channel.
         * `sent` - outgoing for which channel has confirmed that it has been sent.
         * `delivered` - outgoing for which channel has confirmed that it has been delivered to the contact.
         * `read` - outgoing for which channel has confirmed that it has been read by the contact.
         * `errored` - outgoing that has errored but will be retried.
         * `failed` - outgoing that has errored too many times and will no longer be retried.
     * **visibility** - the visibility of the message (one of `visible`, `archived` or `deleted`)
     * **text** - the text of the message received (string). Note this is the logical view and the message may have been received as multiple physical messages.
     * **attachments** - the attachments on the message (array of objects).
     * **quick_replies** - the quick_replies on the message (array of objects).
     * **labels** - any labels set on this message (array of objects).
     * **flow** - the UUID and name of the flow if message was part of a flow (object, optional).
     * **created_on** - when this message was either received by the channel or created (datetime), filterable as `before` and `after`.
     * **sent_on** - for outgoing messages, when the channel sent the message (null if not yet sent or an incoming message) (datetime).
     * **modified_on** - when the message was last modified (datetime).

    You can also filter by `folder` where folder is one of `inbox`, `flows`, `archived`, `outbox`, `sent` or `failed`.

    The sort order for the `sent` folder is the sent date. All other requests are sorted by the message creation date.

    Without any parameters this endpoint will return all incoming and outgoing messages ordered by creation date.

    Example:

        GET /api/v2/messages.json?folder=inbox

    Response is the list of messages for that contact, most recently created first:

        {
            "next": "http://example.com/api/v2/messages.json?folder=inbox&cursor=cD0yMDE1LTExLTExKzExJTNBM40NjQlMkIwMCUzRv",
            "previous": null,
            "results": [
            {
                "uuid": "0199bb98-3637-778d-9dfc-0ab85c950d7c",
                "contact": {"uuid": "d33e9ad5-5c35-414c-abd4-e7451c69ff1d", "name": "Bob McFlow"},
                "urn": "tel:+1234567890",
                "channel": {"uuid": "9a8b001e-a913-486c-80f4-1356e23f582e", "name": "Vonage"},
                "direction": "out",
                "type": "text",
                "status": "wired",
                "visibility": "visible",
                "text": "How are you?",
                "attachments": [{"content_type": "audio/wav" "url": "http://domain.com/recording.wav"}],
                "quick_replies": [{"text": "Great"}, {"text": "Improving"}],
                "labels": [{"name": "Important", "uuid": "5a4eb79e-1b1f-4ae3-8700-09384cca385f"}],
                "flow": {"uuid": "254fd2ff-4990-4621-9536-0a448d313692", "name": "Registration"},
                "created_on": "2016-01-06T15:33:00.813162Z",
                "sent_on": "2016-01-06T15:35:03.675716Z",
                "modified_on": "2016-01-06T15:35:03.675716Z"
            },
            ...
        }

    ## Sending a Message

    A **POST** can be used to create and send a new message. Attachments are media object UUIDs returned from POSTing
    to the [media](/api/v2/media) endpoint.

     * **contact** - the UUID of the contact (string)
     * **text** - the text of the message (string)
     * **attachments** - the attachments of the message (list of strings, maximum 10)
     * **quick_replies** - the quick_replies of the message (list of objects, maximum 10)

    Example:

        POST /api/v2/messages.json
        {
            "contact": "d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
            "text": "Burger or pizza?",
            "attachments": [],
            "quick_repies": [{"text": "Burger", "extra": "With cheese"}, {"text": "Pizza"}]

        }

    You will receive the new message object as a response if successful:

        {
            "uuid": "0199bb98-3637-778d-9dfc-0ab85c950d7c",
            "contact": {"uuid": "d33e9ad5-5c35-414c-abd4-e7451c69ff1d", "name": "Bob McFlow"},
            "urn": "tel:+1234567890",
            "channel": {"uuid": "9a8b001e-a913-486c-80f4-1356e23f582e", "name": "Vonage"},
            "direction": "out",
            "type": "text",
            "status": "queued",
            "visibility": "visible",
            "text": "Burger or pizza?",
            "attachments": [],
            "quick_replies": [{"text": "Burger", "extra": "With cheese"}, {"text": "Pizza"}],
            "labels": [],
            "flow": null,
            "created_on": "2023-01-06T15:33:00.813162Z",
            "sent_on": "2023-01-06T15:35:03.675716Z",
            "modified_on": "2023-01-06T15:35:03.675716Z"
        }
    """

    class Pagination(CreatedOnCursorPagination):
        """
        Overridden paginator that switches depending on folder being requested.
        """

        ordering = {"sent": SentOnCursorPagination.ordering}

        def get_ordering(self, request, queryset, view=None):
            folder = request.query_params.get("folder", "").lower()
            return self.ordering.get(folder, CreatedOnCursorPagination.ordering)

    model = Msg
    serializer_class = MsgReadSerializer
    write_serializer_class = MsgWriteSerializer
    write_with_transaction = False
    pagination_class = Pagination
    exclusive_params = ("contact", "folder", "label", "broadcast")
    throttle_scope = "v2.messages"

    FOLDER_FILTERS = {
        "inbox": MsgFolder.INBOX,
        "flows": MsgFolder.HANDLED,
        "archived": MsgFolder.ARCHIVED,
        "outbox": MsgFolder.OUTBOX,
        "sent": MsgFolder.SENT,
        "failed": MsgFolder.FAILED,
    }

    def derive_queryset(self):
        org = self.request.org
        folder = self.request.query_params.get("folder")

        if folder:
            if msg_folder := self.FOLDER_FILTERS.get(folder.lower()):
                return msg_folder.get_queryset(org)
            else:
                return self.model.objects.none()
        else:
            return self.model.objects.filter(
                org=org, visibility__in=(Msg.VISIBILITY_VISIBLE, Msg.VISIBILITY_ARCHIVED)
            ).exclude(status=Msg.STATUS_PENDING)

    def filter_queryset(self, queryset):
        params = self.request.query_params
        org = self.request.org

        # filter by UUID (optional)
        if uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=uuid)

        # filter by id (optional, deprecated)
        if msg_id := self.get_int_param("id"):
            queryset = queryset.filter(id=msg_id)

        # filter by broadcast (optional, deprecated)
        if broadcast_id := params.get("broadcast"):
            queryset = queryset.filter(broadcast_id=broadcast_id)

        # filter by contact (optional)
        if contact_uuid := params.get("contact"):
            contact = Contact.objects.filter(org=org, is_active=True, uuid=contact_uuid).first()
            if contact:
                queryset = queryset.filter(contact=contact)
            else:
                queryset = queryset.none()

        # filter by label name/uuid (optional)
        if label_ref := params.get("label"):
            label_filter = Q(name=label_ref)
            if is_uuid(label_ref):
                label_filter |= Q(uuid=label_ref)

            label = Label.get_active_for_org(org).filter(label_filter).first()
            if label:
                queryset = queryset.filter(labels=label)
            else:
                queryset = queryset.none()

        # use prefetch rather than select_related for foreign keys to avoid joins
        queryset = queryset.prefetch_related(
            Prefetch("contact", queryset=Contact.objects.only("uuid", "name")),
            Prefetch("contact_urn", queryset=ContactURN.objects.only("scheme", "path", "display")),
            Prefetch("channel", queryset=Channel.objects.only("uuid", "name")),
            Prefetch("labels", queryset=Label.objects.only("uuid", "name").order_by("id")),
            Prefetch("flow", queryset=Flow.objects.only("uuid", "name")),
        )

        return self.filter_before_after(queryset, "created_on")

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Messages",
            "url": reverse("api.v2.messages"),
            "slug": "msg-list",
            "params": [
                {"name": "uuid", "required": False, "help": "A message UUID to filter by"},
                {
                    "name": "folder",
                    "required": False,
                    "help": "A folder name to filter by, one of: inbox, flows, archived, outbox, sent, failed",
                },
                {
                    "name": "before",
                    "required": False,
                    "help": "Only return messages created before this date, ex: 2015-01-28T18:00:00.000",
                },
                {
                    "name": "after",
                    "required": False,
                    "help": "Only return messages created after this date, ex: 2015-01-28T18:00:00.000",
                },
            ],
            "example": {"query": "folder=inbox&after=2014-01-01T00:00:00.000"},
        }

    @classmethod
    def get_write_explorer(cls):
        return {
            "method": "POST",
            "title": "Send Messages",
            "url": reverse("api.v2.messages"),
            "slug": "message-write",
            "fields": [
                {"name": "contact", "required": True, "help": "The UUID of the contact"},
                {"name": "text", "required": False, "help": "The text of the message (string)"},
                {"name": "attachments", "required": False, "help": "The attachments on the message (array of strings)"},
                {
                    "name": "quick_replies",
                    "required": False,
                    "help": "The quick replies on the message (array of objects)",
                },
            ],
        }


class MessageActionsEndpoint(BulkWriteAPIMixin, BaseEndpoint):
    """
    ## Bulk Message Updating

    A **POST** can be used to perform an action on a set of messages in bulk.

    * **messages** - the message ids (array of up to 100 integers).
    * **action** - the action to perform, a string one of:

        * `label` - apply the given label to the messages.
        * `unlabel` - remove the given label from the messages.
        * `archive` - archive the messages.
        * `restore` - restore the messages if they are archived.
        * `delete` - permanently delete the messages.

    * **label** - the UUID or name of an existing label (string, optional).
    * **label_name** - the name of a label which can be created if it doesn't exist (string, optional).

    If labelling or unlabelling messages using `label` you will get an error response (400) if the label doesn't exist.
    If labelling with `label_name` the label will be created if it doesn't exist, and if unlabelling it is ignored if
    it doesn't exist.

    Example:

        POST /api/v2/message_actions.json
        {
            "messages": [1234, 2345, 3456],
            "action": "label",
            "label": "Testing"
        }

    You will receive an empty response with status code 204 if successful. In the case that some messages couldn't be
    updated because they no longer exist, the status code will be 200 and the body will include the failed message ids:

    Example response:

        {"failures": [2345, 3456]}

    """

    permission = "msgs.msg_update"
    serializer_class = MsgBulkActionSerializer

    @classmethod
    def get_write_explorer(cls):
        actions = cls.serializer_class.ACTIONS

        return {
            "method": "POST",
            "title": "Update Multiple Messages",
            "url": reverse("api.v2.message_actions"),
            "slug": "message-actions",
            "fields": [
                {"name": "messages", "required": True, "help": "The ids of the messages to update"},
                {"name": "action", "required": True, "help": "One of the following strings: " + ", ".join(actions)},
                {"name": "label", "required": False, "help": "The UUID or name of a message label"},
            ],
        }


class OptInsEndpoint(ListAPIMixin, WriteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list the opt-ins in your workspace and create new ones.

    ## Listing Opt-Ins

    A **GET** returns the opt-ins for your organization, most recent first.

     * **uuid** - the UUID of the opt-in (string).
     * **name** - the name of the opt-in (string).
     * **created_on** - when this opt-in was created (datetime).

    Example:

        GET /api/v2/optins.json

    Response:

        {
            "next": null,
            "previous": null,
            "results": [
            {
                "uuid": "9a8b001e-a913-486c-80f4-1356e23f582e",
                "name": "Jokes",
                "created_on": "2013-02-27T09:06:15.456"
            },
            ...

    ## Adding a New Opt-In

    By making a `POST` request with a unique name you can create a new opt-in.

     * **name** - the name of the opt-in to create (string)

    Example:

        POST /api/v2/optins.json
        {
            "name": "Weather Updates"
        }
    """

    model = OptIn
    serializer_class = OptInReadSerializer
    write_serializer_class = OptInWriteSerializer
    pagination_class = CreatedOnCursorPagination

    @classmethod
    def get_read_explorer(cls):  # pragma: no cover
        return {"method": "GET", "title": "List Opt-Ins", "url": reverse("api.v2.optins"), "slug": "optin-list"}

    @classmethod
    def get_write_explorer(cls):  # pragma: no cover
        return {
            "method": "POST",
            "title": "Add New Opt-Ins",
            "url": reverse("api.v2.optins"),
            "slug": "optin-write",
            "fields": [{"name": "name", "required": True, "help": "The name of the opt-in"}],
        }


class ResthooksEndpoint(ListAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list configured resthooks in your account.

    ## Listing Resthooks

    A `GET` returns the resthooks on your organization. Each resthook has the following attributes:

     * **resthook** - the slug for the resthook (string).
     * **created_on** - the datetime when this resthook was created (datetime).
     * **modified_on** - the datetime when this resthook was last modified (datetime).

    Example:

        GET /api/v2/resthooks.json

    Response is the list of resthooks on your organization, most recently modified first:

        {
            "next": "http://example.com/api/v2/resthooks.json?cursor=cD0yMDE1LTExLTExKzExJTNBM40NjQlMkIwMCUzRv",
            "previous": null,
            "results": [
            {
                "resthook": "new-report",
                "created_on": "2015-11-11T13:05:57.457742Z",
                "modified_on": "2015-11-11T13:05:57.457742Z",
            },
            ...
        }
    """

    model = Resthook
    serializer_class = ResthookReadSerializer
    pagination_class = ModifiedOnCursorPagination

    def filter_queryset(self, queryset):
        return queryset.filter(is_active=True)

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Resthooks",
            "url": reverse("api.v2.resthooks"),
            "slug": "resthook-list",
            "params": [],
        }


class ResthookSubscribersEndpoint(ListAPIMixin, WriteAPIMixin, DeleteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list, add or remove subscribers to resthooks.

    ## Listing Resthook Subscribers

    A `GET` returns the subscribers on your organization. Each resthook subscriber has the following attributes:

     * **id** - the id of the subscriber (integer, filterable).
     * **resthook** - the resthook they are subscribed to (string, filterable).
     * **target_url** - the url that will be notified when this event occurs.
     * **created_on** - when this subscriber was added.

    Example:

        GET /api/v2/resthook_subscribers.json

    Response is the list of resthook subscribers on your organization, most recently created first:

        {
            "next": "http://example.com/api/v2/resthook_subscribers.json?cursor=cD0yMDE1LTExLTExKzExJTNBM40NjQlMkIwMCUzRv",
            "previous": null,
            "results": [
            {
                "id": "10404016"
                "resthook": "mother-registration",
                "target_url": "https://zapier.com/receive/505019595",
                "created_on": "2013-08-19T19:11:21.082Z"
            },
            {
                "id": "10404055",
                "resthook": "new-birth",
                "target_url": "https://zapier.com/receive/605010501",
                "created_on": "2013-08-19T19:11:21.082Z"
            },
            ...
        }

    ## Subscribing to a Resthook

    By making a `POST` request with the event you want to subscribe to and the target URL, you can subscribe to be
    notified whenever your resthook event is triggered.

     * **resthook** - the slug of the resthook to subscribe to
     * **target_url** - the URL you want called (will be called with a POST)

    Example:

        POST /api/v2/resthook_subscribers.json
        {
            "resthook": "new-report",
            "target_url": "https://zapier.com/receive/505019595"
        }

    Response is the created subscription:

        {
            "id": "10404016",
            "resthook": "new-report",
            "target_url": "https://zapier.com/receive/505019595",
            "created_on": "2013-08-19T19:11:21.082Z"
        }

    ## Deleting a Subscription

    A **DELETE** can be used to delete a subscription if you specify its id in the URL.

    Example:

        DELETE /api/v2/resthook_subscribers.json?id=10404016

    You will receive either a 204 response if a subscriber was deleted, or a 404 response if no matching subscriber was found.

    """

    model = ResthookSubscriber
    serializer_class = ResthookSubscriberReadSerializer
    write_serializer_class = ResthookSubscriberWriteSerializer
    pagination_class = CreatedOnCursorPagination
    lookup_params = {"id": "id"}

    def get_queryset(self):
        return self.model.objects.filter(resthook__org=self.request.org, is_active=True)

    def filter_queryset(self, queryset):
        params = self.request.query_params

        # filter by id (optional)
        subscriber_id = self.get_int_param("id")
        if subscriber_id:
            queryset = queryset.filter(id=subscriber_id)

        resthook = params.get("resthook")
        if resthook:
            queryset = queryset.filter(resthook__slug=resthook)

        return queryset.select_related("resthook")

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Resthook Subscribers",
            "url": reverse("api.v2.resthook_subscribers"),
            "slug": "resthooksubscriber-list",
            "params": [],
        }

    @classmethod
    def get_write_explorer(cls):
        return dict(
            method="POST",
            title="Add Resthook Subscriber",
            url=reverse("api.v2.resthook_subscribers"),
            slug="resthooksubscriber-write",
            fields=[
                dict(name="resthook", required=True, help="The slug for the resthook you want to subscribe to"),
                dict(
                    name="target_url",
                    required=True,
                    help="The URL that will be called when the resthook is triggered.",
                ),
            ],
            example=dict(body='{"resthook": "new-report", "target_url": "https://zapier.com/handle/1515155"}'),
        )

    @classmethod
    def get_delete_explorer(cls):
        return dict(
            method="DELETE",
            title="Delete Resthook Subscriber",
            url=reverse("api.v2.resthook_subscribers"),
            slug="resthooksubscriber-delete",
            params=[dict(name="id", required=True, help="The id of the subscriber to delete")],
        )


class ResthookEventsEndpoint(ListAPIMixin, BaseEndpoint):
    """
    This endpoint lists recent events for the passed in Resthook.

    ## Listing Resthook Events

    A `GET` returns the recent resthook events on your organization. Each event has the following attributes:

     * **resthook** - the slug for the resthook (filterable)
     * **data** - the data for the resthook
     * **created_on** - the datetime when this resthook was created (datetime)

    Example:

        GET /api/v2/resthook_events.json

    Response is the list of recent resthook events on your organization, most recently created first:

        {
            "next": "http://example.com/api/v2/resthook_events.json?cursor=cD0yMDE1LTExLTExKzExJTNBM40NjQlMkIwMCUzRv",
            "previous": null,
            "results": [
            {
                "resthook": "new-report",
                "data": {
                    "flow": {
                        "name": "Water Survey",
                        "uuid": "13fed2d2-160e-48e5-b52e-6eea3f74f27d"
                    },
                    "contact": {
                        "uuid": "dc2b3709-3261-465f-b39a-fc7312b2ab95",
                        "name": "Ben Haggerty",
                        "urn": "tel:+12065551212"
                    },
                    "channel": {
                        "name": "Twilio +12065552020",
                        "uuid": "f49d3dd6-beef-40ba-b86b-f526c649175c"
                    },
                    "run": {
                        "uuid": "7facea33-9fbc-4bdd-ba63-b2600cd4f69b",
                        "created_on":"2014-06-03T08:20:03.242525+00:00"
                    },
                    "input": {
                        "urn": "tel:+12065551212",
                        "text": "stream",
                        "attachments": []
                    }
                    "path": [
                        {
                            "node_uuid": "40019102-e621-4b88-acd2-1288961dc214",
                            "arrived_on": "2014-06-03T08:21:09.865526+00:00",
                            "exit_uuid": "207d919d-ac4d-451a-9892-3ceca16430ff"
                        },
                        {
                            "node_uuid": "207d919d-ac4d-451a-9892-3ceca16430ff",
                            "arrived_on": "2014-06-03T08:21:09.865526+00:00"
                        }
                    ],
                    "results": {
                        "water_source": {
                            "node_uuid": "40019102-e621-4b88-acd2-1288961dc214",
                            "name": "Water Source",
                            "category": "Stream",
                            "value": "stream",
                            "input": "stream",
                            "created_on": "2017-12-05T16:47:57.875680+00:00"
                        }
                    }
                },
                "created_on": "2017-11-11T13:05:57.457742Z",
            },
            ...
        }
    """

    model = WebHookEvent
    serializer_class = WebHookEventReadSerializer
    pagination_class = CreatedOnCursorPagination

    def filter_queryset(self, queryset):
        params = self.request.query_params
        queryset = queryset.exclude(resthook=None)

        resthook = params.get("resthook")
        if resthook:  # pragma: needs cover
            queryset = queryset.filter(resthook__slug=resthook)

        return queryset.select_related("resthook")

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Resthook Events",
            "url": reverse("api.v2.resthook_events"),
            "slug": "resthook-event-list",
            "params": [],
        }


class RunsEndpoint(ListAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to fetch flow runs. A run represents a single contact's path through a flow and is created
    each time a contact is started in a flow.

    ## Listing Flow Runs

    A `GET` request returns the flow runs for your organization, filtering them as needed. Each
    run has the following attributes:

     * **uuid** - the ID of the run (string), filterable as `uuid`.
     * **flow** - the UUID and name of the flow (object), filterable as `flow` with UUID.
     * **contact** - the UUID and name of the contact (object).
     * **start** - the UUID of the flow start (object).
     * **responded** - whether the contact responded (boolean), filterable as `responded`.
     * **values** - values generated by rulesets in the flow (array of objects).
     * **created_on** - the datetime when this run was started (datetime).
     * **modified_on** - when this run was last modified (datetime), filterable as `before` and `after`.
     * **exited_on** - the datetime when this run exited or null if it is still active (datetime).
     * **exit_type** - how the run ended, one of `interrupted`, `completed`, `expired`.

    Note that you cannot filter by `flow` and `contact` at the same time.

    Example:

        GET /api/v2/runs.json?flow=f5901b62-ba76-4003-9c62-72fdacc1b7b7

    Response is the list of runs on the flow, most recently modified first:

        {
            "next": "http://example.com/api/v2/runs.json?cursor=cD0yMDE1LTExLTExKzExJTNBM40NjQlMkIwMCUzRv",
            "previous": null,
            "results": [
            {
                "uuid": "0199c5c0-8f9b-76ea-a955-193ad8ed8606",
                "flow": {"uuid": "f5901b62-ba76-4003-9c62-72fdacc1b7b7", "name": "Favorite Color"},
                "contact": {
                    "uuid": "d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
                    "urn": "tel:+12065551212",
                    "name": "Bob McFlow"
                },
                "responded": true,
                "values": {
                    "color": {
                        "name": "Color",
                        "value": "blue",
                        "category": "Blue",
                        "node": "fc32aeb0-ac3e-42a8-9ea7-10248fdf52a1",
                        "time": "2015-11-11T13:03:51.635662Z"
                    },
                    "reason": {
                        "name": "Reason",
                        "value": "Because it's the color of sky",
                        "category": "All Responses",
                        "node": "4c9cb68d-474f-4b9a-b65e-c2aa593a3466",
                        "time": "2015-11-11T13:05:57.576056Z"
                    }
                },
                "created_on": "2015-11-11T13:05:57.457742Z",
                "modified_on": "2015-11-11T13:05:57.576056Z",
                "exited_on": "2015-11-11T13:05:57.576056Z",
                "exit_type": "completed"
            },
            ...
        }
    """

    model = FlowRun
    serializer_class = FlowRunReadSerializer
    pagination_class = ModifiedOnCursorPagination
    exclusive_params = ("contact", "flow")
    throttle_scope = "v2.runs"

    def filter_queryset(self, queryset):
        params = self.request.query_params
        org = self.request.org

        # filter by uuid (optional)
        if run_uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=run_uuid)

        # filter by id (optional, deprecated)
        if run_id := self.get_int_param("id"):
            queryset = queryset.filter(id=run_id)

        # filter by flow (optional)
        if flow_uuid := self.get_uuid_param("flow"):
            if flow := org.flows.filter(uuid=flow_uuid, is_active=True).first():
                queryset = queryset.filter(flow=flow)
            else:
                queryset = queryset.none()

        # filter by contact (optional, deprecated)
        if contact_uuid := params.get("contact"):
            if contact := org.contacts.filter(is_active=True, uuid=contact_uuid).first():
                queryset = queryset.filter(contact=contact)
            else:
                queryset = queryset.none()

        # limit to responded runs (optional)
        if str_to_bool(params.get("responded")):
            queryset = queryset.filter(responded=True)

        # use prefetch rather than select_related for foreign keys to avoid joins
        queryset = queryset.prefetch_related(
            Prefetch("flow", queryset=Flow.objects.only("uuid", "name", "base_language")),
            Prefetch("contact", queryset=Contact.objects.only("uuid", "name", "language", "org")),
            Prefetch("contact__org"),
            Prefetch("start", queryset=FlowStart.objects.only("uuid")),
        )

        return self.filter_before_after(queryset, "modified_on")

    def prepare_for_serialization(self, object_list, using: str):
        Contact.bulk_urn_cache_initialize([r.contact for r in object_list], using=using)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["include_paths"] = str_to_bool(self.request.query_params.get("paths", "true"))
        return context

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Flow Runs",
            "url": reverse("api.v2.runs"),
            "slug": "run-list",
            "params": [
                {"name": "uuid", "required": False, "help": "A run UUID to filter by"},
                {
                    "name": "flow",
                    "required": False,
                    "help": "A flow UUID to filter by, ex: f5901b62-ba76-4003-9c62-72fdacc1b7b7",
                },
                {"name": "responded", "required": False, "help": "Whether to only return runs with contact responses"},
                {
                    "name": "before",
                    "required": False,
                    "help": "Only return runs modified before this date, ex: 2015-01-28T18:00:00.000",
                },
                {
                    "name": "after",
                    "required": False,
                    "help": "Only return runs modified after this date, ex: 2015-01-28T18:00:00.000",
                },
            ],
            "example": {"query": "after=2016-01-01T00:00:00.000"},
        }


class FlowStartsEndpoint(ListAPIMixin, WriteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list manual flow starts in your account, and add or start contacts in a flow.

    ## Listing Flow Starts

    By making a `GET` request you can list all the manual flow starts on your organization, in the order of last
    modified. Each flow start has the following attributes:

     * **uuid** - the UUID of this flow start (string), filterable as `uuid`.
     * **flow** - the flow which was started (object).
     * **contacts** - the list of contacts that were started in the flow (objects).
     * **groups** - the list of groups that were started in the flow (objects).
     * **status** - the status, one of `pending`, `queued`, `started`, `completed`, `failed`, `interrupted`.
     * **params** - the dictionary of extra parameters passed to the flow start (object).
     * **created_on** - the datetime when this flow start was created (datetime).
     * **modified_on** - the datetime when this flow start was modified (datetime).

    Example:

        GET /api/v2/flow_starts.json

    Response is the list of flow starts on your organization, most recently modified first:

        {
            "next": "http://example.com/api/v2/flow_starts.json?cursor=cD0yMDE1LTExLTExKzExJTNBM40NjQlMkIwMCUzRv",
            "previous": null,
            "results": [
                {
                    "uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
                    "flow": {"uuid": "f5901b62-ba76-4003-9c62-72fdacc1b7b7", "name": "Thrift Shop"},
                    "groups": [
                         {"uuid": "f5901b62-ba76-4003-9c62-72fdacc1b7b7", "name": "Ryan & Macklemore"}
                    ],
                    "contacts": [
                         {"uuid": "f5901b62-ba76-4003-9c62-fjjajdsi15553", "name": "Wanz"}
                    ],
                    "status": "complete",
                    "params": {
                        "first_name": "Ryan",
                        "last_name": "Lewis"
                    },
                    "created_on": "2013-08-19T19:11:21.082Z",
                    "modified_on": "2013-08-19T19:11:21.082Z"
                },
                ...
            ]
        }

    ## Starting contacts down a flow

    By making a `POST` request with the contacts, groups and URNs you want to start down a flow you can trigger a flow
    start. Note that that contacts will be added to the flow asynchronously, you can use the runs endpoint to monitor the
    runs created by this start.

     * **flow** - the UUID of the flow to start contacts in (required)
     * **groups** - the UUIDs of the groups you want to start in this flow (array of up to 100 strings, optional)
     * **contacts** - the UUIDs of the contacts you want to start in this flow (array of up to 100 strings, optional)
     * **urns** - the URNs you want to start in this flow (array of up to 100 strings, optional)
     * **restart_participants** - whether to restart participants already in this flow (optional, defaults to true)
     * **exclude_active** - whether to exclude contacts currently in other flow (optional, defaults to false)
     * **params** - extra parameters to pass to the flow start (object, must be at most 10K characters, accessible via `@trigger.params` in the flow)

    Example:

        POST /api/v2/flow_starts.json
        {
            "flow": "f5901b62-ba76-4003-9c62-72fdacc1b7b7",
            "groups": ["f5901b62-ba76-4003-9c62-72fdacc15515"],
            "contacts": ["f5901b62-ba76-4003-9c62-fjjajdsi15553"],
            "urns": ["twitter:sirmixalot", "tel:+12065551212"],
            "params": {"first_name": "Ryan", "last_name": "Lewis"}
        }

    Response is the created flow start:

        {
            "uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
            "flow": {"uuid": "f5901b62-ba76-4003-9c62-72fdacc1b7b7", "name": "Thrift Shop"},
            "groups": [
                 {"uuid": "c24813d2-3bc7-4467-8916-255b6525c6be", "name": "Ryan & Macklemore"}
            ],
            "contacts": [
                 {"uuid": "f1ea776e-c923-4c1a-b3a3-0c466932b2cc", "name": "Wanz"}
            ],
            "status": "pending",
            "params": {
                "first_name": "Ryan",
                "last_name": "Lewis"
            },
            "created_on": "2013-08-19T19:11:21.082Z",
            "modified_on": "2013-08-19T19:11:21.082Z"
        }

    """

    model = FlowStart
    serializer_class = FlowStartReadSerializer
    write_serializer_class = FlowStartWriteSerializer
    pagination_class = ModifiedOnCursorPagination

    def filter_queryset(self, queryset):
        # ignore flow starts created by flows or triggers
        queryset = queryset.exclude(created_by=None)

        # filter by UUID (optional)
        if uuid := self.get_uuid_param("uuid"):
            queryset = queryset.filter(uuid=uuid)

        # use prefetch rather than select_related for foreign keys to avoid joins
        queryset = queryset.prefetch_related(
            Prefetch("flow", queryset=Flow.objects.only("uuid", "name")),
            Prefetch("contacts", queryset=Contact.objects.only("uuid", "name").order_by("id")),
            Prefetch("groups", queryset=ContactGroup.objects.only("uuid", "name").order_by("id")),
        )

        return self.filter_before_after(queryset, "modified_on")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["is_zapier"] = "Zapier" in self.request.META.get("HTTP_USER_AGENT", "")
        return context

    def prepare_for_serialization(self, object_list, using: str):
        FlowStartCount.bulk_annotate(object_list)

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Flow Starts",
            "url": reverse("api.v2.flow_starts"),
            "slug": "flow-start-list",
            "params": [
                {"name": "id", "required": False, "help": "Only return the flow start with this id"},
                {"name": "after", "required": False, "help": "Only return flow starts modified after this date"},
                {"name": "before", "required": False, "help": "Only return flow starts modified before this date"},
            ],
            "example": {"query": "after=2016-01-01T00:00:00.000"},
        }

    @classmethod
    def get_write_explorer(cls):
        return dict(
            method="POST",
            title="Start Contacts in a Flow",
            url=reverse("api.v2.flow_starts"),
            slug="flow-start-write",
            fields=[
                dict(name="flow", required=True, help="The UUID of the flow to start"),
                dict(name="groups", required=False, help="The UUIDs of any contact groups you want to start"),
                dict(name="contacts", required=False, help="The UUIDs of any contacts you want to start"),
                dict(name="urns", required=False, help="The URNS of any contacts you want to start"),
                dict(
                    name="restart_participants",
                    required=False,
                    help="Whether to restart any participants already in the flow",
                ),
                dict(
                    name="params",
                    required=False,
                    help=_("Extra parameters that will be accessible in the flow"),
                ),
            ],
            example=dict(body='{"flow":"f5901b62-ba76-4003-9c62-72fdacc1b7b7","urns":["twitter:sirmixalot"]}'),
        )


class TicketsEndpoint(ListAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list the tickets opened on your account.

    ## Listing Tickets

    A **GET** returns the tickets for your organization, most recent first.

     * **uuid** - the UUID of the ticket, filterable as `uuid`.
     * **contact** - the UUID and name of the contact (object), filterable as `contact` with UUID.
     * **status** - the status of the ticket, either `open` or `closed`.
     * **topic** - the topic of the ticket (object).
     * **assignee** - the user assigned to the ticket (object).
     * **opened_on** - when this ticket was opened (datetime).
     * **opened_by** - the user who opened the ticket (object).
     * **opened_in** - the flow which opened the ticket (object).
     * **modified_on** - when this ticket was last modified (datetime).
     * **closed_on** - when this ticket was closed (datetime).

    Example:

        GET /api/v2/tickets.json

    Response:

        {
            "next": null,
            "previous": null,
            "results": [
            {
                "uuid": "9a8b001e-a913-486c-80f4-1356e23f582e",
                "contact": {"uuid": "f1ea776e-c923-4c1a-b3a3-0c466932b2cc", "name": "Jim"},
                "status": "open",
                "topic": {"uuid": "040edbfe-be55-48f3-864d-a4a7147c447b", "name": "Support"},
                "assignee": {"email": "bob@flow.com", "name": "Bob McFlow"},
                "opened_on": "2013-02-27T09:06:15.456",
                "opened_by": null,
                "opened_in": {"uuid": "54cd8e2c-6334-49a4-abf9-f0fa8d0971da", "name": "Support Flow"},
                "modified_on": "2013-02-27T09:07:18.234",
                "closed_on": null
            },
            ...
    """

    model = Ticket
    serializer_class = TicketReadSerializer
    pagination_class = ModifiedOnCursorPagination

    def filter_queryset(self, queryset):
        params = self.request.query_params
        org = self.request.org

        queryset = queryset.filter(org=org)

        # filter by contact (optional)
        contact_uuid = params.get("contact")
        if contact_uuid:
            contact = org.contacts.filter(is_active=True, uuid=contact_uuid).first()
            if contact:
                queryset = queryset.filter(contact=contact)
            else:
                queryset = queryset.filter(id=-1)

        uuid = params.get("uuid") or params.get("ticket")
        if uuid:
            queryset = queryset.filter(uuid=uuid)

        queryset = queryset.prefetch_related(
            Prefetch("topic", queryset=Topic.objects.only("uuid", "name")),
            Prefetch("contact", queryset=Contact.objects.only("uuid", "name")),
            Prefetch("assignee", queryset=User.objects.only("email", "first_name", "last_name")),
            Prefetch("opened_by", queryset=User.objects.only("email", "first_name", "last_name")),
            Prefetch("opened_in", queryset=Flow.objects.only("uuid", "name")),
        )

        return queryset

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Tickets",
            "url": reverse("api.v2.tickets"),
            "slug": "ticket-list",
            "params": [
                {
                    "name": "contact",
                    "required": False,
                    "help": "A contact UUID to filter by, ex: 09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
                },
            ],
        }


class TicketActionsEndpoint(BulkWriteAPIMixin, BaseEndpoint):
    """
    ## Bulk Ticket Updating

    A **POST** can be used to perform an action on a set of tickets in bulk.

    * **tickets** - the ticket UUIDs (array of up to 100 strings).
    * **action** - the action to perform, a string one of:

        * `assign` - assign the tickets to the given user.
        * `note` - add the given note to the tickets.
        * `close` - close the tickets.
        * `reopen` - re-open the tickets.

    * **assignee** - the email of a user (string, optional).
    * **note** - the note to add to the tickets (string, optional).

    Example:

        POST /api/v2/ticket_actions.json
        {
            "tickets": ["55b6606d-9e89-45d1-a3e2-dc11f19f78df", "bef96b71-865d-480a-a660-33db466a210a"],
            "action": "assign",
            "assignee": "jim@textit.com"
        }

    You will receive an empty response with status code 204 if successful.
    """

    permission = "tickets.ticket_update"
    serializer_class = TicketBulkActionSerializer

    @classmethod
    def get_write_explorer(cls):
        actions = cls.serializer_class.ACTION_CHOICES
        return {
            "method": "POST",
            "title": "Update Multiple Tickets",
            "url": reverse("api.v2.ticket_actions"),
            "slug": "ticket-actions",
            "fields": [
                {"name": "tickets", "required": True, "help": "The UUIDs of the tickets to update"},
                {"name": "action", "required": True, "help": "One of the following strings: " + ", ".join(actions)},
                {"name": "assignee", "required": False, "help": "The email address of a user"},
                {"name": "note", "required": False, "help": "The note text"},
            ],
        }


class TopicsEndpoint(ListAPIMixin, WriteAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list the topics in your workspace.

    ## Listing Topics

    A **GET** returns the topics for your organization, most recent first.

     * **uuid** - the UUID of the topic (string).
     * **name** - the name of the topic (string).
     * **counts** - the counts of open and closed tickets with this topic (object).
     * **system** - whether this is a system topic that can't be modified (bool).
     * **created_on** - when this topic was created (datetime).

    Example:

        GET /api/v2/topics.json

    Response:

        {
            "next": null,
            "previous": null,
            "results": [
            {
                "uuid": "9a8b001e-a913-486c-80f4-1356e23f582e",
                "name": "Support",
                "counts": {"open": 12, "closed": 345},
                "system": false,
                "created_on": "2013-02-27T09:06:15.456"
            },
            ...

    ## Adding o New Topic

    By making a `POST` request with a unique name you can create a new topic.

     * **name** - the name of the topic to create (string)

    Example:

        POST /api/v2/topics.json
        {
            "name": "Complaints"
        }
    """

    model = Topic
    serializer_class = TopicReadSerializer
    write_serializer_class = TopicWriteSerializer
    pagination_class = CreatedOnCursorPagination

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def prepare_for_serialization(self, object_list, using: str):
        open_counts = Ticket.get_topic_counts(self.request.org, object_list, Ticket.STATUS_OPEN)
        closed_counts = Ticket.get_topic_counts(self.request.org, object_list, Ticket.STATUS_CLOSED)
        for topic in object_list:
            topic.open_count = open_counts[topic]
            topic.closed_count = closed_counts[topic]

    @classmethod
    def get_read_explorer(cls):
        return {"method": "GET", "title": "List Topics", "url": reverse("api.v2.topics"), "slug": "topic-list"}

    @classmethod
    def get_write_explorer(cls):
        return {
            "method": "POST",
            "title": "Add or Update Topics",
            "url": reverse("api.v2.topics"),
            "slug": "topic-write",
            "params": [{"name": "uuid", "required": False, "help": "The UUID of the topic to update"}],
            "fields": [{"name": "name", "required": True, "help": "The name of the topic"}],
        }


class UsersEndpoint(ListAPIMixin, BaseEndpoint):
    """
    This endpoint allows you to list the user logins in your workspace.

    ## Listing Users

    A **GET** returns the users in your workspace, ordered by newest created first.

     * **uuid** - the UUID of the user (string), filterable as `uuid`.
     * **email** - the email address of the user (string).
     * **first_name** - the first name of the user (string).
     * **last_name** - the last name of the user (string).
     * **role** - the role of the user (string).
     * **team** - team user belongs to (object).
     * **created_on** - when this user was created (datetime).

    Example:

        GET /api/v2/users.json

    Response:

        {
            "next": null,
            "previous": null,
            "results": [
            {
                "avatar": "https://..."
                "email": "bob@flow.com",
                "first_name": "Bob",
                "last_name": "McFlow",
                "role": "agent",
                "team": {"uuid": "f5901b62-ba76-4003-9c62-72fdacc1b7b7", "name": "All Topics"},
                "created_on": "2013-03-02T17:28:12.123456Z"
            },
            ...
    """

    model = User
    serializer_class = UserReadSerializer
    pagination_class = DateJoinedCursorPagination

    def derive_queryset(self):
        org = self.request.org

        # limit to roles if specified
        roles = self.request.query_params.getlist("role")
        if roles:
            role_by_name = {name: role for role, name in UserReadSerializer.ROLES.items()}
            roles = [role_by_name.get(r) for r in roles if r in role_by_name]
        else:
            roles = None

        return org.get_users(roles=roles)

    def filter_queryset(self, queryset):
        # filter by UUID if specified
        if uuids := self.get_uuid_param("uuid", list=True):
            queryset = queryset.filter(uuid__in=uuids)

        # filter by email (undocumented)
        if emails := self.request.query_params.getlist("email"):
            queryset = queryset.filter(or_list([Q(email__iexact=e) for e in emails]))

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()

        # build a map of users to memberships
        memberships = {}
        for m in OrgMembership.objects.filter(org=self.request.org).select_related("user", "team"):
            memberships[m.user] = m

        context["memberships"] = memberships
        return context

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Users",
            "url": reverse("api.v2.users"),
            "slug": "user-list",
            "params": [
                {"name": "email", "required": False, "help": "Only return users with this email"},
                {"name": "role", "required": False, "help": "Only return users with this role"},
            ],
        }


class WorkspaceEndpoint(BaseEndpoint):
    """
    This endpoint allows you to view details about your workspace.

    ## Viewing Current Workspace

    A **GET** returns the details of your workspace. There are no parameters.

    Example:

        GET /api/v2/workspace.json

    Response containing your workspace details:

        {
            "uuid": "6a44ca78-a4c2-4862-a7d3-2932f9b3a7c3",
            "name": "TextIt",
            "country": "RW",
            "languages": ["eng", "fra"],
            "timezone": "Africa/Kigali",
            "date_style": "day_first",
            "anon": false
        }
    """

    permission = "orgs.org_read"

    def get(self, request, *args, **kwargs):
        serializer = WorkspaceReadSerializer(request.org)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "View Workspace",
            "url": reverse("api.v2.workspace"),
            "slug": "workspace-read",
        }
