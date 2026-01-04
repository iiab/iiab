from django import template
from django.urls import reverse
from django.conf import settings
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.simple_tag
def get_urls():
    urls = {
        "root": getattr(settings, "FORCE_SCRIPT_NAME", "/"),
        "api_internal_notifications": reverse("api.internal.notifications"),
        "api_internal_orgs": reverse("api.internal.orgs"),
        
        # API v2 (for frontend fetch calls & frame.html attributes)
        "api_v2_campaigns": reverse("api.v2.campaigns"),
        "api_v2_campaign_events": reverse("api.v2.campaign_events"),
        "api_v2_contacts": reverse("api.v2.contacts"),
        "api_v2_fields": reverse("api.v2.fields"),
        "api_v2_globals": reverse("api.v2.globals"),
        "api_v2_groups": reverse("api.v2.groups"),
        "api_v2_users": reverse("api.v2.users"),
        "api_v2_workspace": reverse("api.v2.workspace"),
        "api_internal_shortcuts": reverse("api.internal.shortcuts"),
        
        # Orgs
        "orgs_org_workspace": reverse("orgs.org_workspace"),
        "orgs_org_choose": reverse("orgs.org_choose"),
        "orgs_org_create": reverse("orgs.org_create"),
        "orgs_org_list": reverse("orgs.org_list"),
        "orgs_user_list": reverse("orgs.user_list"),
        "orgs_invitation_list": reverse("orgs.invitation_list"),
        "orgs_invitation_create": reverse("orgs.invitation_create"),
        "orgs_invitation_delete": reverse("orgs.invitation_delete", args=[0]).replace("/0/", "/%s/"),
        "orgs_org_languages": reverse("orgs.org_languages"),
        "orgs_org_menu": reverse("orgs.org_menu"),
        
        # Staff
        "staff_org_list": reverse("staff.org_list"),
        "staff_org_service": reverse("staff.org_service"),
        "staff_user_list": reverse("staff.user_list"),
        
        # Contacts
        "contacts_contact_list": reverse("contacts.contact_list"),
        "contacts_contact_create": reverse("contacts.contact_create"),
        "contacts_contactgroup_create": reverse("contacts.contactgroup_create"),
        "contacts_contactfield_list": reverse("contacts.contactfield_list"),
        
        # Messages
        "msgs_msg_inbox": reverse("msgs.msg_inbox"),
        "msgs_broadcast_list": reverse("msgs.broadcast_list"),
        "msgs_broadcast_create": reverse("msgs.broadcast_create"),
        "msgs_label_create": reverse("msgs.label_create"),
        
        # Flows
        "flows_flow_list": reverse("flows.flow_list"),
        "flows_flowlabel_create": reverse("flows.flowlabel_create"),
        
        # Triggers
        "triggers_trigger_list": reverse("triggers.trigger_list"),
        "triggers_trigger_menu": reverse("triggers.trigger_menu"),
        "triggers_trigger_create": reverse("triggers.trigger_create_keyword"), # Default to keyword
        
        # Tickets
        "tickets_ticket_list": reverse("tickets.ticket_list"),
        "tickets_ticket_menu": reverse("tickets.ticket_menu"),
        
        # Flows
        "flows_flow_list": reverse("flows.flow_list"),
        "flows_flow_menu": reverse("flows.flow_menu"),
        
        # Tickets
        "tickets_ticket_list": reverse("tickets.ticket_list"),
        # tickets.ticket_folder requires 2 args (folder, status). Replaced with %s for JS.
        "tickets_ticket_folder": reverse("tickets.ticket_folder", args=["mine", "open"]).replace("mine", "%s").replace("open", "%s"),
        
        # Campaigns
        "campaigns_campaign_list": reverse("campaigns.campaign_list"),
        
        # Public
        "public_public_index": reverse("public.public_index"),
        
        # Django I18n
        "django_js_cat": reverse("django.views.i18n.javascript_catalog"),
    }
    # Prepend subpath to all URLs
    subpath = getattr(settings, "FORCE_SCRIPT_NAME", "")
    if subpath and subpath != "/":
        if subpath.endswith("/"):
            subpath = subpath[:-1]
        for k, v in urls.items():
            if isinstance(v, str) and v.startswith("/") and not v.startswith(subpath):
                urls[k] = subpath + v

    return mark_safe(json.dumps(urls))
