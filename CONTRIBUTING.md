# How to contribute to Let It Snow ?

Thank you for taking the time to contribute to LIS! This document will guide you
through the workflow and best practices you need to know to send your
contribution.

There are many ways to contribute to LIS:

* [Reporting a bug](#reporting-bugs)
* [Making a feature request](#feature-requests-and-discussions)
* [Contributing code (C++, Python, CMake, etc.)](#code-contribution)

Our main workflow uses GitLab for source control, issues and task tracking. We
use a self-hosted GitLab instance:

[`https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow`](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow)

## Reporting bugs

If you have found a bug, you can first [search the existing issues](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/issues?label_name%5B%5D=bug)
to see if it has already been reported.

If it's a new bug, please [open a new issue on GitLab](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/issues/new).
The 'Bug' issue template will help you provide all important information and
help fixing the bug quicker. Remember to add as much information as possible!

## Feature requests and discussions

Feature requests are welcome! Generally you are welcome to simply [open an issue](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/issues)
and discuss your idea there.

## Documentation improvements


## Code contribution

The LIS workflow is based on GitLab [Merge Requests](https://docs.gitlab.com/ee/gitlab-basics/add-merge-request.html).
Clone the repository, create a feature branch, commit your changes, push the
feature branch to a fork (or the main repository if you are a core developer),
then send a merge request. Direct push to develop without review must be avoided.


### Commit message

On your feature branch, write a good [commit message](https://xkcd.com/1296/):
short and descriptive. If fixing an issue or bug, put the issue number in the
commit message so that GitLab can [cross-link it](https://docs.gitlab.com/ce/user/project/issues/crosslinking_issues.html).
You can prefix your commit message with an indicating flag (DOC, BUG, PKG,
TEST, SuperBuild, etc.).

Standard prefixes for LIS commit messages:

    BUG: Fix for runtime crash or incorrect result
    COMP: Compiler error or warning fix
    DOC: Documentation change
    ENH: New functionality
    PERF: Performance improvement
    STYLE: No logic impact (indentation, comments)
    WIP: Work In Progress not ready for merge

For example, here are some good commit messages:

    BUG: #1701 Warn users if parameter string is unset
    DOC: Fix typo in Monteverdi French translation
    COMP: Allow GeoTIFF and TIFF to be disabled when no 3rd party drags them

### Merge request

Your contribution is ready to be added to the main LIS repository? Send a Merge
Request against the `develop` branch on GitLab using the merge request
template. The merge request will then be discussed by the community and the core
LIS team.

* Merge requests can not be merged until all discussions have been resolved (this is enforced by GitLab)
* Merge requests **must receive at least 2 positives votes from core developers** (members of Main Repositories group in Gitlab with at least "Developer" level) before being merged
* The merger is responsible for checking that the branch is up-to-date with develop
* Merge requests can be merged by anyone (not just PSC or RM) with push access to develop
* Merge requests can be merged once the CI is proven green for this branch.

### Contribution license agreement

LIS requires that contributors sign out a [Contributor License
Agreement](https://en.wikipedia.org/wiki/Contributor_License_Agreement). The
purpose of this CLA is to ensure that the project has the necessary ownership or
grants of rights over all contributions to allow them to distribute under the
chosen license (AGPL v3.0)

To accept your contribution, we need you to complete, sign and email to *cla [at]
orfeo-toolbox [dot] org* an [Individual Contributor Licensing
Agreement](https://www.orfeo-toolbox.org/cla/icla-en.doc) (ICLA) form and a
[Corporate Contributor Licensing
Agreement](https://www.orfeo-toolbox.org/cla/ccla-en.doc) (CCLA) form if you are
contributing on behalf of your company or another entity which retains copyright
for your contribution.

The copyright owner (or owner's agent) must be mentioned in headers of all
modified source files.

## GitLab guidelines

In order to organize the issues in our GitLab instance, we use both labels and
milestones.

The [milestones](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/milestones) should be used to track in which release a feature is merged.
GitLab can then provide a summary of all features and bugs added to a given release
version.

Regarding labels, we use the following set:
* ~story: significant feature to be implemented with a detailed work plan, it can
  correspond to a Request for Comments that has turned into a development action
* ~bug: Bug, crash or unexpected behavior, reported by a user or a developer
* ~feature: Feature request expressed by an LIS user/developer
* ~patch: A small patch fixing build warnings, compilation errors, typos in logs or documentation
* ~"To Do": action is planned
* ~Doing: work in progress
* ~api ~app ~documentation ~monteverdi ~packaging ~qgis: optional context information
