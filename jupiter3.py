To exit a detached HEAD state, create a new branch or switch back to an existing branch:
git checkout -b new-branch
2. Rebase vs. Merge
Rebase:
Rebasing moves or combines a sequence of commits to a new base commit.
git rebase main


git status
# Shows:
# Changes to be committed:
#   (use "git restore --staged <file>..." to unstage)
#   modified: file_A.txt
#   modified: file_C.txt
Use code with caution.
