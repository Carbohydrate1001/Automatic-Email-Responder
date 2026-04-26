# Challenges Encountered

## 1. OAuth2 Token Expiration (401 Unauthorized Error)

### Problem
Backend failed to fetch emails from Microsoft Graph API with error:
```
401 Client Error: Unauthorized for url: https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages
```

### Root Cause
- Microsoft OAuth2 access tokens expire after approximately 1 hour
- System only stored the `access_token` in session, not the `refresh_token`
- No logic to detect token expiration or refresh expired tokens
- After 1 hour, all API calls failed with 401 errors

### Solution
Implemented automatic token refresh mechanism:

1. **Store refresh token** - Modified `auth_routes.py` callback to store:
   - `access_token` - for API calls
   - `refresh_token` - for getting new access tokens
   - `token_expires_at` - timestamp when token expires

2. **Token refresh function** - Added `refresh_access_token()`:
   - Uses MSAL's `acquire_token_by_refresh_token()` method
   - Gets new access token without requiring user to log in again
   - Updates session with new tokens

3. **Automatic validation** - Added `get_valid_token()`:
   - Checks if token is expired or expiring soon (within 5 minutes)
   - Automatically refreshes token if needed
   - Returns valid token or indicates re-authentication needed

4. **Integration** - Updated `_require_auth()` in `email_routes.py`:
   - Calls `get_valid_token()` instead of directly reading from session
   - Ensures all API calls use valid, non-expired tokens

### Files Modified
- `backend/routes/auth_routes.py` - Added token refresh logic
- `backend/routes/email_routes.py` - Updated authentication check

### Result
- System now automatically refreshes tokens before they expire
- No more 401 errors after 1 hour of usage
- Users don't need to manually re-login every hour
- Seamless continuous operation

### Note
Users who were logged in before this fix need to log out and log back in once to get a refresh token stored in their session.

---

## 2. Order Validation Issue

### Problem
System accepted any order number (even randomly made-up ones) and responded with "已处理，七日内退款" (processed, refund within 7 days) without validating against database.

### Root Cause
- No `orders` table in database
- Order numbers were randomly generated, not looked up
- Reply templates didn't check if orders actually existed

### Solution
1. Created `orders` table in database with order details
2. Built `OrderService` class to validate orders against database
3. Modified reply templates to check order existence before responding
4. Added proper error messages for invalid orders

### Files Created/Modified
- `backend/models/database.py` - Added orders table
- `backend/services/order_service.py` - Order validation service
- `backend/services/reply_service.py` - Updated templates
- `backend/scripts/init_orders.py` - Initialize sample data
- `docs/ORDER_VALIDATION_UPDATE.md` - Full documentation

### Result
- System now validates all orders against database
- Shows real order information in responses
- Returns "order not found" for invalid orders
- Proper security: users can only access their own orders
