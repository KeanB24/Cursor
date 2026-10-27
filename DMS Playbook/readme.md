# Cognite DMS proficiency path

Practice path for the Cognite Data Fusion Data Modeling Service (DMS). Do the activities in order. The runnable version of each activity is in [dms-practice.ipynb](dms-practice.ipynb).

The notebook builds one small lab graph and then deletes it:

- a **pump** and a **valve** in an **area**
- the area link stored as a **direct relation**
- the flow from the pump to the valve stored as an **edge** that carries its own comment

Writes stay inside three spaces named from the `PREFIX` in the first code cell (`dms_lab` unless you change it): `{prefix}_schema`, `{prefix}_types`, and `{prefix}_data`.

Official concept index: [Data modeling concepts](https://docs.cognite.com/cdf/dm/dm_concepts).

## Before you start

1. Install the Cognite Python SDK (`cognite-sdk`) in the interpreter you use for Jupyter.
2. Put `CDF_PROJECT`, `CDF_CLUSTER`, `CDF_TENANT_ID`, `CDF_CLIENT_ID`, and `CDF_CLIENT_SECRET` in the environment, or in `redonline-cdf-ingest/.env`. The notebook loads that file when the variables are missing and does not print the secret.
3. Confirm the service principal can write schema and instances in the three lab spaces. The access-control activity shows how to read this off the token.
4. Run the notebook from top to bottom. Run the reset cell before a second full pass.

## 1. Property graph

A DMS graph is nodes, edges, and properties. Every instance is identified by `(space, externalId)`.

Activities:

1. Name the lab nodes: area `area-1`, pump `pump-42`, valve `valve-1`.
2. Mark the area link as a direct relation and the flow as an edge.
3. State which link can carry a comment and be walked backwards (the flow edge).

Reference: [Spaces, instances, direct relations](https://docs.cognite.com/cdf/dm/dm_concepts/dm_spaces_instances).

## 2. Spaces

A space is the namespace and the access-control boundary. Schema, type nodes, and instance data belong in different spaces.

Activities:

1. Create `{prefix}_schema` for containers, views, and the data model.
2. Create `{prefix}_types` for the type nodes `area`, `pump`, `valve`, and `flows-to`.
3. Create `{prefix}_data` for the pump, valve, area, and flow instances.
4. List the three spaces back and read their names.

## 3. Containers

Containers are the physical property storage. You query through views, and you still have to design containers: types, nullability, indexes, and constraints.

Activities:

1. Create `Area` (`name` text) and `Equipment` (`manufacturer` text, `area` direct relation into `Area`) with `usedFor: node`.
2. Add a cursorable btree index on `manufacturer`, and a btree index on `area`.
3. Create `Pump` (`maxPressure` float64) with a `requires` constraint on `Equipment`.
4. Create `Flow` (`comment` text) with `usedFor: edge`.
5. Set `maxTextSize` on every indexed text property so the btree index is allowed to build.

Reference: [Containers, views, polymorphism, data models](https://docs.cognite.com/cdf/dm/dm_concepts/dm_containers_views_datamodels).

## 4. Views

Views are the versioned read/write contract. Map container properties into a view, and describe edges as connection properties.

Activities:

1. Map `Area.name` and `Equipment.manufacturer` into version `1` views.
2. Map `Equipment.area` and set its source view to `Area`, so the direct relation has a target type.
3. Create `Pump` version `1` that implements `Equipment`, maps `maxPressure`, and declares an outwards `flowsTo` edge connection of type `flows-to`.
4. Create `Flow` version `1` so the edge comment is written through a view.
5. Retrieve `Pump` and read the implemented views plus the effective properties.

## 5. Data models

A data model groups the views an application consumes, and it has its own version.

Activities:

1. Create `EquipmentLab` version `1` in the schema space containing `Area`, `Equipment`, `Pump`, and `Flow`.
2. Retrieve that model and list the view identifiers it exposes.

## 6. System schemas

CDF ships global schemas in spaces whose names start with `cdf_`. Extend those when the concept already exists (asset, file, time series reference).

Activities:

1. List spaces and data models with `include_global=True`.
2. Open one global data model, usually `cdf_cdm` / `CogniteCore`, and list its views.
3. Find a view whose name contains `Asset` and read its property identifiers.
4. Decide, in a sentence you can say out loud, whether the lab pump should have been a new container or an extension of that asset view. The lab uses a new container so the exercise stays isolated.

## 7. Nodes

Instances are written with apply and read back through a view.

Activities:

1. Apply the four type nodes in the types space.
2. Apply `area-1`, `valve-1`, and `pump-42` in the data space, with properties written through `Area`, `Equipment`, and `Pump`.
3. Retrieve `pump-42` through the `Pump` view and read `version`, `manufacturer`, and `maxPressure`.
4. List nodes in the data space filtered to `manufacturer = Acme`.

## 8. Direct relations and edges

Use a direct relation for a foreign key. Use an edge when the link has its own properties or you must traverse it in either direction.

Activities:

1. Point `pump-42` and `valve-1` at `area-1` with the `area` direct relation. Send `auto_create_direct_relations=False` so a missing target fails.
2. Apply the edge `pump-42-to-valve-1` from the pump to the valve, type `(types space, flows-to)`, with comment `Directs liquid to valve 1` written through the `Flow` view.
3. Retrieve the edge and read `start_node`, `end_node`, `type`, and `comment`.

## 9. Apply, merge, replace, and delete

`instances.apply(..., replace=False)` merges properties and is the property patch. `replace=True` replaces the property set you send for that view. Each real change increments `version`. A type node cannot be deleted while an instance still points at it. Deleting a node also deletes its edges.

Activities:

1. Merge a new `maxPressure` on `pump-42` and confirm `manufacturer` is still present and `version` increased.
2. Replace the full `Pump` property set with a new manufacturer and confirm `version` increased again.
3. Apply a scratch node, delete it, and retrieve it to confirm it is gone.

## 10. Query

Filters select instances. A query chains result sets, accepts parameters, and traverses edges. `hasData` is the default view filter when you do not set one: a node matches when it has data in the containers that view maps.

Activities:

1. Build a query parameter `maker` and return pumps whose manufacturer equals that parameter.
2. From those pumps, traverse outwards edges of type `flows-to` and return the valve at the end.
3. Select `manufacturer` and `maxPressure` on the pump, and `manufacturer` on the valve.

Reference: [Query features](https://docs.cognite.com/cdf/dm/dm_concepts/dm_querying).

## 11. Search and aggregation

Search matches text properties. Aggregation counts and summarizes, including by group.

Activities:

1. Search the `Equipment` view for `Acme` in `manufacturer`, limited to the data space.
2. Count equipment nodes grouped by `manufacturer`.
3. Average `maxPressure` on the `Pump` view.

## 12. Access control, inspection, and reset

Spaces are governed with `dataModelsAcl` (schema) and `dataModelInstancesAcl` (nodes and edges). Index and constraint creation finishes in the background; the container read model exposes `pending`, `current`, or `failed`.

Activities:

1. Inspect the token and write down the actions and space scope for `dataModelsAcl` and `dataModelInstancesAcl`.
2. Retrieve the `Equipment` container and read the btree index state.
3. Retrieve the `Pump` container and read the `requires` constraint state.
4. Inspect instance `pump-42` and list the views and containers that hold its data.
5. Delete the lab in this order, then run the notebook again:
   1. Edges and nodes in `{prefix}_data`.
   2. Type nodes in `{prefix}_types`.
   3. Data model, then views `Pump`, `Flow`, `Equipment`, `Area`, then containers in that same order.
   4. The three spaces.

## Done when

You can create the schema space, write the pump through a view, connect it with one direct relation and one edge, query across that edge, and delete the lab without leaving a container behind.
