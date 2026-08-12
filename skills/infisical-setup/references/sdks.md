# SDK Integration

For applications that need to fetch secrets programmatically — not just as environment variables, but within application logic. All SDKs follow the same pattern: initialize → authenticate → fetch secrets.

All SDKs cache secrets and fall back to cached values if requests fail. If no cache exists, they fall back to `process.env` (or equivalent).

## Quick reference

There are **nine** official SDKs.

| Language | Package | Min version |
|----------|---------|-------------|
| Node.js | `@infisical/sdk` | Node 20+ (v5+); Node 14+ on v4 |
| Python | `infisicalsdk` | Python 3.7+ |
| Go | `github.com/infisical/go-sdk` | Go 1.19+ |
| Java | `com.infisical:sdk` | Java 11+ |
| .NET | `Infisical.Sdk` | .NET 6+ |
| Ruby | `infisical-sdk` (require `"infisical"`) | Ruby 3.0.0+ |
| PHP | `infisical/php-sdk` (Composer) | — |
| Rust | `infisical` (crates.io) | — |
| C++ | `Infisical/infisical-cpp-sdk` (CMake) | C++17+ (GCC 8+/clang 3.8+) |

## Node.js

```bash
npm install @infisical/sdk
```

```typescript
import { InfisicalSDK } from '@infisical/sdk';

const client = new InfisicalSDK({
  siteUrl: "https://app.infisical.com" // optional, this is the default
});

// Authenticate with a machine identity
await client.auth().universalAuth.login({
  clientId: "<machine-identity-client-id>",
  clientSecret: "<machine-identity-client-secret>"
});

// List all secrets
const secrets = await client.secrets().listSecrets({
  environment: "dev",
  projectId: "<your-project-id>",
  secretPath: "/"
});

// Get a single secret
const secret = await client.secrets().getSecret({
  secretName: "API_KEY",
  environment: "prod",
  projectId: "<your-project-id>"
});
console.log(secret.secretValue);

// Create a secret
await client.secrets().createSecret({
  secretName: "NEW_KEY",
  secretValue: "value",
  environment: "dev",
  projectId: "<your-project-id>"
});
```

The Node SDK is the most complete. Its method categories are: `auth`, `secrets`,
`dynamicSecrets` (including `dynamicSecrets().leases`), `projects`, `environments`, `folders`,
and `kms` (key management, encryption, and signing).

## Python

```bash
pip install infisicalsdk
```

```python
from infisical_sdk import InfisicalSDKClient

client = InfisicalSDKClient(
    host="https://app.infisical.com",
    cache_ttl=60  # seconds, None to disable
)

client.auth.universal_auth.login(
    client_id="<client-id>",
    client_secret="<client-secret>"
)

# List secrets
secrets = client.secrets.list_secrets(
    project_id="<project-id>",
    environment_slug="dev",
    secret_path="/"
)

# Get one secret
secret = client.secrets.get_secret(
    secret_name="API_KEY",
    project_id="<project-id>",
    environment_slug="prod"
)
print(secret.secret_value)
```

Auth methods: Universal Auth, AWS IAM, OIDC, LDAP, Token Auth.

## Go

```bash
go get github.com/infisical/go-sdk
```

```go
package main

import (
    "context"
    "fmt"
    infisical "github.com/infisical/go-sdk"
)

func main() {
    client := infisical.NewInfisicalClient(context.Background(), infisical.Config{
        SiteUrl:          "https://app.infisical.com",
        AutoTokenRefresh: true,
    })

    _, err := client.Auth().UniversalAuthLogin("CLIENT_ID", "CLIENT_SECRET")
    if err != nil {
        panic(err)
    }

    secret, err := client.Secrets().Retrieve(infisical.RetrieveSecretOptions{
        SecretKey:   "API_KEY",
        Environment: "prod",
        ProjectID:   "YOUR_PROJECT_ID",
        SecretPath:  "/",
    })
    fmt.Println(secret.SecretValue)
}
```

