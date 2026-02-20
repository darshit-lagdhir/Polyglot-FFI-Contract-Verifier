# Contributing to Polyglot FFI Contract Verifier

Thank you for your interest in contributing to the Polyglot FFI Contract Verifier (PFCV) ecosystem. 

PFCV operates under a highly structured governance framework designed to protect the integrity of the project's intellectual property and architectural innovations. We welcome contributions from the community, provided they align with our structural protocols and legal requirements.

## 1. Contributor License Agreement (CLA)

All contributions are accepted exclusively under the PFCV Contributor License Agreement. By submitting a Pull Request, you explicitly agree to the following terms, which are enforceable under the laws of the Republic of India, with jurisdiction in Bengaluru, Karnataka:

* **Affirmation of Originality**: You warrant that your contribution is your original creation and that you possess the necessary rights to submit it.
* **Rights Transfer**: You grant Darshit Lagdhir and Team LOGLORE an irrevocable, worldwide, royalty-free, transferable, and sublicensable right and license to use, modify, distribute, reproduce, and commercially license your contribution in any form.
* **Retention of Authorship**: You retain authorship and moral rights over your original work, but you agree not to assert claims against the maintainers or their commercial licensees regarding the use of your contribution.

### 1.1 CLA Sign-Off Requirement
All commits must include a Developer Certificate of Origin (DCO) sign-off. You can sign off your commits using the `-s` flag in Git:

`git commit -s -m "Your commit message"`

A sign-off looks like this:
`Signed-off-by: Your Name <your.email@example.com>`

## 2. Trademark and Branding Policies

* “Polyglot FFI Contract Verifier,” “MOVEX,” “Antigravity Enforcement,” and “Team LOGLORE” are reserved trademarks.
* If you fork this repository, you **must not** use these marks in a manner that implies endorsement, origin, or official status. If your fork diverges significantly, you must rebrand your project to avoid consumer confusion.

## 3. Legal Linting and Compliance Sentry

Our Continuous Integration (CI) pipeline includes a mandatory `legal_linting` stage. 
* The **Compliance Sentry** tool automatically injects or verifies the presence of the ASTPL file header in all source code files. 
* Any Pull Request that fails the Compliance Sentry check will be automatically rejected.
* Do not manually bypass, modify, or delete the ASTPL headers in the source files.

## 4. No Machine Training

By interacting with this repository, you acknowledge that the codebase is strictly off-limits for Machine Training Use (e.g., LLM fine-tuning, dataset creation) as set forth in the ASTPL. Contributing to the repository does not grant you the right to scrape it for AI research.

Thank you for respecting the governance architecture of PFCV. Collaboration thrives within well-defined boundaries.