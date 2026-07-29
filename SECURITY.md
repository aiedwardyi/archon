# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Archon, please report it by:

1. **DO NOT** open a public GitHub issue
2. Email the maintainer directly with details at [create issue with security label]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to understand and address the issue.

## Security Best Practices for Deployment

### Environment Variables

**NEVER commit the following to version control:**
- API keys (Anthropic, Google, IBM Watson, OpenAI, Ollama endpoints)
- JWT secret keys
- Google OAuth client secrets
- Database credentials
- Any `.env` files

Always use environment variables for sensitive configuration. See `.env.example` for required variables.

### Production Deployment

1. **API Keys**: Use environment variables or secure secret management (AWS Secrets Manager, HashiCorp Vault, etc.)

2. **JWT Secret**: Generate a strong random secret for production:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Set as `JWT_SECRET_KEY` environment variable.

3. **CORS Configuration**: Update CORS origins in `backend/app.py` to match your production domains. Remove `localhost` origins in production.

4. **Database Security**:
   - Use proper file permissions for SQLite database
   - Consider PostgreSQL/MySQL for production with proper authentication
   - Enable connection encryption

5. **Google OAuth**:
   - Register production domains in Google Cloud Console
   - Set proper authorized redirect URIs
   - Keep client secrets secure

6. **HTTPS**: Always use HTTPS in production. Configure your reverse proxy (nginx/Apache) or hosting platform accordingly.

7. **Rate Limiting**: Implement rate limiting on authentication endpoints to prevent brute force attacks.

8. **Input Validation**: All user inputs are validated, but always review generated code before deployment.

### Code Generation Security

This platform generates and executes code. Important security considerations:

1. **Generated Code Review**: Always review generated code before deploying to production
2. **Sandboxing**: Generated code runs in isolated preview environments
3. **Asset Handling**: Uploaded assets are validated and sanitized
4. **Build Process**: Generated applications build in isolated environments

### Known Security Considerations

1. **Development Mode Password Reset**: Reset tokens are hidden by default. Local and test environments can expose them with `ARCHON_EXPOSE_RESET_TOKEN=true`. This repository does not include email delivery, so production deployments must add a mail transport before enabling password reset.

2. **Default JWT Secret**: The default JWT secret (`archon-dev-secret-change-in-prod`) MUST be changed in production.

3. **Debug Endpoints**: Ensure no debug endpoints are exposed in production.

4. **CORS Origins**: Restrict CORS to your actual domains in production.

## Security Features

### Implemented

- ✅ JWT-based authentication with token blocklist
- ✅ Password hashing with bcrypt
- ✅ Google OAuth integration
- ✅ SQL injection protection via SQLAlchemy ORM
- ✅ HTML escaping for user-generated content
- ✅ Input validation on API endpoints
- ✅ Project ownership and authorization checks
- ✅ CORS protection
- ✅ Secure session management

### Recommendations for Enhancement

- 🔄 Add rate limiting on authentication endpoints
- 🔄 Implement CSRF protection for state-changing operations
- 🔄 Add security headers (CSP, X-Frame-Options, etc.)
- 🔄 Enable HTTPS-only cookies in production
- 🔄 Add automated dependency vulnerability scanning
- 🔄 Implement audit logging for sensitive operations
- 🔄 Add email verification for new accounts
- 🔄 Implement 2FA support
- 🔄 Add password complexity requirements
- 🔄 Implement account lockout after failed login attempts

## Secure Development Practices

1. **Dependency Management**: Regularly update dependencies and review security advisories
2. **Code Review**: All changes should be reviewed for security implications
3. **Testing**: Write tests for authentication and authorization logic
4. **Secrets Management**: Never commit secrets; use environment variables
5. **Error Messages**: Avoid leaking sensitive information in error messages
6. **Logging**: Log security events but never log sensitive data (passwords, tokens, etc.)

## Contact

For security concerns, please open an issue with the `security` label or contact the maintainers directly.
