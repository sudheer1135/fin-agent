tar -czvf backup.tar.gz /home/user/documents
✔ What this does:
c: creates a new tar archive

z: compresses it using gzip

v: prints each file being added

f: names the output file backup.tar.gz

Archives /home/user/documents

What is a Detached HEAD?
The HEAD in Git refers to the current branch or commit you are working on. A detached HEAD state occurs when you are not on a branch but on a specific commit.

Why it’s Confusing?
When in a detached HEAD state, any commits you make do not belong to any branch, which can lead to confusion and potential data loss if not handled correctly.
