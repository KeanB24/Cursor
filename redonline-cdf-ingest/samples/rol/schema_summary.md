# ROL API schema discovery

Generated: `2026-10-04T14:42:41.009291+00:00`
Base URL: `https://apigw.ct-test.hse-compliance.net`
TLS verify: `True`

## `list_sites`

- URL: `https://apigw.ct-test.hse-compliance.net/v2/secure-clients/legapi-general/sites`
- Raw: `samples\rol\list_sites_raw.json`
- Items: 61
- Suggested items_path: `sites`
- Suggested id field: `id_site`

| Field | Types |
|-------|-------|
| `code_iso` | string |
| `country_name` | string |
| `id_country` | int, null |
| `id_parent` | int, null |
| `id_ref_status` | int |
| `id_site` | int |
| `id_site_type` | int |
| `name` | string |

## `list_users_by_site`

- URL: `https://apigw.ct-test.hse-compliance.net/v2/secure-clients/legapi-general/users/sites/112087`
- Raw: `samples\rol\list_users_by_site_raw.json`
- Items: 100
- Suggested items_path: `users`
- Suggested id field: `id_user`

| Field | Types |
|-------|-------|
| `email` | string |
| `firstname` | string |
| `id_client` | int |
| `id_langue` | int |
| `id_ref_status` | int |
| `id_user` | int |
| `language` | string |
| `lastname` | string |
| `locale` | string |
| `profiles` | array |
| `profiles[].id_profile` | int |
| `profiles[].name` | string |
| `user_name` | string |

## `list_mapping_references`

- URL: `https://apigw.ct-test.hse-compliance.net/v2/secure-clients/tasks/configs/references`
- Raw: `samples\rol\list_mapping_references_raw.json`
- Items: 1
- Suggested items_path: `None`
- Suggested id field: `success`

| Field | Types |
|-------|-------|
| `data` | object |
| `data.accepted_mime_types` | array |
| `data.applicability` | array |
| `data.applicability[].label` | string |
| `data.applicability[].value` | int |
| `data.authorized_html_tags` | array |
| `data.categories` | array |
| `data.categories[].label` | string |
| `data.categories[].value` | int |
| `data.dashboard_templates` | array |
| `data.dashboard_templates[].is_active` | bool |
| `data.dashboard_templates[].is_default` | bool |
| `data.dashboard_templates[].label` | string |
| `data.dashboard_templates[].value` | int |
| `data.dashboard_templates[].widgets` | array |
| `data.dashboard_templates[].widgets[].created_at` | string |
| `data.dashboard_templates[].widgets[].dashboard_template_id` | int |
| `data.dashboard_templates[].widgets[].default_config` | null |
| `data.dashboard_templates[].widgets[].default_order` | int |
| `data.dashboard_templates[].widgets[].id` | int |
| `data.dashboard_templates[].widgets[].label` | null |
| `data.dashboard_templates[].widgets[].updated_at` | null |
| `data.dashboard_templates[].widgets[].widget` | object |
| `data.dashboard_templates[].widgets[].widget.created_at` | string |
| `data.dashboard_templates[].widgets[].widget.dashboard_template_widgets` | array |
| `data.dashboard_templates[].widgets[].widget.dashboard_type_id` | int |
| `data.dashboard_templates[].widgets[].widget.default_config` | null |
| `data.dashboard_templates[].widgets[].widget.default_displayed` | bool |
| `data.dashboard_templates[].widgets[].widget.default_order` | int |
| `data.dashboard_templates[].widgets[].widget.id` | int |
| `data.dashboard_templates[].widgets[].widget.label` | string |
| `data.dashboard_templates[].widgets[].widget.updated_at` | string |
| `data.dashboard_templates[].widgets[].widget.widget_type` | object |
| `data.dashboard_templates[].widgets[].widget.widget_type.created_at` | string |
| `data.dashboard_templates[].widgets[].widget.widget_type.id` | int |
| `data.dashboard_templates[].widgets[].widget.widget_type.label` | string |
| `data.dashboard_templates[].widgets[].widget.widget_type.updated_at` | string |
| `data.dashboard_templates[].widgets[].widget.widget_type_id` | int |
| `data.dashboard_templates[].widgets[].widget_id` | int |
| `data.endless_recurring_max_count_rules` | object |
| `data.endless_recurring_max_count_rules.DAILY` | int |
| `data.endless_recurring_max_count_rules.MONTHLY` | int |
| `data.endless_recurring_max_count_rules.WEEKLY` | int |
| `data.endless_recurring_max_count_rules.YEARLY` | int |
| `data.max_attachment_size` | object |
| `data.max_attachment_size.size` | int |
| `data.max_attachment_size.unit` | string |
| `data.occurrence_statuses` | array |
| `data.occurrence_statuses[].label` | string |
| `data.occurrence_statuses[].next_status_ids` | array |
| `data.occurrence_statuses[].value` | int |
| `data.priorities` | array |
| `data.priorities[].label` | string |
| `data.priorities[].value` | int |
| `data.recurring_frequencies` | array |
| `data.recurring_frequencies[].label` | string |
| `data.recurring_frequencies[].value` | string |
| `data.reference_types` | array |
| `data.reference_types[].label` | string |
| `data.reference_types[].module_id` | null |
| `data.reference_types[].value` | int |
| `data.scopes` | array |
| `data.scopes[].label` | string |
| `data.scopes[].value` | int |
| `data.states` | array |
| `data.states[].label` | string |
| `data.states[].value` | int |
| `data.types` | array |
| `data.types[].label` | string |
| `data.types[].reference_type_id` | int |
| `data.types[].value` | int |
| `data.widget_types` | array |
| `data.widget_types[].label` | string |
| `data.widget_types[].value` | int |
| `debug` | object |
| `debug.body` | null |
| `debug.client` | object |
| `debug.client.city` | null |
| `debug.client.firstName` | null |
| `debug.client.id` | int |
| `debug.client.lastName` | null |
| `debug.client.mobile` | null |
| `debug.client.name` | string |
| `debug.client.phone` | null |
| `debug.context` | object |
| `debug.context.domainId` | null |
| `debug.context.perimeterConnectionId` | null |
| `debug.context.profileId` | int |
| `debug.context.selectedSiteId` | null |
| `debug.context.siteIdsList` | array |
| `debug.context.siteIdsListByCountryId` | null |
| `debug.context.spaceId` | null |
| `debug.context.ssoAllowed` | null |
| `debug.context.userId` | int |
| `debug.exceptions` | array |
| `debug.execution_time` | string |
| `debug.logs` | array |
| `debug.logs[].context` | string |
| `debug.logs[].method` | string |
| `debug.logs[].options` | object |
| `debug.logs[].options.http_errors` | bool |
| `debug.logs[].payload` | object |
| `debug.logs[].payload.data` | array |
| `debug.logs[].payload.data[].email` | string |
| `debug.logs[].payload.data[].firstname` | string |
| `debug.logs[].payload.data[].id_client` | int |
| `debug.logs[].payload.data[].id_langue` | int |
| `debug.logs[].payload.data[].id_ref_status` | int |
| `debug.logs[].payload.data[].id_user` | int |
| `debug.logs[].payload.data[].language` | string |
| `debug.logs[].payload.data[].lastname` | string |
| `debug.logs[].payload.data[].locale` | string |
| `debug.logs[].payload.data[].profiles` | array |
| `debug.logs[].payload.data[].profiles[].id_profile` | int |
| `debug.logs[].payload.data[].profiles[].name` | string |
| `debug.logs[].payload.data[].user_name` | string |
| `debug.logs[].request_time` | string |
| `debug.logs[].uri` | string |
| `debug.memory_usage` | string |
| `debug.method` | string |
| `debug.requests_nb` | int |
| `debug.url` | string |
| `debug.user` | object |
| `debug.user.clientId` | int |
| `debug.user.createdAt` | null |
| `debug.user.email` | string |
| `debug.user.firstName` | string |
| `debug.user.id` | int |
| `debug.user.iso6391` | null |
| `debug.user.lastName` | string |
| `debug.user.mobile` | null |
| `debug.user.phone` | null |
| `debug.user.profilesIds` | array |
| `debug.user.rightsPerProfile` | array |
| `debug.user.rightsPerProfile[].id_profile` | int |
| `debug.user.rightsPerProfile[].name` | string |
| `debug.user.sensitiveData` | null |
| `debug.user.updatedAt` | null |
| `message` | string |
| `success` | bool |

