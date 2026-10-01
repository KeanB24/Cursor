# HSE Compliance API Endpoints

Base environment: `ct-test.hse-compliance.net`

## 1. Get Sites

Retrieves the available sites.

**Endpoint:**

```http
GET https://apigw.ct-test.hse-compliance.net/v2/secure-clients/legapi-general/sites
```

[Open endpoint](https://apigw.ct-test.hse-compliance.net/v2/secure-clients/legapi-general/sites)

---

## 2. Get List of Users by Site

Retrieves the users associated with a site.

The number at the end of the URL is the **site ID**.

**Example endpoint using site ID `112087`:**

```http
GET https://apigw.ct-test.hse-compliance.net/v2/secure-clients/legapi-general/users/sites/112087
```

[Open endpoint](https://apigw.ct-test.hse-compliance.net/v2/secure-clients/legapi-general/users/sites/112087)

**Template:**

```text
https://apigw.ct-test.hse-compliance.net/v2/secure-clients/legapi-general/users/sites/{site_id}
```

---

## 3. Get Mapping Reference Labels

Retrieves mapping reference labels for a specified user.

The `user_id` query parameter is the **user ID**.

**Example endpoint using user ID `156028`:**

```http
GET https://apigw.ct-test.hse-compliance.net/v2/secure-clients/tasks/configs/references?user_id=156028
```

[Open endpoint](https://apigw.ct-test.hse-compliance.net/v2/secure-clients/tasks/configs/references?user_id=156028)

**Template:**

```text
https://apigw.ct-test.hse-compliance.net/v2/secure-clients/tasks/configs/references?user_id={user_id}
```

---

## 4. Get Tasks by User

Retrieves tasks for a specified user.

The `user_id` query parameter is the **user ID**.

**Example endpoint using user ID `584646`:**

```http
GET https://apigw.ct-test.hse-compliance.net/v2/secure-clients/tasks?user_id=584646
```

[Open endpoint](https://apigw.ct-test.hse-compliance.net/v2/secure-clients/tasks?user_id=584646)

**Template:**

```text
https://apigw.ct-test.hse-compliance.net/v2/secure-clients/tasks?user_id={user_id}
```
