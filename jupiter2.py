What is a Detached HEAD?
The HEAD in Git refers to the current branch or commit you are working on. A detached HEAD state occurs when you are not on a branch but on a specific commit.

Why it’s Confusing?
When in a detached HEAD state, any commits you make do not belong to any branch, which can lead to confusion and potential data loss if not handled correctly.


To exit a detached HEAD state, create a new branch or switch back to an existing branch:
git checkout -b new-branch
2. Rebase vs. Merge
Rebase:
Rebasing moves or combines a sequence of commits to a new base commit.
git rebase main
