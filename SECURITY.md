# Security Policy 🔒

## Supported Versions

Only the latest release version of **DocMind** receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## 🛡️ Reporting a Vulnerability

We take document data security seriously. DocMind is designed for enterprise internal knowledge management, meaning data privacy and access control are paramount.

### How to Report
If you discover a security vulnerability or security flaw within DocMind:

1. **Do NOT open a public GitHub issue.**
2. Send an email directly to `security@docmind.internal` with:
   - Description of the vulnerability.
   - Steps to reproduce or proof-of-concept.
   - Impact assessment on document data privacy or system authorization.

### Response Timeline
- **Acknowledgement**: Within 24 hours.
- **Initial Assessment**: Within 3 business days.
- **Patch & Release**: Priority hotfix within 7 business days.

---

## 🔑 Data Privacy & LLM Compliance
- Document contents uploaded to DocMind are processed locally for embedding generation.
- Vector embeddings are stored in isolated local ChromaDB databases or secure self-hosted pgvector instances.
- External API calls to Groq transmit only retrieved relevant context chunks over TLS.
