Here's the full flow for fetching `API_KEY` from `prod` with the Ruby SDK.

**1. Install**

```bash
gem install infisical-sdk
```

Or add to your Gemfile:

```ruby
gem 'infisical-sdk'
```

**2. Client setup**

```ruby
require 'infisical-sdk'

client = InfisicalSDK::InfisicalClient.new('https://app.infisical.com')
```

**3. Authenticate with a machine identity**

This uses Universal Auth with a client ID and client secret from a machine identity you've already created in Infisical. Don't hardcode these, pull them from environment variables or another secure source.

```ruby
client.auth.universal_auth(
  client_id: ENV['INFISICAL_CLIENT_ID'],
  client_secret: ENV['INFISICAL_CLIENT_SECRET']
)
```

**4. Read the secret**

```ruby
secret = client.secrets.get(
  secret_name: 'API_KEY',
  project_id: '<your-project-id>',
  environment: 'prod'
)

puts secret.secret_value
```

Notes:
- Replace `<your-project-id>` with your actual Infisical project ID.
- The Ruby SDK caches secrets for 5 minutes by default. If you need fresher reads, you'd need to check the client config options for disabling or adjusting that.
- Never log `secret.secret_value` directly in production code, that example `puts` line is just for local verification.
- If you're not on Infisical Cloud, pass your self-hosted URL instead of `https://app.infisical.com` when constructing the client.
