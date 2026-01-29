# User Access Control

The Hearings AI portal uses a two-tier authentication system:

1. **Azure Static Web Apps Authentication** - Users must log in with GitHub or Microsoft account
2. **Backend Allowlist** - Only specific email addresses can access the API

## How It Works

When a user logs in:
1. Static Web Apps authenticates them via GitHub/Microsoft
2. Their email is sent to the API in the `X-MS-CLIENT-PRINCIPAL` header
3. The API checks if their email is in the `ALLOWED_USERS` allowlist
4. If not in the list, they get a 403 Forbidden error

## Managing the Allowlist

The allowlist is stored as an environment variable in Azure Container Apps: `ALLOWED_USERS`

### View Current Allowlist

```bash
az containerapp show \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --query "properties.template.containers[0].env[?name=='ALLOWED_USERS'].value" -o tsv
```

### Add a User

To add `newuser@example.com` to the existing list:

```bash
# Get current list
CURRENT=$(az containerapp show \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --query "properties.template.containers[0].env[?name=='ALLOWED_USERS'].value" -o tsv)

# Update with new user (comma-separated)
az containerapp update \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --set-env-vars "ALLOWED_USERS=${CURRENT},newuser@example.com"
```

### Replace Entire Allowlist

```bash
az containerapp update \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --set-env-vars "ALLOWED_USERS=user1@example.com,user2@example.com,user3@example.com"
```

### Remove All Restrictions (Allow Anyone)

```bash
az containerapp update \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --set-env-vars "ALLOWED_USERS="
```

## Email Format

- Emails are **case-insensitive**: `User@Example.com` matches `user@example.com`
- Use **commas** to separate multiple emails
- Whitespace is trimmed automatically

## Examples

### Single User
```bash
ALLOWED_USERS=john.smith@example.com
```

### Multiple Users
```bash
ALLOWED_USERS=john.smith@example.com,jane.doe@example.com,admin@company.com
```

### No Restrictions
```bash
ALLOWED_USERS=
```

## Troubleshooting

**User gets 403 error after logging in:**
- Check if their email is in the allowlist
- Verify the email matches exactly (check for typos, extra spaces)
- Check which email their GitHub/Microsoft account uses

**How to see what email a user is authenticating with:**
- Check the API logs in Azure Container Apps for authentication attempts
- The user can check `/.auth/me` endpoint on the Static Web App to see their claims

## Implementation Details

- **Code:** `api/src/auth/__init__.py` - `_validate_user_access()` function
- **Environment Variable:** `ALLOWED_USERS` in Container App
- **Updates:** Take effect immediately (no deployment needed)
- **Error Code:** `AUTH_002` when user is denied access
