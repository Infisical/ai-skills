# Projects and Identities

## Projects

Projects are containers for secrets, environments, and team members. Always use `/api/v1/projects` (not the deprecated `/api/v1/workspace`).

### List Projects

#### Endpoint

```
GET /api/v1/projects
```

#### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| offset | integer | 0 | - | Number of items to skip |
| limit | integer | 20 | 100 | Number of items to return |

#### Response

```json
{
  "projects": [
    {
      "id": "project-id-uuid",
      "name": "My Project",
      "slug": "my-project",
      "createdAt": "2026-04-01T10:00:00.000Z",
      "updatedAt": "2026-04-16T10:30:00.000Z",
      "version": 1
    }
  ],
  "total": 5
}
```

#### Example

```bash
curl -X GET 'https://us.infisical.com/api/v1/projects?offset=0&limit=20' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Project

#### Endpoint

```
GET /api/v1/projects/{projectId}
```

#### Response

```json
{
  "project": {
    "id": "project-id-uuid",
    "name": "My Project",
    "slug": "my-project",
    "createdAt": "2026-04-01T10:00:00.000Z",
    "updatedAt": "2026-04-16T10:30:00.000Z",
    "version": 1,
    "environments": [
      {
        "id": "env-id",
        "name": "Development",
        "slug": "dev",
        "version": 1
      },
      {
        "id": "env-id-2",
        "name": "Production",
        "slug": "prod",
        "version": 1
      }
    ]
  }
}
```

#### Example

```bash
curl -X GET 'https://us.infisical.com/api/v1/projects/abc123' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create Project

#### Endpoint

```
POST /api/v1/projects
```

#### Request Body

```json
{
  "name": "string",
  "slug": "string (optional)"
}
```

#### Response

Returns the created project object.

#### Example

```bash
curl -X POST 'https://us.infisical.com/api/v1/projects' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Project",
    "slug": "new-project"
  }'
```

### Update Project

#### Endpoint

```
PATCH /api/v1/projects/{projectId}
```

#### Request Body

```json
{
  "name": "string (optional)",
  "slug": "string (optional)"
}
```

#### Example

```bash
curl -X PATCH 'https://us.infisical.com/api/v1/projects/abc123' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Project Name"
  }'
```

### Delete Project

#### Endpoint

```
DELETE /api/v1/projects/{projectId}
```

#### Example

```bash
curl -X DELETE 'https://us.infisical.com/api/v1/projects/abc123' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Environments

Environments (dev, staging, prod) organize secrets by deployment target.

### List Project Environments

#### Endpoint

```
GET /api/v1/projects/{projectId}/environments
```

#### Response

```json
{
  "environments": [
    {
      "id": "env-id-uuid",
      "name": "Development",
      "slug": "dev",
      "version": 1
    },
    {
      "id": "env-id-2",
      "name": "Production",
      "slug": "prod",
      "version": 1
    }
  ]
}
```

#### Example

```bash
curl -X GET 'https://us.infisical.com/api/v1/projects/abc123/environments' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Project Members

Manage who has access to a project and their role.

### List Project Members

#### Endpoint

```
GET /api/v1/projects/{projectId}/memberships
```

#### Query Parameters

| Parameter | Type | Default | Max |
|-----------|------|---------|-----|
| offset | integer | 0 | - |
| limit | integer | 20 | 100 |

#### Response

```json
{
  "memberships": [
    {
      "id": "membership-id",
      "projectId": "project-id",
      "userId": "user-id",
      "user": {
        "id": "user-id",
        "email": "user@example.com"
      },
      "role": "admin"
    }
  ],
  "total": 3
}
```

#### Example

```bash
curl -X GET 'https://us.infisical.com/api/v1/projects/abc123/memberships' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Machine Identities

Machine identities allow non-human accounts to authenticate and access secrets.

### List Identities

#### Endpoint

```
GET /api/v1/identities
```

#### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| offset | integer | 0 | - | Number to skip |
| limit | integer | 20 | 100 | Number to return |

#### Response

```json
{
  "identities": [
    {
      "id": "identity-id-uuid",
      "name": "Production API",
      "createdAt": "2026-04-01T10:00:00.000Z",
      "updatedAt": "2026-04-16T10:30:00.000Z"
    }
  ],
  "total": 1
}
```

#### Example

```bash
curl -X GET 'https://us.infisical.com/api/v1/identities?offset=0&limit=20' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Identity

