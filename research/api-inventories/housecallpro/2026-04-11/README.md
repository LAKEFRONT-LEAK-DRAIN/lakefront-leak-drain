# Housecall Pro API Inventory (2026-04-11)

This folder contains crawl outputs and normalized inventories captured from Housecall Pro Stoplight docs on 2026-04-11.

## Recommended Reuse

- Use `*_operations.json` for feature planning and endpoint mapping.
- Use `*_models.txt` for payload/schema design references.
- Use `*_nodes.json` for full source-of-truth node metadata.
- Use `*_fullcontent_nodes.json` for node metadata plus snapshot payloads (`data` and `spec`) for offline reference.
- Keep `*_raw.html` and bundle files for reproducibility/debugging.

## Key Files

- `hcp_housecall-public-api_operations.json`: Public API operations list.
- `hcp_partner-jobs_operations.json`: Partner Jobs operations list.
- `hcp_terms_nodes.json`: Terms project nodes.
- `hcp_housecall-public-api_nodes.json`: Full Public API node inventory.
- `hcp_partner-jobs_nodes.json`: Full Partner Jobs node inventory.
- `hcp_housecall-public-api_fullcontent_nodes.json`: Public API nodes including full snapshot payloads.
- `hcp_partner-jobs_fullcontent_nodes.json`: Partner Jobs nodes including full snapshot payloads.
- `hcp_terms_fullcontent_nodes.json`: Terms nodes including full snapshot payloads.

## Folder Convention For Future Captures

Store new captures as:

`research/api-inventories/<provider>/<YYYY-MM-DD>/`

Example:

`research/api-inventories/housecallpro/2026-05-01/`
