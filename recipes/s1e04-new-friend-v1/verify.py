"""Read-only integrity check for the S1E04 accepted references; no GPU/network/TTS."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(2 ** 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    frozen = json.loads((HERE / 'frozen-files.json').read_text())
    recipe = json.loads((HERE / 'recipe.json').read_text())
    errors = []
    for name, expected in frozen['files'].items():
        p = HERE / name
        if not p.is_file():
            errors.append('missing ' + name)
        elif sha(p) != expected:
            errors.append('changed ' + name)
    for master in recipe['scene_masters']:
        p = (HERE / master['path']).resolve()
        if not p.is_file():
            errors.append('missing master ' + master['path'])
        elif sha(p) != master['sha256']:
            errors.append('changed master ' + master['path'])
    video = (HERE / recipe['accepted_video']['path']).resolve()
    if not video.is_file():
        errors.append('missing accepted video ' + recipe['accepted_video']['path'])
    elif sha(video) != recipe['accepted_video']['sha256']:
        errors.append('changed accepted video (user-accepted bytes must stay)')
    d = recipe['delivery']
    assert sum(recipe['take_frames']) + d['op_frames'] == d['frames'] == 1026, 'timeline mismatch'
    assert d['fps'] == 24 and recipe['status'] == 'user_accepted'
    if errors:
        raise SystemExit('\n'.join(errors))
    print('Verified {} frozen files, {} masters, the accepted movie and the {}-frame S1E04 timeline.'.format(
        len(frozen['files']), len(recipe['scene_masters']), d['frames']))


if __name__ == '__main__':
    main()
