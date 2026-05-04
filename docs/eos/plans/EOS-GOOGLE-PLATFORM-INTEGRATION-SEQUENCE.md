# EOS Google Platform Integration Sequence

Status: merge-order planning document. No live calls are verified here.

1. Fix DB Runtime P0 so Daily/Weekly no longer fail on readonly database state.
2. Stabilize PR #5, PR #6, and PR #7 if they remain part of the foundation queue.
3. Merge PR #4 Gmail Classifier.
4. Rebase PR #3 after PR #4 and resolve the `src/eos_mail/__init__.py` conflict.
5. Merge or rebase Drive metadata read-only readiness.
6. Merge or rebase Maps/Location readiness.
7. Integrate Calendar travel-time proposals into calendar planning after PR #9.
8. Run live E2E only after the read-only contracts and provider syntax are verified.

This sequence keeps Gmail, Drive, Calendar, and Maps readiness independent until the runtime blocker and open PR conflicts are resolved.