Auth methods: Universal Auth, GCP (ID Token & IAM), AWS IAM, Azure, Kubernetes, JWT, LDAP, OCI.

**Note**: Set `AutoTokenRefresh: true` for long-running processes. For multiple clients, manage context cancellation properly to avoid leaked goroutines.

## Java

```xml
<dependency>
    <groupId>com.infisical</groupId>
    <artifactId>sdk</artifactId>
    <version>{version}</version>
</dependency>
```

```java
var sdk = new InfisicalSdk(
    new SdkConfig.Builder()
        .withSiteUrl("https://app.infisical.com")
        .build()
);

sdk.Auth().UniversalAuthLogin("CLIENT_ID", "CLIENT_SECRET");

var secret = sdk.Secrets().GetSecret(
    "API_KEY",       // secret name
    "<project-id>",  // project ID
    "prod",          // environment
    "/",             // path
    null, null, null // optional: expandRefs, includeImports, type
);
System.out.println(secret.getValue());
```

## .NET

```bash
dotnet add package Infisical.Sdk
```

```csharp
var settings = new InfisicalSdkSettingsBuilder()
    .WithHostUri("https://app.infisical.com")
    .Build();

var client = new InfisicalClient(settings);

await client.Auth().UniversalAuth().LoginAsync("<client-id>", "<client-secret>");

var secrets = await client.Secrets().ListAsync(new ListSecretsOptions {
    EnvironmentSlug = "prod",
    SecretPath = "/",
    ProjectId = "<project-id>",
    SetSecretsAsEnvironmentVariables = true  // optional: auto-set as env vars
});
```

## Ruby

Requires Ruby 3.0.0 or higher.

```bash
gem install infisical-sdk
```

Or in a Gemfile: `gem "infisical-sdk"`

Note the gem is named `infisical-sdk` but the **require path is `"infisical"`**:

```ruby
require "infisical"

client = Infisical::Client.new(
  site_url: "https://app.infisical.com" # Optional, defaults to https://app.infisical.com
)

client.auth.universal_auth_login(
  client_id: ENV.fetch("INFISICAL_CLIENT_ID"),
  client_secret: ENV.fetch("INFISICAL_CLIENT_SECRET")
)

# Secret name is the first POSITIONAL argument, not a keyword
secret = client.secrets.get(
  "API_KEY",
  project_id: "<project-id>",
  environment: "prod"
)
puts secret.secret_value

# List secrets
secrets = client.secrets.list(
  project_id: "<project-id>",
  environment: "dev",
  secret_path: "/"
)
```

Client options: `site_url` and `timeout` (seconds, default 10).

Other methods: `client.secrets.create(name, value, opts)`, `client.secrets.update(name, opts)`,
`client.secrets.delete(name, opts)`. A missing secret raises `Infisical::NotFoundError`.

**Common mistakes to avoid:**
- `require 'infisical-sdk'` — wrong, it is `require "infisical"`
- `InfisicalSDK::InfisicalClient.new(...)` — wrong, it is `Infisical::Client.new(site_url:)`
- `client.auth.universal_auth(...)` — wrong, it is `universal_auth_login(...)`
- `client.secrets.get(secret_name: "X", ...)` — wrong, the name is positional

## PHP

```bash
composer require infisical/php-sdk
```

```php
<?php

use Infisical\SDK\InfisicalSDK;

$sdk = new InfisicalSDK('https://app.infisical.com');

$sdk->auth()->universalAuth()->login(
    "your-machine-identity-client-id",
    "your-machine-identity-client-secret"
);

$params = new \Infisical\SDK\Models\ListSecretsParameters(
    environment: "dev",
    secretPath: "/",
    projectId: "your-project-id"
);

$secrets = $sdk->secrets()->list($params);
```

Covers `auth` and `secrets`.

## Rust

```bash
cargo add infisical
```

