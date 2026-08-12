Here's the full flow for fetching `API_KEY` from `prod` using the Ruby SDK.

**1. Install** (Ruby 3.0.0+ required)

```bash
gem install infisical-sdk
```

Or in a Gemfile:

```ruby
gem "infisical-sdk"
```

**2. Client setup and authentication**

The gem is named `infisical-sdk`, but the require path is `"infisical"`:

```ruby
require "infisical"

client = Infisical::Client.new(
  site_url: "https://app.infisical.com" # optional, this is the default
)

client.auth.universal_auth_login(
  client_id: ENV.fetch("INFISICAL_CLIENT_ID"),
  client_secret: ENV.fetch("INFISICAL_CLIENT_SECRET")
)
```

Pull the client ID and secret from your own machine identity credentials (env vars here, but use whatever secret source is appropriate for your setup). Don't hardcode them.

**3. Read the secret**

```ruby
secret = client.secrets.get(
  "API_KEY",
  project_id: "<your-project-id>",
  environment: "prod"
)

puts secret.secret_value
```

Note the secret name is a positional argument, not a keyword like `secret_name:`.

**Full example:**

```ruby
require "infisical"

client = Infisical::Client.new(
  site_url: "https://app.infisical.com"
)

client.auth.universal_auth_login(
  client_id: ENV.fetch("INFISICAL_CLIENT_ID"),
  client_secret: ENV.fetch("INFISICAL_CLIENT_SECRET")
)

begin
  secret = client.secrets.get(
    "API_KEY",
    project_id: "<your-project-id>",
    environment: "prod"
  )
  puts secret.secret_value
rescue Infisical::NotFoundError
  puts "API_KEY not found in prod"
end
```

A few things worth knowing:
- If you don't already have a machine identity with Universal Auth configured, that needs to be set up in Infisical first (via the dashboard or API) so you have a client ID and secret to authenticate with.
- `Infisical::NotFoundError` is raised if the secret doesn't exist at that path/environment.
- `Infisical::Client.new` also accepts `timeout:` (seconds, default 10).
