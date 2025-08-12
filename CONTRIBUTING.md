# Contributing to Stream-Forge

First off, thank you for considering contributing to Stream-Forge! It's people like you that make Stream-Forge such a great tool.

## Where do I go from here?

If you've noticed a bug or have a feature request, [make one](https://github.com/oleh-kondratov/stream-forge/issues/new)! It's generally best if you get confirmation of your bug or approval for your feature request this way before starting to code.

### Fork & create a branch

If this is something you think you can fix, then [fork Stream-Forge](https://github.com/oleh-kondratov/stream-forge/fork) and create a branch with a descriptive name.

A good branch name would be (where issue #33 is the ticket you're working on):

```bash
feat/33-add-new-service
```

### Get the test suite running

Make sure you're running the test suite locally before you start making changes. This will help you ensure you don't break anything.

### Implement your fix or feature

At this point, you're ready to make your changes! Feel free to ask for help; everyone is a beginner at first :smile_cat:

### Make a Pull Request

At this point, you should switch back to your master branch and make sure it's up to date with Stream-Forge's master branch:

```bash
git remote add upstream git@github.com:oleh-kondratov/stream-forge.git
git checkout master
git pull upstream master
```

Then update your feature branch from your local copy of master, and push it!

```bash
git checkout feat/33-add-new-service
git rebase master
git push --force-with-lease origin feat/33-add-new-service
```

Finally, go to GitHub and [make a Pull Request](https://github.com/oleh-kondratov/stream-forge/compare) :D

## Keeping your Pull Request updated

If a maintainer asks you to "rebase" your PR, they're saying that a lot of code has changed, and that you need to update your branch so it's easier to merge.

To learn more about rebasing and merging, check out this guide on [merging vs. rebasing](https://www.atlassian.com/git/tutorials/merging-vs-rebasing).

## Merging a PR (for maintainers)

A PR can only be merged by a maintainer if:

*   It is passing CI.
*   It has been approved by at least one maintainer.
*   It has no requested changes.
*   It is up to date with the master branch.

Any maintainer is allowed to merge a PR if all of these conditions are met.
