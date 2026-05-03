# EOS Google Drive Read-only Contract v1

Status: readiness only. Live Drive provider calls are not verified.

## Allowed Metadata

EOS Drive readiness may expose only:

```text
id
name
mimeType
modifiedTime
webViewLink
```

## Required Scope

```text
https://www.googleapis.com/auth/drive.metadata.readonly
```

## Forbidden Behavior

EOS must not download file content, write files, delete files, change permissions, persist raw documents, or store document bodies.

## Preflight Shape

The read-only preflight returns sanitized booleans and metadata:

```json
{
  "status": "warning",
  "drive_readonly_enabled": false,
  "live_verified": false,
  "write_actions_available": false,
  "issues": []
}
```

No account values, token paths, credential paths, provider output, or document content are emitted.
