# Should be imported first before anything else.
from vim_mrglab import virtualenv

# Don't import vim yet, so we can run commands outside of vim too.
vim = None


import os
import gitlab
import git
import jinja2


_buffer_keybindings = {
    'mr-list': {
        '<Enter>': 'ViewRequest()',
        'l': 'ViewRequest()',
        'v': 'ViewRequest()',
        'j': 'MoveDown("reviews-list")',
        'm': 'LoadMore("")',
        'G': 'LoadMore("1")',
        },
    'reviews-request': {
        '<Enter>': 'LoadDiff()',
        '<Esc>': 'TabClose()',
        'q': 'TabClose()',
        'R': 'ViewDraftReview()',
        },
    'diff': {
        '<Esc>': 'TabClose()',
        'q': 'TabClose()',
        ('v','c'): 'MakeComment()',
        ('n','c'): 'MakeComment()',
        'R': 'ViewDraftReview()',
        },
    'diff-comment': {
        'y': 'SaveComment()',
        'n': 'TabClose()',
        'q': 'TabClose()',
        },
    'review-draft': {
        '<Esc>': 'TabClose()',
        'q': 'TabClose()',
        'b': 'EditBody("h")',
        'B': 'EditBody("H")',
        'y': 'SubmitReview()',
        }
    }
mrs_template = """{%- for mr in mrs -%}
{{ mr.attributes.reference }} [{{mr.attributes.state}}] {{ mr.attributes.title }} - {{ mr.attributes.description[:20] }} {{ mr.attributes.user_notes_count }} ({{- mr.attributes.author.name }})
{% endfor -%}
"""

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
    vim.command("command LoadMergeRequests :py3 vim_mrglab.load_merge_requests()")
    """
    command LoadReviewBoard call rboard#LoadReviewBoard()
    map <leader>lr :LoadReviewBoard<CR>
    """


@require_vim
def load_merge_requests():
    """Load merge requests page."""
    merge_requests_buffer = create_named_scratch("MRs", "mr-list", method="tabnew")
    repo_location = '.'
    git_info = get_git_info(repo_location)
    repo_name = git_info['repo_name']
    repo_name = 'inkscape/inkscape'
    gl = get_gitlab_connection()
    proj = gl.projects.get(repo_name)
    mrs = proj.mergerequests.list(get_all=False)
    merge_requests_buffer[:] = render_template(
        mrs_template,
        mrs=mrs,
    ).splitlines()


@require_vim
def create_named_scratch(name, buffertype, method=None):
    """Create a named scratch window."""
    for buffer_index, buffer in enumerate(vim.buffers):
        if buffer.name.endswith(f'[{name}]'):
            vim.command(f"buffer {buffer_index+1}")
            return vim.current.buffer

    method = method or ""
    vim.command(f"{method} new")
    vim.command("setlocal buftype=nofile")
    vim.command("setlocal bufhidden=hide")
    vim.command("setlocal noswapfile")
    vim.command(f"file [{name}]")

    keybindings = _buffer_keybindings.get(buffertype, {})

    #if extra_bindings:
    #   keybindings.update(extra_bindings)

    for key, command in keybindings.items():
        if isinstance(key, tuple):
            vim.command('%snoremap <buffer> %s :call <SID>%s<CR>' % (
                key[0], key[1], command))
        else:
            vim.command('nnoremap <buffer> %s :call <SID>%s<CR>' % (
                key, command))

    return vim.current.buffer


def render_template(template, **payload):
    return jinja2.Environment().from_string(template).render(**payload).encode('utf-8')


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
    messages = render_template(
        discussions_template,
        notes=rnotes,
        discussion=discussions['discussions']['discussion'],
        mr=mr,
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
def get_gitlab_connection():
    """Get GL connection."""
    sites = vim.eval('g:mrglab_sites')
    url = list(sites.keys())[0]
    token = sites[url]

    return gitlab.Gitlab(
        url=url,
        private_token=token,
    )

@require_vim
def get_mr_file_discussions(filename, repo_name, branch):

    gl = get_gitlab_connection()
    proj = gl.projects.get(repo_name)


    # Only reading first MR
    current_mr = None
    for mr in proj.mergerequests.list(get_all=False):
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
            notes = d['notes']


if __name__ == '__main__':
    test()