#### Endpoint

```
GET /api/v1/identities/{identityId}
```

#### Response

```json
{
  "identity": {
    "id": "identity-id-uuid",
    "name": "Production API",
    "universalAuthClientId": "machine-identity-uuid",
    "createdAt": "2026-04-01T10:00:00.000Z",
    "updatedAt": "2026-04-16T10:30:00.000Z"
  }
}
```

### Create Identity

#### Endpoint

```
POST /api/v1/identities
```

#### Request Body

```json
{
  "name": "string"
}
```

### Update Identity

#### Endpoint

```
PATCH /api/v1/identities/{identityId}
```

#### Request Body

```json
{
  "name": "string (optional)"
}
```

### Delete Identity

#### Endpoint

```
DELETE /api/v1/identities/{identityId}
```

## Identity Auth Methods

Configure how machine identities authenticate.

### Universal Auth (Recommended)

#### Endpoint

```
GET /api/v1/auth/universal-auth/identities/{identityId}
POST /api/v1/auth/universal-auth/identities/{identityId}
DELETE /api/v1/auth/universal-auth/identities/{identityId}
```

#### Example: Get Universal Auth Config

```bash
curl -X GET 'https://us.infisical.com/api/v1/auth/universal-auth/identities/identity-id' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response includes `clientId` and regenerated `clientSecret`.

#### AWS Auth

```
POST /api/v1/auth/aws-auth/identities/{identityId}
PATCH /api/v1/auth/aws-auth/identities/{identityId}
```

#### Azure Auth

```
POST /api/v1/auth/azure-auth/identities/{identityId}
PATCH /api/v1/auth/azure-auth/identities/{identityId}
```

#### GCP Auth

```
POST /api/v1/auth/gcp-auth/identities/{identityId}
PATCH /api/v1/auth/gcp-auth/identities/{identityId}
```

#### Kubernetes Auth

```
POST /api/v1/auth/kubernetes-auth/identities/{identityId}
PATCH /api/v1/auth/kubernetes-auth/identities/{identityId}
```

## Groups

Organize machine identities and manage permissions at scale.

### Endpoint

```
GET /api/v1/groups
POST /api/v1/groups
GET /api/v1/groups/{groupId}
PATCH /api/v1/groups/{groupId}
DELETE /api/v1/groups/{groupId}
```

### Example: List Groups

```bash
curl -X GET 'https://us.infisical.com/api/v1/groups' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Folders

Organize secrets into hierarchical folder structures.

### Endpoint

```
GET /api/v2/folders
POST /api/v2/folders
PATCH /api/v2/folders/{folderId}
DELETE /api/v2/folders/{folderId}
```

### List Folders

```bash
curl -X GET 'https://us.infisical.com/api/v2/folders?projectId=abc123&environment=dev' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Secret Imports

Import secrets from one environment into another.

### Endpoint

```
GET /api/v2/secret-imports
POST /api/v2/secret-imports
PATCH /api/v2/secret-imports/{importId}
DELETE /api/v2/secret-imports/{importId}
```

### Example: List Secret Imports

```bash
curl -X GET 'https://us.infisical.com/api/v2/secret-imports?projectId=abc123&environment=dev' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Deprecated Endpoints

**Do not use these endpoints in new code:**

- `/api/v1/workspace/*` — Use `/api/v1/projects` instead
- Service token endpoints — Use machine identities with Universal Auth instead

## Common Workflows

### Set Up a New Machine Identity

1. Create identity: `POST /api/v1/identities` → get `identityId`
2. Configure auth: `POST /api/v1/auth/universal-auth/identities/{identityId}`
3. Login: `POST /api/v1/auth/universal-auth/login` with `clientId` and `clientSecret`
4. Use returned `accessToken` for all subsequent API calls

### Add Identity to Project

1. Create identity and auth method (see above)
2. Create a folder/path in the target project
3. Create project membership or use RBAC rules to grant access
4. Test login with the new credentials

### Organize Secrets with Folders

1. Create folder: `POST /api/v2/folders` with `projectId`, `environment`, `folderName`
2. Create secrets under folder: `POST /api/v4/secrets/SECRET_NAME` with `secretPath: "/folder-name"`
3. List secrets in folder: `GET /api/v4/secrets?secretPath=/folder-name`
