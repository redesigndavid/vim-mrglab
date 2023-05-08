import os
import sys
import site

p = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
virtual_env_dir = os.path.join(p, 'venv')
virtual_install = os.path.join(p, 'venv_install.sh')

if not os.path.exists(virtual_env_dir):
    os.system('sh {} {}.{}'.format(
        virtual_install,
        sys.version_info.major,
        sys.version_info.minor,
    ))


if sys.platform == "win32":
    site_packages = os.path.join(virtual_env_dir, "Lib", "site-packages")
else:
    site_packages = os.path.join(
        virtual_env_dir,
        "lib", f"python{sys.version_info.major}.{sys.version_info.minor}",
        "site-packages",
    )

prev_sys_path = list(sys.path)
site.addsitedir(site_packages)
sys.real_prefix = sys.prefix
sys.prefix = virtual_env_dir
# Move the added items to the front of the path:
new_sys_path = []
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path

#import vim
vim = None
import pprint
import sys
import gitlab
import git
import jinja2


discussions_template = """
{% for note in notes %}
{%- if not note.system %}
{{ note.author.name }} said:
{{ note.body }}
{%- else %}
{{ note.author.name }} {{ note.body }}
{% endif %}
{% endfor %}

[{% if notes[0].resolved -%} RESOLVED {%- else-%} UNRESOLVED {%- endif %}]

_
"""

def require_vim(method):
    """Wrapper to import vim before running method."""
    def wrapped(*args, **kwargs):
        try:
            global vim
            import vim
        except ImportError:
            return
        return method(*args, **kwargs)
    return wrapped


@require_vim
def init_vim():
    """Initialize vim plugin."""
    vim.command("map <silent> <leader>mr :py3 vim_mrglab.load_reviews()<enter>")
    vim.command("map <silent> <leader>omr :py3 vim_mrglab.load_review()<enter>")

@require_vim
def load_review():
    """Load reviews."""
    current_window_number = vim.current.window.number
    current_file = vim.current.buffer.name
    current_line = vim.current.range.start 

    git_info = get_git_info('.')
    current_file = current_file.replace(git_info['root'] + '/', '')
    repo_name = git_info['repo_name']
    discussions = get_mr_file_discussions(
        current_file,
        git_info['repo_name'],
        git_info['branch'],
    )
    mr = discussions['mr']
    notes = discussions['notes']
    rnotes = []
    for note_index, note in enumerate(notes):
        line = note['position']['new_line']
        if (line - 1) != current_line:
            continue
        rnotes.append(note)

    vim.command(f"belowright new")
    vim.command("setlocal buftype=nofile")
    vim.command("setlocal bufhidden=hide")
    vim.command("setlocal noswapfile")

    messages = jinja2.Environment().from_string(discussions_template).render(
        notes=rnotes,
        discussion=discussions['discussions']['discussion'],
        mr=mr
    )
    vim.current.buffer[:] = messages.splitlines()
    vim.command("norm ")


@require_vim
def load_reviews():
    """Load reviews."""
    # topleft vnew | 0read ! git show master:README.md
    current_window_number = vim.current.window.number
    current_file = vim.current.buffer.name

    git_info = get_git_info('.')
    current_file = current_file.replace(git_info['root'] + '/', '')
    repo_name = git_info['repo_name']
    discussions = get_mr_file_discussions(
        current_file,
        git_info['repo_name'],
        git_info['branch'],
    )
    mr = discussions['mr']
    notes = discussions['notes']
    discs = discussions['discussions']
    pprint.pprint(discs['discussion'].attributes)

    target_branch = mr.attributes['target_branch']

    vim.command("diffthis")

    # Load file from git as a scratch.
    vim.command(f"topleft vnew | 0read ! git show {target_branch}:{current_file}")
    vim.command("setlocal buftype=nofile")
    vim.command("setlocal bufhidden=hide")
    vim.command("setlocal noswapfile")

    vim.command("diffthis")

    # Go back to original window
    vim.command("norm ")

    vim.command("sign unplace *")
    vim.command("sign define MR text=IS texthl=Seach linehl=DiffText")

    for note_index, note in enumerate(notes):
        line = note['position']['new_line']
        command = (
            f"sign place {note_index + 1} line={line} "
            f"name=MR file={current_file}"
        )
        vim.command(command)




def get_git_info(repo_location):
    """Get git info.

    Returns:
        Dict[str, Any]: A mapping of with info from git.

    """
    repo = git.Repo('.')
    repo_root = repo.git.rev_parse("--show-toplevel")
    gl_remotes = [
        remote
        for remote in list(repo.remote().urls)
        if 'gitlab.com' in remote
    ]
    repo_name = gl_remotes[0].split(':')[1].split('.')[0]
    branch = repo.active_branch.name
    return {
        "repo_name": repo_name,
        "branch": branch,
        "root": repo_root,
    }


@require_vim
def get_mr_file_discussions(filename, repo_name, branch):

    sites = vim.eval('g:mrglab_sites')
    url = list(sites.keys())[0]
    token = sites[url]

    gl = gitlab.Gitlab(
        url=url,
        private_token=token,
    )
    proj = gl.projects.get(repo_name)


    # Only reading first MR
    current_mr = None
    for mr in proj.mergerequests.list():
        attrs = mr.attributes
        if branch != attrs['source_branch']:
            continue
        current_mr = proj.mergerequests.get(mr.iid)
        break

    file_notes = []
    r = {}
    for d in current_mr.discussions.list(all=True):
        for note in d.attributes['notes']:
            if 'position' not in note:
                # Not a line note
                continue

            if not os.path.samefile(note['position']['new_path'], filename):
                continue
            r.setdefault('mr', mr)
            r.setdefault('discussions', {}).setdefault(
                'discussion', mr.discussions.get(d.id)
            )
            r.setdefault(
                'discussions', {}).setdefault('notes', []).append(note)
            r.setdefault(
                'notes', []).append(note)

            file_notes.append(note)

    return r


def test():
    repo_location = '.'
    git_info = get_git_info(repo_location)
    repo_name = git_info['repo_name']
    branch = git_info['branch']
    for dp, dirnames, filenames in os.walk(repo_location):
        if '/.git' in dp:
            continue
        for filename in filenames:
            fp = os.path.join(dp, filename)
            d = get_mr_file_discussions(fp, repo_name, branch)
            pprint.pprint(d)
            notes = d['notes']
            pprint.pprint(notes)


if __name__ == '__main__':
    test()
