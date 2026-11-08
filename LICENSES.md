# Third-party components

This project's own code is Apache-2.0 (see LICENSE). The study runs
against these installed components; their licences are their own
projects' and are recorded here for provenance.

| Component | Version (pinned) | Role | Licence |
| --- | --- | --- | --- |
| boto3 | 1.43.126 | AWS SDK for Python: the client surface under study | Apache-2.0 |
| botocore | 1.43.126 | low-level AWS client library under boto3 | Apache-2.0 |
| moto | 5.2.5 | the AWS emulator under test (`moto[server]`) | Apache-2.0 |
| pytest | 9.2.0 | unit and smoke tests | MIT |
| requests | 2.34.2 | unauthenticated fetch of the presigned URL (S3-09) | Apache-2.0 |

No AWS service, account or credential is involved at any point; see
PREREGISTRATION.md Section 2 for the scope rule and src/factory.py
for how it is enforced.
