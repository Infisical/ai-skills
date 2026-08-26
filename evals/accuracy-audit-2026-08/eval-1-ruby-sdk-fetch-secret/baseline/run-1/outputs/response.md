Here's the full flow using Infisical's Ruby SDK, following the same pattern used across Infisical's other official SDKs (Universal Auth for machine identities, then a `secrets` client call).

## 1. Installation

Add the gem to your `Gemfile`:

```ruby
gem "infisical-sdk"
```

Then run:

```
bundle install
```

Or install directly:

```
gem install infisical-sdk
```

## 2. Client setup

```ruby
require "infisical-sdk"

client = InfisicalSDK::Client.new(
  site_url: "https://app.infisical.com" # use your self-hosted URL if applicable
)
```

## 3. Authenticate with a machine identity (Universal Auth)

In Infisical, create a Machine Identity, enable Universal Auth on it, generate a Client ID / Client Secret, and give it access to your project (and the `prod` environment specifically).

```ruby
client.auth.universal_auth.login(
  client_id: ENV["INFISICAL_MACHINE_IDENTITY_CLIENT_ID"],
  client_secret: ENV["INFISICAL_MACHINE_IDENTITY_CLIENT_SECRET"]
)
```

## 4. Read the secret

```ruby
secret = client.secrets.get_secret_by_name(
  secret_name: "API_KEY",
  project_id: "YOUR_PROJECT_ID",
  environment_slug: "prod",
  secret_path: "/"
)

puts secret.secret_value
```

## Full example

```ruby
require "infisical-sdk"

client = InfisicalSDK::Client.new(site_url: "https://app.infisical.com")

client.auth.universal_auth.login(
  client_id: ENV["INFISICAL_MACHINE_IDENTITY_CLIENT_ID"],
  client_secret: ENV["INFISICAL_MACHINE_IDENTITY_CLIENT_SECRET"]
)

secret = client.secrets.get_secret_by_name(
  secret_name: "API_KEY",
  project_id: ENV["INFISICAL_PROJECT_ID"],
  environment_slug: "prod",
  secret_path: "/"
)

puts "API_KEY = #{secret.secret_value}"
```

One caveat: I don't have web access in this session to re-verify the current gem name and exact method signatures against the live docs. This mirrors the well-established pattern from Infisical's Node/Python/Go/.NET SDKs (Universal Auth login, then `secrets.get_secret_by_name`), but since you're at Infisical, it's worth a quick diff against `infisical.com/docs/sdks/languages/ruby` (or the gemspec on RubyGems) before shipping it, in case the Ruby SDK's method naming differs slightly.