## `list_tasks_by_user`

- URL: `https://apigw.ct-test.hse-compliance.net/v2/secure-clients/tasks`
- Raw: `samples\rol\list_tasks_by_user_raw.json`
- Items: 10
- Suggested items_path: `data`
- Suggested id field: `id`

| Field | Types |
|-------|-------|
| `attachments` | array |
| `author_name` | string |
| `category` | int |
| `created_at` | string |
| `created_by` | int |
| `created_from` | string |
| `criticality` | int |
| `description` | string |
| `due_scheduled_at` | string |
| `id` | int |
| `instances` | array |
| `instances[].created_by` | int |
| `instances[].id` | int |
| `instances[].occurrences` | array |
| `instances[].occurrences[].attachments` | array |
| `instances[].occurrences[].completed_at` | null |
| `instances[].occurrences[].created_by` | int |
| `instances[].occurrences[].due_scheduled_at` | string |
| `instances[].occurrences[].feedbacks` | array |
| `instances[].occurrences[].id` | int |
| `instances[].occurrences[].instance_id` | int |
| `instances[].occurrences[].original_due_scheduled_at` | string |
| `instances[].occurrences[].status_id` | int |
| `instances[].occurrences[].temporal_criticality` | string |
| `instances[].occurrences[].updated_by` | null |
| `instances[].owners` | array |
| `instances[].owners[].can_access` | bool |
| `instances[].owners[].id` | int |
| `instances[].owners[].is_active` | bool |
| `instances[].owners[].user_id` | int |
| `instances[].owners[].user_name` | string |
| `instances[].reviewers` | array |
| `instances[].reviewers[].can_access` | bool |
| `instances[].reviewers[].id` | int |
| `instances[].reviewers[].is_active` | bool |
| `instances[].reviewers[].user_id` | int |
| `instances[].reviewers[].user_name` | string |
| `instances[].site` | object |
| `instances[].site.country_name` | string |
| `instances[].site.id_country` | int |
| `instances[].site.id_site` | int |
| `instances[].site.is_active` | bool |
| `instances[].site.name` | string |
| `instances[].state` | int |
| `instances[].temporal_criticality` | string |
| `instances[].updated_by` | null |
| `internal_code` | null |
| `perimeter_state` | int |
| `priority` | int |
| `recurring_count_rule` | null |
| `recurring_end_date_rule` | null |
| `recurring_frequency_rule` | string |
| `recurring_interval_rule` | int |
| `recurring_start_date_rule` | string |
| `references` | array |
| `references[].reference_type_id` | int |
| `references[].references_nb` | int |
| `references_nb` | int |
| `rescheduled_at` | null |
| `scope` | int |
| `state` | int |
| `temporal_criticality` | string |
| `title` | string |
| `type_id` | int |
| `updated_at` | string |
| `updated_by` | null |
| `updated_from` | null |
| `updater_name` | null |
