#!/usr/bin/env python3
"""Tests for trash-guard hook."""

from trash_guard import contains_destructive_command, strip_quotes, is_allowed_rm


# --- Should BLOCK ---

def test_basic_rm():
    assert contains_destructive_command("rm file.txt")

def test_rm_rf():
    assert contains_destructive_command("rm -rf directory/")

def test_rm_r():
    assert contains_destructive_command("rm -r directory/")

def test_rm_with_path():
    assert contains_destructive_command("/bin/rm file.txt")

def test_rm_usr_bin():
    assert contains_destructive_command("/usr/bin/rm -rf /home/user")

def test_sudo_rm():
    assert contains_destructive_command("sudo rm -rf /var/data")

def test_rm_after_and():
    assert contains_destructive_command("echo hello && rm file.txt")

def test_rm_after_or():
    assert contains_destructive_command("test -f x || rm file.txt")

def test_rm_after_semicolon():
    assert contains_destructive_command("echo hello; rm file.txt")

def test_rm_in_pipe():
    assert contains_destructive_command("find . | xargs rm")

def test_xargs_rm():
    assert contains_destructive_command("find . -name '*.tmp' | xargs rm -rf")

def test_command_rm():
    assert contains_destructive_command("command rm file.txt")

def test_env_rm():
    assert contains_destructive_command("env rm file.txt")

def test_backslash_rm():
    assert contains_destructive_command("\\rm file.txt")

def test_find_delete():
    assert contains_destructive_command("find . -name '*.tmp' -delete")

def test_find_exec_rm():
    assert contains_destructive_command("find . -exec rm {} \\;")

def test_shred():
    assert contains_destructive_command("shred secret.txt")

def test_unlink():
    assert contains_destructive_command("unlink file.txt")

def test_subshell_rm():
    assert contains_destructive_command("bash -c 'rm -rf /tmp/test'")

def test_subshell_sh():
    assert contains_destructive_command("sh -c 'rm file'")

def test_relative_path_rm():
    assert contains_destructive_command("./rm file.txt")

def test_sudo_path_rm():
    assert contains_destructive_command("sudo /usr/bin/rm -rf /data")

def test_rm_home():
    assert contains_destructive_command("rm -rf ~/Documents")

def test_rm_dot():
    assert contains_destructive_command("rm -rf .")

def test_rm_star():
    assert contains_destructive_command("rm -rf *")


# --- Should ALLOW ---

def test_git_rm():
    assert not contains_destructive_command("git rm file.txt")

def test_git_rm_cached():
    assert not contains_destructive_command("git rm --cached file.txt")

def test_echo_rm():
    assert not contains_destructive_command("echo 'rm file.txt'")

def test_echo_double_quote_rm():
    assert not contains_destructive_command('echo "rm -rf /"')

def test_git_commit_message_rm():
    assert not contains_destructive_command("git commit -m 'rm old files'")

def test_grep_rm():
    assert not contains_destructive_command("grep 'rm' Makefile")

def test_ls_command():
    assert not contains_destructive_command("ls -la")

def test_cat_command():
    assert not contains_destructive_command("cat file.txt")

def test_mkdir_command():
    assert not contains_destructive_command("mkdir -p dir/subdir")

def test_empty_command():
    assert not contains_destructive_command("")


# --- Allowlist tests ---

def test_rm_tmp():
    assert not contains_destructive_command("rm -rf /tmp/build-12345")

def test_rm_var_tmp():
    assert not contains_destructive_command("rm -rf /var/tmp/cache")

def test_rm_private_tmp():
    assert not contains_destructive_command("rm -rf /private/tmp/test")

def test_rm_pycache():
    assert not contains_destructive_command("rm -rf __pycache__")

def test_rm_pytest_cache():
    assert not contains_destructive_command("rm -rf .pytest_cache")

def test_rm_mypy_cache():
    assert not contains_destructive_command("rm -rf .mypy_cache")

def test_rm_ruff_cache():
    assert not contains_destructive_command("rm -rf .ruff_cache")

def test_rm_node_modules():
    assert not contains_destructive_command("rm -rf node_modules")

def test_rm_egg_info():
    assert not contains_destructive_command("rm -rf mypackage.egg-info")

def test_rm_tox():
    assert not contains_destructive_command("rm -rf .tox")

def test_rm_nox():
    assert not contains_destructive_command("rm -rf .nox")

def test_rm_pycache_nested():
    assert not contains_destructive_command("rm -rf src/__pycache__")

def test_rm_node_modules_nested():
    assert not contains_destructive_command("rm -rf frontend/node_modules")

def test_rm_mixed_allowed_disallowed():
    # If ANY path is not allowed, block the whole command
    assert contains_destructive_command("rm -rf __pycache__ src/")


# --- strip_quotes tests ---

def test_strip_single_quotes():
    assert strip_quotes("echo 'rm -rf /'") == "echo ''"

def test_strip_double_quotes():
    assert strip_quotes('echo "rm -rf /"') == 'echo ""'

def test_strip_escaped_quotes():
    assert strip_quotes('echo "he said \\"hello\\""') == 'echo ""'


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "pytest", __file__, "-v"],
        cwd="/Users/mm725821/code/trash-guard",
    )
    sys.exit(result.returncode)