```rust
use infisical::{AuthMethod, Client, InfisicalError};
use infisical::secrets::GetSecretRequest;

async fn fetch_secret() -> Result<(), InfisicalError> {
    let mut client = Client::builder()
        .base_url("https://app.infisical.com") // Optional
        .build()
        .await?;

    let auth_method = AuthMethod::new_universal_auth("<client-id>", "<client-secret>");
    client.login(auth_method).await?;

    // Required params go to builder(); optional ones are builder methods
    let request = GetSecretRequest::builder("API_KEY", "<project-id>", "dev")
        .path("/")
        .build();

    let secret = client.secrets().get(request).await?;
    println!("Fetched key: {}", secret.secret_key);

    Ok(())
}
```

Builder pattern for both the client and each request.

## C++

Compatible with C++17 and later. Depends on `cURL` and OpenSSL. Install via CMake
`FetchContent`:

```cmake
FetchContent_Declare(
  infisical
  GIT_REPOSITORY https://github.com/Infisical/infisical-cpp-sdk.git
  GIT_TAG 1.0.0 # Replace with the desired version
)
FetchContent_MakeAvailable(infisical)

target_link_libraries(my_app PRIVATE infisical OpenSSL::SSL OpenSSL::Crypto)
target_include_directories(my_app PRIVATE ${infisical_SOURCE_DIR}/include)
```

```cpp
#include <iostream>
#include <libinfisical/InfisicalClient.h>

int main() {
  try {
    Infisical::InfisicalClient client(
        Infisical::ConfigBuilder()
            .withHostUrl("https://app.infisical.com")
            .withAuthentication(
                Infisical::AuthenticationBuilder()
                    .withUniversalAuth("<client-id>", "<client-secret>")
                    .build())
            .build());

    const auto options = Infisical::Input::GetSecretOptionsBuilder()
                             .withEnvironment("dev")
                             .withProjectId("<project-id>")
                             .withSecretKey("API_KEY")
                             .build();

    const auto secret = client.secrets().getSecret(options);
    std::cout << secret.getSecretKey() << std::endl;
  } catch (const Infisical::InfisicalError &e) {
    std::cerr << "Error: " << e.what() << std::endl;
    return 1;
  }
  return 0;
}
```

Everything lives in the `Infisical` namespace and uses a builder pattern for all input. Values
are returned as classes with getter methods.

## When to use SDK vs. CLI

| Scenario | Use |
|----------|-----|
| Local dev, any framework | CLI (`infisical run -- ...`) |
| Docker containers | CLI (see `docker-integration.md`) |
| Need secrets in application logic (not just env vars) | SDK |
| Dynamic secrets / leases | SDK |
| KMS encrypt/decrypt | SDK |
| Kubernetes pods | Operator (see `kubernetes-operator.md`) or SDK |
| CI/CD pipelines | CLI or OIDC action (see `cicd-integration.md`) |

## Auth method availability by SDK

All nine SDKs support Universal Auth. Cloud-native auth varies — the Go SDK has the broadest
coverage. Verify against the SDK's own docs before promising a method:

| Auth method | Node | Python | Go | Java | .NET | Ruby | PHP | Rust | C++ |
|------------|------|--------|-----|------|------|------|-----|------|-----|
| Universal Auth | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| AWS IAM | Yes | Yes | Yes | — | — | — | — | — | — |
| GCP ID Token | — | — | Yes | — | — | — | — | — | — |
| Azure | — | — | Yes | — | — | — | — | — | — |
| Kubernetes | — | — | Yes | — | — | — | — | — | — |
| JWT | — | — | Yes | — | — | — | — | — | — |
| OCI | — | — | Yes | — | — | — | — | — | — |
| OIDC | — | Yes | — | — | — | — | — | — | — |
| LDAP | — | Yes | Yes | Yes | Yes | — | — | — | — |

If a workload needs a platform-native auth method its SDK doesn't implement, use the CLI or the
Infisical Agent instead, or authenticate against the REST API directly and pass the resulting
access token to the SDK.
