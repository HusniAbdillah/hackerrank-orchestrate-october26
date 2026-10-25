"""Literal catalog aliases joined to original document/listing observations."""
import re
from dataclasses import replace

from .observations import identifiers


def enrich_artifacts(store):
    existing = {o.observation_id for o in store.observations}
    contexts = [o for o in store.observations if o.collection in {"pdf_text", "ocr_text"}]
    extra = []
    for link in store.observations:
        if link.fields.get("event_type") != "LINK_RESOURCE_IDENTITY" or not link.resource_id:
            continue
        details = link.fields.get("details", "")
        match = re.search(r"\(([^()]+)\)", details)
        if not match:
            continue
        alias = match[1]
        sole_attachment = (link.system_id == "object_storage" and
            "Attachment catalog confirmed" in details and "belongs only to" in details and
            "no other subject is linked" in details)
        for source in contexts:
            text = source.fields.get("text", "")
            if not re.search(r"(?<![\w])" + re.escape(alias) + r"(?![\w])", text):
                continue
            category = None
            if (sole_attachment and source.collection == "ocr_text" and
                all(label in text for label in ("Object Storage", "support-attachments", "Version", "Size", "application/pdf"))):
                category = "SUPPORT_ATTACHMENT"
            elif (link.system_id == "export_service" and source.collection == "pdf_text" and
                  "CUSTOMER STATEMENT" in text and "Statement " + alias in text):
                # Unlike a filename, a statement must also expose the same exact
                # subject identifier. Names, order IDs and timing alone do not join.
                subject = {token for token in identifiers(text) if token[0] in {"email", "user_id"}}
                linked = set(link.identifiers)
                if subject and subject <= linked:
                    category = "USER_EXPORT"
            if category is None or source.observed_at is None:
                continue
            oid = source.observation_id + ":catalog:" + link.source_id
            if oid in existing:
                continue
            fields = {"asset_reference": alias, "source_text": text}
            if category == "SUPPORT_ATTACHMENT":
                fields["shared_attachment"] = False
            extra.append(replace(source, observation_id=oid, system_id=link.system_id,
                resource_id=link.resource_id, category=category, kind="direct", fields=fields,
                # Availability of the conjunction, not a backdated catalog link.
                captured_at=max(source.captured_at, link.captured_at, link.observed_at),
                identifiers=link.identifiers, scope={**source.scope, "extraction": "literal_catalog_artifact",
                    "original_file_captured_at": source.captured_at.isoformat(),
                    "catalog_link_id": link.source_id, "alias": alias},
                provenance={**source.provenance, "catalog_link": link.to_dict()}))
            existing.add(oid)
    store.add(extra)
    return [o.observation_id for o in extra]
