"""Buffer adapter for post_pins.py. Reuses Reel Studio's Buffer client (tools/upload_buffer.py).

config.json: pinterest.buffer_adapter = "buffer_adapter:schedule_pin", pinterest.adapter_path = this folder.
Signature expected by post_pins.py: (channel_id, text, image_url, link, when) -> post id.

STATUS: written but NOT yet tested against a live Pinterest channel (none is connected in Buffer yet).
Connect Pinterest at publish.buffer.com, then run `python tools/buffer_adapter.py check` and put the id in
config.json pinterest.channel_id. The Pinterest-specific `metadata` fields below follow Buffer's GraphQL schema
as understood; confirm them with one draft post before enabling autopilot.
Never posts anything unless post_pins.py calls schedule_pin (which needs a live book with amazon_url).
"""
import sys
from datetime import datetime
from pathlib import Path

REEL_TOOLS = Path("D:/Projects/reel-studio/tools")


def _buffer():
    sys.path.insert(0, str(REEL_TOOLS))
    import upload_buffer  # reads BUFFER_API_KEY from Reel Studio's .env
    return upload_buffer


def pinterest_channel():
    """The connected Pinterest channel, or None."""
    ub = _buffer()
    orgs = ub.gql("query { account { organizations { id } } }")["account"]["organizations"]
    q = "query($o: OrganizationId!) { channels(input: {organizationId: $o}) { id name service isDisconnected } }"
    for org in orgs:
        for c in ub.gql(q, {"o": org["id"]})["channels"]:
            if c["service"] == "pinterest" and not c["isDisconnected"]:
                return c
    return None


def schedule_pin(channel_id, text, image_url, link, when: datetime, draft: bool = False):
    if not channel_id:
        raise SystemExit("pinterest.channel_id is empty: connect Pinterest in Buffer first.")
    ub = _buffer()
    title, _, body = text.partition("\n\n")
    inp = {"channelId": channel_id, "text": body or title, "assets": [{"image": {"url": image_url}}],
           "schedulingType": "automatic", "needsApproval": False,
           "metadata": {"pinterest": {"title": title[:100], "url": link}}}
    if draft:
        inp.update({"mode": "addToQueue", "saveToDraft": True})
    else:
        when = when if when.tzinfo else when.replace(tzinfo=ub.IST)
        inp.update({"mode": "customScheduled", "dueAt": when.astimezone(ub.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")})
    res = ub.gql("""mutation($input: CreatePostInput!) { createPost(input: $input) {
                   ... on PostActionSuccess { post { id status dueAt } }
                   ... on MutationError { message } } }""", {"input": inp})["createPost"]
    if "post" not in res:
        raise SystemExit(f"Buffer refused the pin: {res.get('message')}")
    return res["post"]["id"]


if __name__ == "__main__":
    if sys.argv[1:] == ["check"]:
        c = pinterest_channel()
        print(f"Pinterest channel: {c['name']} ({c['id']})" if c else "No Pinterest channel connected in Buffer yet.")
    else:
        print(__doc__)
