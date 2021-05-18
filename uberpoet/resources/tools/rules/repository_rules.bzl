"""
Repository rules used in the WORKSPACE.
"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def github_repo(name, project, repo, ref, sha256 = None):
    github_url = "https://github.com/%s/%s/archive/%s.zip" % (project, repo, ref)
    http_archive(
        name = name,
        strip_prefix = "%s-%s" % (repo, ref.replace("/", "-")),
        url = github_url,
        sha256 = sha256,
        canonical_id = github_url,
    )

def check_execute(repository_ctx, *args, **kwargs):
    exec_result = repository_ctx.execute(*args, **kwargs)
    if exec_result.return_code != 0:
        fail("{}: executing {} {} failed {}:\n{}\n{}".format(
            repository_ctx.name,
            args,
            kwargs,
            exec_result.return_code,
            exec_result.stdout,
            exec_result.stderr,
        ).rstrip())
    return exec_result
