# Security Configuration Guide

## Overview

This document outlines the security configuration for the Mindframe backend application, including security headers, HTTPS enforcement, and other security measures.

## Security Middleware

The application uses a comprehensive security middleware (`SecurityMiddleware`) that implements multiple security headers and protections.

### Features Implemented

- **Content Security Policy (CSP)**: Prevents XSS attacks by controlling resource loading
- **HTTP Strict Transport Security (HSTS)**: Forces HTTPS connections
- **X-Frame-Options**: Prevents clickjacking attacks
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **X-XSS-Protection**: Enables browser XSS filtering
- **Referrer Policy**: Controls referrer information sent with requests
- **Permissions Policy**: Controls browser feature access
- **HTTPS Enforcement**: Redirects HTTP to HTTPS in production
- **Host Validation**: Validates allowed hosts
- **Content Length Limits**: Prevents oversized requests

## Environment Variables

### Security Headers Configuration

```bash
# Content Security Policy
SECURITY_CSP_ENABLED=true

# HTTP Strict Transport Security
SECURITY_HSTS_ENABLED=true
SECURITY_HSTS_MAX_AGE=31536000  # 1 year in seconds

# Frame Options
SECURITY_X_FRAME_OPTIONS=DENY  # Options: DENY, SAMEORIGIN, ALLOW-FROM uri

# Content Type Options
SECURITY_X_CONTENT_TYPE_OPTIONS=nosniff

# Referrer Policy
SECURITY_REFERRER_POLICY=strict-origin-when-cross-origin

# HTTPS Enforcement (Production only)
SECURITY_FORCE_HTTPS=false  # Set to true in production

# Allowed Hosts (Production)
SECURITY_ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
```

### CORS Configuration

```bash
# CORS Origins
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Production Security Checklist

### 1. HTTPS Configuration

- [ ] SSL/TLS certificate installed
- [ ] Set `SECURITY_FORCE_HTTPS=true`
- [ ] Configure reverse proxy (nginx/Apache) for HTTPS
- [ ] Enable HSTS with `SECURITY_HSTS_ENABLED=true`

### 2. Host Validation

- [ ] Set `SECURITY_ALLOWED_HOSTS` to your production domains
- [ ] Remove wildcard CORS origins
- [ ] Configure specific CORS origins for your frontend

### 3. Content Security Policy

Customize CSP based on your application needs:

```python
# Example: Allow specific CDNs for fonts and scripts
app.config['SECURITY_CSP_POLICY'] = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
    'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com"],
    'img-src': ["'self'", "data:", "https:"],
    'connect-src': ["'self'", "https://api.yourdomain.com"]
}
```

### 4. Rate Limiting

- [ ] Enable rate limiting: `RATE_LIMIT_ENABLED=true`
- [ ] Configure appropriate limits: `RATE_LIMIT_DEFAULT=100 per hour`

### 5. File Upload Security

- [ ] Set appropriate `MAX_CONTENT_LENGTH`
- [ ] Validate file types and extensions
- [ ] Scan uploaded files for malware

## Security Headers Reference

### Content Security Policy (CSP)

Prevents XSS attacks by controlling which resources can be loaded:

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
```

### HTTP Strict Transport Security (HSTS)

Forces browsers to use HTTPS:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

### X-Frame-Options

Prevents clickjacking:

```
X-Frame-Options: DENY
```

### X-Content-Type-Options

Prevents MIME type sniffing:

```
X-Content-Type-Options: nosniff
```

### X-XSS-Protection

Enables browser XSS filtering:

```
X-XSS-Protection: 1; mode=block
```

### Referrer Policy

Controls referrer information:

```
Referrer-Policy: strict-origin-when-cross-origin
```

## Testing Security Headers

### Using curl

```bash
# Test security headers
curl -I https://your-api-domain.com/health

# Look for these headers in the response:
# Content-Security-Policy
# Strict-Transport-Security
# X-Frame-Options
# X-Content-Type-Options
# X-XSS-Protection
# Referrer-Policy
```

### Online Tools

- [Security Headers](https://securityheaders.com/)
- [Mozilla Observatory](https://observatory.mozilla.org/)
- [SSL Labs](https://www.ssllabs.com/ssltest/)

## Common Security Issues

### 1. Mixed Content

Ensure all resources (images, scripts, stylesheets) are loaded over HTTPS in production.

### 2. Overly Permissive CSP

Avoid using `'unsafe-inline'` and `'unsafe-eval'` in production. Use nonces or hashes instead.

### 3. Missing Security Headers

Regularly test your application with security scanning tools to ensure all headers are present.

### 4. Weak CORS Configuration

Never use `*` for CORS origins in production. Always specify exact domains.

## Monitoring and Logging

The security middleware automatically:

- Logs security violations
- Adds request IDs for tracking
- Monitors for suspicious activity

Review security logs regularly for:

- CSP violations
- Failed host validations
- Oversized requests
- HTTPS enforcement triggers

## Updates and Maintenance

- Regularly update security configurations
- Monitor security advisories for Flask and dependencies
- Review and update CSP policies as application evolves
- Test security headers after deployments

## Additional Security Measures

Consider implementing:

- Web Application Firewall (WAF)
- DDoS protection
- Regular security audits
- Dependency vulnerability scanning
- Container security scanning
- Infrastructure security hardening