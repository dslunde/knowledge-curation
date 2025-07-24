# Security Guidelines for Knowledge Curator

## 🔒 Environment Variable Security

### Critical Security Principles

1. **NEVER commit passwords to version control**
2. **Use environment-specific credentials**
3. **Rotate passwords regularly**
4. **Follow principle of least privilege**

## 📁 Environment File Management

### Development Environment
```bash
# Create your local development environment
cp .env.development.example .env.development
# Edit with your secure passwords
# This file is excluded from Git
```

### File Security Levels

| File | Security Level | Purpose | Committed to Git? |
|------|---------------|---------|------------------|
| `.env.development` | 🔴 SECRET | Local development credentials | ❌ NO |
| `.env.development.example` | ✅ SAFE | Template with placeholders | ✅ YES |
| `devops/.env_gha` | 🟡 LIMITED | CI/CD test credentials only | ✅ YES (isolated) |

## 🚀 Deployment Security

### Development
```bash
# Set environment variables securely
export DB_PASSWORD=$(openssl rand -base64 32)
export $(cat .env.development | xargs)
make full-start
```

### Production (GitHub Actions)
- Use GitHub Secrets for sensitive values
- Never hardcode production passwords
- Environment variables injected at deploy time

### Production (Manual)
```bash
# Use secure environment variable injection
export DB_PASSWORD="your-production-password"
export DOMAIN="your-domain.com"
docker stack deploy -c production-stack.yml knowledge-curator
```

## 🛡️ Password Generation

### Generate Secure Passwords
```bash
# Generate 32-character base64 password
openssl rand -base64 32

# Generate 20-character alphanumeric password  
python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20)))"

# Generate using system tools
pwgen -s 32 1
```

### Password Requirements
- **Minimum 20 characters**
- **Mix of letters, numbers, symbols**
- **Unique per environment**
- **Regularly rotated**

## 🔍 Security Checklist

### Before Deployment
- [ ] No passwords in committed files
- [ ] Environment files properly excluded from Git
- [ ] Strong, unique passwords generated
- [ ] Production secrets stored in secure secret management
- [ ] Regular password rotation schedule established

### Environment Separation
- [ ] Different passwords for dev/staging/production
- [ ] Isolated credentials per environment
- [ ] No production credentials in development
- [ ] Secure backup of critical credentials

## 🚨 Security Incident Response

### If Credentials Are Compromised
1. **Immediately rotate all affected passwords**
2. **Audit access logs for unauthorized activity**
3. **Update all environment configurations**
4. **Review and strengthen security practices**

### If Passwords Are Accidentally Committed
1. **Immediately change the exposed passwords**
2. **Force push to remove from Git history** (if possible)
3. **Rotate all related credentials**
4. **Audit recent repository access**

## 📞 Security Contact

For security concerns or incidents:
- Review this documentation
- Follow incident response procedures
- Update security practices as needed

Remember: **Security is everyone's responsibility!** 🛡️ 