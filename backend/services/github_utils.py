import json

import requests

def _read_token(file_path):
    with open(file_path, 'r') as f:
        return f.read().strip()

def _github_login(token):
    url = 'https://api.github.com/user'
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user = response.json()
        print(f"Login successful! User: {user['login']}")
    else:
        print(f"Login error! Status code: {response.status_code}")
        print(response.text)

def get_repos(token):
    url_repos = 'https://api.github.com/user/repos'
    headers = {'Authorization': f'token {token}'}
    params = {'per_page': 100}
    response = requests.get(url_repos, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error fetching repos! Status code: {response.status_code}")
        print(response.text)
        return []
    return response.json()

def _build_commit_data(name, date, msg, sha, files):
    import re
    commit_data = {
        'repo': name,
        'date': date,
        'msg': msg,
        'sha': sha,
        'files': []
    }
    hunk_header_re = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
    if date and msg and sha and files:
        for f in files:
            file_info = {
                'filename_after': f['filename'],
                'filename_before': f['filename'],
                'status': f['status'],
                'patch': f.get('patch', ''),
                'hunks': []
            }
            if f['status'] == 'modified' and 'patch' in f:
                lines = f['patch'].splitlines()
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if line.startswith('@@'):
                        m = hunk_header_re.match(line)
                        if not m:
                            i += 1
                            continue
                        old_start = int(m.group(1))
                        old_len = int(m.group(2) or '1')
                        new_start = int(m.group(3))
                        new_len = int(m.group(4) or '1')
                        hunk = {
                            'old_start': old_start,
                            'old_end': old_start + old_len - 1,
                            'new_start': new_start,
                            'new_end': new_start + new_len - 1,
                            'lines': []
                        }
                        i += 1
                        old_line_num = old_start
                        new_line_num = new_start
                        while i < len(lines) and not lines[i].startswith('@@'):
                            l = lines[i]
                            if l.startswith('+') and not l.startswith('+++'):
                                hunk['lines'].append({
                                    'type': 'added',
                                    'value': l[1:],
                                    'old_lineno': None,
                                    'new_lineno': new_line_num
                                })
                                new_line_num += 1
                            elif l.startswith('-') and not l.startswith('---'):
                                hunk['lines'].append({
                                    'type': 'removed',
                                    'value': l[1:],
                                    'old_lineno': old_line_num,
                                    'new_lineno': None
                                })
                                old_line_num += 1
                            else:
                                hunk['lines'].append({
                                    'type': 'unchanged',
                                    'value': l[1:] if l.startswith(' ') else l,
                                    'old_lineno': old_line_num,
                                    'new_lineno': new_line_num
                                })
                                old_line_num += 1
                                new_line_num += 1
                            i += 1
                        file_info['hunks'].append(hunk)
                    else:
                        i += 1
            commit_data['files'].append(file_info)
    return commit_data


def _get_commits_range(token, owner, repo_name, start, end):
    """
    Returns a list of commits from index start to end (inclusive, zero-based, counting from the latest commit).
    start=0 means the latest commit, end=1 means the second latest, etc.
    """
    # GitHub API returns commits in reverse chronological order (latest first)
    per_page = end + 1
    url_commits = f"https://api.github.com/repos/{owner}/{repo_name}/commits"
    headers = {'Authorization': f'token {token}'}
    params = {'per_page': per_page, 'page': 1}
    response = requests.get(url_commits, headers=headers, params=params)
    if response.status_code == 200 and response.json():
        commits = response.json()
        # slice from start to end+1 (inclusive)
        return commits[start:end+1]
    else:
        return []

def get_commits_range(token, owner, repo_name, start, end):
    commits = _get_commits_range(token, owner, repo_name, start, end)
    commits_info = []
    for commit in commits:
        msg = commit['commit']['message']
        date = commit['commit']['committer']['date']
        sha = commit['sha']
        # Get commit details for file changes
        url_commit_details = f"https://api.github.com/repos/{owner}/{repo_name}/commits/{sha}"
        headers = {'Authorization': f'token {token}'}
        details_resp = requests.get(url_commit_details, headers=headers)
        files = []
        if details_resp.status_code == 200:
            details = details_resp.json()
            files = details.get('files', [])
        commit_data = _build_commit_data(repo_name, date, msg, sha, files)
        commits_info.append(commit_data)
    return commits_info





